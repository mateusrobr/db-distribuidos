-- Script de inicialização automática para containers MySQL
-- Este arquivo é executado automaticamente quando o container inicia

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir alguns dados de exemplo (opcional)
-- INSERT INTO users (name, email) VALUES ('Sistema', 'sistema@ddb.com');
