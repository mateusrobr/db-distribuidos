import mysql.connector
from mysql.connector import Error
from typing import List, Dict, Any, Optional, Tuple
import logging
from contextlib import contextmanager
import time


class MySQLManager:
    """Gerencia conexões e operações com MySQL"""
    
    def __init__(self, host: str, user: str, password: str, database: str, port: int = 3306):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.logger = logging.getLogger(__name__)
        self._connection = None
    
    def connect(self) -> bool:
        """Estabelece conexão com o banco de dados"""
        try:
            self._connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                autocommit=False  # Controle manual de transações
            )
            self.logger.info(f"Conectado ao MySQL em {self.host}:{self.port}")
            return True
        except Error as e:
            self.logger.error(f"Erro ao conectar ao MySQL: {e}")
            return False
    
    def disconnect(self):
        """Fecha conexão com o banco de dados"""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            self.logger.info("Desconectado do MySQL")
    
    def is_connected(self) -> bool:
        """Verifica se está conectado"""
        return self._connection is not None and self._connection.is_connected()
    
    @contextmanager
    def get_cursor(self, dictionary: bool = True):
        """Context manager para cursor"""
        if not self.is_connected():
            self.connect()
        
        cursor = self._connection.cursor(dictionary=dictionary, buffered=True)
        try:
            yield cursor
        finally:
            cursor.close()
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Tuple[bool, Optional[List[Dict]], Optional[str], int]:
        """
        Executa uma query SQL
        
        Args:
            query: Query SQL
            params: Parâmetros da query
            
        Returns:
            Tupla (sucesso, dados, erro, rows_affected)
        """
        start_time = time.time()
        
        try:
            with self.get_cursor() as cursor:
                self.logger.info(f"Executando query: {query[:100]}...")
                
                cursor.execute(query, params or ())
                
                # Verifica se é SELECT
                if query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    execution_time = time.time() - start_time
                    self.logger.info(f"Query executada com sucesso em {execution_time:.3f}s - {len(results)} registros")
                    return True, results, None, len(results)
                else:
                    # INSERT, UPDATE, DELETE
                    rows_affected = cursor.rowcount
                    execution_time = time.time() - start_time
                    self.logger.info(f"Query executada com sucesso em {execution_time:.3f}s - {rows_affected} linhas afetadas")
                    return True, None, None, rows_affected
                    
        except Error as e:
            execution_time = time.time() - start_time
            error_msg = f"Erro ao executar query: {e}"
            self.logger.error(error_msg)
            return False, None, error_msg, 0
    
    def begin_transaction(self) -> bool:
        """Inicia uma transação"""
        try:
            if not self.is_connected():
                self.connect()
            self._connection.start_transaction()
            self.logger.info("Transação iniciada")
            return True
        except Error as e:
            self.logger.error(f"Erro ao iniciar transação: {e}")
            return False
    
    def commit(self) -> bool:
        """Commit da transação"""
        try:
            self._connection.commit()
            self.logger.info("Transação commitada")
            return True
        except Error as e:
            self.logger.error(f"Erro ao commitar transação: {e}")
            return False
    
    def rollback(self) -> bool:
        """Rollback da transação"""
        try:
            self._connection.rollback()
            self.logger.info("Transação revertida")
            return True
        except Error as e:
            self.logger.error(f"Erro ao reverter transação: {e}")
            return False
    
    def execute_transaction(self, queries: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Executa múltiplas queries em uma transação
        
        Args:
            queries: Lista de queries SQL
            
        Returns:
            Tupla (sucesso, erro)
        """
        try:
            self.begin_transaction()
            
            for query in queries:
                success, _, error, _ = self.execute_query(query)
                if not success:
                    self.rollback()
                    return False, error
            
            self.commit()
            return True, None
            
        except Exception as e:
            self.rollback()
            error_msg = f"Erro na transação: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def test_connection(self) -> bool:
        """Testa a conexão com o banco"""
        try:
            if not self.is_connected():
                self.connect()
            
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Error as e:
            self.logger.error(f"Teste de conexão falhou: {e}")
            return False
