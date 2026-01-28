import logging
import threading
import time
from typing import List, Optional, Callable
from datetime import datetime
from ..core.models import Message, MessageType, NodeInfo, NodeStatus, CommunicationType


class Coordinator:
    """
    Implementa coordenação e algoritmo de eleição Bully
    O nó com maior ID sempre se torna coordenador
    """
    
    def __init__(self, node_id: int, send_message_callback: Callable[[Message, List[NodeInfo]], int]):
        self.node_id = node_id
        self.current_coordinator: Optional[int] = None
        self.is_coordinator = False
        self.election_in_progress = False
        self.logger = logging.getLogger(__name__)
        self.send_message = send_message_callback
        self.election_timeout = 5  # segundos
        self.election_responses = set()
        self.election_lock = threading.Lock()
    
    def start_election(self, all_nodes: List[NodeInfo]):
        """
        Inicia processo de eleição (Bully Algorithm)
        
        Args:
            all_nodes: Lista de todos os nós
        """
        with self.election_lock:
            if self.election_in_progress:
                self.logger.info("Eleição já em andamento, ignorando")
                return
            
            self.election_in_progress = True
            self.election_responses.clear()
        
        self.logger.info(f"Nó {self.node_id} iniciando eleição")
        
        # Encontra nós com ID maior
        higher_nodes = [n for n in all_nodes if n.node_id > self.node_id and n.status == NodeStatus.ACTIVE]
        
        if not higher_nodes:
            # Nenhum nó com ID maior, este nó se torna coordenador
            self._become_coordinator(all_nodes)
            return
        
        # Envia mensagem de eleição para nós com ID maior
        election_msg = Message(
            message_type=MessageType.ELECTION,
            sender_id=self.node_id,
            timestamp=datetime.now(),
            communication_type=CommunicationType.MULTICAST,
            target_nodes=[n.node_id for n in higher_nodes]
        )
        
        self.send_message(election_msg, all_nodes)
        
        # Aguarda respostas por um timeout
        threading.Thread(target=self._wait_for_election_responses, args=(all_nodes,), daemon=True).start()
    
    def _wait_for_election_responses(self, all_nodes: List[NodeInfo]):
        """
        Aguarda respostas da eleição
        
        Args:
            all_nodes: Lista de todos os nós
        """
        time.sleep(self.election_timeout)
        
        with self.election_lock:
            if self.election_responses:
                # Recebeu respostas de nós com ID maior, espera eles assumirem
                self.logger.info(f"Recebidas {len(self.election_responses)} respostas - aguardando coordenador")
                self.election_in_progress = False
            else:
                # Nenhuma resposta, este nó se torna coordenador
                self._become_coordinator(all_nodes)
    
    def _become_coordinator(self, all_nodes: List[NodeInfo]):
        """
        Este nó se torna o coordenador
        
        Args:
            all_nodes: Lista de todos os nós
        """
        self.is_coordinator = True
        self.current_coordinator = self.node_id
        self.election_in_progress = False
        
        self.logger.info(f"*** Nó {self.node_id} é o novo COORDENADOR ***")
        
        # Anuncia para todos os nós
        coordinator_msg = Message(
            message_type=MessageType.COORDINATOR,
            sender_id=self.node_id,
            timestamp=datetime.now(),
            communication_type=CommunicationType.BROADCAST
        )
        
        self.send_message(coordinator_msg, all_nodes)
    
    def handle_election_message(self, message: Message, all_nodes: List[NodeInfo]):
        """
        Responde a mensagem de eleição
        
        Args:
            message: Mensagem de eleição recebida
            all_nodes: Lista de todos os nós
        """
        sender_id = message.sender_id
        
        if sender_id < self.node_id:
            # Nó com ID maior responde e inicia própria eleição
            self.logger.info(f"Recebida eleição do nó {sender_id} (menor que {self.node_id})")
            
            # Envia ACK
            ack_msg = Message(
                message_type=MessageType.ACK,
                sender_id=self.node_id,
                timestamp=datetime.now(),
                communication_type=CommunicationType.UNICAST,
                target_nodes=[sender_id]
            )
            self.send_message(ack_msg, all_nodes)
            
            # Inicia própria eleição
            self.start_election(all_nodes)
        else:
            self.logger.info(f"Recebida eleição do nó {sender_id} (maior que {self.node_id}) - ignorando")
    
    def handle_election_ack(self, message: Message):
        """
        Processa ACK de eleição
        
        Args:
            message: Mensagem de ACK
        """
        with self.election_lock:
            self.election_responses.add(message.sender_id)
            self.logger.info(f"ACK de eleição recebido do nó {message.sender_id}")
    
    def handle_coordinator_announcement(self, message: Message):
        """
        Processa anúncio de novo coordenador
        
        Args:
            message: Mensagem de coordenador
        """
        new_coordinator = message.sender_id
        
        if new_coordinator >= self.node_id or not self.election_in_progress:
            self.current_coordinator = new_coordinator
            self.is_coordinator = False
            self.election_in_progress = False
            self.logger.info(f"Nó {new_coordinator} é o novo coordenador")
        else:
            # Nó com ID menor não pode ser coordenador se este nó está ativo
            self.logger.warning(f"Nó {new_coordinator} anunciou coordenação, mas ID é menor - iniciando eleição")
            # Não fazemos nada aqui, o heartbeat vai detectar e iniciar eleição
    
    def check_coordinator_alive(self, all_nodes: List[NodeInfo]) -> bool:
        """
        Verifica se o coordenador atual está vivo
        
        Args:
            all_nodes: Lista de todos os nós
            
        Returns:
            True se coordenador está vivo, False caso contrário
        """
        if self.current_coordinator is None:
            return False
        
        if self.is_coordinator:
            return True
        
        # Verifica status do coordenador
        coordinator_node = next((n for n in all_nodes if n.node_id == self.current_coordinator), None)
        
        if coordinator_node and coordinator_node.status == NodeStatus.ACTIVE:
            return True
        
        self.logger.warning(f"Coordenador {self.current_coordinator} não está ativo")
        return False
    
    def get_coordinator_id(self) -> Optional[int]:
        """Retorna ID do coordenador atual"""
        return self.current_coordinator
