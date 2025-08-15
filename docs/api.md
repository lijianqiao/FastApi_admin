## API 文档

### 基础信息
- **Base URL**: `http://127.0.0.1:8000/api`
- **Version**: `/v1`
- **认证方式**: Bearer Token（请求头 `Authorization: Bearer <access_token>`）
- **Content-Type**: `application/json; charset=utf-8`

### 统一响应
- **BaseResponse[T]**: `{ code: number, message: string, data: T | null, timestamp: string }`
- **SuccessResponse**: `{ code: 200, message: string, data: {}, timestamp: string }`
- **PaginatedResponse[T]**: `{ code: 200, message: string, data: T[], total: number, page: number, page_size: number, timestamp: string }`
- **ErrorResponse**: `{ code: number, message: string, detail?: any }`

未认证/未授权等错误也统一为上述 ErrorResponse 结构，例如：

```json
{
  "code": 401,
  "message": "Not authenticated",
  "detail": null
}
```

### 速率限制（后端统一 Redis）
- 登录: 3 次/10 秒
- 刷新: 10 次/60 秒
- 修改密码: 5 次/60 秒

## 系统与监控
### 健康检查
- GET `/api/health`
  - 公开
  - 返回: 系统状态、版本、环境、时间戳

### 指标（Prometheus）
- GET `/metrics`
  - 公开（Prometheus 文本）
  - 指标示例: `http_requests_total`, `http_request_duration_seconds_*`, `http_errors_total`, `active_connections`, `redis_up`

### 应用指标（JSON）
- GET `/api/metrics`
  - 需认证
  - 返回: 应用与系统资源指标（JSON）

## 认证 Auth（/api/v1/auth）
- POST `/login`
  - Body: `{ username, password }`
  - 返回: `TokenResponse`
- POST `/login/form`
  - Form: `username, password`
  - 返回: `TokenResponse`
- POST `/logout`
  - 需认证
  - 返回: `SuccessResponse`
- POST `/refresh`
  - Body: `{ refresh_token }`
  - 返回: `TokenResponse`
- GET `/profile`
  - 需认证
  - 返回: `BaseResponse<UserDetailResponse>`
- PUT `/profile`
  - 需认证，Body: `UpdateProfileRequest`
  - 返回: `BaseResponse<UserResponse>`
- PUT `/password`
  - 需认证，Body: `ChangePasswordRequest`
  - 返回: `SuccessResponse`

## 用户管理 Users（/api/v1/users）
- GET ``
  - 权限: `user:read`
  - Query: `UserListRequest`（分页/筛选）
  - 返回: `PaginatedResponse<UserResponse>`
- GET `/{user_id}`
  - 权限: `user:read`
  - 返回: `BaseResponse<UserDetailResponse>`
- POST ``
  - 权限: `user:create`
  - Body: `UserCreateRequest`
  - 返回: `BaseResponse<UserResponse>`
- PUT `/{user_id}`
  - 权限: `user:update`
  - Body: `UserUpdateRequest`（必须包含 `version`）
  - 返回: `BaseResponse<UserResponse>`
- DELETE `/{user_id}`
  - 权限: `user:delete`
  - 返回: `SuccessResponse`
- PUT `/{user_id}/status`
  - 权限: `user:update`
  - Query: `is_active: bool`
  - 返回: `SuccessResponse`

### 用户-角色
- POST `/{user_id}/roles`（全量设置） 权限: `user:assign_roles` → `BaseResponse<UserDetailResponse>`
- POST `/{user_id}/roles/add`（增量添加） 权限: `user:assign_roles` → `BaseResponse<UserDetailResponse>`
- DELETE `/{user_id}/roles/remove`（移除指定） 权限: `user:assign_roles` → `BaseResponse<UserDetailResponse>`
- GET `/{user_id}/roles` 权限: `user:read` → `BaseResponse<list>`

