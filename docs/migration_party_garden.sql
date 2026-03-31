-- 党建园地模块数据库迁移脚本
-- 版本：1.0
-- 日期：2024-01-15

USE party_building;

-- 1. 扩展users表，添加党员相关字段
ALTER TABLE `users` ADD COLUMN `avatar` VARCHAR(255) DEFAULT NULL COMMENT '头像';
ALTER TABLE `users` ADD COLUMN `bio` TEXT DEFAULT NULL COMMENT '个人简介';
ALTER TABLE `users` ADD COLUMN `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱';
ALTER TABLE `users` ADD COLUMN `phone` VARCHAR(20) DEFAULT NULL COMMENT '电话';
ALTER TABLE `users` ADD COLUMN `last_login_at` DATETIME DEFAULT NULL COMMENT '最后登录时间';

-- 2. 党建知识学习表
CREATE TABLE IF NOT EXISTS `party_knowledge` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NOT NULL COMMENT '标题',
  `content` TEXT NOT NULL COMMENT '内容',
  `category` VARCHAR(50) NOT NULL COMMENT '分类',
  `author_id` INT NOT NULL COMMENT '发布者ID',
  `view_count` INT DEFAULT 0 COMMENT '浏览量',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_category` (`category`),
  INDEX `idx_author_id` (`author_id`),
  FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='党建知识学习';

-- 3. 组织活动表
CREATE TABLE IF NOT EXISTS `party_activities` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NOT NULL COMMENT '活动标题',
  `content` TEXT NOT NULL COMMENT '活动内容',
  `start_time` DATETIME NOT NULL COMMENT '开始时间',
  `end_time` DATETIME NOT NULL COMMENT '结束时间',
  `location` VARCHAR(255) NOT NULL COMMENT '活动地点',
  `organizer` VARCHAR(100) NOT NULL COMMENT '组织者',
  `max_participants` INT DEFAULT NULL COMMENT '最大参与人数',
  `current_participants` INT DEFAULT 0 COMMENT '当前参与人数',
  `status` ENUM('upcoming', 'ongoing', 'completed') DEFAULT 'upcoming' COMMENT '活动状态',
  `author_id` INT NOT NULL COMMENT '发布者ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_status` (`status`),
  INDEX `idx_author_id` (`author_id`),
  FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='组织活动';

-- 4. 活动参与表
CREATE TABLE IF NOT EXISTS `activity_participants` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `activity_id` INT NOT NULL COMMENT '活动ID',
  `user_id` INT NOT NULL COMMENT '用户ID',
  `status` ENUM('registered', 'attended', 'absent') DEFAULT 'registered' COMMENT '参与状态',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '报名时间',
  UNIQUE KEY `uk_activity_user` (`activity_id`, `user_id`),
  INDEX `idx_activity_id` (`activity_id`),
  INDEX `idx_user_id` (`user_id`),
  FOREIGN KEY (`activity_id`) REFERENCES `party_activities` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='活动参与记录';

-- 5. 党费缴纳表
CREATE TABLE IF NOT EXISTS `party_fees` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL COMMENT '用户ID',
  `amount` DECIMAL(10,2) NOT NULL COMMENT '缴纳金额',
  `payment_date` DATE NOT NULL COMMENT '缴纳日期',
  `payment_period` VARCHAR(20) NOT NULL COMMENT '缴纳周期',
  `status` ENUM('pending', 'paid', 'overdue', 'completed') DEFAULT 'pending' COMMENT '缴费状态: pending-待处理, paid-已缴费/处理中, overdue-逾期, completed-处理完毕',
  `payment_method` VARCHAR(50) DEFAULT NULL COMMENT '缴费方式',
  `remark` VARCHAR(255) DEFAULT NULL COMMENT '备注',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_payment_date` (`payment_date`),
  INDEX `idx_status` (`status`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='党费缴纳记录';

-- 6. 党员积分表
CREATE TABLE IF NOT EXISTS `party_integral` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL COMMENT '用户ID',
  `points` INT NOT NULL COMMENT '积分变动',
  `reason` VARCHAR(255) NOT NULL COMMENT '积分原因',
  `type` ENUM('add', 'deduct') NOT NULL COMMENT '积分类型',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_created_at` (`created_at`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='党员积分记录';

-- 7. 在线考试表
CREATE TABLE IF NOT EXISTS `party_exams` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NOT NULL COMMENT '考试标题',
  `description` TEXT DEFAULT NULL COMMENT '考试描述',
  `duration` INT NOT NULL COMMENT '考试时长（分钟）',
  `pass_score` INT NOT NULL COMMENT '及格分数',
  `total_score` INT NOT NULL COMMENT '总分',
  `start_time` DATETIME NOT NULL COMMENT '开始时间',
  `end_time` DATETIME NOT NULL COMMENT '结束时间',
  `status` ENUM('draft', 'active', 'ended') DEFAULT 'draft' COMMENT '考试状态',
  `author_id` INT NOT NULL COMMENT '创建者ID',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_status` (`status`),
  INDEX `idx_author_id` (`author_id`),
  FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='在线考试';

-- 8. 考试题目表
CREATE TABLE IF NOT EXISTS `party_exam_questions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `exam_id` INT NOT NULL COMMENT '考试ID',
  `question_type` ENUM('single', 'multiple', 'judgment') NOT NULL COMMENT '题目类型',
  `content` TEXT NOT NULL COMMENT '题目内容',
  `options` JSON DEFAULT NULL COMMENT '选项（JSON格式）',
  `correct_answer` JSON NOT NULL COMMENT '正确答案（JSON格式）',
  `score` INT NOT NULL COMMENT '题目分数',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_exam_id` (`exam_id`),
  FOREIGN KEY (`exam_id`) REFERENCES `party_exams` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考试题目';

-- 9. 考试记录表
CREATE TABLE IF NOT EXISTS `party_exam_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `exam_id` INT NOT NULL COMMENT '考试ID',
  `user_id` INT NOT NULL COMMENT '用户ID',
  `score` INT NOT NULL COMMENT '考试分数',
  `answers` JSON NOT NULL COMMENT '用户答案（JSON格式）',
  `start_time` DATETIME NOT NULL COMMENT '开始时间',
  `end_time` DATETIME NOT NULL COMMENT '结束时间',
  `status` ENUM('in_progress', 'completed') DEFAULT 'in_progress' COMMENT '考试状态',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  UNIQUE KEY `uk_exam_user` (`exam_id`, `user_id`),
  INDEX `idx_exam_id` (`exam_id`),
  INDEX `idx_user_id` (`user_id`),
  FOREIGN KEY (`exam_id`) REFERENCES `party_exams` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='考试记录';

-- 10. 党员档案表
CREATE TABLE IF NOT EXISTS `party_member_profiles` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL COMMENT '用户ID',
  `party_join_date` DATE DEFAULT NULL COMMENT '入党日期',
  `party_branch` VARCHAR(100) DEFAULT NULL COMMENT '所属党支部',
  `position` VARCHAR(100) DEFAULT NULL COMMENT '党内职务',
  `education` VARCHAR(50) DEFAULT NULL COMMENT '学历',
  `work_unit` VARCHAR(255) DEFAULT NULL COMMENT '工作单位',
  `address` VARCHAR(255) DEFAULT NULL COMMENT '联系地址',
  `emergency_contact` VARCHAR(100) DEFAULT NULL COMMENT '紧急联系人',
  `emergency_phone` VARCHAR(20) DEFAULT NULL COMMENT '紧急联系电话',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_user_id` (`user_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='党员档案';

-- 11. 学习记录
CREATE TABLE IF NOT EXISTS `party_study_records` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL COMMENT '用户ID',
  `knowledge_id` INT NOT NULL COMMENT '知识ID',
  `study_time` INT DEFAULT 0 COMMENT '学习时长（分钟）',
  `completed` BOOLEAN DEFAULT FALSE COMMENT '是否完成学习',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_user_knowledge` (`user_id`, `knowledge_id`),
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_knowledge_id` (`knowledge_id`),
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`knowledge_id`) REFERENCES `party_knowledge` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学习记录';

