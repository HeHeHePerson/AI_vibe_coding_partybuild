# 智慧党建系统部署文档

## 1. 环境要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 1核 | 2核 |
| 内存 | 512MB | 1GB |
| 磁盘 | 5GB | 10GB |
| 网络 | 1Mbps | 5Mbps |

### 1.2 软件要求

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| 操作系统 | Ubuntu 20.04+ / CentOS 7+ | 推荐使用Ubuntu 22.04 |
| Python | 3.8+ | 推荐Python 3.10 |
| MySQL | 5.7+ | 推荐MySQL 8.0 |
| Nginx | 1.18+ | 用于生产环境反向代理 |

---

## 2. 安装步骤

### 2.1 安装Python环境

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# 验证安装
python3 --version
```

### 2.2 安装MySQL数据库

```bash
# Ubuntu
sudo apt install -y mysql-server

# 启动MySQL服务
sudo systemctl start mysql
sudo systemctl enable mysql

# 安全初始化
sudo mysql_secure_installation

# 登录MySQL
sudo mysql -u root -p
```

### 2.3 创建数据库和用户

```sql
-- 创建数据库
CREATE DATABASE party_building CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建数据库用户（请修改密码）
CREATE USER 'party_user'@'localhost' IDENTIFIED BY 'your_password';

-- 授权
GRANT ALL PRIVILEGES ON party_building.* TO 'party_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2.4 创建数据表

```sql
USE party_building;

-- 用户表
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('user', 'admin') DEFAULT 'user',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 内容表
CREATE TABLE IF NOT EXISTS `contents` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) NOT NULL,
  `body` TEXT NOT NULL,
  `images` JSON,
  `author_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_author_id` (`author_id`),
  INDEX `idx_created_at` (`created_at`),
  FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 评论表
CREATE TABLE IF NOT EXISTS `comments` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `content_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `body` TEXT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_content_id` (`content_id`),
  INDEX `idx_user_id` (`user_id`),
  FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 内容点赞表
CREATE TABLE IF NOT EXISTS `likes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `content_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `created_at` DATE NOT NULL,
  UNIQUE KEY `uk_content_user_date` (`content_id`, `user_id`, `created_at`),
  INDEX `idx_content_id` (`content_id`),
  FOREIGN KEY (`content_id`) REFERENCES `contents` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 评论点赞表
CREATE TABLE IF NOT EXISTS `comment_likes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `comment_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `created_at` DATE NOT NULL,
  UNIQUE KEY `uk_comment_user_date` (`comment_id`, `user_id`, `created_at`),
  INDEX `idx_comment_id` (`comment_id`),
  FOREIGN KEY (`comment_id`) REFERENCES `comments` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 访问统计表
CREATE TABLE IF NOT EXISTS `visits` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `visit_date` DATE NOT NULL UNIQUE,
  `visit_count` INT DEFAULT 0,
  INDEX `idx_visit_date` (`visit_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 公告表
CREATE TABLE IF NOT EXISTS `notices` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(200) NOT NULL,
  `content` TEXT NOT NULL,
  `author_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_created_at` (`created_at`),
  FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2.5 创建管理员账号

```sql
USE party_building;

-- 插入管理员账号（用户名：admin，密码：admin123）
-- 密码使用bcrypt加密
INSERT INTO `users` (`username`, `password_hash`, `role`) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.AFL3zB.SLu/8q', 'admin');

-- 验证插入
SELECT id, username, role FROM users WHERE username = 'admin';
```

> **注意**: 上面使用的密码哈希对应的明文密码是 `admin123`。如需创建其他管理员账号，可使用项目提供的 `change_password.py` 工具生成密码哈希。

### 2.6 部署项目代码

```bash
# 克隆项目
git clone <repository-url> /var/www/party-building
cd /var/www/party-building

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install flask pymysql bcrypt

# 创建必要目录
mkdir -p logs webapp/uploads

# 配置环境变量
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=party_user
export DB_PASSWORD=your_password
export DB_NAME=party_building
export SECRET_KEY=your-secret-key
```