### 用户-权限
- POST `/{user_id}/permissions`（全量设置） 权限: `user:assign_permissions` → `BaseResponse<UserDetailResponse>`
- POST `/{user_id}/permissions/add`（增量添加） 权限: `user:assign_permissions` → `BaseResponse<UserDetailResponse>`
- DELETE `/{user_id}/permissions/remove`（移除指定） 权限: `user:assign_permissions` → `BaseResponse<UserDetailResponse>`
- GET `/{user_id}/permissions` 权限: `user:read` → `BaseResponse<PermissionResponse[]>`

## 角色管理 Roles（/api/v1/roles）
- GET `` 权限: `role:read` → `RoleListResponse`
- GET `/{role_id}` 权限: `role:read` → `BaseResponse<RoleDetailResponse>`
- POST `` 权限: `role:create` → `BaseResponse<RoleResponse>`
- PUT `/{role_id}` 权限: `role:update` → `BaseResponse<RoleResponse>`
- DELETE `/{role_id}` 权限: `role:delete` → `SuccessResponse`
- PUT `/{role_id}/status` 权限: `role:update` → `SuccessResponse`

### 角色-权限
- POST `/{role_id}/permissions`（全量设置） 权限: `role:assign_permissions` → `BaseResponse<RoleDetailResponse>`
- POST `/{role_id}/permissions/add`（增量添加） 权限: `role:assign_permissions` → `BaseResponse<RoleDetailResponse>`
- DELETE `/{role_id}/permissions/remove`（移除指定） 权限: `role:assign_permissions` → `BaseResponse<RoleDetailResponse>`
- GET `/{role_id}/permissions` 权限: `role:read` → `BaseResponse<list>`

## 权限管理 Permissions（/api/v1/permissions）
- GET `` 权限: `permission:read` → `PermissionListResponse`
- GET `/{permission_id}` 权限: `permission:read` → `BaseResponse<PermissionResponse>`
- POST `` 权限: `permission:create` → `BaseResponse<PermissionResponse>`
- PUT `/{permission_id}` 权限: `permission:update` → `BaseResponse<PermissionResponse>`
- DELETE `/{permission_id}` 权限: `permission:delete` → `SuccessResponse`
- PUT `/{permission_id}/status` 权限: `permission:update` → `SuccessResponse`

## 操作日志 Operation Logs（/api/v1/operation-logs）
- GET `` 权限: `log:view` → `OperationLogListResponse`
- GET `/statistics` 权限: `log:view` → `BaseResponse<OperationLogStatisticsResponse>`
- DELETE `/cleanup?days=30` 权限: `log:delete` → `SuccessResponse`

## 权限缓存管理 Permission Cache（/api/v1/permission-cache）
- GET `/stats` 权限: `system:admin` → `BaseResponse<dict>`
- GET `/test/{user_id}` 权限: `system:admin` → `BaseResponse<dict>`（调试用途，不建议前端集成）
- DELETE `/user/{user_id}` 权限: `system:admin` → `BaseResponse`
- DELETE `/role/{role_id}` 权限: `system:admin` → `BaseResponse`
- DELETE `/all` 权限: `system:admin` → `BaseResponse`

## 用户关系管理 User Relations（/api/v1/user-relations）
### 批量用户-角色
- POST `/batch/users/roles/assign` 权限: `user:assign_roles` → `BaseResponse<dict>`
- POST `/batch/users/roles/add` 权限: `user:assign_roles` → `BaseResponse<dict>`
- DELETE `/batch/users/roles/remove` 权限: `user:assign_roles` → `BaseResponse<dict>`

### 批量用户-权限
- POST `/batch/users/permissions/assign` 权限: `user:assign_permissions` → `BaseResponse<dict>`

### 复杂查询
- GET `/roles/{role_id}/users` 权限: `user:read` → `BaseResponse<UserResponse[]>`
- GET `/permissions/{permission_id}/users` 权限: `user:read` → `BaseResponse<UserResponse[]>`
- GET `/users/{user_id}/summary` 权限: `user:read` → `BaseResponse<UserRolePermissionSummary>`

