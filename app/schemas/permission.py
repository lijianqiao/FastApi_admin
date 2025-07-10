"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: permission.py
@DateTime: 2025/01/01
@Docs: 权限管理相关的Pydantic模型
"""

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse, ListQueryRequest, ORMBase, PaginatedResponse


class PermissionBase(ORMBase):
    """权限基础字段"""

    permission_name: str = Field(description="权限名称", min_length=2, max_length=100)
    permission_code: str = Field(description="权限编码", min_length=2, max_length=100)
    permission_type: str = Field(description="权限类型（如: module, button）", max_length=50)
    description: str | None = Field(default=None, description="权限描述", max_length=200)


class PermissionCreateRequest(BaseModel):
    """创建权限请求"""

    permission_name: str = Field(description="权限名称", min_length=2, max_length=100)
    permission_code: str = Field(description="权限编码", min_length=2, max_length=100)
    permission_type: str = Field(description="权限类型（如: module, button）", max_length=50)
    description: str | None = Field(default=None, description="权限描述", max_length=200)


class PermissionUpdateRequest(BaseModel):
    """更新权限请求"""

    permission_name: str | None = Field(default=None, description="权限名称", min_length=2, max_length=100)
    permission_type: str | None = Field(default=None, description="权限类型", max_length=50)
    description: str | None = Field(default=None, description="权限描述", max_length=200)


class PermissionResponse(PermissionBase):
    """权限响应"""

    # 可以在服务层填充这些计数字段
    role_count: int = Field(default=0, description="使用此权限的角色数量")
    user_count: int = Field(default=0, description="拥有此权限的用户数量")


class PermissionListRequest(ListQueryRequest):
    """权限列表查询请求"""

    permission_type: str | None = Field(default=None, description="权限类型筛选")


class PermissionListResponse(PaginatedResponse[PermissionResponse]):
    """权限列表响应"""

    pass


class PermissionDetailResponseWrapper(BaseResponse[PermissionResponse]):
    """权限详情响应包装"""

    pass
