# Middleware de Banco de Dados Distribuído

Sistema de banco de dados distribuído (DDB) homogêneo autônomo baseado em MySQL com replicação automática, coordenação distribuída e garantias ACID.

## 📋 Características Implementadas

✅ **1. Linguagem**: Python 3.8+  
✅ **2. Distribuição**: Suporta 3+ nós em máquinas diferentes  
✅ **3. SGBD**: MySQL  
✅ **4. Comunicação**: Sockets TCP  
✅ **5. Protocolo**: Protocolo customizado com checksum MD5  
✅ **6. Configuração**: IPs e portas configuráveis via JSON  
✅ **7. Homogeneidade**: DDB homogêneo autônomo  
✅ **8. Replicação**: Todas alterações replicadas automaticamente  
✅ **9. Coordenador**: Eleição automática via Bully Algorithm  
✅ **10. Tipos de Comunicação**: Unicast, Broadcast, Multicast  
✅ **11. ACID**: Two-Phase Commit para transações distribuídas  
✅ **12. Heartbeat**: Monitoramento periódico de nós  
✅ **13. Checksum**: Validação MD5 de integridade  
✅ **14. Load Balancing**: Round-Robin e Least-Loaded  
✅ **15. Logging**: Queries e conteúdo transmitido registrados  
✅ **16. Interface Cliente**: Aplicação CLI interativa  

## 🏗️ Arquitetura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nó 1      │◄───►│   Nó 2      │◄───►│   Nó 3      │
│ (Coord.)    │     │             │     │             │
├─────────────┤     ├─────────────┤     ├─────────────┤
│ MySQL DB    │     │ MySQL DB    │     │ MySQL DB    │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                   ▲                   ▲
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    ┌──────┴──────┐
                    │   Cliente   │
                    └─────────────┘
```

## 🔧 Instalação

### 1. Pré-requisitos

```bash
# Python 3.8+
python3 --version

# MySQL Server 8.0+
mysql --version
```

### 2. Instalar dependências

```bash
cd distributed-db
pip install -r requirements.txt
```

### 3. Configurar MySQL

```bash
# Executar script de configuração
mysql -u root -p < setup_mysql.sql
```

### 4. Configurar nós

Edite `config/nodes_config.json` com os IPs e portas das suas máquinas:

```json
{
  "nodes": [
    {
      "node_id": 1,
      "network": {
        "host": "192.168.1.10",  # IP da máquina 1
        "port": 5001
      },
      "database": {
        "host": "localhost",
        "user": "ddb_user",
        "password": "ddb_password",
        "database": "ddb_node1"
      }
    }
    // ... outros nós
  ]
}
```

## 🚀 Execução

### Iniciar os nós (em cada máquina)

```bash
# Máquina 1 - Nó 1
python3 node_server.py --config config/nodes_config.json --node-id 1

# Máquina 2 - Nó 2
python3 node_server.py --config config/nodes_config.json --node-id 2

# Máquina 3 - Nó 3
python3 node_server.py --config config/nodes_config.json --node-id 3
```

### Usar o cliente

```bash
# Modo interativo
python3 client_app.py --config config/nodes_config.json

# Modo comando único
python3 client_app.py --config config/nodes_config.json --query "SELECT * FROM users"
```

## 📖 Comandos do Cliente

```
DDB> SELECT * FROM users;              # Consultar dados
DDB> INSERT INTO users (name, email) VALUES ('João', 'joao@email.com');
DDB> UPDATE users SET name='Maria' WHERE id=1;
DDB> DELETE FROM users WHERE id=1;

