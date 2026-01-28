# Guia de Início Rápido - DDB Middleware

## 🚀 Configuração Rápida (Ambiente Local de Teste)

### Passo 1: Preparar MySQL

```bash
# Instalar MySQL (se necessário)
# Ubuntu/Debian
sudo apt-get install mysql-server

# Iniciar MySQL
sudo systemctl start mysql

# Executar script de configuração
mysql -u root -p < setup_mysql.sql
```

### Passo 2: Instalar Dependências Python

```bash
pip install mysql-connector-python pymysql pydantic python-dotenv
```

### Passo 3: Testar Componentes

```bash
# Tornar scripts executáveis
chmod +x node_server.py client_app.py test_components.py

# Executar testes
python3 test_components.py
```

### Passo 4: Iniciar Nós (3 terminais diferentes)

**Terminal 1:**
```bash
python3 node_server.py --config config/nodes_config.json --node-id 1
```

**Terminal 2:**
```bash
python3 node_server.py --config config/nodes_config.json --node-id 2
```

**Terminal 3:**
```bash
python3 node_server.py --config config/nodes_config.json --node-id 3
```

### Passo 5: Usar Cliente (4º terminal)

```bash
python3 client_app.py --config config/nodes_config.json
```

## 📝 Exemplo de Uso

```sql
-- Criar tabela (faça em todos os bancos primeiro via MySQL)
CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10,2)
);

-- No cliente DDB:
DDB> INSERT INTO products (name, price) VALUES ('Notebook', 2500.00);
-- Resultado mostrará: Nó executado: 1, Linhas afetadas: 1
-- A inserção será automaticamente replicada para nós 2 e 3!

DDB> SELECT * FROM products;
-- Resultado mostrará todos os produtos
-- Próxima query SELECT irá para o nó 2 (round-robin)

DDB> UPDATE products SET price = 2300.00 WHERE id = 1;
-- Atualização replicada para todos os nós

DDB> nodes
-- Lista todos os nós disponíveis
```

## 🔍 O que Observar nos Logs

### Log do Nó Coordenador (ID maior):
```
*** Nó 3 é o novo COORDENADOR ***
Transação abc-123 criada para query: INSERT INTO...
Replicação enviada para 2 nós
ACK de replicação do nó 1 (sucesso) - 1/2
ACK de replicação do nó 2 (sucesso) - 2/2
Todas as replicações confirmadas
```

### Log dos Nós Participantes:
```
Replicando query do nó 3: INSERT INTO products...
Replicação executada com sucesso - 1 linhas afetadas
ACK de replicação enviado para nó 3
```

### Log do Cliente:
```
Query: INSERT INTO products (name, price) VALUES ('Mouse', 50.00);
================================================================================
📊 Resultado:
  • Nó executado: 2
  • Tempo: 0.045s
  • Status: ✓ Sucesso
  • Linhas afetadas: 1
```

## 🧪 Cenários de Teste

### Teste 1: Replicação Funciona?
1. INSERT via cliente
2. Conecte diretamente em cada MySQL:
   ```bash
   mysql -u ddb_user -p ddb_node1 -e "SELECT * FROM products"
   mysql -u ddb_user -p ddb_node2 -e "SELECT * FROM products"
   mysql -u ddb_user -p ddb_node3 -e "SELECT * FROM products"
   ```
3. Todos devem ter os mesmos dados!

### Teste 2: Eleição Funciona?
1. Identifique o coordenador (ID maior)
2. Pare o nó coordenador (Ctrl+C)
3. Observe logs dos outros nós - nova eleição acontece
4. Nó com segundo maior ID vira coordenador

### Teste 3: Load Balancing Funciona?
1. Execute 6 SELECTs seguidos
2. Observe que queries são distribuídas: 1→2→3→1→2→3

### Teste 4: Heartbeat Detecta Falhas?
1. Pare um nó não-coordenador
2. Aguarde 15 segundos
3. Outros nós marcarão ele como INACTIVE
4. Queries não serão mais enviadas para ele

## ⚙️ Configuração para Máquinas Diferentes

Edite `config/nodes_config.json`:

```json
{
  "nodes": [
    {
      "node_id": 1,
      "network": {
        "host": "192.168.1.10",  # IP da Máquina 1
        "port": 5001
      },
      "database": {
        "host": "localhost",     # MySQL local na Máquina 1
        "user": "ddb_user",
        "password": "ddb_password",
        "database": "ddb_node1"
      }
    },
    {
      "node_id": 2,
      "network": {
        "host": "192.168.1.20",  # IP da Máquina 2
        "port": 5001
      },
      "database": {
        "host": "localhost",     # MySQL local na Máquina 2
        "user": "ddb_user",
        "password": "ddb_password",
        "database": "ddb_node2"
      }
    },
    {
      "node_id": 3,
      "network": {
        "host": "192.168.1.30",  # IP da Máquina 3
        "port": 5001
      },
      "database": {
        "host": "localhost",     # MySQL local na Máquina 3
        "user": "ddb_user",
        "password": "ddb_password",
        "database": "ddb_node3"
      }
    }
  ]
}
```

**Importante:** 
- Copie o mesmo `nodes_config.json` para todas as máquinas
- Certifique-se que as máquinas podem se comunicar (portas abertas no firewall)
- Execute `setup_mysql.sql` em cada máquina

## 🐛 Problemas Comuns

**"Connection refused"**
- Verifique se o nó está rodando
- Verifique firewall: `sudo ufw allow 5001/tcp`

**"Access denied for user 'ddb_user'"**
- Execute novamente o `setup_mysql.sql`
- Verifique senha no arquivo de configuração

**"Database 'ddb_nodeX' doesn't exist"**
- Execute o `setup_mysql.sql` para criar os bancos

**Nós não se comunicam**
- Verifique IPs no `nodes_config.json`
- Use `ping` para testar conectividade
- Verifique portas: `netstat -tuln | grep 5001`

## 📊 Verificando Status

### Ver logs em tempo real:
```bash
# Nó
python3 node_server.py --config config/nodes_config.json --node-id 1 | tee node1.log

# Cliente com queries específicas
python3 client_app.py --config config/nodes_config.json --query "SELECT COUNT(*) FROM products"
```

### Conectar diretamente ao MySQL:
```bash
mysql -u ddb_user -p -e "USE ddb_node1; SELECT * FROM products"
```

## ✅ Checklist de Validação

- [ ] 3 nós rodando simultaneamente
- [ ] Cliente conecta e executa queries
- [ ] INSERT/UPDATE/DELETE replicam para todos os nós
- [ ] SELECT usa load balancing (distribui entre nós)
- [ ] Coordenador eleito automaticamente
- [ ] Falha de coordenador dispara nova eleição
- [ ] Heartbeats detectam nós inativos
- [ ] Checksum valida integridade das mensagens
- [ ] Transações respeitam ACID
- [ ] Logs mostram queries e replicações

## 🎯 Próximos Passos

1. Teste em ambiente distribuído (3 máquinas físicas)
2. Adicione mais nós (node_id 4, 5, etc.)
3. Execute testes de carga
4. Simule falhas de rede
5. Adicione métricas de performance

---

**Pronto para testar!** 🚀
