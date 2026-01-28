-- Script de Configuração do MySQL para DDB
-- Execute este script em cada instância do MySQL

-- Cria usuário para o DDB
CREATE USER IF NOT EXISTS 'ddb_user'@'localhost' IDENTIFIED BY 'ddb_password';
CREATE USER IF NOT EXISTS 'ddb_user'@'%' IDENTIFIED BY 'ddb_password';

-- Cria bancos de dados para cada nó
CREATE DATABASE IF NOT EXISTS ddb_node1;
CREATE DATABASE IF NOT EXISTS ddb_node2;
CREATE DATABASE IF NOT EXISTS ddb_node3;

-- Concede permissões
GRANT ALL PRIVILEGES ON ddb_node1.* TO 'ddb_user'@'localhost';
GRANT ALL PRIVILEGES ON ddb_node1.* TO 'ddb_user'@'%';
GRANT ALL PRIVILEGES ON ddb_node2.* TO 'ddb_user'@'localhost';
GRANT ALL PRIVILEGES ON ddb_node2.* TO 'ddb_user'@'%';
GRANT ALL PRIVILEGES ON ddb_node3.* TO 'ddb_user'@'localhost';
GRANT ALL PRIVILEGES ON ddb_node3.* TO 'ddb_user'@'%';

FLUSH PRIVILEGES;

-- Tabela de exemplo (criar em cada banco)
USE ddb_node1;
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

USE ddb_node2;
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

USE ddb_node3;
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