DDB> nodes                             # Listar nós
DDB> stats                             # Estatísticas
DDB> help                              # Ajuda
DDB> exit                              # Sair
```

## 🔍 Funcionalidades Detalhadas

### 1. Protocolo de Comunicação

Mensagens em JSON com os campos:
- `message_type`: QUERY, REPLICATE, HEARTBEAT, ELECTION, etc.
- `sender_id`: ID do nó remetente
- `transaction_id`: UUID da transação
- `query`: Query SQL
- `checksum`: MD5 para validação
- `communication_type`: UNICAST/BROADCAST/MULTICAST

### 2. Coordenação (Bully Algorithm)

- Nó com maior ID sempre vira coordenador
- Eleição automática quando coordenador falha
- Heartbeats detectam falhas em 15 segundos

### 3. Replicação

- Todas escritas (INSERT/UPDATE/DELETE) são replicadas
- ACKs garantem que replicação foi bem-sucedida
- Fallback para rollback em caso de falha

### 4. ACID (Two-Phase Commit)

- **Atomicidade**: Transações são all-or-nothing
- **Consistência**: Dados sincronizados em todos os nós
- **Isolamento**: Transações isoladas
- **Durabilidade**: Commit persistente

### 5. Load Balancing

Estratégias disponíveis:
- **Round-Robin**: Distribui queries sequencialmente
- **Least-Loaded**: Escolhe nó com menos queries
- **Random**: Seleciona nó aleatoriamente

### 6. Monitoramento

Logs incluem:
- Query executada e nó de execução
- Tempo de resposta
- Dados transmitidos
- Status de replicação
- Eleições e mudanças de coordenador

## 🧪 Testando

### Teste 1: Replicação

```bash
# Terminal 1 - Nó 1
python3 node_server.py --config config/nodes_config.json --node-id 1

# Terminal 2 - Nó 2
python3 node_server.py --config config/nodes_config.json --node-id 2

# Terminal 3 - Cliente
python3 client_app.py --config config/nodes_config.json

DDB> INSERT INTO users (name, email) VALUES ('Teste', 'teste@email.com');
# Verifique que foi replicado em ambos os nós
```

### Teste 2: Eleição de Coordenador

```bash
# 1. Inicie todos os nós
# 2. Observe que o nó com maior ID vira coordenador
# 3. Mate o coordenador (Ctrl+C)
# 4. Observe nova eleição acontecer automaticamente
```

### Teste 3: Load Balancing

```bash
# Execute múltiplas queries e observe distribuição
DDB> SELECT * FROM users;  # Vai para nó 1
DDB> SELECT * FROM users;  # Vai para nó 2
DDB> SELECT * FROM users;  # Vai para nó 3
DDB> SELECT * FROM users;  # Volta para nó 1
```

## 📊 Estrutura do Código

```
distributed-db/
├── src/
│   ├── core/                  # Modelos e utilitários base
│   │   ├── models.py         # Classes de dados
│   │   └── checksum.py       # Validação de integridade
│   ├── database/             # Gerenciamento de banco
│   │   ├── mysql_manager.py  # Conexões MySQL
│   │   └── transaction_manager.py  # 2PC
│   ├── network/              # Comunicação
│   │   ├── socket_server.py  # Servidor TCP
│   │   └── socket_client.py  # Cliente TCP
│   ├── coordination/         # Coordenação distribuída
│   │   └── coordinator.py    # Bully Algorithm
│   ├── replication/          # Replicação
│   │   └── replicator.py     # Sincronização
│   └── load_balancer/        # Balanceamento
│       └── balancer.py       # Estratégias de distribuição
├── node_server.py            # Servidor do nó
├── client_app.py             # Aplicação cliente
└── config/
    └── nodes_config.json     # Configuração
```

## 🔒 Segurança e Garantias

- **Checksum MD5**: Valida integridade de todas as mensagens
- **Two-Phase Commit**: Garante ACID em transações distribuídas
- **Heartbeat**: Detecta falhas de nós em 15s
- **Replicação Síncrona**: Alterações só confirmadas após replicação
- **Eleição Automática**: Sistema continua operando mesmo com falhas

## 📝 Notas de Implementação

1. **Homogeneidade**: Todos os nós executam o mesmo SGBD (MySQL)
2. **Autonomia**: Cada nó mantém seu próprio banco de dados
3. **Transparência**: Cliente não precisa saber qual nó executa a query
4. **Tolerância a Falhas**: Sistema continua operando com nós falhando
5. **Escalabilidade**: Adicione mais nós editando a configuração

## 🐛 Troubleshooting

**Problema**: Nó não conecta ao MySQL  
**Solução**: Verifique credenciais em `nodes_config.json` e execute `setup_mysql.sql`

**Problema**: Timeout ao conectar entre nós  
**Solução**: Verifique firewall e se os IPs/portas estão corretos

**Problema**: Eleição não acontece  
**Solução**: Verifique se todos os nós estão rodando e heartbeats estão funcionando

## 📄 Licença

MIT License - Projeto educacional para demonstração de sistemas distribuídos.

## 👨‍💻 Autor

Desenvolvido como implementação de middleware para banco de dados distribuído.
