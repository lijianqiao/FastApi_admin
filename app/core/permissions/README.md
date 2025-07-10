# 权限系统改进说明

## 新增功能

### 1. 权限缓存装饰器

#### 功能特点
- 支持TTL（生存时间）设置
- 可配置缓存键前缀
- 支持参数序列化
- 自动处理并发访问（使用锁机制）
- 提供缓存统计信息

#### 使用示例

```python
from app.core.permissions import cache_with_ttl

@cache_with_ttl(ttl=3600, key_prefix="user_permissions:")
async def get_user_permissions(user_id: str) -> list[str]:
    # 耗时的数据库查询
    return ["user:read", "user:update"]
```

#### 缓存失效装饰器

```python
from app.core.permissions import invalidate_user_cache, invalidate_role_cache

@invalidate_user_cache("user_123")
async def update_user_permissions(user_id: str, permissions: list[str]):
    # 更新用户权限后自动清除相关缓存
    pass

@invalidate_role_cache("admin")
async def update_role_permissions(role_code: str, permissions: list[str]):
    # 更新角色权限后自动清除相关缓存
    pass
```

### 2. 完善权限清理功能

#### 功能特点
- 检测未使用的权限
- 检测无效格式的权限
- 检测孤立权限（数据库有但代码中没有）
- 支持试运行模式
- 提供详细的清理报告

#### 使用示例

```python
from app.core.permissions.initializer import create_permission_initializer

initializer = create_permission_initializer()

# 试运行模式，不实际删除
result = await initializer.cleanup_permissions(dry_run=True)

# 实际清理模式
result = await initializer.cleanup_permissions(dry_run=False)
```

#### 清理结果结构

```python
{
    "total_permissions": 50,
    "unused_permissions": [
        {
            "id": "uuid",
            "code": "old:permission",
            "name": "旧权限",
            "reason": "未被任何角色或用户使用"
        }
    ],
    "invalid_permissions": [
        {
            "id": "uuid", 
            "code": "invalid_format",
            "name": "格式错误权限",
            "reason": "权限格式不符合规范"
        }
    ],
    "orphaned_permissions": [
        {
            "id": "uuid",
            "code": "database:only",
            "name": "数据库权限",
            "reason": "代码中未找到对应权限定义"
        }
    ],
    "deleted_count": 5,
    "dry_run": false
}
```

## 应用缓存的组件

### 1. PermissionConfig
- `get_permission_groups()` - 3600秒缓存
- `get_permission_group()` - 3600秒缓存  
- `get_group_permissions()` - 3600秒缓存
- `get_all_permissions_from_groups()` - 3600秒缓存
- `get_default_roles()` - 7200秒缓存
- `get_role_permissions()` - 7200秒缓存

### 2. Decorators
- `check_user_permission()` - 1800秒缓存
- `check_user_role()` - 1800秒缓存

### 3. MenuGenerator  
- `generate_user_menu()` - 1800秒缓存
- `generate_role_menu()` - 3600秒缓存
- `_get_user_all_permissions()` - 1800秒缓存

## 缓存管理

### 获取缓存统计
```python
from app.core.permissions import get_cache_stats

stats = await get_cache_stats()
# 返回: {"total_entries": 10, "expired_entries": 2, "active_entries": 8, ...}
```

### 清除所有缓存
```python
from app.core.permissions import clear_all_permission_cache

result = await clear_all_permission_cache()
# 返回: {"cleared_count": 10, "message": "所有权限缓存已清除"}
```

## 性能优化

1. **减少数据库查询**: 权限检查结果被缓存，避免重复查询
2. **菜单生成优化**: 用户菜单生成结果缓存30分钟
3. **配置读取优化**: 权限配置读取结果缓存1小时
4. **并发安全**: 使用锁机制避免缓存击穿

## 注意事项

1. **内存使用**: 当前使用内存缓存，生产环境建议集成Redis
2. **缓存一致性**: 权限更新时需要手动清除相关缓存
3. **TTL设置**: 根据业务需求调整缓存时间
4. **监控**: 定期检查缓存命中率和内存使用情况
