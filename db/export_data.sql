-- 智慧党建系统数据导出脚本
-- 用于导出现有数据，以便在低版本MySQL中重新导入
-- 执行方式：mysql -u username -p party_building < export_data.sql

USE party_building;

-- ============================================
-- 1. 导出用户数据
-- ============================================
SELECT '--- 用户数据 ---' AS 'Export Section';

SELECT id, username, password_hash, role, avatar, bio, email, phone, last_login_at, created_at
FROM users;

-- ============================================
-- 2. 导出党建内容数据
-- ============================================
SELECT '--- 党建内容数据 ---' AS 'Export Section';

SELECT id, title, body, images, author_id, created_at
FROM contents;

-- ============================================
-- 3. 导出评论数据
-- ============================================
SELECT '--- 评论数据 ---' AS 'Export Section';

SELECT id, content_id, user_id, body, parent_id, created_at
FROM comments;

-- ============================================
-- 4. 导出点赞数据
-- ============================================
SELECT '--- 点赞数据 ---' AS 'Export Section';

SELECT id, content_id, user_id, created_at
FROM likes;

-- ============================================
-- 5. 导出评论点赞数据
-- ============================================
SELECT '--- 评论点赞数据 ---' AS 'Export Section';

SELECT id, comment_id, user_id, created_at
FROM comment_likes;

-- ============================================
-- 6. 导出访问统计数据
-- ============================================
SELECT '--- 访问统计数据 ---' AS 'Export Section';

SELECT id, visit_date, visit_count
FROM visits;

-- ============================================
-- 7. 导出公告数据
-- ============================================
SELECT '--- 公告数据 ---' AS 'Export Section';

SELECT id, title, content, author_id, created_at
FROM notices;

-- ============================================
-- 8. 导出党建知识数据
-- ============================================
SELECT '--- 党建知识数据 ---' AS 'Export Section';

SELECT id, title, content, category, author_id, view_count, status, created_at, updated_at
FROM party_knowledge;

-- ============================================
-- 9. 导出学习记录数据
-- ============================================
SELECT '--- 学习记录数据 ---' AS 'Export Section';

SELECT id, user_id, knowledge_id, study_time, completed, created_at, updated_at
FROM party_study_records;

-- ============================================
-- 10. 导出组织活动数据
-- ============================================
SELECT '--- 组织活动数据 ---' AS 'Export Section';

SELECT id, title, content, start_time, end_time, location, organizer, max_participants, current_participants, status, review_status, author_id, created_at, updated_at
FROM party_activities;

-- ============================================
-- 11. 导出活动参与数据
-- ============================================
SELECT '--- 活动参与数据 ---' AS 'Export Section';

SELECT id, activity_id, user_id, status, created_at
FROM activity_participants;

-- ============================================
-- 12. 导出党费缴纳数据
-- ============================================
SELECT '--- 党费缴纳数据 ---' AS 'Export Section';

SELECT id, user_id, amount, payment_date, payment_period, status, payment_method, remark, created_at
FROM party_fees;

-- ============================================
-- 13. 导出党员积分数据
-- ============================================
SELECT '--- 党员积分数据 ---' AS 'Export Section';

SELECT id, user_id, points, reason, type, created_at
FROM party_integral;

-- ============================================
-- 14. 导出党员档案数据
-- ============================================
SELECT '--- 党员档案数据 ---' AS 'Export Section';

SELECT id, user_id, party_join_date, party_branch, position, education, work_unit, address, emergency_contact, emergency_phone, updated_at
FROM party_member_profiles;

-- 导出完成
SELECT '数据导出完成，请手动复制结果并保存为CSV或SQL文件' AS 'Export Complete';

-- ============================================
-- 数据导入说明
-- ============================================
-- 1. 首先在低版本MySQL中执行 init_low_version.sql 创建数据库结构
-- 2. 然后使用以下命令将导出的数据导入到新数据库：
--    mysql -u username -p party_building < export_data.sql
-- 3. 或者手动将导出的结果转换为INSERT语句后导入

-- 注意事项：
-- 1. 低版本MySQL可能不支持JSON数据类型，因此images字段已改为TEXT类型
-- 2. 低版本MySQL可能不支持BOOLEAN数据类型，因此completed字段已改为TINYINT(1)类型
-- 3. 确保使用utf8字符集和utf8_general_ci校对规则以提高兼容性