-- 12. 初始化数据
-- 插入党建知识分类
INSERT INTO `party_knowledge` (`title`, `content`, `category`, `author_id`) VALUES
('中国共产党章程', '中国共产党是中国工人阶级的先锋队，同时是中国人民和中华民族的先锋队...', '党章党规', 1),
('习近平新时代中国特色社会主义思想', '党的十九大把习近平新时代中国特色社会主义思想确立为党必须长期坚持的指导思想...', '理论学习', 1),
('党的历史', '中国共产党自1921年成立以来，已经走过了100多年的光辉历程...', '党史学习', 1);

-- 插入测试活动
INSERT INTO `party_activities` (`title`, `content`, `start_time`, `end_time`, `location`, `organizer`, `max_participants`, `author_id`) VALUES
('党员大会', '讨论年度工作计划和党员发展事宜', '2024-01-20 14:00:00', '2024-01-20 16:00:00', '会议室', '党支部', 50, 1),
('志愿服务活动', '社区清洁和关爱老人活动', '2024-01-25 09:00:00', '2024-01-25 11:00:00', '社区', '志愿服务队', 30, 1);

-- 插入测试党费记录
INSERT INTO `party_fees` (`user_id`, `amount`, `payment_date`, `payment_period`, `status`) VALUES
(1, 10.00, '2024-01-01', '2024年1月', 'paid'),
(1, 10.00, '2024-02-01', '2024年2月', 'pending');

-- 插入测试积分记录
INSERT INTO `party_integral` (`user_id`, `points`, `reason`, `type`) VALUES
(1, 10, '参与组织活动', 'add'),
(1, 5, '学习党建知识', 'add');

-- 插入测试考试
INSERT INTO `party_exams` (`title`, `description`, `duration`, `pass_score`, `total_score`, `start_time`, `end_time`, `status`, `author_id`) VALUES
('党章知识测试', '测试党员对党章的了解程度', 30, 60, 100, '2024-01-15 00:00:00', '2024-01-31 23:59:59', 'active', 1);

-- 插入测试题目
INSERT INTO `party_exam_questions` (`exam_id`, `question_type`, `content`, `options`, `correct_answer`, `score`) VALUES
(1, 'single', '中国共产党成立于哪一年？', '["1919年", "1921年", "1949年", "1978年"]', '["1921年"]', 10),
(1, 'multiple', '以下哪些是党的基本路线的内容？', '["领导和团结全国各族人民", "以经济建设为中心", "坚持四项基本原则", "坚持改革开放"]', '["领导和团结全国各族人民", "以经济建设为中心", "坚持四项基本原则", "坚持改革开放"]', 20),
(1, 'judgment', '中国共产党的最高理想和最终目标是实现共产主义。', NULL, '["true"]', 10);

-- 插入党员档案
INSERT INTO `party_member_profiles` (`user_id`, `party_join_date`, `party_branch`, `position`) VALUES
(1, '2020-07-01', '第一党支部', '支部委员');

-- 提交事务
COMMIT;