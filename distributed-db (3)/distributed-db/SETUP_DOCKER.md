# 🐳 Setup Rápido com Docker - DDB

## ✅ Pré-requisito: Instalar Docker

### Windows / macOS:
1. Baixe Docker Desktop: https://www.docker.com/products/docker-desktop
2. Instale e inicie o Docker Desktop
3. Aguarde até aparecer "Docker Desktop is running"

### Linux (Ubuntu/Debian):
```bash
# Instalar Docker
sudo apt update
sudo apt install docker.io docker-compose -y

# Iniciar serviço
sudo systemctl start docker
sudo systemctl enable docker

# Adicionar seu usuário ao grupo docker (para não precisar de sudo)
sudo usermod -aG docker $USER

# IMPORTANTE: Faça logout e login novamente para aplicar
```

### Verificar se Docker está instalado:
```bash
docker --version
docker-compose --version
```

Se mostrar as versões, está pronto! ✅

---

## 🚀 PASSO A PASSO COMPLETO

### 1️⃣ Extrair e entrar no projeto

```bash
# Extrair o ZIP
unzip distributed-db.zip
cd distributed-db
```

### 2️⃣ Verificar arquivos necessários

```bash
# Deve ter estes arquivos:
ls -l docker-compose.yml  # ✓
ls -l init.sql           # ✓
```

### 3️⃣ Iniciar os 3 MySQL com Docker

```bash
# Baixa as imagens e inicia os containers
docker-compose up -d
```

**Saída esperada:**
```
Creating network "distributed-db_default" with the default driver
Creating volume "distributed-db_mysql_data1" with default driver
Creating volume "distributed-db_mysql_data2" with default driver
Creating volume "distributed-db_mysql_data3" with default driver
Creating ddb_mysql_node1 ... done
Creating ddb_mysql_node2 ... done
Creating ddb_mysql_node3 ... done
```

### 4️⃣ Aguardar MySQL inicializar (importante!)

```bash
# Aguarde 30 segundos para garantir que tudo iniciou
sleep 30

# OU verifique o status:
docker-compose ps
```

**Deve mostrar 3 containers "Up" e "healthy":**
```
NAME              STATUS
ddb_mysql_node1   Up 30 seconds (healthy)
ddb_mysql_node2   Up 30 seconds (healthy)
ddb_mysql_node3   Up 30 seconds (healthy)
```

### 5️⃣ Verificar se MySQL está funcionando

```bash
# Teste conectar no primeiro banco
docker exec -it ddb_mysql_node1 mysql -u ddb_user -pddb_password -e "SHOW DATABASES;"
```

**Deve mostrar:**
```
+--------------------+
| Database           |
+--------------------+
| ddb_node1          |
| information_schema |
+--------------------+
```

**Teste os outros 2:**
```bash
docker exec -it ddb_mysql_node2 mysql -u ddb_user -pddb_password -e "SHOW DATABASES;"
docker exec -it ddb_mysql_node3 mysql -u ddb_user -pddb_password -e "SHOW DATABASES;"
```

### 6️⃣ Verificar se a tabela foi criada automaticamente

```bash
docker exec -it ddb_mysql_node1 mysql -u ddb_user -pddb_password ddb_node1 -e "SHOW TABLES;"
```

**Deve mostrar:**
```
+---------------------+
| Tables_in_ddb_node1 |
+---------------------+
| users               |
+---------------------+
```

✅ **Se tudo acima funcionou, o MySQL está 100% pronto!**

### 7️⃣ Instalar dependências Python

```bash
pip install -r requirements.txt
```

### 8️⃣ Testar componentes

```bash
python3 test_components.py
```

**Deve mostrar:**
```
================================================================================
  RESULTADO: 5 passou, 0 falhou
================================================================================
```

---

## 🎯 AGORA EXECUTAR O DDB!

### Abra 4 terminais diferentes:

**Terminal 1 - Nó 1:**
```bash
cd distributed-db
python3 node_server.py --config config/nodes_config.json --node-id 1
```

**Terminal 2 - Nó 2:**
```bash
cd distributed-db
python3 node_server.py --config config/nodes_config.json --node-id 2
```

**Terminal 3 - Nó 3:**
```bash
cd distributed-db
python3 node_server.py --config config/nodes_config.json --node-id 3
```

**Terminal 4 - Cliente:**
```bash
cd distributed-db
python3 client_app.py --config config/nodes_config.json
```

### Testar no cliente:

```sql
DDB> INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
DDB> SELECT * FROM users;
DDB> INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com');
DDB> SELECT * FROM users;
```

---

## 🎉 PRONTO! Sistema funcionando!

### Verificar que replicação funcionou:

