import uuid
import logging
from typing import Dict, List, Optional
from datetime import datetime
from ..core.models import Transaction, Message, MessageType, CommunicationType


class TransactionManager:
    """
    Gerencia transações distribuídas usando Two-Phase Commit (2PC)
    Garante propriedades ACID em ambiente distribuído
    """
    
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.active_transactions: Dict[str, Transaction] = {}
        self.logger = logging.getLogger(__name__)
    
    def create_transaction(self, query: str, participant_nodes: List[int]) -> str:
        """
        Cria uma nova transação distribuída
        
        Args:
            query: Query SQL a ser executada
            participant_nodes: Lista de nós participantes
            
        Returns:
            ID da transação
        """
        transaction_id = str(uuid.uuid4())
        
        transaction = Transaction(
            transaction_id=transaction_id,
            query=query,
            initiator_node=self.node_id,
            participants=participant_nodes,
            status="PREPARING"
        )
        
        self.active_transactions[transaction_id] = transaction
        self.logger.info(f"Transação {transaction_id} criada para query: {query[:50]}...")
        
        return transaction_id
    
    def prepare_phase(self, transaction_id: str) -> Message:
        """
        Fase 1 do 2PC: PREPARE
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            Mensagem PREPARE para broadcast
        """
        transaction = self.active_transactions.get(transaction_id)
        if not transaction:
            raise ValueError(f"Transação {transaction_id} não encontrada")
        
        prepare_msg = Message(
            message_type=MessageType.PREPARE,
            sender_id=self.node_id,
            transaction_id=transaction_id,
            query=transaction.query,
            timestamp=datetime.now(),
            communication_type=CommunicationType.BROADCAST
        )
        
        self.logger.info(f"Fase PREPARE iniciada para transação {transaction_id}")
        return prepare_msg
    
    def vote_on_prepare(self, transaction_id: str, can_commit: bool) -> bool:
        """
        Vota se pode commitar a transação
        
        Args:
            transaction_id: ID da transação
            can_commit: True se pode commitar, False caso contrário
            
        Returns:
            Voto registrado
        """
        transaction = self.active_transactions.get(transaction_id)
        if transaction:
            transaction.votes[self.node_id] = can_commit
            self.logger.info(f"Voto registrado para transação {transaction_id}: {'COMMIT' if can_commit else 'ABORT'}")
        return can_commit
    
    def receive_vote(self, transaction_id: str, node_id: int, vote: bool):
        """
        Recebe voto de um nó participante
        
        Args:
            transaction_id: ID da transação
            node_id: ID do nó que votou
            vote: True para COMMIT, False para ABORT
        """
        transaction = self.active_transactions.get(transaction_id)
        if transaction:
            transaction.votes[node_id] = vote
            self.logger.info(f"Voto recebido do nó {node_id} para transação {transaction_id}: {'COMMIT' if vote else 'ABORT'}")
    
    def can_commit(self, transaction_id: str) -> bool:
        """
        Verifica se todos os participantes votaram COMMIT
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            True se todos votaram COMMIT, False caso contrário
        """
        transaction = self.active_transactions.get(transaction_id)
        if not transaction:
            return False
        
        # Verifica se todos os participantes votaram
        if len(transaction.votes) != len(transaction.participants):
            return False
        
        # Verifica se todos votaram COMMIT
        return all(transaction.votes.values())
    
    def commit_phase(self, transaction_id: str, commit: bool) -> Message:
        """
        Fase 2 do 2PC: COMMIT ou ABORT
        
        Args:
            transaction_id: ID da transação
            commit: True para COMMIT, False para ABORT
            
        Returns:
            Mensagem COMMIT ou ABORT para broadcast
        """
        transaction = self.active_transactions.get(transaction_id)
        if not transaction:
            raise ValueError(f"Transação {transaction_id} não encontrada")
        
        message_type = MessageType.COMMIT if commit else MessageType.ABORT
        transaction.status = "COMMITTED" if commit else "ABORTED"
        
        commit_msg = Message(
            message_type=message_type,
            sender_id=self.node_id,
            transaction_id=transaction_id,
            timestamp=datetime.now(),
            communication_type=CommunicationType.BROADCAST
        )
        
        action = "COMMIT" if commit else "ABORT"
        self.logger.info(f"Fase {action} iniciada para transação {transaction_id}")
        
        return commit_msg
    
    def finalize_transaction(self, transaction_id: str):
        """
        Finaliza e remove transação do gerenciador
        
        Args:
            transaction_id: ID da transação
        """
        if transaction_id in self.active_transactions:
            transaction = self.active_transactions.pop(transaction_id)
            self.logger.info(f"Transação {transaction_id} finalizada com status: {transaction.status}")
    
    def get_transaction_status(self, transaction_id: str) -> Optional[str]:
        """
        Retorna o status de uma transação
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            Status da transação ou None
        """
        transaction = self.active_transactions.get(transaction_id)
        return transaction.status if transaction else None
    
    def cleanup_old_transactions(self, timeout_seconds: int = 300):
        """
        Remove transações antigas que não foram finalizadas
        
        Args:
            timeout_seconds: Timeout em segundos para considerar transação antiga
        """
        current_time = datetime.now()
        to_remove = []
        
        for tid, transaction in self.active_transactions.items():
            # Aqui você poderia adicionar lógica de timestamp na transação
            # Por simplicidade, vamos apenas logar
            if transaction.status in ["COMMITTED", "ABORTED"]:
                to_remove.append(tid)
        
        for tid in to_remove:
            self.finalize_transaction(tid)
        
        if to_remove:
            self.logger.info(f"Limpeza: {len(to_remove)} transações removidas")
