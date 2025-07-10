# 数据库模块

本模块提供了 FastAPI 应用的数据库连接和管理功能，基于 Tortoise ORM 和 Aerich 迁移工具。

## 功能特性

- ✅ **Tortoise ORM 集成** - 异步数据库操作
- ✅ **Aerich 迁移支持** - 数据库版本管理
- ✅ **连接池管理** - 高性能数据库连接
- ✅ **开发工具** - 便捷的数据库管理命令
- ✅ **读写分离支持** - 可扩展的数据库路由

## 文件结构

```
app/db/
├── __init__.py       # 模块导出
├── connection.py     # 数据库连接和基础操作
├── router.py         # 数据库路由器（读写分离）
└── README.md         # 本文档
```

## 快速开始

### 1. 环境配置

在 `.env` 文件中配置数据库连接：

```env
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
DB_POOL_MAX=20
DB_POOL_CONN_LIFE=500
```

### 2. 数据库迁移

```bash
# 初始化迁移
aerich init-db

# 创建迁移文件
aerich migrate --name="initial_migration"

# 应用迁移
aerich upgrade

# 查看迁移历史
aerich history
```

### 3. 开发工具

使用项目提供的管理脚本：

```bash
# 测试数据库连接
python manage_db.py test

# 生成数据库表结构（仅开发环境）
python manage_db.py create
```

## API 参考

### 核心函数

#### `init_database()`
初始化数据库连接

```python
from app.db import init_database

await init_database()
```

#### `close_database()`
关闭数据库连接

```python
from app.db import close_database

await close_database()
```

#### `check_database_connection()`
检查数据库连接状态

```python
from app.db import check_database_connection

is_connected = await check_database_connection()
```

#### `generate_schemas()`
生成数据库表结构（仅开发环境）

```python
from app.db import generate_schemas

await generate_schemas()  # 警告：仅用于开发环境
```

### 配置对象

#### `TORTOISE_ORM`
Tortoise ORM 配置字典，供 Aerich 等工具使用

```python
from app.db import TORTOISE_ORM

# Aerich 会自动使用此配置
```

## 数据库路由器

支持读写分离等高级功能：

```python
from app.db.router import DatabaseRouter

router = DatabaseRouter()

# 自定义读操作数据库选择
def db_for_read(self, model):
    if model._meta.app == "analytics":
        return "analytics_read_db"
    return None  # 使用默认连接
```

## 最佳实践

### 1. 生产环境部署
- ✅ 使用 Aerich 进行数据库迁移
- ✅ 配置适当的连接池参数
- ✅ 使用环境变量管理敏感配置
- ❌ 不要在生产环境使用 `generate_schemas()`

### 2. 开发环境
- ✅ 使用 `python manage_db.py test` 验证连接
- ✅ 可以使用 `generate_schemas()` 快速创建表
- ✅ 定期备份开发数据库

### 3. 错误处理
```python
from app.db import init_database
from app.utils.logger import logger

try:
    await init_database()
    logger.info("数据库连接成功")
except Exception as e:
    logger.error(f"数据库连接失败: {e}")
    raise
```

## 配置参数

| 参数                | 默认值    | 说明               |
| ------------------- | --------- | ------------------ |
| `DB_HOST`           | localhost | 数据库主机         |
| `DB_PORT`           | 5432      | 数据库端口         |
| `DB_USER`           | -         | 数据库用户名       |
| `DB_PASSWORD`       | -         | 数据库密码         |
| `DB_NAME`           | -         | 数据库名称         |
| `DB_POOL_MAX`       | 20        | 最大连接数         |
| `DB_POOL_CONN_LIFE` | 500       | 连接生命周期（秒） |

## 故障排除

### 常见问题

**1. 连接被拒绝**
```bash
# 检查数据库服务是否运行
sudo systemctl status postgresql

# 检查防火墙设置
sudo ufw status
```

**2. 权限错误**
```sql
-- 确保用户有正确的权限
GRANT ALL PRIVILEGES ON DATABASE your_database TO your_username;
```

**3. 迁移失败**
```bash
# 查看迁移状态
aerich history

# 回滚到上一个版本
aerich downgrade -t 1
```

## 相关文档

- [Tortoise ORM 文档](https://tortoise.github.io/)
- [Aerich 迁移工具](https://github.com/tortoise/aerich)
- [FastAPI 数据库集成](https://fastapi.tiangolo.com/tutorial/sql-databases/)
