# 🌐 Guia para Testar em Computadores Diferentes

## 📋 Visão Geral

Vamos configurar o DDB em **3 computadores diferentes** (ou máquinas virtuais):

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   MÁQUINA 1     │         │   MÁQUINA 2     │         │   MÁQUINA 3     │
│  IP: 192.168.1.10│◄───────►│ IP: 192.168.1.20│◄───────►│ IP: 192.168.1.30│
│                 │         │                 │         │                 │
│  - Nó 1 (5001)  │         │  - Nó 2 (5001)  │         │  - Nó 3 (5001)  │
│  - MySQL (3306) │         │  - MySQL (3306) │         │  - MySQL (3306) │
└─────────────────┘         └─────────────────┘         └─────────────────┘
        ▲                           ▲                           ▲
        │                           │                           │
        └───────────────────────────┴───────────────────────────┘
                                    │
                            ┌───────┴────────┐
                            │  CLIENTE       │
                            │  (Qualquer PC) │
                            └────────────────┘
```

---

## 🎯 CENÁRIO 1: Rede Local (Mesma WiFi/LAN)

### Pré-requisitos:

- **3 computadores** na mesma rede (ou VMs)
- **Sistema operacional**: Windows, Linux ou Mac (pode misturar)
- **Conexão de rede** entre os computadores

---

## 📝 PASSO A PASSO COMPLETO

### ETAPA 1: Descobrir IPs das Máquinas

Execute em cada máquina para descobrir o IP:

**Windows:**
```cmd
ipconfig
```
Procure por "IPv4 Address" em "Ethernet adapter" ou "Wireless LAN adapter"

**Linux/Mac:**
```bash
ip addr show
# OU
ifconfig
```
Procure por "inet" (geralmente em eth0 ou wlan0)

**Anote os IPs:**
```
Máquina 1: 192.168.1.10  (exemplo)
Máquina 2: 192.168.1.20  (exemplo)
Máquina 3: 192.168.1.30  (exemplo)
```

### ETAPA 2: Preparar Cada Máquina

**Execute em TODAS as 3 máquinas:**

#### 2.1 Baixar e extrair o projeto

```bash
# Em cada máquina, baixe o distributed-db.zip
unzip distributed-db.zip
cd distributed-db
```

#### 2.2 Instalar Python e dependências

```bash
# Verificar Python
python3 --version

# Instalar dependências
pip install -r requirements.txt
```

#### 2.3 Instalar Docker (em cada máquina)

**Linux:**
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl start docker
sudo usermod -aG docker $USER
# Faça logout e login
```

**Windows/Mac:**
- Baixe Docker Desktop: https://www.docker.com/products/docker-desktop

---

### ETAPA 3: Configurar Firewall (IMPORTANTE!)

**Em TODAS as 3 máquinas, libere as portas:**

**Linux (Ubuntu/Debian):**
```bash
# Liberar porta do nó DDB
sudo ufw allow 5001/tcp

# Liberar MySQL (se quiser acessar de outras máquinas)
sudo ufw allow 3306/tcp

# Ativar firewall
sudo ufw enable

# Verificar
sudo ufw status
```

**Windows:**
```powershell
# Execute como Administrador no PowerShell
New-NetFirewallRule -DisplayName "DDB Node" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "MySQL" -Direction Inbound -LocalPort 3306 -Protocol TCP -Action Allow
```

**Mac:**
```bash
# No Mac, geralmente não precisa configurar firewall para rede local
# Se tiver problemas, desative temporariamente:
# System Preferences → Security & Privacy → Firewall
```

---

### ETAPA 4: Criar Arquivo de Configuração

**Crie um arquivo `config/nodes_config_distributed.json` IGUAL em todas as 3 máquinas:**

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

**⚠️ IMPORTANTE: Substitua os IPs pelos IPs REAIS das suas máquinas!**

---

### ETAPA 5: Iniciar MySQL em Cada Máquina

