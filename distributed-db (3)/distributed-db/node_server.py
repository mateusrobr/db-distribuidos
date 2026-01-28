#!/usr/bin/env python3
"""
Servidor de Nó do Banco de Dados Distribuído
Executa em cada máquina do DDB
"""

import sys
import json
import logging
import threading
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from src.core.models import (
    NodeInfo, NodeStatus, Message, MessageType, 
    CommunicationType, QueryResult
)
from src.database.mysql_manager import MySQLManager
from src.database.transaction_manager import TransactionManager
from src.network.socket_server import SocketServer
from src.network.socket_client import SocketClient
from src.coordination.coordinator import Coordinator
from src.replication.replicator import Replicator
from src.load_balancer.balancer import LoadBalancer


class DistributedDBNode:
    """Nó do Banco de Dados Distribuído"""
    
    def __init__(self, config_file: str, node_id: int):
        self.node_id = node_id
        self.setup_logging()
        
        # Carrega configuração
        self.config = self.load_config(config_file)
        self.node_config = self.get_node_config(node_id)
        
        # Componentes
        self.db_manager = None
        self.transaction_manager = None
        self.socket_server = None
        self.socket_client = SocketClient()
        self.coordinator = None
        self.replicator = None
        self.load_balancer = LoadBalancer()
        
        # Estado
        self.all_nodes: List[NodeInfo] = []
        self.running = False
        self.heartbeat_interval = 5  # segundos
        self.heartbeat_timeout = 15  # segundos
        
        self.logger.info(f"Nó {self.node_id} inicializado")
    
    def setup_logging(self):
        """Configura logging"""
        logging.basicConfig(
            level=logging.INFO,
            format=f'%(asctime)s [NÓ {self.node_id}] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_config(self, config_file: str) -> dict:
        """Carrega arquivo de configuração"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Configuração carregada de {config_file}")
            return config
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            sys.exit(1)
    
    def get_node_config(self, node_id: int) -> dict:
        """Obtém configuração específica do nó"""
        for node in self.config['nodes']:
            if node['node_id'] == node_id:
                return node
        raise ValueError(f"Configuração para nó {node_id} não encontrada")
    
    def initialize_components(self):
        """Inicializa todos os componentes"""
        # MySQL
        db_config = self.node_config['database']
        self.db_manager = MySQLManager(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            port=db_config.get('port', 3306)
        )
        
        if not self.db_manager.connect():
            self.logger.error("Falha ao conectar ao MySQL")
            sys.exit(1)
        
        # Gerenciadores
        self.transaction_manager = TransactionManager(self.node_id)
        self.replicator = Replicator(
            self.node_id,
            self.db_manager,
            self.send_message_wrapper
        )
        
        # Coordenador
        self.coordinator = Coordinator(
            self.node_id,
            self.send_message_wrapper
        )
        
        # Socket Server
        network_config = self.node_config['network']
        self.socket_server = SocketServer(
            host=network_config['host'],
            port=network_config['port'],
            message_handler=self.handle_message
        )
        
        # Inicializa lista de nós
        self.initialize_nodes_list()
        
        self.logger.info("Componentes inicializados")
    
    def initialize_nodes_list(self):
        """Inicializa lista de nós conhecidos"""
        for node_config in self.config['nodes']:
            node_info = NodeInfo(
                node_id=node_config['node_id'],
                host=node_config['network']['host'],
                port=node_config['network']['port'],
                status=NodeStatus.ACTIVE,
                last_heartbeat=datetime.now()
            )
            self.all_nodes.append(node_info)
        
        self.logger.info(f"{len(self.all_nodes)} nós registrados")
    
    def start(self):
        """Inicia o nó"""
        self.running = True
        
        # Inicia socket server
        self.socket_server.start()
        
        # Inicia threads de manutenção
        threading.Thread(target=self.heartbeat_loop, daemon=True).start()
        threading.Thread(target=self.check_nodes_health, daemon=True).start()
        
        # Aguarda um pouco e inicia eleição
        time.sleep(2)
        self.coordinator.start_election(self.all_nodes)
        
        self.logger.info(f"*** Nó {self.node_id} ATIVO ***")
        
        # Mantém servidor rodando
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Interrompido pelo usuário")
            self.stop()
    
    def stop(self):
        """Para o nó"""
        self.logger.info("Parando nó...")
        self.running = False
        
        if self.socket_server:
            self.socket_server.stop()
        
        if self.db_manager:
            self.db_manager.disconnect()
        
        self.logger.info("Nó parado")
    
    def heartbeat_loop(self):
        """Envia heartbeats periódicos"""
        while self.running:
            self.send_heartbeat()
            time.sleep(self.heartbeat_interval)
    
    def send_heartbeat(self):
        """Envia heartbeat para todos os nós"""
        heartbeat_msg = Message(
            message_type=MessageType.HEARTBEAT,
            sender_id=self.node_id,
            timestamp=datetime.now(),
            communication_type=CommunicationType.BROADCAST,
            data={'is_coordinator': self.coordinator.is_coordinator}
        )
        
        self.send_message_wrapper(heartbeat_msg, self.all_nodes)
    
    def check_nodes_health(self):
        """Verifica saúde dos nós periodicamente"""
        while self.running:
            time.sleep(self.heartbeat_interval * 2)
            
            current_time = datetime.now()
            timeout = timedelta(seconds=self.heartbeat_timeout)
            
            for node in self.all_nodes:
                if node.node_id == self.node_id:
                    continue
                
                if node.last_heartbeat:
                    elapsed = current_time - node.last_heartbeat
                    
                    if elapsed > timeout and node.status == NodeStatus.ACTIVE:
                        self.logger.warning(f"Nó {node.node_id} sem heartbeat há {elapsed.seconds}s - marcando como INATIVO")
                        node.status = NodeStatus.INACTIVE
                        
                        # Se era o coordenador, inicia eleição
                        if node.node_id == self.coordinator.current_coordinator:
                            self.logger.warning("Coordenador falhou - iniciando eleição")
                            self.coordinator.start_election(self.all_nodes)
    
    def handle_message(self, message: Message):
        """
        Processa mensagem recebida
        
        Args:
            message: Mensagem recebida
        """
        try:
            handler_map = {
                MessageType.HEARTBEAT: self.handle_heartbeat,
                MessageType.QUERY: self.handle_query,
                MessageType.PREPARE: self.handle_prepare,
                MessageType.COMMIT: self.handle_commit,
                MessageType.ABORT: self.handle_abort,
                MessageType.REPLICATE: self.handle_replicate,
                MessageType.REPLICATE_ACK: self.handle_replicate_ack,
                MessageType.ELECTION: self.handle_election,
                MessageType.ACK: self.handle_election_ack,
                MessageType.COORDINATOR: self.handle_coordinator_announcement,
            }
            
            handler = handler_map.get(message.message_type)
            if handler:
                handler(message)
            else:
                self.logger.warning(f"Tipo de mensagem desconhecido: {message.message_type}")
                
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
    
    def handle_heartbeat(self, message: Message):
        """Processa heartbeat"""
        sender_id = message.sender_id
        
        # Atualiza informação do nó
        node = next((n for n in self.all_nodes if n.node_id == sender_id), None)
        if node:
            node.last_heartbeat = datetime.now()
            if node.status != NodeStatus.ACTIVE:
                self.logger.info(f"Nó {sender_id} voltou a ficar ativo")
                node.status = NodeStatus.ACTIVE
    
    def handle_query(self, message: Message):
        """Executa query localmente"""
        query = message.query
        transaction_id = message.transaction_id
        
        self.logger.info(f"Executando query local: {query[:50]}...")
        
        # Executa query
        success, data, error, rows_affected = self.db_manager.execute_query(query)
        
        # Incrementa contador
        me = next(n for n in self.all_nodes if n.node_id == self.node_id)
        self.load_balancer.increment_query_count(me)
        
        # Se foi escrita bem-sucedida, COMMITA ANTES
        if success and self.replicator.is_write_query(query):
            self.db_manager.commit()
        
        # Prepara resposta
        result = QueryResult(
            success=success,
            data=data,
            error=error,
            node_id=self.node_id,
            rows_affected=rows_affected
        )
        
        # ENVIA RESPOSTA IMEDIATAMENTE (antes de replicar!)
        response_msg = Message(
            message_type=MessageType.QUERY_RESPONSE,
            sender_id=self.node_id,
            transaction_id=transaction_id,
            data=result.to_dict(),
            timestamp=datetime.now(),
            communication_type=CommunicationType.UNICAST,
            target_nodes=[message.sender_id]
        )
        
        self.send_message_wrapper(response_msg, self.all_nodes)
        
        # DEPOIS replica (assíncrono em relação ao cliente)
        if success and self.replicator.is_write_query(query):
            self.replicator.replicate_query(query, transaction_id, self.all_nodes)
    
    def handle_prepare(self, message: Message):
        """Fase PREPARE do 2PC"""
        transaction_id = message.transaction_id
        query = message.query
        
        # Tenta preparar transação
        self.db_manager.begin_transaction()
        success, _, error, _ = self.db_manager.execute_query(query)
        
        # Vota
        vote = success
        self.transaction_manager.vote_on_prepare(transaction_id, vote)
        
        # Envia voto
        vote_msg = Message(
            message_type=MessageType.ACK,
            sender_id=self.node_id,
            transaction_id=transaction_id,
            data={'vote': vote, 'error': error},
            timestamp=datetime.now(),
            communication_type=CommunicationType.UNICAST,
            target_nodes=[message.sender_id]
        )
        
        self.send_message_wrapper(vote_msg, self.all_nodes)
    
    def handle_commit(self, message: Message):
        """Fase COMMIT do 2PC"""
        self.db_manager.commit()
        self.logger.info(f"Transação {message.transaction_id} commitada")
    
    def handle_abort(self, message: Message):
        """Fase ABORT do 2PC"""
        self.db_manager.rollback()
        self.logger.info(f"Transação {message.transaction_id} abortada")
    
    def handle_replicate(self, message: Message):
        """Processa requisição de replicação"""
        success = self.replicator.handle_replication_request(message)
        
        if success:
            self.db_manager.commit()
        else:
            self.db_manager.rollback()
        
        # Envia ACK
        self.replicator.send_replication_ack(
            message.transaction_id,
            message.sender_id,
            success,
            self.all_nodes
        )
    
    def handle_replicate_ack(self, message: Message):
        """Processa ACK de replicação"""
        self.replicator.handle_replication_ack(message)
    
    def handle_election(self, message: Message):
        """Processa mensagem de eleição"""
        self.coordinator.handle_election_message(message, self.all_nodes)
    
    def handle_election_ack(self, message: Message):
        """Processa ACK de eleição"""
        self.coordinator.handle_election_ack(message)
    
    def handle_coordinator_announcement(self, message: Message):
        """Processa anúncio de coordenador"""
        self.coordinator.handle_coordinator_announcement(message)
    
    def send_message_wrapper(self, message: Message, all_nodes: List[NodeInfo]) -> int:
        """Wrapper para enviar mensagens"""
        return self.socket_client.send_by_type(message, all_nodes, self.node_id)


def main():
    parser = argparse.ArgumentParser(description='Servidor de Nó do DDB')
    parser.add_argument('--config', required=True, help='Arquivo de configuração JSON')
    parser.add_argument('--node-id', type=int, required=True, help='ID do nó')
    
    args = parser.parse_args()
    
    node = DistributedDBNode(args.config, args.node_id)
    node.initialize_components()
    node.start()


if __name__ == '__main__':
    main()
