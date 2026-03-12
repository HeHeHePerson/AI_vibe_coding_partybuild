# 智慧党建系统部署文档

## 系统概述

智慧党建系统是一个基于Python Flask + MySQL的Web应用，用于党组织的信息化管理。

## 环境要求

- Python 3.8+
- MySQL 5.7+
- 系统内存: 至少 512MB

## 快速部署

### 1. 准备数据库

```bash
# 登录MySQL
mysql -u root -p

# 执行初始化脚本
source /path/to/db/init.sql
```

### 2. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt
```

### 3. 配置环境变量（可选）

```bash
# 数据库配置
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=root
export DB_PASSWORD=your_password
export DB_NAME=party_building

# 密钥配置
export SECRET_KEY=your-secret-key
```

### 4. 启动应用

```bash
# 方式一：直接运行
python app.py

# 方式二：使用gunicorn（生产环境推荐）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

应用启动后，访问 `http://localhost:5000` 即可。

## 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | admin | admin123 |

**注意**: 首次运行应用时，系统会自动创建默认管理员账号。请及时修改密码！

## 目录结构

```
party-building-system/
├── app.py                 # Flask应用主入口
├── config.py              # 配置文件
├── database.py            # 数据库连接模块
├── requirements.txt       # Python依赖
├── webapp/
│   ├── routes/            # 路由模块
│   │   ├── auth.py        # 认证路由
│   │   ├── users.py       # 用户管理路由
│   │   ├── contents.py    # 内容路由
│   │   └── stats.py       # 统计路由
│   ├── utils/             # 工具函数
│   │   ├── auth.py        # 认证工具
│   │   ├── security.py    # 安全工具
│   │   └── stats.py       # 统计工具
│   ├── static/            # 静态文件
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── main.js
│   ├── templates/         # HTML模板
│   └── uploads/           # 上传的图片目录
├── db/
│   └── init.sql          # 数据库初始化脚本
└── deploy/
    └── README.md          # 部署文档
```

## 功能说明

### 1. 登录认证

- 支持用户登录、注册、登出
- 区分管理员和普通用户角色
- 管理员可进行用户管理

### 2. 党建之声

- 创建内容（支持文本和图片）
- 查看内容列表和详情
- 评论功能
- 点赞功能（每日限一次）

### 3. 统计功能

- 访问统计（今日、本月、总计）
- 内容点赞数统计

## 安全配置

### 生产环境建议

1. **修改 SECRET_KEY**: 在 `config.py` 中设置复杂的随机字符串
2. **使用HTTPS**: 配置SSL证书
3. **限制上传文件**: 检查文件类型和大小
4. **定期备份数据库**: 建立备份机制

### 数据库安全

```sql
-- 创建专用数据库用户
CREATE USER 'party_user'@'localhost' IDENTIFIED BY 'strong_password';
GRANT ALL PRIVILEGES ON party_building.* TO 'party_user'@'localhost';
FLUSH PRIVILEGES;
```

## 常见问题

### 1. 数据库连接失败

确保MySQL服务已启动，且用户名密码配置正确。

### 2. 上传图片失败

检查 `uploads` 目录是否有写权限。

### 3. Session失效

检查浏览器Cookie是否被禁用。

## 维护

### 备份数据库

```bash
mysqldump -u root -p party_building > backup_$(date +%Y%m%d).sql
```

### 恢复数据库

```bash
mysql -u root -p party_building < backup_20240101.sql
```