### 角色-用户批量
- POST `/roles/{role_id}/users/assign` 权限: `user:assign_roles` → `BaseResponse<dict>`
- DELETE `/roles/{role_id}/users/remove` 权限: `user:assign_roles` → `BaseResponse<dict>`

## 备注
- 未暴露模块：`admin_dashboard`（后台管理仪表板）、`admin_routes`（管理员专用）。
- 列表类接口支持分页与筛选，排序字段应使用后端允许的白名单字段。
- 错误码规范：400 参数错误/版本缺失；401 未认证；403 权限不足；409 乐观锁冲突；429 频率受限；5xx 服务端错误。



## 接口请求/响应示例汇总

### Auth
- POST /api/v1/auth/login
请求:
```json
{
  "username": "admin",
  "password": "Admin@123",
  "remember_me": false
}
```
成功响应:
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 3600
}
```
失败响应(401):
```json
{"code":401,"message":"未授权访问","detail":"用户名或密码错误"}
```

- POST /api/v1/auth/logout
请求: 仅需 Authorization 头
成功响应:
```json
{"code":200,"message":"成功","data":{},"timestamp":"2025-01-01T00:00:00+00:00"}
```

- POST /api/v1/auth/refresh
请求:
```json
{"refresh_token": "<jwt>"}
```
成功响应: 同 login 成功响应

- GET /api/v1/auth/profile
请求: 仅需 Authorization 头
成功响应(示例截断):
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": "7c7a2d2b-1111-2222-3333-6f3e2f7f7f7f",
    "username": "admin",
    "is_active": true,
    "is_superuser": true,
    "roles": [],
    "permissions": []
  },
  "timestamp": "2025-01-01T00:00:00+00:00"
}
```
失败响应(401):
```json
{"code":401,"message":"Not authenticated","detail":null}
```

- PUT /api/v1/auth/profile
请求:
```json
{"version": 2, "nickname": "new name", "avatar_url": null, "bio": "hi"}
```
成功响应: 包裹 `UserResponse`

- PUT /api/v1/auth/password
请求:
```json
{
  "version": 2,
  "old_password": "Old@1234",
  "new_password": "New@1234",
  "confirm_password": "New@1234"
}
```
成功响应:
```json
{"code":200,"message":"成功","data":{},"timestamp":"..."}
```
失败响应(400/422):
```json
{"code":422,"message":"请求数据验证失败","detail":[{"loc":["body","confirm_password"],"msg":"两次输入的密码不一致","type":"value_error"}]}
```

### Users
- GET /api/v1/users?page=1&page_size=10
成功响应:
```json
{
  "code": 200,
  "message": "成功",
  "data": [
    {
      "id": "c9c2b7e0-aaaa-bbbb-cccc-d1e2f3a4b5c6",
      "version": 1,
      "created_at": "2025-01-01T00:00:00+00:00",
      "updated_at": "2025-01-01T00:00:00+00:00",
      "username": "user1",
      "phone": "13800000001",
      "nickname": "u1",
      "avatar_url": null,
      "bio": null,
      "is_active": true,
      "is_superuser": false,
      "last_login_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "timestamp": "..."
}
```

- GET /api/v1/users/{user_id}
成功响应: `BaseResponse<UserDetailResponse>`（含 roles/permissions）

- POST /api/v1/users
请求:
```json
{
  "username": "u1",
  "password": "Passw0rd!",
  "phone": "13800000000",
  "nickname": "u1",
  "role_ids": ["8e2c1f9b-0000-1111-2222-333344445555"]
}
```
成功响应: `BaseResponse<UserResponse>`
失败响应(409 重复用户名):
```json
{"code":409,"message":"用户名已存在","detail":null}
```

- PUT /api/v1/users/{user_id}
请求:
```json
{"version": 3, "nickname": "newnick", "is_active": true}
```
失败响应(409 版本冲突):
```json
{"code":409,"message":"数据版本已过期，服务器当前版本为 3，您提交的版本为 2。请刷新后重试。","detail":null}
```

