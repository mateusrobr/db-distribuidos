# 🚀 Setup Rápido - Máquinas Diferentes

## Cenário: 3 Computadores na mesma rede

---

## PASSO 1: Descobrir IPs

Execute em cada máquina:

**Windows:**
```cmd
ipconfig
```
Anote o "IPv4 Address"

**Linux/Mac:**
```bash
ip addr show
# OU
ifconfig
```
Anote o "inet"

**Exemplo de IPs:**
```
Máquina 1: 192.168.1.10
Máquina 2: 192.168.1.20
Máquina 3: 192.168.1.30
```

---

## PASSO 2: Preparar CADA Máquina

Execute em TODAS as 3 máquinas:

### 2.1 Extrair projeto
```bash
unzip distributed-db.zip
cd distributed-db
```

### 2.2 Instalar Docker

**Linux:**
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo usermod -aG docker $USER
# Faça logout e login novamente
```

**Windows/Mac:**
- Baixe: https://www.docker.com/products/docker-desktop
- Instale e inicie

### 2.3 Instalar Python
```bash
pip install -r requirements.txt
```

---

## PASSO 3: Configurar Firewall

**Em TODAS as 3 máquinas:**

**Linux:**
```bash
sudo ufw allow 5001/tcp
sudo ufw enable
```

**Windows (PowerShell como Admin):**
```powershell
New-NetFirewallRule -DisplayName "DDB" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow
```

---

## PASSO 4: Criar Arquivo de Configuração

**Crie `config/nodes_config_distributed.json` IGUAL em todas as 3 máquinas:**

```json
{
  "nodes": [
    {
      "node_id": 1,
      "network": {
        "host": "192.168.1.10",
        "port": 5001
      },
      "database": {
        "host": "localhost",
        "port": 3306,
        "user": "ddb_user",
        "password": "ddb_password",
        "database": "ddb_node1"
      }
    },
    {
      "node_id": 2,
      "network": {
        "host": "192.168.1.20",
        "port": 5001
      },
      "database": {
        "host": "localhost",
        "port": 3306,
        "user": "ddb_user",
        "password": "ddb_password",
        "database": "ddb_node2"
      }
    },
    {
      "node_id": 3,
      "network": {
        "host": "192.168.1.30",
        "port": 5001
      },
      "database": {
        "host": "localhost",
        "port": 3306,
        "user": "ddb_user",
        "password": "ddb_password",
        "database": "ddb_node3"
      }
    }
  ]
}
```

**⚠️ SUBSTITUA os IPs pelos IPs reais das suas máquinas!**

---

## PASSO 5: Iniciar MySQL

**Execute em cada máquina (ajustando o database):**

### MÁQUINA 1:
```bash
cd distributed-db

# Edite o database no docker-compose-single.yml
# Mude MYSQL_DATABASE para ddb_node1

docker-compose -f docker-compose-single.yml up -d
sleep 30
```

### MÁQUINA 2:
```bash
cd distributed-db

# Edite docker-compose-single.yml
# Mude MYSQL_DATABASE para ddb_node2
# Mude container_name para ddb_mysql_node2

docker-compose -f docker-compose-single.yml up -d
sleep 30
```

### MÁQUINA 3:
```bash
cd distributed-db

# Edite docker-compose-single.yml
# Mude MYSQL_DATABASE para ddb_node3
# Mude container_name para ddb_mysql_node3

docker-compose -f docker-compose-single.yml up -d
sleep 30
```

**OU use este comando para editar automaticamente:**

**MÁQUINA 1:**
```bash
cat > docker-compose-node1.yml << 'EOF'
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: ddb_mysql_node1
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: ddb_node1
      MYSQL_USER: ddb_user
      MYSQL_PASSWORD: ddb_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
volumes:
  mysql_data:
EOF

docker-compose -f docker-compose-node1.yml up -d
```

**MÁQUINA 2:**
```bash
cat > docker-compose-node2.yml << 'EOF'
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: ddb_mysql_node2
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: ddb_node2
      MYSQL_USER: ddb_user
      MYSQL_PASSWORD: ddb_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
volumes:
  mysql_data:
EOF

docker-compose -f docker-compose-node2.yml up -d
```

**MÁQUINA 3:**
```bash
cat > docker-compose-node3.yml << 'EOF'
version: '3.8'
services:
  mysql:
    image: mysql:8.0
    container_name: ddb_mysql_node3
    environment:
      MYSQL_ROOT_PASSWORD: root123
      MYSQL_DATABASE: ddb_node3
      MYSQL_USER: ddb_user
      MYSQL_PASSWORD: ddb_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
volumes:
  mysql_data:
EOF

docker-compose -f docker-compose-node3.yml up -d
```

---

## PASSO 6: Testar Conectividade

**Da MÁQUINA 1:**
```bash
ping 192.168.1.20  # Máquina 2
ping 192.168.1.30  # Máquina 3
```

Se funcionar, está OK! ✅

---

## PASSO 7: Iniciar os Nós

**MÁQUINA 1:**
```bash
cd distributed-db
python3 node_server.py --config config/nodes_config_distributed.json --node-id 1
```

**MÁQUINA 2:**
```bash
cd distributed-db
python3 node_server.py --config config/nodes_config_distributed.json --node-id 2
```

**MÁQUINA 3:**
```bash
cd distributed-db
python3 node_server.py --config config/nodes_config_distributed.json --node-id 3
```

Aguarde ver mensagens de conexão entre os nós! 🎉

---

## PASSO 8: Rodar Cliente

**De qualquer máquina:**
```bash
cd distributed-db
python3 client_app.py --config config/nodes_config_distributed.json
```

**Teste:**
```sql
DDB> INSERT INTO users (name, email) VALUES ('Teste', 'teste@example.com');
DDB> SELECT * FROM users;
```

---

## PASSO 9: Verificar Replicação

**Em cada máquina, verifique o MySQL:**

**MÁQUINA 1:**
```bash
docker exec -it ddb_mysql_node1 mysql -u ddb_user -pddb_password ddb_node1 -e "SELECT * FROM users;"
```

**MÁQUINA 2:**
```bash
docker exec -it ddb_mysql_node2 mysql -u ddb_user -pddb_password ddb_node2 -e "SELECT * FROM users;"
```

**MÁQUINA 3:**
```bash
docker exec -it ddb_mysql_node3 mysql -u ddb_user -pddb_password ddb_node3 -e "SELECT * FROM users;"
```

**Todos devem ter os mesmos dados!** ✅

---

## ✅ Checklist

- [ ] Descobriu IPs das 3 máquinas
- [ ] Criou `nodes_config_distributed.json` com IPs corretos
- [ ] Liberou porta 5001 no firewall
- [ ] Docker rodando nas 3 máquinas
- [ ] MySQL iniciado em cada máquina
- [ ] `ping` funciona entre máquinas
- [ ] 3 nós DDB rodando
- [ ] Cliente conecta
- [ ] Dados replicam

---

## 🐛 Problemas Comuns

**"Connection refused":**
- Verifique firewall: `sudo ufw status`
- Verifique IP: `ip addr show`
- Teste porta: `telnet 192.168.1.20 5001`

**"Can't connect to MySQL":**
```bash
docker ps  # Deve mostrar container rodando
docker logs ddb_mysql_node1  # Ver erros
```

**Nós não se comunicam:**
- Verifique IPs no `nodes_config_distributed.json`
- Use IPs corretos (não use 127.0.0.1)
- Teste ping entre máquinas

---

**Pronto! Sistema distribuído funcionando! 🌐🚀**
