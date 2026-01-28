#!/usr/bin/env python3
"""
Aplicação Cliente para o Banco de Dados Distribuído
Interface simples para executar queries
"""

import sys
import json
import socket
import argparse
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from src.core.models import Message, MessageType, CommunicationType, QueryResult
from src.core.checksum import ChecksumValidator


class DDBClient:
    """Cliente para acessar o DDB"""
    
    def __init__(self, config_file: str):
        self.config = self.load_config(config_file)
        self.nodes = self.config['nodes']
        self.current_node_index = 0
        print(f"Cliente DDB inicializado com {len(self.nodes)} nós disponíveis")
    
    def load_config(self, config_file: str) -> dict:
        """Carrega arquivo de configuração"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
            sys.exit(1)
    
    def get_next_node(self) -> dict:
        """Obtém próximo nó (Round-Robin)"""
        node = self.nodes[self.current_node_index]
        self.current_node_index = (self.current_node_index + 1) % len(self.nodes)
        return node
    
    def send_query(self, query: str, target_node: Optional[dict] = None) -> Optional[Dict[str, Any]]:
        """
        Envia query para o DDB
        
        Args:
            query: Query SQL
            target_node: Nó específico (opcional)
            
        Returns:
            Resultado da query ou None
        """
        if target_node is None:
            target_node = self.get_next_node()
        
        transaction_id = str(uuid.uuid4())
        
        # Cria mensagem
        message = Message(
            message_type=MessageType.QUERY,
            sender_id=9999,  # ID especial para cliente
            transaction_id=transaction_id,
            query=query,
            timestamp=datetime.now(),
            communication_type=CommunicationType.UNICAST,
            target_nodes=[target_node['node_id']]
        )
        
        # Serializa e adiciona checksum
        message_str = message.to_json()
        message_dict = json.loads(message_str)
        message_dict = ChecksumValidator.add_checksum(message_dict)
        message_str = json.dumps(message_dict)
        
        # Conecta e envia
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(30)
                
                network = target_node['network']
                sock.connect((network['host'], network['port']))
                
                # Envia query
                sock.sendall((message_str + '\n').encode('utf-8'))
                
                # Aguarda resposta
                buffer = ""
                while '\n' not in buffer:
                    data = sock.recv(4096).decode('utf-8')
                    if not data:
                        break
                    buffer += data
                
                if '\n' in buffer:
                    response_str = buffer.split('\n')[0]
                    response_dict = json.loads(response_str)
                    
                    # Valida checksum
                    if not ChecksumValidator.verify_message(response_dict):
                        print("⚠ Aviso: Checksum inválido na resposta")
                    
                    response = Message.from_json(response_str)
                    return response.data
                
                return None
                
        except socket.timeout:
            print(f"✗ Timeout ao conectar ao nó {target_node['node_id']}")
            return None
        except ConnectionRefusedError:
            print(f"✗ Conexão recusada pelo nó {target_node['node_id']}")
            return None
        except Exception as e:
            print(f"✗ Erro ao enviar query: {e}")
            return None
    
    def execute_query(self, query: str):
        """
        Executa query e exibe resultado
        
        Args:
            query: Query SQL
        """
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        start_time = datetime.now()
        result_data = self.send_query(query)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result_data is None:
            print("✗ Falha ao executar query")
            return
        
        # Converte para QueryResult
        result = QueryResult(
            success=result_data.get('success', False),
            data=result_data.get('data'),
            error=result_data.get('error'),
            node_id=result_data.get('node_id'),
            rows_affected=result_data.get('rows_affected')
        )
        
        # Exibe resultado
        print(f"\n📊 Resultado:")
        print(f"  • Nó executado: {result.node_id}")
        print(f"  • Tempo: {elapsed:.3f}s")
        print(f"  • Status: {'✓ Sucesso' if result.success else '✗ Erro'}")
        
        if result.success:
            if result.data:
                print(f"  • Registros retornados: {len(result.data)}")
                print(f"\n  Dados:")
                for i, row in enumerate(result.data[:10], 1):  # Limita a 10 linhas
                    print(f"    {i}. {row}")
                if len(result.data) > 10:
                    print(f"    ... e mais {len(result.data) - 10} registros")
            elif result.rows_affected is not None:
                print(f"  • Linhas afetadas: {result.rows_affected}")
        else:
            print(f"  • Erro: {result.error}")
        
        print(f"{'='*80}\n")
    
    def interactive_mode(self):
        """Modo interativo para executar queries"""
        print("\n" + "="*80)
        print("  CLIENTE DO BANCO DE DADOS DISTRIBUÍDO")
        print("="*80)
        print("\nComandos:")
        print("  - Digite uma query SQL para executar")
        print("  - 'exit' ou 'quit' para sair")
        print("  - 'help' para ajuda")
        print("  - 'nodes' para listar nós")
        print("  - 'stats' para estatísticas")
        print("\n" + "="*80 + "\n")
        
        while True:
            try:
                query = input("DDB> ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['exit', 'quit']:
                    print("Saindo...")
                    break
                
                if query.lower() == 'help':
                    self.show_help()
                    continue
                
                if query.lower() == 'nodes':
                    self.show_nodes()
                    continue
                
                if query.lower() == 'stats':
                    self.show_stats()
                    continue
                
                # Executa query
                self.execute_query(query)
                
            except KeyboardInterrupt:
                print("\n\nInterrompido pelo usuário")
                break
            except Exception as e:
                print(f"Erro: {e}")
    
    def show_help(self):
        """Exibe ajuda"""
        print("\n" + "="*80)
        print("  AJUDA")
        print("="*80)
        print("\nExemplos de queries:")
        print("  SELECT * FROM tabela;")
        print("  INSERT INTO tabela (col1, col2) VALUES ('val1', 'val2');")
        print("  UPDATE tabela SET col1='novo_valor' WHERE id=1;")
        print("  DELETE FROM tabela WHERE id=1;")
        print("\nComandos especiais:")
        print("  nodes - Lista nós disponíveis")
        print("  stats - Exibe estatísticas")
        print("  help  - Exibe esta ajuda")
        print("  exit  - Sai da aplicação")
        print("="*80 + "\n")
    
    def show_nodes(self):
        """Exibe lista de nós"""
        print("\n" + "="*80)
        print("  NÓS DO DDB")
        print("="*80)
        for node in self.nodes:
            network = node['network']
            print(f"\nNó {node['node_id']}:")
            print(f"  • Endereço: {network['host']}:{network['port']}")
        print("="*80 + "\n")
    
    def show_stats(self):
        """Exibe estatísticas básicas"""
        print("\n" + "="*80)
        print("  ESTATÍSTICAS")
        print("="*80)
        print(f"\nNós disponíveis: {len(self.nodes)}")
        print(f"Nó atual (Round-Robin): {self.current_node_index}")
        print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Cliente do DDB')
    parser.add_argument('--config', required=True, help='Arquivo de configuração JSON')
    parser.add_argument('--query', help='Query SQL para executar (modo não-interativo)')
    
    args = parser.parse_args()
    
    client = DDBClient(args.config)
    
    if args.query:
        # Modo não-interativo
        client.execute_query(args.query)
    else:
        # Modo interativo
        client.interactive_mode()


if __name__ == '__main__':
    main()