- DELETE /api/v1/users/{user_id}
成功响应:
```json
{"code":200,"message":"成功","data":{},"timestamp":"..."}
```

- PUT /api/v1/users/{user_id}/status?is_active=false
成功响应: 同上 `SuccessResponse`

- POST /api/v1/users/{user_id}/roles
请求:
```json
{"role_ids":["8e2c1f9b-0000-1111-2222-333344445555"]}
```
成功响应: `BaseResponse<UserDetailResponse>`

- POST /api/v1/users/{user_id}/roles/add
请求: 同上（增量）

- DELETE /api/v1/users/{user_id}/roles/remove
请求:
```json
{"role_ids":["8e2c1f9b-0000-1111-2222-333344445555"]}
```

- GET /api/v1/users/{user_id}/roles
成功响应:
```json
{"code":200,"message":"成功","data":[{"id":"uuid","role_name":"管理员","role_code":"admin"}],"timestamp":"..."}
```

- POST /api/v1/users/{user_id}/permissions
请求:
```json
{"permission_ids":["7a7a7a7a-aaaa-bbbb-cccc-ddddeeeeffff"]}
```
成功响应: `BaseResponse<UserDetailResponse>`

- POST /api/v1/users/{user_id}/permissions/add
请求: 同上（增量）

- DELETE /api/v1/users/{user_id}/permissions/remove
请求:
```json
{"permission_ids":["7a7a7a7a-aaaa-bbbb-cccc-ddddeeeeffff"]}
```

- GET /api/v1/users/{user_id}/permissions
成功响应（简化）:
```json
{"code":200,"message":"成功","data":[{"permission_name":"查看用户","permission_code":"user:read","permission_type":"button"}],"timestamp":"..."}
```

### Roles
- GET /api/v1/roles?page=1&page_size=10
成功响应（列表项为 RoleResponse）

- GET /api/v1/roles/{role_id}
成功响应: `BaseResponse<RoleDetailResponse>`（含 permissions）

- POST /api/v1/roles
请求:
```json
{"role_name":"管理员","role_code":"admin","description":"desc"}
```
成功响应: `BaseResponse<RoleResponse>`

- PUT /api/v1/roles/{role_id}
请求:
```json
{"version": 2, "description": "new desc"}
```

- DELETE /api/v1/roles/{role_id}
成功响应: `SuccessResponse`

- PUT /api/v1/roles/{role_id}/status?is_active=true
成功响应: `SuccessResponse`

- POST /api/v1/roles/{role_id}/permissions
请求:
```json
{"permission_ids":["7a7a...","9b9b..."]}
```
成功响应: `BaseResponse<RoleDetailResponse>`

- POST /api/v1/roles/{role_id}/permissions/add
请求: 同上（增量）

- DELETE /api/v1/roles/{role_id}/permissions/remove
请求:
```json
{"permission_ids":["7a7a..."]}
```

- GET /api/v1/roles/{role_id}/permissions
成功响应（示例）:
```json
{"code":200,"message":"成功","data":[{"id":"uuid","permission_name":"用户查看","permission_code":"user:read","permission_type":"button"}],"timestamp":"..."}
```

### Permissions
- GET /api/v1/permissions?page=1&page_size=10
成功响应（列表项为 PermissionResponse）

- GET /api/v1/permissions/{permission_id}
成功响应: `BaseResponse<PermissionResponse>`

- POST /api/v1/permissions
请求:
```json
{"permission_name":"用户查看","permission_code":"user:read","permission_type":"button","description":"desc"}
```
成功响应: `BaseResponse<PermissionResponse>`

- PUT /api/v1/permissions/{permission_id}
请求:
```json
{"version":2,"description":"new"}
```

- DELETE /api/v1/permissions/{permission_id}
成功响应: `SuccessResponse`

- PUT /api/v1/permissions/{permission_id}/status?is_active=false
成功响应: `SuccessResponse`

### Operation Logs
- GET /api/v1/operation-logs?page=1&page_size=10
成功响应: `OperationLogListResponse`（列表项为 OperationLogResponse）

