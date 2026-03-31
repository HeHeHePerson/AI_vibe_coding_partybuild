# 数据库迁移指南

## 概述

本文档说明如何在智慧党建系统中进行数据库迁移，包括全新部署和增量升级两种方式。

## 迁移脚本清单

| 脚本文件 | 用途 | 适用场景 |
|---------|------|---------|
| `db/init.sql` | 完整数据库初始化 | 全新部署 |
| `docs/migration_party_garden.sql` | 党建园地模块迁移 | 现有系统升级 |
| `db/migration_audit.sql` | 审计日志表创建 | 早期版本升级 |
| `db/migration_security.sql` | 安全相关表创建 | 早期版本升级 |

## 一、全新部署

### 1.1 使用 init.sql（推荐）

适用于全新安装系统，包含所有表结构和初始数据。

```bash
# 登录MySQL并执行
mysql -u root -p

# 在MySQL中执行
source db/init.sql;
```

或者命令行直接执行：

```bash
mysql -u party_user -p party_building < db/init.sql
```

### 1.2 init.sql 包含的内容

- **基础表结构**：users, contents, comments, likes, comment_likes, visits, notices
- **党建园地表**：party_knowledge, party_study_records, party_activities, activity_participants, party_fees, party_integral, party_member_profiles
- **初始数据**：默认管理员账号(admin/admin123)、示例党建知识、示例活动、党员档案

## 二、增量升级

### 2.1 从基础版本升级到党建园地版本

适用于已有基础系统（用户、内容、评论等功能），需要添加党建园地功能。

```bash
# 1. 备份现有数据库（重要！）
mysqldump -u party_user -p party_building > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 执行迁移脚本
mysql -u party_user -p party_building < docs/migration_party_garden.sql
```

### 2.2 migration_party_garden.sql 变更说明

该脚本会执行以下操作：

1. **扩展 users 表**：添加 avatar, bio, email, phone, last_login_at 字段
2. **创建党建知识表** (party_knowledge)：支持审核状态(status字段)
3. **创建学习记录表** (party_study_records)：记录用户学习进度
4. **创建组织活动表** (party_activities)：支持审核状态(review_status字段)
5. **创建活动参与表** (activity_participants)：记录用户报名和参与状态
6. **创建党费缴纳表** (party_fees)：支持4种缴费状态
7. **创建党员积分表** (party_integral)：记录积分变动
8. **创建党员档案表** (party_member_profiles)：存储党员详细信息
9. **插入示例数据**：便于测试和演示

### 2.3 特定字段升级

如果只需要升级特定功能，可以执行单独的ALTER TABLE语句：

#### 升级党费缴纳状态字段（添加 completed 状态）

```sql
USE party_building;

ALTER TABLE party_fees 
MODIFY COLUMN status ENUM('pending', 'paid', 'overdue', 'completed') 
DEFAULT 'pending' 
COMMENT '缴费状态: pending-待处理, paid-已缴费/处理中, overdue-逾期, completed-处理完毕';
```

## 三、迁移验证

### 3.1 验证表结构

```sql
USE party_building;

-- 查看所有表
SHOW TABLES;

-- 查看特定表结构
DESCRIBE party_fees;
DESCRIBE party_activities;
DESCRIBE party_knowledge;
```

### 3.2 验证数据

```sql
-- 检查党建知识数据
SELECT COUNT(*) FROM party_knowledge;

-- 检查活动数据
SELECT COUNT(*) FROM party_activities;

-- 检查党费记录
SELECT id, status FROM party_fees LIMIT 5;
```

## 四、常见问题

### 4.1 迁移失败处理

**问题1**: 表已存在导致创建失败

**解决**: 脚本使用 `IF NOT EXISTS`，通常不会报错。如仍有问题，可手动删除后重建：

```sql
-- 危险操作！请确保已备份
DROP TABLE IF EXISTS party_knowledge;
DROP TABLE IF EXISTS party_study_records;
-- ... 其他表
```

**问题2**: 外键约束失败

**解决**: 确保 users 表已存在且有数据：

```sql
SELECT id, username FROM users LIMIT 5;
```

**问题3**: 字符集问题

**解决**: 确保数据库使用 utf8mb4：

```sql
ALTER DATABASE party_building CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4.2 回滚操作

如果迁移后出现问题，可使用备份恢复：

```bash
# 恢复数据库
mysql -u party_user -p party_building < backup_20260331_120000.sql
```

## 五、版本兼容性

| 系统版本 | 数据库要求 | 迁移脚本 |
|---------|-----------|---------|
| v1.0 (基础版) | init.sql | - |
| v2.0 (党建园地版) | init.sql 或 migration_party_garden.sql | migration_party_garden.sql |

## 六、最佳实践

1. ** always backup**: 执行任何迁移前务必备份数据库
2. **测试环境先行**: 先在测试环境验证迁移脚本
3. **逐步升级**: 大型系统建议分步执行迁移
4. **记录变更**: 保留迁移日志便于追溯
5. **验证功能**: 迁移后全面测试相关功能

## 七、联系支持

如遇到迁移问题，请检查：
1. MySQL版本是否 >= 5.7
2. 数据库用户是否有足够权限
3. 磁盘空间是否充足