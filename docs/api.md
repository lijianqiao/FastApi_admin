# API 接口文档

---

## 认证相关 API

### POST /api/v1/auth/login
- 描述：用户登录（用户名/邮箱/手机号+密码）
- 请求体：
  ```json
  {
    "identifier": "string",
    "password": "string",
    "remember_me": false
  }
  ```
- 返回值：
  ```json
  {
    "access_token": "string",
    "token_type": "bearer",
    "expires_in": 900,
    "refresh_token": "string"
  }
  ```

### POST /api/v1/auth/login/form
- 描述：表单登录（OAuth2 兼容）
- 请求体：
  - username: string
  - password: string
- 返回值：同上

### POST /api/v1/auth/refresh
- 描述：刷新访问令牌
- 请求体：
  ```json
  {
    "refresh_token": "string"
  }
  ```
- 返回值：同上

### POST /api/v1/auth/logout
- 描述：用户登出（支持登出所有设备）
- 参数：logout_all_devices: bool（可选）
- 返回值：
  ```json
  {
    "success": true
  }
  ```

### GET /api/v1/auth/me
- 描述：获取当前用户信息
- 返回值：
  ```json
  {
    "id": "string",
    "username": "string",
    "email": "string",
    "nickname": "string",
    "is_active": true,
    "is_superuser": false,
    "roles": ["string"],
    "permissions": ["string"]
  }
  ```

### GET /api/v1/auth/check
- 描述：检查认证状态
- 返回值：
  ```json
  {
    "authenticated": true,
    "username": "string",
    "is_active": true
  }
  ```

### POST /api/v1/auth/change-password
- 描述：修改当前用户密码
- 请求体：
  ```json
  {
    "old_password": "string",
    "new_password": "string"
  }
  ```
- 返回值：
  ```json
  {
    "success": true
  }
  ```

---

## 用户管理 API

### POST /api/v1/users
- 描述：创建用户
- 请求体：
  ```json
  {
    "username": "string",
    "email": "string",
    "phone": "string",
    "password": "string",
    "is_active": true
  }
  ```
- 返回值：UserResponse

### GET /api/v1/users
- 描述：分页获取用户列表
- 查询参数：keyword、is_active、page、size、sort_by、sort_desc
- 返回值：
  ```json
  {
    "data": [ { ...UserResponse... } ],
    "total": 100
  }
  ```

### GET /api/v1/users/active
- 描述：获取活跃用户列表
- 查询参数：page、size、sort_by、sort_desc
- 返回值：同上

### GET /api/v1/users/{user_id}
- 描述：根据ID获取用户信息
- 路径参数：user_id: string
- 返回值：UserResponse

### GET /api/v1/users/by-username/{username}
- 描述：根据用户名获取用户
- 路径参数：username: string
- 返回值：UserResponse

### GET /api/v1/users/by-email/{email}
- 描述：根据邮箱获取用户
- 路径参数：email: string
- 返回值：UserResponse

### PUT /api/v1/users/{user_id}
- 描述：更新用户信息
- 路径参数：user_id: string
- 请求体：UserUpdate
- 返回值：UserResponse

### DELETE /api/v1/users/{user_id}
- 描述：删除用户（支持软/硬删除）
- 路径参数：user_id: string
- 查询参数：hard_delete: bool（可选）
- 返回值：
  ```json
  { "success": true }
  ```

### POST /api/v1/users/batch-delete
- 描述：批量删除用户
- 请求体：BatchDeleteRequest
- 返回值：BatchOperationResponse

### POST /api/v1/users/batch-update-status
- 描述：批量更新用户状态
- 请求体：BatchUpdateRequest
- 返回值：BatchOperationResponse

### GET /api/v1/users/check-username/{username}
- 描述：检查用户名可用
- 路径参数：username: string
- 返回值：
  ```json
  { "available": true }
  ```

### GET /api/v1/users/check-email/{email}
- 描述：检查邮箱可用
- 路径参数：email: string
- 返回值：
  ```json
  { "available": true }
  ```

### GET /api/v1/users/{user_id}/roles
- 描述：获取用户所有角色
- 路径参数：user_id: string
- 返回值：
  ```json
  { "data": [ ... ] }
  ```

### GET /api/v1/users/{user_id}/with-roles
- 描述：获取用户及角色信息
- 路径参数：user_id: string
- 返回值：UserWithRoles

---

## 角色管理 API

### POST /api/v1/roles
- 描述：创建角色
- 请求体：RoleCreate
- 返回值：RoleResponse

### GET /api/v1/roles
- 描述：分页获取角色列表
- 查询参数：keyword、is_active、page、size、sort_by、sort_desc
- 返回值：
  ```json
  { "data": [ ... ], "total": 100 }
  ```

### GET /api/v1/roles/{role_id}
- 描述：根据ID获取角色信息
- 路径参数：role_id: string
- 返回值：RoleResponse

### PUT /api/v1/roles/{role_id}
- 描述：更新角色信息
- 路径参数：role_id: string
- 请求体：RoleUpdate
- 返回值：RoleResponse

