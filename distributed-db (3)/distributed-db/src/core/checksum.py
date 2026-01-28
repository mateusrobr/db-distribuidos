import hashlib
import json
from typing import Any


class ChecksumValidator:
    """Valida integridade dos dados usando checksum"""
    
    @staticmethod
    def calculate_checksum(data: Any) -> str:
        """
        Calcula checksum MD5 dos dados
        
        Args:
            data: Dados para calcular checksum
            
        Returns:
            String hexadecimal do checksum
        """
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    @staticmethod
    def validate_checksum(data: Any, checksum: str) -> bool:
        """
        Valida se o checksum corresponde aos dados
        
        Args:
            data: Dados para validar
            checksum: Checksum esperado
            
        Returns:
            True se válido, False caso contrário
        """
        calculated = ChecksumValidator.calculate_checksum(data)
        return calculated == checksum
    
    @staticmethod
    def add_checksum(message_dict: dict) -> dict:
        """
        Adiciona checksum a um dicionário de mensagem
        
        Args:
            message_dict: Dicionário da mensagem
            
        Returns:
            Dicionário com checksum adicionado
        """
        # Remove checksum existente se houver
        msg_copy = message_dict.copy()
        msg_copy.pop('checksum', None)
        
        # Calcula checksum
        checksum = ChecksumValidator.calculate_checksum(msg_copy)
        msg_copy['checksum'] = checksum
        
        return msg_copy
    
    @staticmethod
    def verify_message(message_dict: dict) -> bool:
        """
        Verifica integridade de uma mensagem
        
        Args:
            message_dict: Dicionário da mensagem
            
        Returns:
            True se a mensagem é válida, False caso contrário
        """
        if 'checksum' not in message_dict:
            return False
        
        received_checksum = message_dict['checksum']
        msg_copy = message_dict.copy()
        msg_copy.pop('checksum')
        
        return ChecksumValidator.validate_checksum(msg_copy, received_checksum)
