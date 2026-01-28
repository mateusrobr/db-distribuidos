from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class MessageType(Enum):
    """Tipos de mensagens no protocolo"""
    QUERY = "QUERY"
    QUERY_RESPONSE = "QUERY_RESPONSE"
    REPLICATE = "REPLICATE"
    REPLICATE_ACK = "REPLICATE_ACK"
    HEARTBEAT = "HEARTBEAT"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"
    ELECTION = "ELECTION"
    COORDINATOR = "COORDINATOR"
    PREPARE = "PREPARE"  # Two-phase commit
    COMMIT = "COMMIT"
    ABORT = "ABORT"
    ACK = "ACK"


class NodeStatus(Enum):
    """Status de um nó"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    COORDINATOR = "COORDINATOR"
    SUSPECT = "SUSPECT"


class CommunicationType(Enum):
    """Tipos de comunicação"""
    UNICAST = "UNICAST"
    BROADCAST = "BROADCAST"
    MULTICAST = "MULTICAST"


@dataclass
class NodeInfo:
    """Informações de um nó do DDB"""
    node_id: int
    host: str
    port: int
    status: NodeStatus = NodeStatus.ACTIVE
    last_heartbeat: Optional[datetime] = None
    query_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'host': self.host,
            'port': self.port,
            'status': self.status.value,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'query_count': self.query_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NodeInfo':
        return cls(
            node_id=data['node_id'],
            host=data['host'],
            port=data['port'],
            status=NodeStatus(data.get('status', 'ACTIVE')),
            last_heartbeat=datetime.fromisoformat(data['last_heartbeat']) if data.get('last_heartbeat') else None,
            query_count=data.get('query_count', 0)
        )


@dataclass
class Message:
    """Mensagem do protocolo de comunicação"""
    message_type: MessageType
    sender_id: int
    transaction_id: Optional[str] = None
    query: Optional[str] = None
    data: Optional[Any] = None
    checksum: Optional[str] = None
    timestamp: Optional[datetime] = None
    communication_type: CommunicationType = CommunicationType.UNICAST
    target_nodes: Optional[List[int]] = None
    
    def to_json(self) -> str:
        """Serializa mensagem para JSON"""
        return json.dumps({
            'message_type': self.message_type.value,
            'sender_id': self.sender_id,
            'transaction_id': self.transaction_id,
            'query': self.query,
            'data': self.data,
            'checksum': self.checksum,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'communication_type': self.communication_type.value,
            'target_nodes': self.target_nodes
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """Deserializa mensagem do JSON"""
        data = json.loads(json_str)
        return cls(
            message_type=MessageType(data['message_type']),
            sender_id=data['sender_id'],
            transaction_id=data.get('transaction_id'),
            query=data.get('query'),
            data=data.get('data'),
            checksum=data.get('checksum'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else None,
            communication_type=CommunicationType(data.get('communication_type', 'UNICAST')),
            target_nodes=data.get('target_nodes')
        )


@dataclass
class Transaction:
    """Representa uma transação distribuída"""
    transaction_id: str
    query: str
    initiator_node: int
    participants: List[int]
    status: str = "PREPARING"  # PREPARING, COMMITTED, ABORTED
    votes: Dict[int, bool] = None
    
    def __post_init__(self):
        if self.votes is None:
            self.votes = {}


@dataclass
class QueryResult:
    """Resultado de uma query"""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    node_id: Optional[int] = None
    execution_time: Optional[float] = None
    rows_affected: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'node_id': self.node_id,
            'execution_time': self.execution_time,
            'rows_affected': self.rows_affected
        }
