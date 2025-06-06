# 缓存系统使用指南

## 概述

系统集成了Redis缓存层，用于提升权限验证、用户状态查询等热点数据的访问性能。缓存系统采用异步设计，支持自动失效、批量操作和错误恢复。

## 架构设计

### 缓存服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Layer     │    │  Service Layer  │    │  Cache Layer    │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   Routes    │ │───▶│ │  Services   │ │───▶│ │ CacheService│ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │  Redis Server   │
                                              └─────────────────┘
```

### 缓存分层策略

1. **L1缓存**：内存缓存（用户会话期间）
2. **L2缓存**：Redis缓存（跨请求共享）
3. **L3存储**：数据库（持久化存储）

## 缓存键设计

### 键命名规范

```python
# 格式：{prefix}:{category}:{identifier}
CACHE_PREFIX = "fastapi_base"

# 用户相关缓存
user_permissions:{user_id}     # 用户权限缓存
user_roles:{user_id}           # 用户角色缓存

# 角色相关缓存  
role_permissions:{role_id}     # 角色权限缓存

# Token相关缓存
token_blacklist:{jti}          # Token黑名单
```

### TTL配置

```python
# 默认配置（单位：秒）
CACHE_DEFAULT_TTL = 1800           # 30分钟
CACHE_USER_PERMISSIONS_TTL = 1800  # 用户权限：30分钟
CACHE_USER_ROLES_TTL = 1800        # 用户角色：30分钟
CACHE_ROLE_PERMISSIONS_TTL = 1800  # 角色权限：30分钟
```

## 使用方法

### 基本缓存操作

```python
from app.services.cache_service import cache_service

# 设置缓存
await cache_service.set("key", {"data": "value"}, ttl=3600)

# 获取缓存
data = await cache_service.get("key")

# 删除缓存
await cache_service.delete("key")

# 批量删除
await cache_service.delete_pattern("user_*")
```

### 权限缓存

```python
# 获取用户权限（自动缓存）
permissions = await cache_service.get_user_permissions(str(user_id))
if permissions is None:
    # 缓存未命中，从数据库查询
    permissions = await permission_service.get_user_permissions(user_id)
    # 设置缓存
    await cache_service.set_user_permissions(str(user_id), permissions)

# 清理用户相关缓存
await cache_service.invalidate_user_cache(str(user_id))
```

### Token黑名单

```python
# 检查Token是否在黑名单
is_blacklisted = await cache_service.is_token_blacklisted(jti)

# 添加Token到黑名单
await cache_service.add_token_to_blacklist(jti, ttl=3600)

# 批量添加Token到黑名单
jtis = ["jti1", "jti2", "jti3"]
await cache_service.batch_add_to_blacklist(jtis, ttl=3600)
```

## 缓存失效策略

### 自动失效

```python
# 基于TTL的自动失效
await cache_service.set("key", data, ttl=1800)  # 30分钟后自动失效
```

### 手动失效

```python
# 用户操作后清理缓存
class UserService:
    async def update_user(self, user_id: int, user_data: UserUpdate):
        # 更新用户信息
        user = await self.user_repo.update(user_id, user_data)
        
        # 清理用户相关缓存
        await cache_service.invalidate_user_cache(str(user_id))
        
        return user
```

### 级联失效

```python
# 角色权限变更时的级联失效
class RoleService:
    async def assign_permissions(self, role_id: int, permission_ids: List[int]):
        # 分配权限
        await self.role_repo.assign_permissions(role_id, permission_ids)
        
        # 清理角色权限缓存
        await cache_service.delete(f"role_permissions:{role_id}")
        
        # 清理拥有该角色的所有用户的权限缓存
        users = await self.user_repo.get_users_by_role(role_id)
        for user in users:
            await cache_service.invalidate_user_cache(str(user.id))
```

## 性能优化

### 批量操作

```python
# 批量获取用户权限
user_ids = ["1", "2", "3"]
keys = [f"user_permissions:{uid}" for uid in user_ids]
results = await cache_service.mget(keys)

# 批量设置缓存
data_dict = {
    "user_permissions:1": permissions_1,
    "user_permissions:2": permissions_2,
}
await cache_service.mset(data_dict, ttl=1800)
```

### 管道操作

```python
# 使用管道减少网络往返
async with cache_service.pipeline() as pipe:
    pipe.set("key1", "value1")
    pipe.set("key2", "value2")
    pipe.expire("key1", 3600)
    results = await pipe.execute()
