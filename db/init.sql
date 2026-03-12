-- 智慧党建系统数据库初始化脚本
-- 数据库名: party_building
-- 默认管理员账号: admin / admin123

-- 创建数据库
CREATE DATABASE IF NOT EXISTS party_building DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE party_building;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '加密后的密码',
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user' COMMENT '角色: admin-管理员, user-普通用户',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 党建内容表
CREATE TABLE IF NOT EXISTS contents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL COMMENT '标题',
    body TEXT NOT NULL COMMENT '正文内容',
    images JSON COMMENT '图片路径数组',
    author_id INT NOT NULL COMMENT '作者ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_author (author_id),
    INDEX idx_created (created_at),
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='党建内容表';

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content_id INT NOT NULL COMMENT '关联内容ID',
    user_id INT NOT NULL COMMENT '评论者ID',
    body TEXT NOT NULL COMMENT '评论内容',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
    INDEX idx_content (content_id),
    INDEX idx_user (user_id),
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论表';

-- 点赞表
CREATE TABLE IF NOT EXISTS likes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content_id INT NOT NULL COMMENT '关联内容ID',
    user_id INT NOT NULL COMMENT '点赞者ID',
    created_at DATE NOT NULL COMMENT '点赞日期',
    UNIQUE KEY uk_user_content_date (content_id, user_id, created_at),
    INDEX idx_content (content_id),
    INDEX idx_user (user_id),
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='点赞表';

-- 访问统计表
CREATE TABLE IF NOT EXISTS visits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    visit_date DATE NOT NULL COMMENT '访问日期',
    visit_count INT NOT NULL DEFAULT 0 COMMENT '访问次数',
    UNIQUE KEY uk_date (visit_date),
    INDEX idx_visit_date (visit_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='访问统计表';

-- 插入默认管理员账号
-- 密码: admin123 (bcrypt加密)
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$2b$12$2/wUkdCo.92EEUelZFH9i.Jc0qZYt3JH2.Tsl89qoWWXkXoA0Y6Z6', 'admin')
ON DUPLICATE KEY UPDATE username=username;

-- 初始化访问统计（当天）
INSERT INTO visits (visit_date, visit_count) VALUES (CURDATE(), 0)
ON DUPLICATE KEY UPDATE visit_count=visit_count;
