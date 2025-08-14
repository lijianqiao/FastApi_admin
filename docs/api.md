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


