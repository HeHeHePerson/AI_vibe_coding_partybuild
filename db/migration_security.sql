-- 登录安全增强数据库迁移脚本
-- 执行此脚本添加登录尝试记录表和用户锁定字段

-- 创建登录尝试记录表
CREATE TABLE IF NOT EXISTS login_attempts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    success TINYINT(1) NOT NULL DEFAULT 0,
    ip_address VARCHAR(45) NOT NULL,
    attempt_time DATETIME NOT NULL,
    INDEX idx_username_time (username, attempt_time),
    INDEX idx_ip_time (ip_address, attempt_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 添加用户锁定字段和扩展信息
ALTER TABLE users ADD COLUMN locked_until DATETIME NULL;
ALTER TABLE users ADD COLUMN failed_login_attempts INT NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN last_login_at DATETIME NULL;
ALTER TABLE users ADD COLUMN avatar VARCHAR(500) NULL;
ALTER TABLE users ADD COLUMN bio VARCHAR(500) NULL;
ALTER TABLE users ADD COLUMN email VARCHAR(100) NULL;
ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL;

-- 创建操作日志表
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    username VARCHAR(50) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    detail TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_time (user_id, created_at),
    INDEX idx_operation_time (operation, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建分类表
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    description VARCHAR(500) NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建标签表
CREATE TABLE IF NOT EXISTS tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(20) NOT NULL,
    color VARCHAR(20) NOT NULL DEFAULT '#1890ff',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 创建内容-标签关联表
CREATE TABLE IF NOT EXISTS content_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content_id INT NOT NULL,
    tag_id INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_content_tag (content_id, tag_id),
    INDEX idx_content_id (content_id),
    INDEX idx_tag_id (tag_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 为内容表添加分类ID字段
ALTER TABLE contents ADD COLUMN category_id INT NULL;
ALTER TABLE contents ADD INDEX idx_category_id (category_id);