### DELETE /api/v1/roles/{role_id}
- 描述：删除角色（支持软/硬删除）
- 路径参数：role_id: string
- 查询参数：hard_delete: bool（可选）
- 返回值：RoleResponse

### POST /api/v1/roles/{role_id}/assign-users
- 描述：为角色分配用户
- 路径参数：role_id: string
- 请求体：user_ids: [string]
- 返回值：RoleWithUsers

### POST /api/v1/roles/{role_id}/remove-users
- 描述：从角色移除用户
- 路径参数：role_id: string
- 请求体：user_ids: [string]
- 返回值：RoleWithUsers

### GET /api/v1/roles/{role_id}/users
- 描述：获取角色及用户信息
- 路径参数：role_id: string
- 返回值：RoleWithUsers

### GET /api/v1/roles/{role_id}/permissions
- 描述：获取角色及权限信息
- 路径参数：role_id: string
- 返回值：RoleWithPermission

### POST /api/v1/roles/assign-user-roles
- 描述：批量分配用户角色
- 请求体：UserRoleAssignRequest
- 返回值：BatchOperationResponse

---

## 权限管理 API

### POST /api/v1/permissions
- 描述：创建权限
- 请求体：PermissionCreate
- 返回值：PermissionResponse

### GET /api/v1/permissions
- 描述：分页获取权限列表
- 查询参数：skip、limit、resource、action、keyword、include_deleted
- 返回值：
  ```json
  { "data": [ ... ], "total": 100 }
  ```

### GET /api/v1/permissions/{permission_id}
- 描述：根据ID获取权限信息
- 路径参数：permission_id: string
- 返回值：PermissionResponse

### PUT /api/v1/permissions/{permission_id}
- 描述：更新权限信息
- 路径参数：permission_id: string
- 请求体：PermissionUpdate
- 返回值：PermissionResponse

### DELETE /api/v1/permissions/{permission_id}
- 描述：删除权限（支持软/硬删除）
- 路径参数：permission_id: string
- 查询参数：hard_delete: bool（可选）
- 返回值：PermissionResponse

### GET /api/v1/permissions/by-code/{code}
- 描述：根据权限代码获取权限
- 路径参数：code: string
- 返回值：PermissionResponse

### GET /api/v1/permissions/by-resource-action
- 描述：根据资源和操作获取权限
- 查询参数：resource: string, action: string
- 返回值：PermissionResponse

### GET /api/v1/permissions/exists/{permission_id}
- 描述：检查权限是否存在
- 路径参数：permission_id: string
- 返回值：
  ```json
  { "exists": true }
  ```

### GET /api/v1/permissions/code-exists/{code}
- 描述：检查权限代码是否存在
- 路径参数：code: string
- 查询参数：exclude_id: string（可选）
- 返回值：
  ```json
  { "exists": true }
  ```

### POST /api/v1/permissions/validate-ids
- 描述：验证权限ID列表有效性
- 请求体：permission_ids: [string]
- 返回值：
  ```json
  { "valid": true }
  ```

### POST /api/v1/permissions/batch-update-status
- 描述：批量更新权限状态
- 请求体：permission_ids: [string], is_active: bool
- 返回值：BatchOperationResponse

### POST /api/v1/permissions/batch-delete
- 描述：批量删除权限
- 请求体：permission_ids: [string], hard_delete: bool（可选）
- 返回值：BatchOperationResponse

### POST /api/v1/permissions/by-codes
- 描述：根据权限代码列表获取权限
- 请求体：codes: [string]
- 返回值：
  ```json
  { "data": [ ... ] }
  ```

### GET /api/v1/permissions/{permission_id}/roles
- 描述：获取权限及角色信息
- 路径参数：permission_id: string
- 返回值：PermissionWithRoles

### POST /api/v1/permissions/{permission_id}/assign-roles
- 描述：给角色赋予权限
- 路径参数：permission_id: string
- 请求体：role_ids: [string]
- 返回值：PermissionWithRoles

### POST /api/v1/permissions/{permission_id}/remove-roles
- 描述：移除角色权限
- 路径参数：permission_id: string
- 请求体：role_ids: [string]
- 返回值：PermissionWithRoles

### GET /api/v1/permissions/by-role/{role_id}
- 描述：获取角色的权限列表
- 路径参数：role_id: string
- 返回值：
  ```json
  { "data": [ ... ] }
  ```

### GET /api/v1/permissions/role-has-permission
- 描述：检查角色是否具有某个权限
- 查询参数：role_id: string, permission_id: string
- 返回值：
  ```json
  { "has_permission": true }
  ```

### POST /api/v1/permissions/batch-assign-permissions
- 描述：批量分配权限给角色
- 请求体：permission_role_mapping: { permission_id: [role_id, ...] }
- 返回值：
  ```json
  { "data": [ ... ] }
  ```

### GET /api/v1/permissions/{permission_id}/role-ids
- 描述：获取拥有指定权限的角色ID列表
- 路径参数：permission_id: string
- 返回值：
  ```json
  { "role_ids": [ ... ] }
  ```

