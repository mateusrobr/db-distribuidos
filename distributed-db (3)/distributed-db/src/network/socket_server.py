import socket
import threading
import logging
import json
from typing import Callable, Optional
from ..core.models import Message
from ..core.checksum import ChecksumValidator


class SocketServer:
    """Servidor de sockets para receber mensagens de outros nós"""
    
    def __init__(self, host: str, port: int, message_handler: Callable[[Message], None]):
        self.host = host
        self.port = port
        self.message_handler = message_handler
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        self.logger = logging.getLogger(__name__)
        self.connections = []
    
    def start(self):
        """Inicia o servidor de sockets"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            self.logger.info(f"Servidor iniciado em {self.host}:{self.port}")
            
            # Thread para aceitar conexões
            accept_thread = threading.Thread(target=self._accept_connections, daemon=True)
            accept_thread.start()
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar servidor: {e}")
            raise
    
    def _accept_connections(self):
        """Aceita conexões de entrada"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                self.logger.info(f"Nova conexão de {address}")
                
                # Thread para lidar com o cliente
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                self.connections.append((client_socket, address))
                
            except Exception as e:
                if self.running:
                    self.logger.error(f"Erro ao aceitar conexão: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address):
        """
        Lida com mensagens de um cliente
        
        Args:
            client_socket: Socket do cliente
            address: Endereço do cliente
        """
        buffer = ""
        
        try:
            while self.running:
                data = client_socket.recv(4096).decode('utf-8')
                
                if not data:
                    break
                
                buffer += data
                
                # Processa mensagens completas (delimitadas por \n)
                while '\n' in buffer:
                    message_str, buffer = buffer.split('\n', 1)
                    
                    if message_str.strip():
                        self._process_message(message_str)
                        
        except Exception as e:
            self.logger.error(f"Erro ao lidar com cliente {address}: {e}")
        finally:
            client_socket.close()
            self.logger.info(f"Conexão com {address} fechada")
    
    def _process_message(self, message_str: str):
        """
        Processa uma mensagem recebida
        
        Args:
            message_str: String JSON da mensagem
        """
        try:
            # Parse JSON
            message_dict = json.loads(message_str)
            
            # Valida checksum
            if not ChecksumValidator.verify_message(message_dict):
                self.logger.warning("Mensagem recebida com checksum inválido - descartada")
                return
            
            # Converte para objeto Message
            message = Message.from_json(message_str)
            
            self.logger.debug(f"Mensagem recebida: {message.message_type.value} do nó {message.sender_id}")
            
            # Chama handler
            self.message_handler(message)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON: {e}")
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {e}")
    
    def stop(self):
        """Para o servidor"""
        self.running = False
        
        # Fecha todas as conexões
        for conn, addr in self.connections:
            try:
                conn.close()
            except:
                pass
        
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info("Servidor parado")
