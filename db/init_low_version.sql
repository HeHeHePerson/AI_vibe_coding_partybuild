-- 智慧党建系统数据库初始化脚本（低版本MySQL兼容）
-- 数据库名: party_building
-- 默认管理员账号: admin / admin123
-- 版本: 2.0 (包含党建园地功能)
-- 更新日期: 2026-03-31
-- 兼容MySQL 5.5及以上版本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS party_building DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;

USE party_building;

-- ============================================
-- 1. 基础表结构
-- ============================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '加密后的密码',
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user' COMMENT '角色: admin-管理员, user-普通用户',
    avatar VARCHAR(255) DEFAULT NULL COMMENT '头像',
    bio TEXT DEFAULT NULL COMMENT '个人简介',
    email VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    phone VARCHAR(20) DEFAULT NULL COMMENT '电话',
    last_login_at DATETIME DEFAULT NULL COMMENT '最后登录时间',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='用户表';

-- 党建内容表
CREATE TABLE IF NOT EXISTS contents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL COMMENT '标题',
    body TEXT NOT NULL COMMENT '正文内容',
    images TEXT COMMENT '图片路径数组（JSON格式）',
    author_id INT NOT NULL COMMENT '作者ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_author (author_id),
    INDEX idx_created (created_at),
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='党建内容表';

-- 评论表
CREATE TABLE IF NOT EXISTS comments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    content_id INT NOT NULL COMMENT '关联内容ID',
    user_id INT NOT NULL COMMENT '评论者ID',
    body TEXT NOT NULL COMMENT '评论内容',
    parent_id INT DEFAULT NULL COMMENT '父评论ID，用于回复功能',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
    INDEX idx_content (content_id),
    INDEX idx_user (user_id),
    INDEX idx_parent (parent_id),
    FOREIGN KEY (content_id) REFERENCES contents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='评论表';

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='点赞表';

