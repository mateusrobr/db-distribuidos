# Demonstração Prática do DDB

## 🎬 Cenários de Demonstração

### Cenário 1: Inserção e Replicação Automática

**Objetivo**: Demonstrar que uma inserção em um nó é automaticamente replicada para todos os outros.

```sql
-- 1. Execute no cliente
DDB> INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');

-- Resultado esperado:
📊 Resultado:
  • Nó executado: 2
  • Tempo: 0.053s
  • Status: ✓ Sucesso
  • Linhas afetadas: 1
```

**Logs esperados:**

**Nó 2 (executor):**
```
Executando query local: INSERT INTO users...
Query executada com sucesso em 0.032s - 1 linhas afetadas
Iniciando replicação da query: INSERT INTO users...
Replicação enviada para 2 nós
```

**Nó 1 (replicação):**
```
Replicando query do nó 2: INSERT INTO users...
Replicação executada com sucesso - 1 linhas afetadas
ACK de replicação enviado para nó 2
```

**Nó 3 (replicação):**
```
Replicando query do nó 2: INSERT INTO users...
Replicação executada com sucesso - 1 linhas afetadas
ACK de replicação enviado para nó 2
```

**Validação:**
```bash
# Conecte em cada MySQL e verifique
mysql -u ddb_user -p ddb_node1 -e "SELECT * FROM users WHERE name='Alice'"
mysql -u ddb_user -p ddb_node2 -e "SELECT * FROM users WHERE name='Alice'"
mysql -u ddb_user -p ddb_node3 -e "SELECT * FROM users WHERE name='Alice'"
# Todos devem retornar o mesmo registro!
```

---

### Cenário 2: Balanceamento de Carga (Round-Robin)

**Objetivo**: Demonstrar distribuição de queries entre nós.

```sql
-- Execute 6 SELECTs consecutivos
DDB> SELECT * FROM users;  # Vai para nó 1
DDB> SELECT * FROM users;  # Vai para nó 2
DDB> SELECT * FROM users;  # Vai para nó 3
DDB> SELECT * FROM users;  # Volta para nó 1
DDB> SELECT * FROM users;  # Vai para nó 2
DDB> SELECT * FROM users;  # Vai para nó 3
```

**Resultado esperado:**
```
📊 Resultado:
  • Nó executado: 1    # Primeira query
  
📊 Resultado:
  • Nó executado: 2    # Segunda query
  
📊 Resultado:
  • Nó executado: 3    # Terceira query
  
📊 Resultado:
  • Nó executado: 1    # Quarta query (volta ao início)
```

---

### Cenário 3: Eleição de Coordenador

**Objetivo**: Demonstrar algoritmo de eleição Bully quando coordenador falha.

**Passo 1 - Identificar coordenador atual:**
```bash
# Nos logs dos nós, procure por:
# "*** Nó X é o novo COORDENADOR ***"
# O nó com maior ID (3) deve ser o coordenador
```

**Passo 2 - Parar o coordenador:**
```bash
# No terminal do Nó 3, pressione Ctrl+C
```

**Passo 3 - Observar eleição:**

**Logs do Nó 2:**
```
Nó 3 sem heartbeat há 16s - marcando como INATIVO
Coordenador falhou - iniciando eleição
Nó 2 iniciando eleição
Nenhum nó com ID maior ativo
*** Nó 2 é o novo COORDENADOR ***
```

**Logs do Nó 1:**
```
Nó 3 sem heartbeat há 16s - marcando como INATIVO
Recebida eleição do nó 2 (maior que 1)
Nó 2 é o novo coordenador
```

**Passo 4 - Reiniciar nó anterior:**
```bash
# Reinicie o Nó 3
python3 node_server.py --config config/nodes_config.json --node-id 3

# Ele reconhece que Nó 2 é coordenador e não inicia nova eleição
```

---

### Cenário 4: Detecção de Nó Inativo

**Objetivo**: Demonstrar heartbeat detectando nós inativos.

**Passo 1 - Parar um nó não-coordenador:**
```bash
# Pare o Nó 1 (Ctrl+C)
```

**Passo 2 - Observar logs dos outros nós:**

**Após ~15 segundos:**
```
Nó 1 sem heartbeat há 16s - marcando como INATIVO
```

**Passo 3 - Tentar query:**
```sql
DDB> SELECT * FROM users;
# Query NÃO será enviada para Nó 1 (está inativo)
# Será distribuída apenas entre Nós 2 e 3
```

---

### Cenário 5: Two-Phase Commit (Transação Distribuída)

**Objetivo**: Demonstrar garantias ACID com 2PC.

**Cenário normal (todos os nós ativos):**

```sql
DDB> INSERT INTO users (name, email) VALUES ('Bob', 'bob@example.com');
```

**Fluxo interno:**
```
1. Cliente → Nó 2 [QUERY]
2. Nó 2 → Todos [PREPARE]
   - Nó 1: executa localmente → vota SIM
   - Nó 3: executa localmente → vota SIM
3. Nó 2 recebe todos os votos SIM
4. Nó 2 → Todos [COMMIT]
   - Todos commitam a transação
5. Nó 2 → Cliente [QUERY_RESPONSE: sucesso]
```

