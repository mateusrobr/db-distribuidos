# Roteiro de Uso — Sem Docker

Sistema de banco de dados distribuído com 3 nós MySQL rodando localmente.

---

## Pré-requisitos

- Python 3.8+
- MySQL Server 8.0+

---

## 1. Instalar o MySQL (WSL/Ubuntu)

```bash
sudo apt update
sudo apt install mysql-server -y
sudo service mysql start
```

Verifique se está rodando:

```bash
sudo service mysql status
```

---

## 2. Instalar dependências Python

```bash
cd "/home/luiz_mateus/db-distribuidos/distributed-db (3)/distributed-db"
pip install -r requirements.txt
```

---

## 3. Configurar o MySQL (executar uma única vez)

Cria o usuário `ddb_user`, os 3 bancos (`ddb_node1`, `ddb_node2`, `ddb_node3`) e a tabela `users` em cada um:

```bash
sudo mysql -u root < setup_mysql.sql
```

Para verificar se foi criado corretamente:

```bash
sudo mysql -u root -e "SHOW DATABASES;"
sudo mysql -u root -e "SELECT User, Host FROM mysql.user WHERE User='ddb_user';"
```

---

## 4. Configuração dos nós

O arquivo `config/nodes_config.json` já está configurado para uso local (sem Docker):

| Nó | Porta TCP | Banco MySQL   |
|----|-----------|---------------|
| 1  | 5001      | ddb_node1     |
| 2  | 5002      | ddb_node2     |
| 3  | 5003      | ddb_node3     |

Todos se conectam ao MySQL na porta **3306** (instância local única).

---

## 5. Iniciar os nós

Abra **3 terminais separados**, cada um rodando um nó.

**Terminal 1 — Nó 1:**
```bash
cd "/home/luiz_mateus/db-distribuidos/distributed-db (3)/distributed-db"
python3 node_server.py --config config/nodes_config.json --node-id 1
```

**Terminal 2 — Nó 2:**
```bash
cd "/home/luiz_mateus/db-distribuidos/distributed-db (3)/distributed-db"
python3 node_server.py --config config/nodes_config.json --node-id 2
```

**Terminal 3 — Nó 3:**
```bash
cd "/home/luiz_mateus/db-distribuidos/distributed-db (3)/distributed-db"
python3 node_server.py --config config/nodes_config.json --node-id 3
```

Aguarde cada nó exibir:
```
*** Nó X ATIVO ***
```

---

## 6. Iniciar o cliente

**Terminal 4:**
```bash
cd "/home/luiz_mateus/db-distribuidos/distributed-db (3)/distributed-db"
python3 client_app.py --config config/nodes_config.json
```

---

## 7. Queries de exemplo

### INSERT — inserir registros

```sql
INSERT INTO users (name, email) VALUES ('Alice Silva', 'alice@email.com');
INSERT INTO users (name, email) VALUES ('Bruno Costa', 'bruno@email.com');
INSERT INTO users (name, email) VALUES ('Carla Souza', 'carla@email.com');
INSERT INTO users (name, email) VALUES ('Daniel Lima', 'daniel@email.com');
INSERT INTO users (name, email) VALUES ('Eva Martins', 'eva@email.com');
```

### SELECT — consultar registros

```sql
-- Todos os registros
SELECT * FROM users;

-- Por ID
SELECT * FROM users WHERE id = 1;

-- Por nome (parcial)
SELECT * FROM users WHERE name LIKE 'A%';

-- Contar registros
SELECT COUNT(*) FROM users;

-- Apenas nome e email
SELECT id, name, email FROM users;
```

### UPDATE — atualizar registros

```sql
UPDATE users SET name = 'Alice Oliveira' WHERE id = 1;
UPDATE users SET email = 'bruno.novo@email.com' WHERE name = 'Bruno Costa';
```

### DELETE — remover registros

```sql
DELETE FROM users WHERE id = 3;
DELETE FROM users WHERE email = 'eva@email.com';
```

---

## 8. Comandos especiais do cliente

```
nodes    # lista os nós configurados e seus endereços
stats    # exibe estatísticas de round-robin
help     # exibe ajuda com exemplos
exit     # sai da aplicação
```

---

## 9. Limpar o banco de dados

### Opção A — pelo cliente (apaga só os dados, mantém estrutura)

```sql
DELETE FROM users;
```

### Opção B — pelo MySQL (apaga e recria a tabela)

```bash
sudo mysql -u root <<'EOF'
USE ddb_node1; TRUNCATE TABLE users;
USE ddb_node2; TRUNCATE TABLE users;
USE ddb_node3; TRUNCATE TABLE users;
EOF
```

### Opção C — remoção completa (apaga tudo e reconfigura do zero)

```bash
sudo mysql -u root <<'EOF'
DROP DATABASE IF EXISTS ddb_node1;
DROP DATABASE IF EXISTS ddb_node2;
DROP DATABASE IF EXISTS ddb_node3;
DROP USER IF EXISTS 'ddb_user'@'localhost';
DROP USER IF EXISTS 'ddb_user'@'%';
EOF
```

Depois execute o setup novamente:

```bash
sudo mysql -u root < setup_mysql.sql
```

---

## 10. Parar o sistema

- Nos terminais dos nós: `Ctrl+C`
- No terminal do cliente: `exit` ou `Ctrl+C`

---

## Solução de problemas

| Sintoma | Causa provável | Solução |
|---|---|---|
| `Timeout ao conectar ao nó X` | Nó não está rodando | Inicie o nó no terminal correspondente |
| `Falha ao conectar ao MySQL` | MySQL parado ou credenciais erradas | `sudo service mysql start` e reexecute `setup_mysql.sql` |
| `Access denied for user 'ddb_user'` | Permissões não configuradas | Reexecute `setup_mysql.sql` |
| `Address already in use` | Nó já está rodando nessa porta | Encerre o processo anterior com `Ctrl+C` |
