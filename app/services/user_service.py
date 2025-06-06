"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: user_service.py
@DateTime: 2025/06/04 14:30:00
@Docs: 用户服务 - 处理用户CRUD操作、资料管理等业务逻辑

用户服务层

提供用户相关的业务逻辑处理，包括用户注册、信息更新、密码修改、角色分配等。
"""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.exceptions import (
    DuplicateRecordError,
    RecordNotFoundError,
    ValidationError,
)
from app.models import User
from app.repositories import UserRepository
from app.schemas.schemas import (
    BatchDeleteRequest,
    BatchOperationResponse,
    BatchUpdateRequest,
    UserCreate,
    UserQuery,
    UserResponse,
    UserUpdate,
    UserWithRoles,
)
from app.services.base import AppBaseService
from app.utils.audit import audit_log


class UserService(AppBaseService[User, UUID]):
    """
    用户服务类

    提供用户的CRUD操作、密码管理、用户查询等功能
    继承AppBaseService以复用基础功能，专注于用户业务逻辑
    支持审计日志记录和后台管理系统完整功能
    """

    repository_type = UserRepository

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    @property
    def user_repo(self) -> UserRepository:
        """获取类型化的用户仓库实例"""
        return self.repository  # type: ignore

    @audit_log(action="CREATE", resource="User", get_resource_id=lambda result: str(result.id))
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """
        创建新用户

        Args:
            user_data: 用户创建数据

        Returns:
            创建的用户响应对象

        Raises:
            DuplicateRecordError: 当用户名、邮箱或手机号已存在时
            ValidationError: 当用户数据验证失败时
        """
        try:
            self.logger.info(f"开始创建用户: {user_data.username}")

            # 检查用户名是否已存在
            if await self.user_repo.check_username_exists(user_data.username):
                self.logger.warning(f"用户名已存在: {user_data.username}")
                raise DuplicateRecordError("用户名已存在")

            # 检查邮箱是否已存在
            if await self.user_repo.check_email_exists(user_data.email):
                self.logger.warning(f"邮箱已存在: {user_data.email}")
                raise DuplicateRecordError("邮箱已存在")

            # 检查手机号是否已存在（如果提供了手机号）
            if user_data.phone and await self.user_repo.get_by_phone(user_data.phone):
                self.logger.warning(f"手机号已存在: {user_data.phone}")
                raise DuplicateRecordError("手机号已存在")

            # 加密密码
            password_hash = get_password_hash(user_data.password)

            # 创建用户数据
            user_dict = user_data.model_dump(exclude={"password"})
            user_dict["password_hash"] = password_hash

            # 使用基类方法创建用户
            user = await self.create_record_svc(user_dict)
            self.logger.info(f"用户创建成功: {user.username} (ID: {user.id})")

            return UserResponse(
                id=user.id,
                username=user.username,
                email=user.email,
                phone=user.phone,
                nickname=user.nickname,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                is_deleted=user.is_deleted,
                last_login=user.last_login,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

        except (DuplicateRecordError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"创建用户失败: {user_data.username} - {e}")
            raise ValidationError(f"创建用户失败: {e}") from e

    @audit_log(action="UPDATE", resource="User", get_resource_id=lambda result: str(result.id))
    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> UserResponse:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            user_data: 用户更新数据

        Returns:
            更新后的用户响应对象

        Raises:
            RecordNotFoundError: 当用户不存在时
            DuplicateRecordError: 当邮箱或手机号已存在时
            ValidationError: 当用户数据验证失败时
        """
        try:
            self.logger.info(f"开始更新用户: {user_id}")

            # 检查用户是否存在
            existing_user = await self.get_record_by_id(user_id)
            if not existing_user:
                raise RecordNotFoundError("用户不存在")

            # 构建更新数据
            update_dict = {}
            if user_data.email and user_data.email != existing_user.email:
                # 检查邮箱是否已被其他用户使用
                if await self.user_repo.check_email_exists(user_data.email, user_id):
                    raise DuplicateRecordError("邮箱已存在")
                update_dict["email"] = user_data.email

            if user_data.phone and user_data.phone != existing_user.phone:
                # 检查手机号是否已被其他用户使用
                existing_phone_user = await self.user_repo.get_by_phone(user_data.phone)
                if existing_phone_user and existing_phone_user.id != user_id:
                    raise DuplicateRecordError("手机号已存在")
                update_dict["phone"] = user_data.phone

            if user_data.nickname and user_data.nickname != existing_user.nickname:
                update_dict["nickname"] = user_data.nickname

            if user_data.is_active is not None and user_data.is_active != existing_user.is_active:
                update_dict["is_active"] = user_data.is_active

            # 如果没有更新内容，直接返回原用户
            if not update_dict:
                self.logger.info(f"用户信息无变化: {user_id}")
                return UserResponse.model_validate(existing_user)

            # 使用基类方法更新用户
            updated_user = await self.update_record_svc(user_id, update_dict)
            username = getattr(updated_user, "username", "未知用户")
            self.logger.info(f"用户更新成功: {username} (ID: {user_id})")

            return UserResponse.model_validate(updated_user)

        except (RecordNotFoundError, DuplicateRecordError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"更新用户失败: {user_id} - {e}")
            raise ValidationError(f"更新用户失败: {e}") from e

    @audit_log(action="VIEW", resource="User", get_resource_id=lambda result: str(result.id))
    async def get_user_by_id(self, user_id: UUID) -> UserResponse:
        """
        根据ID获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户响应对象

        Raises:
            RecordNotFoundError: 当用户不存在时
        """
        try:
            user = await self.get_record_by_id(user_id)
            if not user:
                raise RecordNotFoundError("用户不存在")

            return UserResponse.model_validate(user)

        except RecordNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"获取用户失败: {user_id} - {e}")
            raise ValidationError(f"获取用户失败: {e}") from e

    @audit_log(action="VIEW", resource="UserWithRoles", get_resource_id=lambda result: str(result.id))
    async def get_user_with_roles(self, user_id: UUID) -> UserWithRoles:
        """
        获取用户信息及其角色

        Args:
            user_id: 用户ID

        Returns:
            带角色的用户响应对象

        Raises:
            RecordNotFoundError: 当用户不存在时
        """
        try:
            # 使用预加载优化的方法获取用户及其角色
            user = await self.user_repo.get_with_roles(user_id)
            if not user:
                raise RecordNotFoundError("用户不存在")

            return UserWithRoles.model_validate(user)

        except RecordNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"获取用户及角色失败: {user_id} - {e}")
            raise ValidationError(f"获取用户及角色失败: {e}") from e

    @audit_log(action="SEARCH", resource="User")
    async def search_users(self, query: UserQuery) -> tuple[Sequence[UserResponse], int]:
        """
        搜索用户

        Args:
            query: 用户查询参数

        Returns:
            用户列表和总数

        Raises:
            ValidationError: 当查询参数无效时
        """
        try:
            users, total = await self.user_repo.search_users(
                keyword=query.keyword,
                is_active=query.is_active,
                page=query.page,
                page_size=query.size,
                sort_by=query.sort_by or "created_at",
                sort_desc=query.sort_desc,
                include_deleted=False,
            )

            user_responses = [UserResponse.model_validate(user) for user in users]
            return user_responses, total

        except Exception as e:
            self.logger.error(f"搜索用户失败: {e}")
            raise ValidationError(f"搜索用户失败: {e}") from e

    @audit_log(action="LIST", resource="User")
    async def get_active_users(self, query: UserQuery) -> tuple[Sequence[UserResponse], int]:
        """
        获取活跃用户列表

        Args:
            query: 查询参数

        Returns:
            活跃用户列表和总数        Raises:
            ValidationError: 当查询参数无效时
        """
        try:
            users, total = await self.user_repo.search_users(
                is_active=True,
                page=query.page,
                page_size=query.size,
                sort_by=query.sort_by or "created_at",
                sort_desc=query.sort_desc,
            )

            user_responses = [UserResponse.model_validate(user) for user in users]
            return user_responses, total

        except Exception as e:
            self.logger.error(f"获取活跃用户失败: {e}")
            raise ValidationError(f"获取活跃用户失败: {e}") from e

    @audit_log(action="DELETE", resource="User", get_resource_id=lambda kwargs: str(kwargs["user_id"]))
    async def delete_user(self, user_id: UUID, hard_delete: bool = False) -> bool:
        """
        删除用户

        Args:
            user_id: 用户ID
            hard_delete: 是否硬删除

        Returns:
            删除是否成功

        Raises:
            RecordNotFoundError: 当用户不存在时
        """
        try:
            self.logger.info(f"开始删除用户: {user_id} (硬删除: {hard_delete})")

            if hard_delete:
                success = await self.user_repo.delete_record(user_id)
            else:
                success = await self.user_repo.delete_record(user_id)

            if success:
                self.logger.info(f"用户删除成功: {user_id}")
            else:
                self.logger.warning(f"用户删除失败: {user_id}")

            return True if success else False

        except RecordNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"删除用户失败: {user_id} - {e}")
            raise ValidationError(f"删除用户失败: {e}") from e

    @audit_log(action="BATCH_DELETE", resource="User")
    async def batch_delete_users(self, request: BatchDeleteRequest) -> BatchOperationResponse:
        """
        批量删除用户

        Args:
            request: 批量删除请求

        Returns:
            批量操作响应

        Raises:
            ValidationError: 当操作失败时
        """
        try:
            self.logger.info(f"开始批量删除用户: {len(request.ids)} 个")

            success_count = 0
            failed_count = 0
            failed_ids: list[UUID] = []

            for user_id in request.ids:
                try:
                    if request.hard_delete:
                        success = await self.user_repo.delete_record(user_id)
                    else:
                        success = await self.user_repo.delete_record(user_id)

                    if success:
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_ids.append(user_id)

                except Exception as e:
                    self.logger.warning(f"删除用户失败: {user_id} - {e}")
                    failed_count += 1
                    failed_ids.append(user_id)

            self.logger.info(f"批量删除用户完成: 成功 {success_count}, 失败 {failed_count}")

            return BatchOperationResponse(
                success_count=success_count,
                failed_count=failed_count,
                total_count=len(request.ids),
                failed_ids=failed_ids,
            )

        except Exception as e:
            self.logger.error(f"批量删除用户失败: {e}")
            raise ValidationError(f"批量删除用户失败: {e}") from e

    @audit_log(action="BATCH_UPDATE", resource="User")
    async def batch_update_user_status(self, request: BatchUpdateRequest) -> BatchOperationResponse:
        """
        批量更新用户状态

        Args:
            request: 批量更新请求

        Returns:
            批量操作响应

        Raises:
            ValidationError: 当操作失败时
        """
        try:
            self.logger.info(f"开始批量更新用户状态: {len(request.ids)} 个")

            # 检查更新数据是否包含 is_active 字段
            if "is_active" not in request.data:
                raise ValidationError("批量更新用户状态需要 is_active 字段")

            is_active = request.data["is_active"]
            if not isinstance(is_active, bool):
                raise ValidationError("is_active 字段必须是布尔值")

            # 使用仓库的批量更新方法
            updated_count = await self.user_repo.batch_update_status(request.ids, is_active)

            success_count = updated_count
            failed_count = len(request.ids) - updated_count
            failed_ids = request.ids[updated_count:] if failed_count > 0 else []

            await self.session.commit()

            self.logger.info(f"批量更新用户状态完成: 成功 {success_count}, 失败 {failed_count}")

            return BatchOperationResponse(
                success_count=success_count,
                failed_count=failed_count,
                total_count=len(request.ids),
                failed_ids=failed_ids,
            )

        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"批量更新用户状态失败: {e}")
            raise ValidationError(f"批量更新用户状态失败: {e}") from e

    @audit_log(action="VIEW", resource="User", get_resource_id=lambda kwargs: kwargs["username"])
    async def get_user_by_username(self, username: str) -> UserResponse | None:
        """
        根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            用户响应对象或None
        """
        try:
            user = await self.user_repo.get_by_username(username)
            return UserResponse.model_validate(user) if user else None

        except Exception as e:
            self.logger.error(f"根据用户名获取用户失败: {username} - {e}")
            return None

    @audit_log(action="VIEW", resource="User", get_resource_id=lambda kwargs: kwargs["email"])
    async def get_user_by_email(self, email: str) -> UserResponse | None:
        """
        根据邮箱获取用户

        Args:
            email: 邮箱

        Returns:
            用户响应对象或None
        """
        try:
            user = await self.user_repo.get_by_email(email)
            return UserResponse.model_validate(user) if user else None

        except Exception as e:
            self.logger.error(f"根据邮箱获取用户失败: {email} - {e}")
            return None

    async def check_username_available(self, username: str, exclude_user_id: UUID | None = None) -> bool:
        """
        检查用户名是否可用

        Args:
            username: 用户名
            exclude_user_id: 排除的用户ID（用于更新时检查）

        Returns:
            用户名是否可用
        """
        try:
            return not await self.user_repo.check_username_exists(username, exclude_user_id)

        except Exception as e:
            self.logger.error(f"检查用户名可用性失败: {username} - {e}")
            return False

    async def check_email_available(self, email: str, exclude_user_id: UUID | None = None) -> bool:
        """
        检查邮箱是否可用

        Args:
            email: 邮箱
            exclude_user_id: 排除的用户ID（用于更新时检查）

        Returns:
            邮箱是否可用
        """
        try:
            return not await self.user_repo.check_email_exists(email, exclude_user_id)
        except Exception as e:
            self.logger.error(f"检查邮箱可用性失败: {email} - {e}")
            return False

    async def get_user_roles(self, user_id: UUID) -> UserWithRoles:
        """获取用户的所有角色信息（优化版 - 预加载角色关系）"""
        self.logger.info(f"获取用户 {user_id} 的角色信息")

        # 使用预加载优化的方法获取用户及其角色
        user_orm = await self.user_repo.get_with_roles(user_id)
        if not user_orm:
            raise RecordNotFoundError(resource="用户", resource_id=user_id)

        return UserWithRoles.model_validate(user_orm)

    @audit_log(action="LIST", resource="UserWithRoles")
    async def list_users_with_roles(self, query: UserQuery) -> tuple[Sequence[UserWithRoles], int]:
        """
        获取用户列表及其角色信息

        Args:
            query: 用户查询参数

        Returns:
            用户列表（含角色）和总数

        Raises:
            ValidationError: 当查询参数无效时
        """
        try:
            # 使用优化后的预加载方法，但需要使用search_users来获取分页和总数
            users, total = await self.user_repo.search_users(
                keyword=query.keyword,
                is_active=query.is_active,
                page=query.page,
                page_size=query.size,
                sort_by=query.sort_by or "created_at",
                sort_desc=query.sort_desc,
                include_deleted=False,
            )

            # 为了获取角色信息，需要重新查询带角色的用户数据
            user_ids = [user.id for user in users]
            if user_ids:
                from advanced_alchemy.filters import CollectionFilter

                users_with_roles = await self.user_repo.list_with_roles(
                    CollectionFilter(field_name="id", values=user_ids),
                    include_deleted=False,
                )
                # 按原顺序排列
                user_dict = {user.id: user for user in users_with_roles}
                users = [user_dict[user_id] for user_id in user_ids if user_id in user_dict]

            user_responses = [UserWithRoles.model_validate(user) for user in users]
            return user_responses, total

        except Exception as e:
            self.logger.error(f"获取用户及角色列表失败: {e}")
            raise ValidationError(f"获取用户及角色列表失败: {e}") from e