- GET /api/v1/operation-logs/statistics?start_date=2025-01-01&end_date=2025-01-31
成功响应（示例）:
```json
{"code":200,"message":"成功","data":{"data":{"count":100}},"timestamp":"..."}
```

- DELETE /api/v1/operation-logs/cleanup?days=30
成功响应: `SuccessResponse`

### Permission Cache（运维）
- GET /api/v1/permission-cache/stats
成功响应（示例）:
```json
{"code":200,"message":"成功","data":{"backend":"redis","permission_keys":10},"timestamp":"..."}
```

- GET /api/v1/permission-cache/test/{user_id}
成功响应（示例）:
```json
{"code":200,"message":"成功","data":{"first_fetch":["user:read"],"second_fetch":["user:read"],"cache_consistent":true,"cache_stats":{"backend":"redis"}},"timestamp":"..."}
```

- DELETE /api/v1/permission-cache/user/{user_id}
成功响应: `BaseResponse{ message }`

- DELETE /api/v1/permission-cache/role/{role_id}
成功响应: 同上

- DELETE /api/v1/permission-cache/all
成功响应: 同上

### User Relations（批量/复杂）
- POST /api/v1/user-relations/batch/users/roles/assign
请求:
```json
{"user_ids":["uuid1","uuid2"],"role_ids":["uuidA","uuidB"]}
```
成功响应:
```json
{"code":200,"message":"成功为 2 个用户分配角色","data":{"success_count":2,"total_count":2},"timestamp":"..."}
```

- POST /api/v1/user-relations/batch/users/permissions/assign
请求:
```json
{"user_ids":["uuid1"],"permission_ids":["permUuid"]}
```
成功响应: 同上（文案不同）

- GET /api/v1/user-relations/roles/{role_id}/users
成功响应: `BaseResponse<UserResponse[]>`

