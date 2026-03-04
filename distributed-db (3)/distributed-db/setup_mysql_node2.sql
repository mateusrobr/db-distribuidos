-- Configuração do MySQL para o Nó 2
-- Execute em Máquina 2: sudo mysql -u root < setup_mysql_node2.sql

CREATE USER IF NOT EXISTS 'ddb_user'@'localhost' IDENTIFIED BY 'ddb_password';
CREATE USER IF NOT EXISTS 'ddb_user'@'%' IDENTIFIED BY 'ddb_password';

CREATE DATABASE IF NOT EXISTS ddb_node2;

GRANT ALL PRIVILEGES ON ddb_node2.* TO 'ddb_user'@'localhost';
GRANT ALL PRIVILEGES ON ddb_node2.* TO 'ddb_user'@'%';

FLUSH PRIVILEGES;

USE ddb_node2;
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
