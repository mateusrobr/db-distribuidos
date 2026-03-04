# Roteiro de Uso — Máquinas Diferentes (Sem Docker)

Sistema de banco de dados distribuído com 3 nós MySQL, cada nó rodando em uma máquina física/virtual separada na mesma rede.

---

## Arquitetura

| Papel       | Máquina   | IP (exemplo)   | Porta TCP | Banco MySQL |
|-------------|-----------|----------------|-----------|-------------|
| Nó 1        | Máquina 1 | 192.168.1.101  | 5001      | ddb_node1   |
| Nó 2        | Máquina 2 | 192.168.1.102  | 5002      | ddb_node2   |
| Nó 3        | Máquina 3 | 192.168.1.103  | 5003      | ddb_node3   |
| Cliente     | Qualquer  | —              | —         | —           |

> **Os nós comunicam-se entre si via TCP (portas 5001-5003). O MySQL fica local em cada máquina — os nós não acessam o MySQL das outras máquinas.**

---

## Pré-requisitos (em cada máquina)

- Python 3.8+
- MySQL Server 8.0+
- Código do projeto copiado (mesma versão em todas as máquinas)
- Rede local com as máquinas visíveis entre si

---

## Passo 1 — Descobrir os IPs das máquinas

Em cada máquina, execute:

```bash
hostname -I
# ou
ip addr show | grep 'inet ' | grep -v '127.0.0.1'
```

Anote os IPs. Eles serão usados no arquivo de configuração.

---

## Passo 2 — Editar o arquivo de configuração

O arquivo `config/nodes_config_distributed.json` já existe como template. **Em todas as máquinas**, edite esse arquivo substituindo os IPs pelos reais:

```json
{
  "nodes": [
    {
      "node_id": 1,
      "network": {
        "host": "192.168.1.101",   <- IP real da Máquina 1
        "port": 5001
      },
      "database": {
        "host": "localhost",        <- sempre localhost (MySQL é local)
        "port": 3306,
        "user": "ddb_user",
        "password": "ddb_password",
        "database": "ddb_node1"
      }
    },
    {
      "node_id": 2,
      "network": {
        "host": "192.168.1.102",   <- IP real da Máquina 2
        "port": 5002
      },
      ...
    },
    {
      "node_id": 3,
      "network": {
        "host": "192.168.1.103",   <- IP real da Máquina 3
        "port": 5003
      },
      ...
    }
  ]
}
```

> O arquivo `config/nodes_config_distributed.json` deve ser **idêntico em todas as máquinas** — apenas os IPs mudam de acordo com o seu ambiente.

---

## Passo 3 — Instalar dependências Python (em cada máquina)

```bash
cd /caminho/para/distributed-db
pip install -r requirements.txt
```

---

## Passo 4 — Instalar e configurar o MySQL (em cada máquina)

```bash
sudo apt update
sudo apt install mysql-server -y
sudo service mysql start
```

Configure o MySQL de cada nó com **o script correspondente à sua máquina**:

**Máquina 1:**
```bash
sudo mysql -u root < setup_mysql_node1.sql
```

**Máquina 2:**
```bash
sudo mysql -u root < setup_mysql_node2.sql
```

**Máquina 3:**
```bash
sudo mysql -u root < setup_mysql_node3.sql
```

Verifique:
```bash
sudo mysql -u root -e "SHOW DATABASES;"
```

---

## Passo 5 — Liberar a porta no firewall (em cada máquina)

Cada máquina precisa aceitar conexões TCP na sua porta de nó:

```bash
# Ubuntu/Debian com ufw
sudo ufw allow 5001/tcp   # Máquina 1
sudo ufw allow 5002/tcp   # Máquina 2
sudo ufw allow 5003/tcp   # Máquina 3
```

Teste a conectividade da Máquina 1 para a Máquina 2 (antes de iniciar os nós):
```bash
nc -zv 192.168.1.102 5002
```

---

## Passo 6 — Iniciar os nós

**Use sempre `config/nodes_config_distributed.json` (com os IPs reais).**

**Máquina 1 — Nó 1:**
```bash
cd /caminho/para/distributed-db
python3 node_server.py --config config/nodes_config_distributed.json --node-id 1
```

**Máquina 2 — Nó 2:**
```bash
cd /caminho/para/distributed-db
python3 node_server.py --config config/nodes_config_distributed.json --node-id 2
```

**Máquina 3 — Nó 3:**
```bash
cd /caminho/para/distributed-db
python3 node_server.py --config config/nodes_config_distributed.json --node-id 3
```

Aguarde cada nó exibir:
```
*** Nó X ATIVO ***
```

---

## Passo 7 — Iniciar o cliente

O cliente pode rodar em **qualquer máquina** que tenha acesso de rede às três.

```bash
cd /caminho/para/distributed-db
python3 client_app.py --config config/nodes_config_distributed.json
```

---

## Passo 8 — Testar

```sql
-- Inserir dados (serão replicados nos 3 nós)
INSERT INTO users (name, email) VALUES ('Alice Silva', 'alice@email.com');
INSERT INTO users (name, email) VALUES ('Bruno Costa', 'bruno@email.com');

-- Consultar (o round-robin distribui entre os nós)
SELECT * FROM users;
```

Verifique nos logs de cada nó se a replicação está ocorrendo.

---

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| `Timeout ao conectar ao nó X` | Firewall bloqueando ou nó não iniciado | Verifique `ufw` e se o nó está rodando |
| `Connection refused` | Nó ainda não iniciou | Aguarde a mensagem `*** Nó X ATIVO ***` |
| `Falha ao conectar ao MySQL` | MySQL parado | `sudo service mysql start` |
| `Access denied for user 'ddb_user'` | Script de setup não executado | Execute `setup_mysql_nodeX.sql` novamente |
| Replicação não ocorre | IP errado no config | Verifique `nodes_config_distributed.json` em todas as máquinas |
| IPs diferentes entre máquinas | Configs dessincronizadas | O arquivo deve ser **idêntico** em todas as máquinas |

---

## Diferença em relação ao roteiro local

| Aspecto | Local (mesmo PC) | Máquinas Diferentes |
|---|---|---|
| Config | `nodes_config.json` | `nodes_config_distributed.json` |
| `network.host` | `localhost` | IP real de cada máquina |
| `database.host` | `localhost` | `localhost` (MySQL é sempre local) |
| SQL de setup | `setup_mysql.sql` (cria os 3 bancos) | `setup_mysql_nodeX.sql` (1 banco por máquina) |
| Firewall | Não necessário | Liberar porta TCP do nó |
| Bind do servidor | `localhost` → agora `0.0.0.0` | `0.0.0.0` (aceita todas as interfaces) |