```bash
# Abra um 5º terminal e verifique cada banco:
docker exec -it ddb_mysql_node1 mysql -u ddb_user -pddb_password ddb_node1 -e "SELECT * FROM users;"
docker exec -it ddb_mysql_node2 mysql -u ddb_user -pddb_password ddb_node2 -e "SELECT * FROM users;"
docker exec -it ddb_mysql_node3 mysql -u ddb_user -pddb_password ddb_node3 -e "SELECT * FROM users;"
```

**Todos os 3 devem mostrar os mesmos dados!** ✅

---

## 🛑 Comandos Úteis do Docker

### Parar tudo:
```bash
docker-compose down
```

### Parar e apagar dados (recomeçar do zero):
```bash
docker-compose down -v
```

### Ver logs dos containers:
```bash
docker-compose logs -f
# Ou de um específico:
docker logs ddb_mysql_node1 -f
```

### Reiniciar os containers:
```bash
docker-compose restart
```

### Ver status:
```bash
docker-compose ps
```

### Entrar no MySQL manualmente:
```bash
# Nó 1
docker exec -it ddb_mysql_node1 mysql -u ddb_user -pddb_password ddb_node1

# Nó 2
docker exec -it ddb_mysql_node2 mysql -u ddb_user -pddb_password ddb_node2

# Nó 3
docker exec -it ddb_mysql_node3 mysql -u ddb_user -pddb_password ddb_node3
```

---

## 🐛 Resolução de Problemas

### Erro: "port is already allocated"

**Problema:** Porta 3306, 3307 ou 3308 já está em uso.

**Solução:**
```bash
# Ver o que está usando a porta
# Windows:
netstat -ano | findstr :3306

# Linux/Mac:
sudo lsof -i :3306

# Parar o processo ou mudar as portas no docker-compose.yml
```

### Erro: "Cannot connect to the Docker daemon"

**Problema:** Docker não está rodando.

**Solução:**
- **Windows/Mac:** Abra o Docker Desktop
- **Linux:** `sudo systemctl start docker`

### Containers não ficam "healthy"

```bash
# Ver logs para identificar o problema
docker logs ddb_mysql_node1

# Comum: MySQL ainda está inicializando, aguarde mais tempo
sleep 60
docker-compose ps
```

### Erro de conexão do Python com MySQL

```bash
# Verificar se as portas estão corretas
docker-compose ps

# Deve mostrar:
# ddb_mysql_node1  0.0.0.0:3306->3306/tcp
# ddb_mysql_node2  0.0.0.0:3307->3306/tcp
# ddb_mysql_node3  0.0.0.0:3308->3306/tcp

# Se estiver diferente, edite config/nodes_config.json
```

---

## 📊 Resumo dos Serviços

| Serviço | Porta Host | Container | Usuário | Senha | Banco |
|---------|------------|-----------|---------|-------|-------|
| Node 1  | 3306       | ddb_mysql_node1 | ddb_user | ddb_password | ddb_node1 |
| Node 2  | 3307       | ddb_mysql_node2 | ddb_user | ddb_password | ddb_node2 |
| Node 3  | 3308       | ddb_mysql_node3 | ddb_user | ddb_password | ddb_node3 |

---

## ✅ Checklist Final

- [ ] Docker Desktop instalado e rodando
- [ ] `docker-compose up -d` executado
- [ ] 3 containers "healthy" (`docker-compose ps`)
- [ ] Tabela `users` existe em todos os bancos
- [ ] `pip install -r requirements.txt` executado
- [ ] `test_components.py` passou
- [ ] 3 nós DDB rodando (Terminais 1, 2, 3)
- [ ] Cliente conecta (Terminal 4)
- [ ] INSERT replica para todos os bancos

**Se todos marcados: SUCESSO TOTAL! 🎉**

---

## 💡 Dica: Script Automático

Crie um arquivo `start.sh` (Linux/Mac) ou `start.bat` (Windows):

**start.sh:**
```bash
#!/bin/bash
echo "🐳 Iniciando MySQL com Docker..."
docker-compose up -d
echo "⏳ Aguardando MySQL inicializar..."
sleep 30
echo "✅ MySQL pronto!"
echo "📊 Status:"
docker-compose ps
echo ""
echo "🚀 Agora execute em terminais separados:"
echo "   python3 node_server.py --config config/nodes_config.json --node-id 1"
echo "   python3 node_server.py --config config/nodes_config.json --node-id 2"
echo "   python3 node_server.py --config config/nodes_config.json --node-id 3"
echo "   python3 client_app.py --config config/nodes_config.json"
```

Torne executável e rode:
```bash
chmod +x start.sh
./start.sh
```

---

**Pronto para usar! 🚀**
