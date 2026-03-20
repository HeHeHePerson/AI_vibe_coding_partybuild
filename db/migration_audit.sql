-- 用户审计日志数据库迁移脚本
-- 执行此脚本确保 operation_logs 表已存在

-- 如果 operation_logs 表不存在，创建它
CREATE TABLE IF NOT EXISTS operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    username VARCHAR(50) NOT NULL,
    operation VARCHAR(100) NOT NULL COMMENT '操作类型: login_success/login_failed/logout/create_content/create_comment等',
    detail TEXT COMMENT '操作详情(JSON格式)',
    ip_address VARCHAR(45) COMMENT '客户端IP地址',
    user_agent VARCHAR(255) COMMENT '浏览器User-Agent',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_time (user_id, created_at),
    INDEX idx_operation_time (operation, created_at),
    INDEX idx_username_time (username, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作审计日志表';