**MÁQUINA 1:**
```bash
cd distributed-db

# Edite docker-compose.yml para usar apenas 1 MySQL
# Ou crie docker-compose-single.yml:
cat > docker-compose-single.yml << 'EOF'
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

docker-compose -f docker-compose-single.yml up -d
```

**MÁQUINA 2:**
```bash
cd distributed-db

# Criar docker-compose para nó 2
cat > docker-compose-single.yml << 'EOF'
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

docker-compose -f docker-compose-single.yml up -d
```

**MÁQUINA 3:**
```bash
cd distributed-db

# Criar docker-compose para nó 3
cat > docker-compose-single.yml << 'EOF'
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

docker-compose -f docker-compose-single.yml up -d
```

**Aguarde 30 segundos em cada máquina:**
```bash
sleep 30
```

---

### ETAPA 6: Testar Conectividade Entre Máquinas

**Da MÁQUINA 1, teste conexão com MÁQUINAS 2 e 3:**

```bash
# Testar conectividade de rede
ping 192.168.1.20  # IP da Máquina 2
ping 192.168.1.30  # IP da Máquina 3

# Testar se a porta 5001 está acessível (quando o nó estiver rodando)
# Use telnet ou nc:
nc -zv 192.168.1.20 5001
nc -zv 192.168.1.30 5001
```

**Se ping não funcionar:**
- Verifique firewall
- Verifique se estão na mesma rede
- Tente desabilitar firewall temporariamente para testar

---

### ETAPA 7: Iniciar os Nós DDB

**MÁQUINA 1:**
```bash
cd distributed-db
python3 node_server.py --config config/nodes_config_distributed.json --node-id 1
```

**Aguarde ver:**
```
[NÓ 1] INFO - Servidor iniciado em 192.168.1.10:5001
[NÓ 1] INFO - *** Nó 1 ATIVO ***
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

**Observe os logs - você deve ver:**
```
[NÓ 1] INFO - Nova conexão de ('192.168.1.20', 54321)
[NÓ 2] INFO - Nova conexão de ('192.168.1.30', 54322)
...
[NÓ 3] INFO - *** Nó 3 é o novo COORDENADOR ***
```

✅ **Se os nós se conectaram, está funcionando!**

---

### ETAPA 8: Rodar Cliente

**Você pode rodar o cliente de QUALQUER máquina (1, 2, 3 ou outra):**

```bash
cd distributed-db
python3 client_app.py --config config/nodes_config_distributed.json
```

**Teste:**
```sql
DDB> INSERT INTO users (name, email) VALUES ('Distribuido', 'dist@example.com');
DDB> SELECT * FROM users;
```

---

### ETAPA 9: Verificar Replicação

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

**Todos devem mostrar os mesmos dados!** 🎉

---

## 🧪 Testes de Funcionalidades Distribuídas

### Teste 1: Replicação Entre Máquinas

1. Insira dados do cliente
2. Verifique que apareceu nas 3 máquinas
3. ✅ Replicação funcionando!

### Teste 2: Falha de Nó

1. Desligue a MÁQUINA 3 (coordenador)
2. Observe MÁQUINA 2 virar coordenador
3. Cliente continua funcionando
4. ✅ Eleição e tolerância a falhas funcionando!

### Teste 3: Partição de Rede

1. Desconecte MÁQUINA 1 da rede
2. MÁQUINAS 2 e 3 continuam operando
3. Reconecte MÁQUINA 1
4. Nó volta a participar do cluster
5. ✅ Recuperação de partição funcionando!

---

## 🌍 CENÁRIO 2: Internet (Computadores em Redes Diferentes)

Se quiser testar com computadores em locais diferentes (via internet):

### Opção A: VPN

1. Use uma VPN como **Hamachi** ou **ZeroTier**
2. Cria uma rede virtual entre as máquinas
3. Use os IPs da VPN no arquivo de configuração

### Opção B: Túneis SSH

1. Configure port forwarding:
```bash
# Na máquina remota, redirecione a porta
ssh -R 5001:localhost:5001 usuario@maquina-remota
```

### Opção C: Servidor na Nuvem

1. Alugue 3 VPS (AWS, DigitalOcean, etc.)
2. Use IPs públicos das VPS
3. Configure firewall para liberar portas

**Exemplo com AWS EC2:**
```
Máquina 1: ec2-user@54.123.45.67
Máquina 2: ec2-user@54.123.45.68
Máquina 3: ec2-user@54.123.45.69
```

---

## 📊 Monitoramento em Tempo Real

### Script de Monitoramento

Crie `monitor.sh` e rode em cada máquina:

```bash
#!/bin/bash
while true; do
    clear
    echo "=== MONITOR DO NÓ $(hostname) ==="
    echo ""
    echo "Container MySQL:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
    echo ""
    echo "Processos DDB:"
    ps aux | grep node_server | grep -v grep
    echo ""
    echo "Conexões Ativas:"
    netstat -an | grep 5001
    echo ""
    sleep 5
