import logging
from typing import List, Callable
from datetime import datetime
from ..core.models import Message, MessageType, NodeInfo, CommunicationType
from ..database.mysql_manager import MySQLManager


class Replicator:
    """
    Gerencia replicação de alterações entre nós
    Garante que todas as alterações sejam propagadas
    """
    
    def __init__(self, node_id: int, db_manager: MySQLManager, send_message_callback: Callable):
        self.node_id = node_id
        self.db_manager = db_manager
        self.send_message = send_message_callback
        self.logger = logging.getLogger(__name__)
        self.pending_replications = {}  # transaction_id -> ack_count
    
    def is_write_query(self, query: str) -> bool:
        """
        Verifica se a query é de escrita (INSERT, UPDATE, DELETE)
        
        Args:
            query: Query SQL
            
        Returns:
            True se é query de escrita, False caso contrário
        """
        query_upper = query.strip().upper()
        write_commands = ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE']
        return any(query_upper.startswith(cmd) for cmd in write_commands)
    
    def replicate_query(self, query: str, transaction_id: str, all_nodes: List[NodeInfo]) -> bool:
        """
        Replica uma query para todos os outros nós
        
        Args:
            query: Query SQL para replicar
            transaction_id: ID da transação
            all_nodes: Lista de todos os nós
            
        Returns:
            True se replicação foi iniciada, False caso contrário
        """
        if not self.is_write_query(query):
            self.logger.debug("Query SELECT não precisa de replicação")
            return False
        
        self.logger.info(f"Iniciando replicação da query: {query[:50]}...")
        
        # Cria mensagem de replicação
        replicate_msg = Message(
            message_type=MessageType.REPLICATE,
            sender_id=self.node_id,
            transaction_id=transaction_id,
            query=query,
            timestamp=datetime.now(),
            communication_type=CommunicationType.BROADCAST
        )
        
        # Envia para todos os outros nós
        success_count = self.send_message(replicate_msg, all_nodes)
        
        # Registra replicação pendente
        self.pending_replications[transaction_id] = {
            'query': query,
            'expected_acks': len(all_nodes) - 1,  # Todos exceto este nó
            'received_acks': 0,
            'timestamp': datetime.now()
        }
        
        self.logger.info(f"Replicação enviada para {success_count} nós")
        return success_count > 0
    
    def handle_replication_request(self, message: Message) -> bool:
        """
        Processa requisição de replicação de outro nó
        
        Args:
            message: Mensagem de replicação
            
        Returns:
            True se replicação foi bem-sucedida, False caso contrário
        """
        query = message.query
        transaction_id = message.transaction_id
        sender_id = message.sender_id
        
        self.logger.info(f"Replicando query do nó {sender_id}: {query[:50]}...")
        
        try:
            # Executa query localmente
            success, data, error, rows_affected = self.db_manager.execute_query(query)
            
            if success:
                self.logger.info(f"Replicação executada com sucesso - {rows_affected} linhas afetadas")
                return True
            else:
                self.logger.error(f"Erro na replicação: {error}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exceção ao replicar query: {e}")
            return False
    
    def send_replication_ack(self, transaction_id: str, sender_id: int, success: bool, all_nodes: List[NodeInfo]):
        """
        Envia ACK de replicação de volta ao nó originador
        
        Args:
            transaction_id: ID da transação
            sender_id: ID do nó que iniciou a replicação
            success: Se a replicação foi bem-sucedida
            all_nodes: Lista de todos os nós
        """
        ack_msg = Message(
            message_type=MessageType.REPLICATE_ACK,
            sender_id=self.node_id,
            transaction_id=transaction_id,
            data={'success': success},
            timestamp=datetime.now(),
            communication_type=CommunicationType.UNICAST,
            target_nodes=[sender_id]
        )
        
        self.send_message(ack_msg, all_nodes)
        self.logger.debug(f"ACK de replicação enviado para nó {sender_id}")
    
    def handle_replication_ack(self, message: Message) -> bool:
        """
        Processa ACK de replicação
        
        Args:
            message: Mensagem de ACK
            
        Returns:
            True se todas as replicações foram confirmadas, False caso contrário
        """
        transaction_id = message.transaction_id
        sender_id = message.sender_id
        success = message.data.get('success', False) if message.data else False
        
        if transaction_id not in self.pending_replications:
            self.logger.warning(f"ACK recebido para transação desconhecida: {transaction_id}")
            return False
        
        replication = self.pending_replications[transaction_id]
        replication['received_acks'] += 1
        
        status = "sucesso" if success else "falha"
        self.logger.info(
            f"ACK de replicação do nó {sender_id} ({status}) - "
            f"{replication['received_acks']}/{replication['expected_acks']}"
        )
        
        # Verifica se todas as replicações foram confirmadas
        if replication['received_acks'] >= replication['expected_acks']:
            self.logger.info(f"Todas as replicações confirmadas para transação {transaction_id}")
            del self.pending_replications[transaction_id]
            return True
        
        return False
    
    def get_pending_replications_count(self) -> int:
        """Retorna número de replicações pendentes"""
        return len(self.pending_replications)
    
    def cleanup_old_replications(self, timeout_seconds: int = 60):
        """
        Remove replicações antigas que não receberam todos os ACKs
        
        Args:
            timeout_seconds: Timeout em segundos
        """
        current_time = datetime.now()
        to_remove = []
        
        for tid, replication in self.pending_replications.items():
            elapsed = (current_time - replication['timestamp']).total_seconds()
            if elapsed > timeout_seconds:
                self.logger.warning(
                    f"Replicação {tid} expirou - "
                    f"recebidos {replication['received_acks']}/{replication['expected_acks']} ACKs"
                )
                to_remove.append(tid)
        
        for tid in to_remove:
            del self.pending_replications[tid]
