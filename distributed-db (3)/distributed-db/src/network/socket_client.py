import socket
import logging
import json
from typing import List
from ..core.models import Message, NodeInfo, CommunicationType
from ..core.checksum import ChecksumValidator


class SocketClient:
    """Cliente de sockets para enviar mensagens para outros nós"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def send_message(self, message: Message, target_node: NodeInfo) -> bool:
        """
        Envia mensagem para um nó específico (UNICAST)
        
        Args:
            message: Mensagem a ser enviada
            target_node: Nó de destino
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            # Serializa mensagem
            message_str = message.to_json()
            message_dict = json.loads(message_str)
            
            # Adiciona checksum
            message_dict = ChecksumValidator.add_checksum(message_dict)
            message_str = json.dumps(message_dict)
            
            # Cria socket e conecta
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)  # Timeout de 5 segundos
                sock.connect((target_node.host, target_node.port))
                
                # Envia mensagem (adiciona \n como delimitador)
                sock.sendall((message_str + '\n').encode('utf-8'))
                
            self.logger.debug(f"Mensagem {message.message_type.value} enviada para nó {target_node.node_id}")
            return True
            
        except socket.timeout:
            self.logger.error(f"Timeout ao enviar mensagem para nó {target_node.node_id}")
            return False
        except ConnectionRefusedError:
            self.logger.error(f"Conexão recusada pelo nó {target_node.node_id}")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao enviar mensagem para nó {target_node.node_id}: {e}")
            return False
    
    def broadcast_message(self, message: Message, nodes: List[NodeInfo], exclude_self: int = None) -> int:
        """
        Envia mensagem para todos os nós (BROADCAST)
        
        Args:
            message: Mensagem a ser enviada
            nodes: Lista de todos os nós
            exclude_self: ID do nó a ser excluído (geralmente o próprio nó)
            
        Returns:
            Número de nós que receberam com sucesso
        """
        success_count = 0
        
        for node in nodes:
            if exclude_self and node.node_id == exclude_self:
                continue
            
            if self.send_message(message, node):
                success_count += 1
        
        self.logger.info(f"Broadcast: {success_count}/{len(nodes)} nós alcançados")
        return success_count
    
    def multicast_message(self, message: Message, target_nodes: List[NodeInfo]) -> int:
        """
        Envia mensagem para um grupo específico de nós (MULTICAST)
        
        Args:
            message: Mensagem a ser enviada
            target_nodes: Lista de nós de destino
            
        Returns:
            Número de nós que receberam com sucesso
        """
        success_count = 0
        
        for node in target_nodes:
            if self.send_message(message, node):
                success_count += 1
        
        self.logger.info(f"Multicast: {success_count}/{len(target_nodes)} nós alcançados")
        return success_count
    
    def send_by_type(self, message: Message, all_nodes: List[NodeInfo], sender_id: int) -> int:
        """
        Envia mensagem de acordo com o tipo de comunicação especificado
        
        Args:
            message: Mensagem a ser enviada
            all_nodes: Lista de todos os nós disponíveis
            sender_id: ID do nó remetente
            
        Returns:
            Número de nós que receberam com sucesso
        """
        if message.communication_type == CommunicationType.UNICAST:
            # Envia para um nó específico
            if message.target_nodes and len(message.target_nodes) > 0:
                target_id = message.target_nodes[0]
                target_node = next((n for n in all_nodes if n.node_id == target_id), None)
                if target_node:
                    return 1 if self.send_message(message, target_node) else 0
            return 0
            
        elif message.communication_type == CommunicationType.BROADCAST:
            # Envia para todos exceto o remetente
            return self.broadcast_message(message, all_nodes, exclude_self=sender_id)
            
        elif message.communication_type == CommunicationType.MULTICAST:
            # Envia para grupo específico
            if message.target_nodes:
                target_nodes = [n for n in all_nodes if n.node_id in message.target_nodes]
                return self.multicast_message(message, target_nodes)
            return 0
        
        return 0
