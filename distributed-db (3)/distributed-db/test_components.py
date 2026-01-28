#!/usr/bin/env python3
"""
Script de testes para validar componentes do DDB
"""

import sys
import json
from src.core.models import Message, MessageType, NodeInfo, NodeStatus, CommunicationType
from src.core.checksum import ChecksumValidator
from datetime import datetime


def test_checksum():
    """Testa validação de checksum"""
    print("\n=== Testando Checksum ===")
    
    data = {"key": "value", "number": 123}
    checksum = ChecksumValidator.calculate_checksum(data)
    print(f"✓ Checksum calculado: {checksum}")
    
    is_valid = ChecksumValidator.validate_checksum(data, checksum)
    print(f"✓ Validação: {is_valid}")
    
    # Teste com dado alterado
    data_modified = {"key": "value2", "number": 123}
    is_valid = ChecksumValidator.validate_checksum(data_modified, checksum)
    print(f"✓ Validação com dado alterado (deve ser False): {is_valid}")
    
    assert not is_valid, "Checksum deveria ser inválido para dado alterado"
    print("✓ Teste de checksum passou!")


def test_message_serialization():
    """Testa serialização de mensagens"""
    print("\n=== Testando Serialização de Mensagens ===")
    
    message = Message(
        message_type=MessageType.QUERY,
        sender_id=1,
        transaction_id="test-123",
        query="SELECT * FROM users",
        timestamp=datetime.now(),
        communication_type=CommunicationType.UNICAST,
        target_nodes=[2]
    )
    
    # Serializa
    json_str = message.to_json()
    print(f"✓ Mensagem serializada: {len(json_str)} bytes")
    
    # Deserializa
    message2 = Message.from_json(json_str)
    print(f"✓ Mensagem deserializada")
    
    assert message.message_type == message2.message_type
    assert message.sender_id == message2.sender_id
    assert message.query == message2.query
    
    print("✓ Teste de serialização passou!")


def test_message_with_checksum():
    """Testa mensagem com checksum"""
    print("\n=== Testando Mensagem com Checksum ===")
    
    message = Message(
        message_type=MessageType.HEARTBEAT,
        sender_id=1,
        timestamp=datetime.now(),
        communication_type=CommunicationType.BROADCAST
    )
    
    # Serializa e adiciona checksum
    message_dict = json.loads(message.to_json())
    message_dict = ChecksumValidator.add_checksum(message_dict)
    
    print(f"✓ Checksum adicionado: {message_dict['checksum']}")
    
    # Verifica
    is_valid = ChecksumValidator.verify_message(message_dict)
    print(f"✓ Verificação: {is_valid}")
    
    assert is_valid, "Checksum deveria ser válido"
    print("✓ Teste de mensagem com checksum passou!")


def test_node_info():
    """Testa NodeInfo"""
    print("\n=== Testando NodeInfo ===")
    
    node = NodeInfo(
        node_id=1,
        host="192.168.1.10",
        port=5001,
        status=NodeStatus.ACTIVE
    )
    
    # Converte para dict
    node_dict = node.to_dict()
    print(f"✓ NodeInfo convertido para dict: {node_dict}")
    
    # Converte de volta
    node2 = NodeInfo.from_dict(node_dict)
    print(f"✓ NodeInfo restaurado do dict")
    
    assert node.node_id == node2.node_id
    assert node.host == node2.host
    assert node.port == node2.port
    
    print("✓ Teste de NodeInfo passou!")


def test_config_loading():
    """Testa carregamento de configuração"""
    print("\n=== Testando Carregamento de Configuração ===")
    
    try:
        with open('config/nodes_config.json', 'r') as f:
            config = json.load(f)
        
        print(f"✓ Configuração carregada")
        print(f"✓ Número de nós: {len(config['nodes'])}")
        
        for node in config['nodes']:
            print(f"  - Nó {node['node_id']}: {node['network']['host']}:{node['network']['port']}")
        
        assert len(config['nodes']) >= 3, "Deve ter pelo menos 3 nós"
        print("✓ Teste de configuração passou!")
        
    except FileNotFoundError:
        print("⚠ Arquivo de configuração não encontrado - pule este teste")


def run_all_tests():
    """Executa todos os testes"""
    print("="*80)
    print("  TESTES DO MIDDLEWARE DDB")
    print("="*80)
    
    tests = [
        test_checksum,
        test_message_serialization,
        test_message_with_checksum,
        test_node_info,
        test_config_loading
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ Teste falhou: {e}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"  RESULTADO: {passed} passou, {failed} falhou")
    print("="*80 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