-- 评论点赞表
CREATE TABLE IF NOT EXISTS comment_likes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    comment_id INT NOT NULL COMMENT '评论ID',
    user_id INT NOT NULL COMMENT '点赞用户ID',
    created_at DATE NOT NULL COMMENT '点赞日期',
    UNIQUE KEY uk_comment_user_date (comment_id, user_id, created_at),
    INDEX idx_comment_id (comment_id),
    FOREIGN KEY (comment_id) REFERENCES comments(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='评论点赞表';

-- 访问统计表
CREATE TABLE IF NOT EXISTS visits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    visit_date DATE NOT NULL COMMENT '访问日期',
    visit_count INT NOT NULL DEFAULT 0 COMMENT '访问次数',
    UNIQUE KEY uk_date (visit_date),
    INDEX idx_visit_date (visit_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='访问统计表';

-- 公告表
CREATE TABLE IF NOT EXISTS notices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL COMMENT '公告标题',
    content TEXT NOT NULL COMMENT '公告内容',
    author_id INT NOT NULL COMMENT '发布者ID',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
    INDEX idx_created_at (created_at),
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='公告表';

-- ============================================
-- 2. 党建园地相关表
-- ============================================

-- 党建知识学习表
CREATE TABLE IF NOT EXISTS party_knowledge (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL COMMENT '标题',
    content TEXT NOT NULL COMMENT '内容',
    category VARCHAR(50) NOT NULL COMMENT '分类',
    author_id INT NOT NULL COMMENT '发布者ID',
    view_count INT DEFAULT 0 COMMENT '浏览量',
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'approved' COMMENT '审核状态: pending-待审核, approved-已通过, rejected-已拒绝',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_category (category),
    INDEX idx_author_id (author_id),
    INDEX idx_status (status),
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='党建知识学习';

-- 学习记录表
CREATE TABLE IF NOT EXISTS party_study_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    knowledge_id INT NOT NULL COMMENT '知识ID',
    study_time INT DEFAULT 0 COMMENT '学习时长（分钟）',
    completed TINYINT(1) DEFAULT 0 COMMENT '是否完成学习',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_user_knowledge (user_id, knowledge_id),
    INDEX idx_user_id (user_id),
    INDEX idx_knowledge_id (knowledge_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (knowledge_id) REFERENCES party_knowledge(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='学习记录';

-- 组织活动表
CREATE TABLE IF NOT EXISTS party_activities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL COMMENT '活动标题',
    content TEXT NOT NULL COMMENT '活动内容',
    start_time DATETIME NOT NULL COMMENT '开始时间',
    end_time DATETIME NOT NULL COMMENT '结束时间',
    location VARCHAR(255) NOT NULL COMMENT '活动地点',
    organizer VARCHAR(100) NOT NULL COMMENT '组织者',
    max_participants INT DEFAULT NULL COMMENT '最大参与人数',
    current_participants INT DEFAULT 0 COMMENT '当前参与人数',
    status ENUM('upcoming', 'ongoing', 'completed') DEFAULT 'upcoming' COMMENT '活动状态: upcoming-即将开始, ongoing-进行中, completed-已完成',
    review_status ENUM('pending', 'approved', 'rejected') DEFAULT 'approved' COMMENT '审核状态: pending-待审核, approved-已通过, rejected-已拒绝',
    author_id INT NOT NULL COMMENT '发布者ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_status (status),
    INDEX idx_review_status (review_status),
    INDEX idx_author_id (author_id),
    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='组织活动';

-- 活动参与表
CREATE TABLE IF NOT EXISTS activity_participants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    activity_id INT NOT NULL COMMENT '活动ID',
    user_id INT NOT NULL COMMENT '用户ID',
    status ENUM('registered', 'attended', 'absent') DEFAULT 'registered' COMMENT '参与状态: registered-已报名, attended-已参加, absent-未参加',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '报名时间',
    UNIQUE KEY uk_activity_user (activity_id, user_id),
    INDEX idx_activity_id (activity_id),
    INDEX idx_user_id (user_id),
    FOREIGN KEY (activity_id) REFERENCES party_activities(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='活动参与记录';

-- 党费缴纳表
CREATE TABLE IF NOT EXISTS party_fees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    amount DECIMAL(10,2) NOT NULL COMMENT '缴纳金额',
    payment_date DATE NOT NULL COMMENT '缴纳日期',
    payment_period VARCHAR(20) NOT NULL COMMENT '缴纳周期',
    status ENUM('pending', 'paid', 'overdue', 'completed') DEFAULT 'pending' COMMENT '缴费状态: pending-待处理, paid-已缴费/处理中, overdue-逾期, completed-处理完毕',
    payment_method VARCHAR(50) DEFAULT NULL COMMENT '缴费方式',
    remark VARCHAR(255) DEFAULT NULL COMMENT '备注',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_payment_date (payment_date),
    INDEX idx_status (status),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='党费缴纳记录';

-- 党员积分表
CREATE TABLE IF NOT EXISTS party_integral (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    points INT NOT NULL COMMENT '积分变动',
    reason VARCHAR(255) NOT NULL COMMENT '积分原因',
    type ENUM('add', 'deduct') NOT NULL COMMENT '积分类型: add-增加, deduct-扣除',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='党员积分记录';

-- 党员档案表
CREATE TABLE IF NOT EXISTS party_member_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    party_join_date DATE DEFAULT NULL COMMENT '入党日期',
    party_branch VARCHAR(100) DEFAULT NULL COMMENT '所属党支部',
    position VARCHAR(100) DEFAULT NULL COMMENT '党内职务',
    education VARCHAR(50) DEFAULT NULL COMMENT '学历',
    work_unit VARCHAR(255) DEFAULT NULL COMMENT '工作单位',
    address VARCHAR(255) DEFAULT NULL COMMENT '联系地址',
    emergency_contact VARCHAR(100) DEFAULT NULL COMMENT '紧急联系人',
    emergency_phone VARCHAR(20) DEFAULT NULL COMMENT '紧急联系电话',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci COMMENT='党员档案';

-- ============================================
-- 3. 初始化数据
-- ============================================

-- 插入默认管理员账号
-- 密码: admin123 (bcrypt加密)
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$2b$12$2/wUkdCo.92EEUelZFH9i.Jc0qZYt3JH2.Tsl89qoWWXkXoA0Y6Z6', 'admin')
ON DUPLICATE KEY UPDATE username=username;

-- 初始化访问统计（当天）
INSERT INTO visits (visit_date, visit_count) VALUES (CURDATE(), 0)
ON DUPLICATE KEY UPDATE visit_count=visit_count;

-- 插入党建知识分类示例数据
INSERT INTO party_knowledge (title, content, category, author_id, status) VALUES
('中国共产党章程', '中国共产党是中国工人阶级的先锋队，同时是中国人民和中华民族的先锋队...', '党章党规', 1, 'approved'),
('习近平新时代中国特色社会主义思想', '党的十九大把习近平新时代中国特色社会主义思想确立为党必须长期坚持的指导思想...', '理论学习', 1, 'approved'),
('党的历史', '中国共产党自1921年成立以来，已经走过了100多年的光辉历程...', '党史学习', 1, 'approved')
ON DUPLICATE KEY UPDATE title=title;

-- 插入测试活动
INSERT INTO party_activities (title, content, start_time, end_time, location, organizer, max_participants, author_id, status, review_status) VALUES
('党员大会', '讨论年度工作计划和党员发展事宜', DATE_ADD(NOW(), INTERVAL 7 DAY), DATE_ADD(NOW(), INTERVAL 7 DAY + INTERVAL 2 HOUR), '会议室', '党支部', 50, 1, 'upcoming', 'approved'),
('志愿服务活动', '社区清洁和关爱老人活动', DATE_ADD(NOW(), INTERVAL 14 DAY), DATE_ADD(NOW(), INTERVAL 14 DAY + INTERVAL 2 HOUR), '社区', '志愿服务队', 30, 1, 'upcoming', 'approved')
ON DUPLICATE KEY UPDATE title=title;

-- 插入党员档案
INSERT INTO party_member_profiles (user_id, party_join_date, party_branch, position) VALUES
(1, '2020-07-01', '第一党支部', '支部委员')
ON DUPLICATE KEY UPDATE user_id=user_id;

COMMIT;