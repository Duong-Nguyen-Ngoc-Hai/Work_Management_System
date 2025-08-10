CREATE DATABASE IF NOT EXISTS work_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Use the database
USE work_management;

-- Grant privileges
GRANT ALL PRIVILEGES ON work_management.* TO 'work_user'@'%';
FLUSH PRIVILEGES;