- GET /api/v1/user-relations/users/{user_id}/summary
成功响应（示例）:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "user_id": "uuid",
    "username": "user1",
    "roles": [{"id":"uuid","role_name":"管理员","role_code":"admin"}],
    "direct_permissions": [{"id":"uuid","name":"用户查看","code":"user:read"}],
    "total_permissions": [{"id":"uuid","name":"用户查看","code":"user:read"}]
  },
  "timestamp": "..."
}
```

## 示例与字段约束（基于 @schemas 展开）

### Auth 相关
- LoginRequest（POST /auth/login | /auth/login/form）
  - 字段
    - username: string，最小 3，最大 50
    - password: string，最小 6，最大 128
    - remember_me: boolean，默认 false
  - 成功响应（TokenResponse）
    - access_token: string (JWT)
    - refresh_token: string|null (JWT)
    - token_type: string，默认 "Bearer"
    - expires_in: number（秒）
  - 失败响应（示例）
    - 401 未认证/凭证错误：{"code":401,"message":"未授权访问","detail":"用户名或密码错误"}
    - 429 频率受限：{"code":429,"message":"请求过于频繁，请稍后再试","detail":null}
  - 请求示例
    ```json
    {"username":"admin","password":"Admin@123"}
    ```

- UpdateProfileRequest（PUT /auth/profile）
  - version: int（必填）
  - nickname?: string ≤100
  - avatar_url?: string ≤500
  - bio?: string

- ChangePasswordRequest（PUT /auth/password）
  - old_password: string 6-128
  - new_password: string 6-128（不得与 old_password 相同）
  - confirm_password: string 6-128（必须与 new_password 一致）
  - version: int（必填）

- UserDetailResponse（GET /auth/profile 成功 data）
  - id: UUID
  - version: int
  - created_at/updated_at: datetime
  - username: string 3-50
  - phone: string|null ≤20
  - nickname: string|null ≤100
  - avatar_url: string|null ≤500
  - bio: string|null
  - is_active: bool
  - is_superuser: bool
  - last_login_at: datetime|null
  - roles: RoleResponse[]
  - permissions: PermissionResponse[]

### Users 相关（/users）
- UserListRequest（GET /users）
  - page: int≥1 默认1
  - page_size: int 1~100 默认10
  - keyword?: string ≤100
  - is_superuser?: bool
  - role_code?: string
  - include_deleted?: bool 默认 false
  - sort_by?: string（默认 created_at）
  - sort_order: asc|desc 默认 desc
  - 成功响应：PaginatedResponse<UserResponse>

- UserCreateRequest（POST /users）
  - username: string 3-50
  - password: string 6-128
  - phone?: string ≤20
  - nickname?: string ≤100
  - role_ids: UUID[] 默认 []
  - 成功响应：BaseResponse<UserResponse>

- UserUpdateRequest（PUT /users/{user_id}）
  - version: int（必填）
  - phone?: string ≤20
  - nickname?: string ≤100
  - avatar_url?: string ≤500
  - bio?: string
  - is_active?: bool
  - 成功响应：BaseResponse<UserResponse>
  - 失败响应：409 版本冲突，400 缺失 version，401/403 权限问题

- 用户-角色/权限变更（POST/DELETE 多个端点）
  - UserAssignRolesRequest: { role_ids: UUID[] (≥0) }
  - UserAssignPermissionsRequest: { permission_ids: UUID[] (≥0) }
  - 成功响应：BaseResponse<UserDetailResponse>

### Roles 相关（/roles）
- RoleListRequest（GET /roles）
  - page/page_size/keyword/sort_by/sort_order
  - role_code?: string
  - is_active?: bool

- RoleCreateRequest（POST /roles）
  - role_name: string 2-50
  - role_code: string 2-50
  - description?: string ≤200

- RoleUpdateRequest（PUT /roles/{role_id}）
  - version: int（必填）
  - role_name?: string 2-50
  - description?: string ≤200
  - is_active?: bool

- RoleDetailResponse
  - 继承 RoleBase + permissions: PermissionResponse[]

- RolePermissionAssignRequest（角色-权限相关端点）
  - permission_ids: UUID[]

### Permissions 相关（/permissions）
- PermissionListRequest（GET /permissions）
  - page/page_size/keyword/sort_by/sort_order
  - permission_type?: string

- PermissionCreateRequest（POST /permissions）
  - permission_name: string 2-100
  - permission_code: string 2-100
  - permission_type: string ≤50
  - description?: string ≤200

- PermissionUpdateRequest（PUT /permissions/{permission_id}）
  - version: int（必填）
  - permission_name?: string 2-100
  - permission_type?: string ≤50
  - description?: string ≤200

- PermissionResponse
  - 继承 PermissionBase + role_count: int, user_count: int

### Operation Logs 相关（/operation-logs）
- OperationLogListRequest（GET /operation-logs）
  - page/page_size/keyword/username/status/start_date/end_date/sort_by/sort_order
  - 成功响应：PaginatedResponse<OperationLogResponse>

- OperationLogStatisticsRequest（GET /operation-logs/statistics）
  - start_date: date
  - end_date: date
  - user_ids?: UUID[]
  - 成功响应：BaseResponse<{ data: object }>

- OperationLogResponse（列表项）
  - 继承 OperationLogBase + user_id: UUID|null, username: string|null, details: dict|null

### 用户关系管理/批量操作（/user-relations）
- BatchUserRoleRequest（多端点）
  - user_ids: UUID[]
  - role_ids: UUID[]

- BatchUserPermissionRequest（/batch/users/permissions/assign）
  - user_ids: UUID[]
  - permission_ids: UUID[]

### 统一错误示例
- 401 未认证
  ```json
  {"code":401,"message":"Not authenticated","detail":null}
  ```
- 403 权限不足
  ```json
  {"code":403,"message":"禁止访问","detail":null}
  ```
- 409 版本冲突（示例）
  ```json
  {"code":409,"message":"数据版本已过期，服务器当前版本为 3，您提交的版本为 2。请刷新后重试。","detail":null}
  ```