**Cenário com falha (simulado com query inválida):**

```sql
DDB> INSERT INTO users (name, email) VALUES ('Invalid', NULL);
# Email é NOT NULL, causará erro
```

**Fluxo interno:**
```
1. Cliente → Nó 2 [QUERY]
2. Nó 2 → Todos [PREPARE]
   - Nó 1: erro SQL → vota NÃO
   - Nó 3: erro SQL → vota NÃO
3. Nó 2 recebe votos NÃO
4. Nó 2 → Todos [ABORT]
   - Todos fazem rollback
5. Nó 2 → Cliente [QUERY_RESPONSE: erro]
```

---

### Cenário 6: Verificação de Checksum

**Objetivo**: Demonstrar validação de integridade com checksum.

Este cenário é automático - todo pacote enviado tem checksum calculado e validado.

**Para observar nos logs:**
```bash
# Adicione nível DEBUG ao logging
# No node_server.py, na função setup_logging:
logging.basicConfig(level=logging.DEBUG, ...)
```

**Logs esperados:**
```
Mensagem QUERY recebida: checksum válido [abc123...]
Mensagem REPLICATE enviada com checksum [def456...]
```

**Se checksum inválido (simulação de corrupção):**
```
⚠ Mensagem recebida com checksum inválido - descartada
```

---

### Cenário 7: Estatísticas de Carga

**Objetivo**: Visualizar distribuição de carga entre nós.

```sql
-- Execute várias queries
DDB> INSERT INTO users (name, email) VALUES ('User1', 'u1@example.com');
DDB> INSERT INTO users (name, email) VALUES ('User2', 'u2@example.com');
DDB> SELECT * FROM users;
DDB> UPDATE users SET name='UpdatedUser1' WHERE id=1;
DDB> SELECT COUNT(*) FROM users;
DDB> DELETE FROM users WHERE id=2;

-- Veja estatísticas
DDB> stats
```

**Resultado esperado:**
```
================================================================================
  ESTATÍSTICAS
================================================================================
Nós disponíveis: 3
Nó atual (Round-Robin): 0

Estatísticas de carga:
  • Nó 1: 2 queries executadas
  • Nó 2: 2 queries executadas
  • Nó 3: 2 queries executadas
  • Carga média: 2.0 queries/nó
  • Distribuição: Balanceada ✓
================================================================================
```

---

### Cenário 8: Teste de Consistência

**Objetivo**: Provar que dados estão consistentes em todos os nós.

**Script de teste:**
```bash
#!/bin/bash
# test_consistency.sh

echo "=== Teste de Consistência ==="

# 1. Inserir dados via DDB
python3 client_app.py --config config/nodes_config.json \
  --query "INSERT INTO users (name, email) VALUES ('TestUser', 'test@example.com')"

# 2. Aguardar replicação
sleep 2

# 3. Verificar em cada nó
echo "Verificando Nó 1:"
mysql -u ddb_user -pddb_password ddb_node1 -e "SELECT * FROM users WHERE name='TestUser'"

echo "Verificando Nó 2:"
mysql -u ddb_user -pddb_password ddb_node2 -e "SELECT * FROM users WHERE name='TestUser'"

echo "Verificando Nó 3:"
mysql -u ddb_user -pddb_password ddb_node3 -e "SELECT * FROM users WHERE name='TestUser'"

echo "=== Se todos mostrarem o mesmo registro, consistência OK! ==="
```

---

## 📊 Dashboard de Monitoramento (Conceitual)

Se você quiser visualizar em tempo real, pode adicionar queries como:

```sql
-- Ver quantos registros cada nó tem
DDB> SELECT COUNT(*) FROM users;

-- Executar em cada nó diretamente
mysql -u ddb_user -p ddb_node1 -e "SELECT COUNT(*) FROM users"
mysql -u ddb_user -p ddb_node2 -e "SELECT COUNT(*) FROM users"
mysql -u ddb_user -p ddb_node3 -e "SELECT COUNT(*) FROM users"
# Devem ter o mesmo número!
```

---

## 🎯 Checklist de Validação Completa

Execute estes testes para validar todas as funcionalidades:

- [ ] **Replicação**: INSERT replicado em todos os nós
- [ ] **Load Balancing**: SELECTs distribuídos (round-robin)
- [ ] **Eleição**: Novo coordenador eleito quando atual falha
- [ ] **Heartbeat**: Nó inativo detectado em ~15s
- [ ] **2PC**: Transação com sucesso comita em todos
- [ ] **2PC Rollback**: Transação com erro aborta em todos
- [ ] **Checksum**: Mensagens validadas (ver logs debug)
- [ ] **Consistência**: Mesmos dados em todos os nós
- [ ] **ACID**: Inserções aparecem completamente ou não aparecem
- [ ] **Tipos de comunicação**:
  - [ ] UNICAST: Resposta de query
  - [ ] BROADCAST: Heartbeat, eleição, replicação
  - [ ] MULTICAST: Eleição para nós específicos

---

**Pronto para demonstrar! 🚀**

Cada cenário demonstra uma funcionalidade específica do DDB conforme os requisitos.
