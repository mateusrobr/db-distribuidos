import logging
from typing import List, Optional
from ..core.models import NodeInfo, NodeStatus
import random


class LoadBalancer:
    """
    Balanceador de carga para distribuir queries entre nós
    Usa estratégia Round-Robin com fallback para Least Connections
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_index = 0
    
    def select_node_round_robin(self, nodes: List[NodeInfo], exclude_node: Optional[int] = None) -> Optional[NodeInfo]:
        """
        Seleciona próximo nó usando Round-Robin
        
        Args:
            nodes: Lista de nós disponíveis
            exclude_node: ID do nó a excluir
            
        Returns:
            Nó selecionado ou None
        """
        active_nodes = [n for n in nodes if n.status == NodeStatus.ACTIVE and n.node_id != exclude_node]
        
        if not active_nodes:
            self.logger.warning("Nenhum nó ativo disponível")
            return None
        
        # Round-robin
        selected = active_nodes[self.current_index % len(active_nodes)]
        self.current_index += 1
        
        self.logger.debug(f"Round-Robin selecionou nó {selected.node_id}")
        return selected
    
    def select_node_least_loaded(self, nodes: List[NodeInfo], exclude_node: Optional[int] = None) -> Optional[NodeInfo]:
        """
        Seleciona nó com menor carga (menos queries executadas)
        
        Args:
            nodes: Lista de nós disponíveis
            exclude_node: ID do nó a excluir
            
        Returns:
            Nó selecionado ou None
        """
        active_nodes = [n for n in nodes if n.status == NodeStatus.ACTIVE and n.node_id != exclude_node]
        
        if not active_nodes:
            self.logger.warning("Nenhum nó ativo disponível")
            return None
        
        # Seleciona nó com menor query_count
        selected = min(active_nodes, key=lambda n: n.query_count)
        
        self.logger.debug(f"Least-Loaded selecionou nó {selected.node_id} (queries: {selected.query_count})")
        return selected
    
    def select_node_random(self, nodes: List[NodeInfo], exclude_node: Optional[int] = None) -> Optional[NodeInfo]:
        """
        Seleciona nó aleatório
        
        Args:
            nodes: Lista de nós disponíveis
            exclude_node: ID do nó a excluir
            
        Returns:
            Nó selecionado ou None
        """
        active_nodes = [n for n in nodes if n.status == NodeStatus.ACTIVE and n.node_id != exclude_node]
        
        if not active_nodes:
            self.logger.warning("Nenhum nó ativo disponível")
            return None
        
        selected = random.choice(active_nodes)
        
        self.logger.debug(f"Random selecionou nó {selected.node_id}")
        return selected
    
    def select_node(self, nodes: List[NodeInfo], strategy: str = "round_robin", exclude_node: Optional[int] = None) -> Optional[NodeInfo]:
        """
        Seleciona nó de acordo com a estratégia especificada
        
        Args:
            nodes: Lista de nós disponíveis
            strategy: Estratégia de seleção ("round_robin", "least_loaded", "random")
            exclude_node: ID do nó a excluir
            
        Returns:
            Nó selecionado ou None
        """
        if strategy == "least_loaded":
            return self.select_node_least_loaded(nodes, exclude_node)
        elif strategy == "random":
            return self.select_node_random(nodes, exclude_node)
        else:
            return self.select_node_round_robin(nodes, exclude_node)
    
    def increment_query_count(self, node: NodeInfo):
        """
        Incrementa contador de queries de um nó
        
        Args:
            node: Nó a incrementar
        """
        node.query_count += 1
        self.logger.debug(f"Nó {node.node_id} agora tem {node.query_count} queries")
    
    def get_load_statistics(self, nodes: List[NodeInfo]) -> dict:
        """
        Retorna estatísticas de carga dos nós
        
        Args:
            nodes: Lista de nós
            
        Returns:
            Dicionário com estatísticas
        """
        active_nodes = [n for n in nodes if n.status == NodeStatus.ACTIVE]
        
        if not active_nodes:
            return {
                'total_nodes': 0,
                'total_queries': 0,
                'avg_queries': 0,
                'min_queries': 0,
                'max_queries': 0
            }
        
        total_queries = sum(n.query_count for n in active_nodes)
        
        return {
            'total_nodes': len(active_nodes),
            'total_queries': total_queries,
            'avg_queries': total_queries / len(active_nodes),
            'min_queries': min(n.query_count for n in active_nodes),
            'max_queries': max(n.query_count for n in active_nodes),
            'nodes': {n.node_id: n.query_count for n in active_nodes}
        }