done
```

---

## 🐛 Problemas Comuns

### "Connection refused" entre nós

**Causa:** Firewall bloqueando ou IP errado

**Solução:**
```bash
# Teste conectividade
ping <IP_DO_OUTRO_NO>
telnet <IP_DO_OUTRO_NO> 5001

# Verifique firewall
sudo ufw status
sudo ufw allow 5001/tcp

# Teste se nó está escutando
netstat -tuln | grep 5001
```

### Nós não se comunicam

**Verifique:**
1. IPs corretos no `nodes_config_distributed.json`
2. Firewall liberado nas 3 máquinas
3. Todos na mesma rede (ou VPN)
4. Portas não estão sendo usadas por outro processo

### Latência alta

**Se estiver na internet:**
- Normal ter latência maior
- Ajuste timeouts no código se necessário
- Use servidores na mesma região geográfica

---

## 📝 Checklist de Deployment

**CADA MÁQUINA:**
- [ ] Python 3.8+ instalado
- [ ] Docker instalado e rodando
- [ ] Projeto extraído em `/path/to/distributed-db`
- [ ] `pip install -r requirements.txt` executado
- [ ] MySQL container rodando
- [ ] Firewall configurado (porta 5001)
- [ ] IP correto no `nodes_config_distributed.json`

**CONECTIVIDADE:**
- [ ] Ping funciona entre todas as máquinas
- [ ] Porta 5001 acessível entre máquinas
- [ ] Arquivo de configuração IGUAL em todas

**EXECUÇÃO:**
- [ ] Nó 1 rodando na Máquina 1
- [ ] Nó 2 rodando na Máquina 2
- [ ] Nó 3 rodando na Máquina 3
- [ ] Logs mostram conexões entre nós
- [ ] Coordenador eleito (maior ID)

**TESTES:**
- [ ] Cliente conecta
- [ ] INSERT replica para todas as máquinas
- [ ] SELECT faz load balancing
- [ ] Falha de coordenador dispara eleição
- [ ] Dados consistentes em todos os bancos

---

## 🎯 Exemplo Prático Real

**Cenário: 3 Notebooks na mesma WiFi**

```
Notebook 1 (Windows):  192.168.0.105 → Nó 1
Notebook 2 (Mac):      192.168.0.106 → Nó 2
Notebook 3 (Linux):    192.168.0.107 → Nó 3
```

1. Descubra IPs: `ipconfig` / `ifconfig`
2. Atualize `nodes_config_distributed.json` com IPs reais
3. Copie arquivo para os 3 notebooks
4. Libere firewall nos 3
5. Rode Docker em cada um
6. Inicie os nós
7. Cliente em qualquer um
8. **Funciona!** 🎉

---

## 💡 Dica: Testar com VMs

Se não tiver 3 computadores físicos, use **VirtualBox** ou **VMware**:

1. Crie 3 VMs Ubuntu
2. Configure rede em modo "Bridge" (para ter IPs diferentes)
3. Siga os passos normalmente
4. Cada VM será uma "máquina diferente"

---

**Pronto para ambiente distribuído real! 🌐🚀**