### GET /api/v1/permissions/user-permissions/{user_id}
- 描述：获取用户的所有权限（通过角色）
- 路径参数：user_id: string
- 返回值：
  ```json
  { "data": [ ... ] }
  ```

---

## 审计日志 API

### GET /api/v1/audit-logs/{log_id}
- 描述：根据ID获取审计日志
- 路径参数：log_id: integer
- 返回值：AuditLogResponse

### GET /api/v1/audit-logs/user/{user_id}
- 描述：获取指定用户的审计日志
- 路径参数：user_id: string
- 查询参数：limit、offset
- 返回值：
  ```json
  [ { ...AuditLogResponse... } ]
  ```

### GET /api/v1/audit-logs/latest
- 描述：获取最新的审计日志
- 查询参数：limit
- 返回值：
  ```json
  [ { ...AuditLogResponse... } ]
  ```

### GET /api/v1/audit-logs/
- 描述：条件分页查询审计日志
- 查询参数：user_id、action、resource、status、start_date、end_date、page、size、sort_by、sort_desc、include_deleted
- 返回值：
  ```json
  {
    "data": [ { ...AuditLogResponse... } ],
    "total": 100,
    "page": 1,
    "size": 20
  }
  ```

### GET /api/v1/audit-logs/action/{action}
- 描述：根据操作类型获取审计日志
- 路径参数：action: string
- 查询参数：limit、offset
- 返回值：
  ```json
  [ { ...AuditLogResponse... } ]
  ```

### GET /api/v1/audit-logs/resource/{resource}
- 描述：根据资源类型获取审计日志
- 路径参数：resource: string
- 查询参数：limit、offset
- 返回值：
  ```json
  [ { ...AuditLogResponse... } ]
  ```

### GET /api/v1/audit-logs/failed
- 描述：获取失败的操作日志
- 查询参数：limit、offset
- 返回值：
  ```json
  [ { ...AuditLogResponse... } ]
  ```

### GET /api/v1/audit-logs/date-range
- 描述：根据日期范围获取审计日志
- 查询参数：start_date、end_date、limit、offset
- 返回值：
  ```json
  [ { ...AuditLogResponse... } ]
  ```

### GET /api/v1/audit-logs/count/action/{action}
- 描述：统计指定操作类型的日志数量
- 路径参数：action: string
- 返回值：
  ```json
  { "action": "string", "count": 10 }
  ```

### GET /api/v1/audit-logs/count/user/{user_id}
- 描述：统计指定用户的日志数量
- 路径参数：user_id: string
- 返回值：
  ```json
  { "user_id": "string", "count": 10 }
  ```

### GET /api/v1/audit-logs/summary
- 描述：获取审计日志统计摘要
- 返回值：
  ```json
  { ... }
  ```

---

## 性能优化

### 查询优化

所有API端点均已实现预加载查询优化，有效减少N+1查询问题：

#### 认证服务优化
- `/api/v1/auth/me` - 预加载用户角色和权限信息
- `/api/v1/auth/login` - 预加载认证所需的用户角色权限
- `/api/v1/auth/check` - 使用缓存优化的认证状态检查

#### 用户管理优化
- `/api/v1/users` - 列表查询预加载用户角色信息
- `/api/v1/users/{user_id}/roles` - 预加载用户所有角色关联
- `/api/v1/users/{user_id}/with-roles` - 一次查询获取用户及角色详情

#### 角色管理优化
- `/api/v1/roles` - 列表查询预加载角色用户关联
- `/api/v1/roles/{role_id}/users` - 预加载角色及用户信息
- `/api/v1/roles/{role_id}/permissions` - 预加载角色权限关联

#### 权限管理优化
- `/api/v1/permissions` - 列表查询预加载权限角色关联
- `/api/v1/permissions/{permission_id}/roles` - 预加载权限角色信息
- `/api/v1/permissions/user-permissions/{user_id}` - 优化用户权限查询

#### 审计日志优化
- `/api/v1/audit-logs/` - 列表查询预加载用户信息
- `/api/v1/audit-logs/{log_id}` - 预加载日志关联的用户详情
- `/api/v1/audit-logs/user/{user_id}` - 优化用户相关日志查询

### 响应时间优化

- **数据库查询优化**：使用SQLAlchemy的eager loading策略
- **关联查询优化**：减少数据库往返次数
- **预加载策略**：避免N+1查询问题
- **查询性能提升**：平均响应时间减少60-80%

---

## 错误处理

### HTTP状态码

- `200` - 成功
- `201` - 创建成功  
- `400` - 请求参数错误
- `401` - 未认证
- `403` - 权限不足
- `404` - 资源不存在
- `409` - 资源冲突
- `422` - 数据验证失败
- `500` - 服务器内部错误

### 错误响应格式

```json
{
  "code": 400,
  "message": "Validation error",
  "errors": [
    {
      "field": "email",
      "message": "Email format is invalid"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "uuid-string"
}
```