```

### 缓存预热

```python
# 登录时预热缓存
class AuthService:
    async def authenticate_user(self, identifier: str, password: str):
        user = await self.get_user_by_identifier(identifier)
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        
        # 预热用户权限和角色缓存
        await self._preheat_user_cache(user.id)
        
        return user
    
    async def _preheat_user_cache(self, user_id: int):
        # 预加载权限和角色
        permissions = await self.permission_service.get_user_permissions(user_id)
        roles = await self.role_service.get_user_roles(user_id)
        
        # 设置缓存
        await cache_service.set_user_permissions(str(user_id), permissions)
        await cache_service.set_user_roles(str(user_id), roles)
```

## 监控和调试

### 缓存命中率监控

```python
# 添加缓存命中率统计
class CacheService:
    def __init__(self):
        self.hit_count = 0
        self.miss_count = 0
    
    async def get(self, key: str):
        value = await self.redis.get(key)
        if value:
            self.hit_count += 1
        else:
            self.miss_count += 1
        return value
    
    def get_hit_ratio(self) -> float:
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
```

### 缓存大小监控

```python
# 监控缓存使用情况
async def get_cache_stats():
    info = await cache_service.redis.info("memory")
    return {
        "used_memory": info["used_memory"],
        "used_memory_human": info["used_memory_human"],
        "max_memory": info.get("maxmemory", 0),
    }
```

### 调试工具

```python
# 查看特定模式的缓存键
async def debug_cache_keys(pattern: str = "*"):
    keys = await cache_service.redis.keys(f"{cache_service.prefix}:{pattern}")
    return keys

# 查看缓存内容
async def debug_cache_value(key: str):
    value = await cache_service.get(key)
    ttl = await cache_service.redis.ttl(f"{cache_service.prefix}:{key}")
    return {"value": value, "ttl": ttl}
```

## 错误处理

### 缓存降级

```python
async def get_user_permissions_with_fallback(user_id: int) -> List[str]:
    try:
        # 尝试从缓存获取
        permissions = await cache_service.get_user_permissions(str(user_id))
        if permissions is not None:
            return permissions
    except Exception as e:
        logger.warning(f"缓存获取失败: {e}")
    
    # 缓存失败时从数据库获取
    permissions = await permission_service.get_user_permissions(user_id)
    
    try:
        # 尝试设置缓存
        await cache_service.set_user_permissions(str(user_id), permissions)
    except Exception as e:
        logger.warning(f"缓存设置失败: {e}")
    
    return permissions
```

### 连接重试

```python
class CacheService:
    async def ensure_connection(self):
        if not self.redis or self.redis.connection_pool.connection_kwargs.get('health_check_interval'):
            await self.connect()
    
    async def get(self, key: str, retries: int = 3):
        for attempt in range(retries):
            try:
                await self.ensure_connection()
                return await self.redis.get(f"{self.prefix}:{key}")
            except Exception as e:
                if attempt == retries - 1:
                    raise
                logger.warning(f"缓存操作重试 {attempt + 1}/{retries}: {e}")
                await asyncio.sleep(0.1 * (2 ** attempt))  # 指数退避
```

## 最佳实践

### 1. 缓存设计原则

- **热点数据优先**：优先缓存访问频率高的数据
- **合理TTL**：根据数据变更频率设置合适的过期时间
- **键名规范**：使用统一的键命名规范，便于管理
- **分层缓存**：结合本地缓存和分布式缓存

### 2. 避免缓存问题

```python
# 避免缓存穿透
async def get_user_safe(user_id: int):
    # 检查缓存
    cache_key = f"user:{user_id}"
    user = await cache_service.get(cache_key)
    
    if user is None:
        # 从数据库查询
        user = await user_repo.get_by_id(user_id)
        
        # 即使查询结果为空也要缓存（设置较短TTL）
        ttl = 3600 if user else 60
        await cache_service.set(cache_key, user, ttl=ttl)
    
    return user

# 避免缓存雪崩
async def set_cache_with_jitter(key: str, value: Any, base_ttl: int):
    # 添加随机时间避免同时失效
    jitter = random.randint(0, base_ttl // 10)
    ttl = base_ttl + jitter
    await cache_service.set(key, value, ttl=ttl)
```

### 3. 性能调优

- **连接池优化**：配置合适的连接池大小
- **管道使用**：批量操作使用管道减少网络往返
- **压缩存储**：大数据可考虑压缩存储
- **定期清理**：清理过期和无用的缓存键

### 4. 安全考虑

- **数据脱敏**：敏感数据缓存时要脱敏处理
- **访问控制**：限制缓存数据的访问权限
- **数据加密**：重要数据可考虑加密存储
- **审计日志**：记录缓存的关键操作

## 配置参考

### Redis配置

```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 300
```

### 应用配置

```python
# app/config.py
class Settings(BaseSettings):
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_PREFIX: str = "fastapi_base"
    CACHE_DEFAULT_TTL: int = 1800
    CACHE_MAX_CONNECTIONS: int = 20
    CACHE_RETRY_ON_TIMEOUT: bool = True
```