---

## 3. 配置说明

### 3.1 配置文件

项目配置文件为 `config.py`，主要配置项：

```python
# config.py

# Session密钥（生产环境请修改为随机字符串）
SECRET_KEY = os.environ.get('SECRET_KEY', 'party-building-secret-key-2024')

# 数据库配置
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'root')
DB_NAME = os.environ.get('DB_NAME', 'party_building')

# 文件上传配置
UPLOAD_FOLDER = 'webapp/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'pdf', 'txt'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

# Session配置
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 3600 * 24  # 24小时
```

---

## 4. 运行项目

### 4.1 开发模式运行

```bash
cd /var/www/party-building
source venv/bin/activate
python app.py
```

服务启动后，访问 http://localhost:5000

### 4.2 使用Systemd管理服务

创建服务文件 `/etc/systemd/system/party-building.service`:

```ini
[Unit]
Description=Party Building System
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/party-building
Environment="PATH=/var/www/party-building/venv/bin"
Environment="DB_HOST=localhost"
Environment="DB_PORT=3306"
Environment="DB_USER=party_user"
Environment="DB_PASSWORD=your_password"
Environment="DB_NAME=party_building"
ExecStart=/var/www/party-building/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start party-building
sudo systemctl enable party-building
```

---

## 5. Nginx反向代理配置（生产环境）

### 5.1 安装Nginx

```bash
sudo apt install -y nginx
```

### 5.2 配置Nginx

创建配置文件 `/etc/nginx/sites-available/party-building`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为您的域名

    access_log /var/log/nginx/party-building-access.log;
    error_log /var/log/nginx/party-building-error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 上传文件目录
    location /uploads {
        alias /var/www/party-building/webapp/uploads;
    }

    # 静态文件
    location /static {
        alias /var/www/party-building/webapp/static;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/party-building /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. 初始化管理员账号

### 6.1 创建管理员账号

项目提供了密码修改工具，可以创建新的管理员账号：

```bash
cd /var/www/party-building
source venv/bin/activate
python change_password.py
```

按照提示输入用户名和新密码，即可创建或修改管理员账号。

---

## 7. 验证部署

### 7.1 检查服务状态

```bash
# 检查Flask应用
curl http://localhost:5000

# 检查MySQL连接
mysql -u party_user -p party_building -e "SELECT 1"

# 检查日志
tail -f /var/www/party-building/logs/access.log
```

### 7.2 功能测试

1. 访问系统首页
2. 使用管理员账号登录（默认：`admin` / `admin123`）
3. 创建普通用户账号
4. 发布内容并测试评论、点赞功能
5. 测试公告发布功能
6. 检查访问统计

---

## 8. 目录权限

```bash
# 设置目录权限
sudo chown -R www-data:www-data /var/www/party-building

# 设置上传目录权限
sudo chmod 755 /var/www/party-building/webapp/uploads
sudo chmod 755 /var/www/party-building/logs
```

---

## 9. 备份与恢复

### 9.1 数据库备份

```bash
# 备份数据库
mysqldump -u party_user -p party_building > backup_$(date +%Y%m%d).sql

# 恢复数据库
mysql -u party_user -p party_building < backup_20240101.sql
```

### 9.2 文件备份

```bash
# 备份上传的文件
tar -czvf uploads_backup_$(date +%Y%m%d).tar.gz webapp/uploads/

# 备份日志
tar -czvf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

---

## 10. 常见问题

### 10.1 数据库连接失败

- 检查MySQL服务是否运行
- 检查用户名和密码是否正确
- 检查数据库是否已创建

### 10.2 文件上传失败

- 检查上传目录权限
- 检查磁盘空间
- 检查文件大小限制

### 10.3 Session失效

- 检查浏览器Cookie是否被阻止
- 检查SECRET_KEY配置是否正确

---

## 11. 默认账号

| 类型 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

> **安全建议**: 首次登录后请立即修改管理员密码。
