"""Initial migration

Revision ID: 3a2c657e394c
Revises: 
Create Date: 2025-06-05 09:48:20.924431

"""
from typing import Sequence, Union

import advanced_alchemy
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a2c657e394c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('permissions',
    sa.Column('name', sa.String(length=100), nullable=False, comment='权限名称'),
    sa.Column('code', sa.String(length=100), nullable=False, comment='权限代码'),
    sa.Column('description', sa.String(length=255), nullable=True, comment='权限描述'),
    sa.Column('resource', sa.String(length=100), nullable=False, comment='资源名称'),
    sa.Column('action', sa.String(length=50), nullable=False, comment='操作类型'),
    sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='是否已删除'),
    sa.Column('id', advanced_alchemy.types.guid.GUID(length=16), nullable=False),
    sa.Column('sa_orm_sentinel', sa.Integer(), nullable=True),
    sa.Column('created_at', advanced_alchemy.types.datetime.DateTimeUTC(timezone=True), nullable=False),
    sa.Column('updated_at', advanced_alchemy.types.datetime.DateTimeUTC(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_permissions'))
    )
    op.create_index(op.f('ix_permissions_code'), 'permissions', ['code'], unique=True)
    op.create_index(op.f('ix_permissions_name'), 'permissions', ['name'], unique=True)
    op.create_table('roles',
    sa.Column('name', sa.String(length=50), nullable=False, comment='角色名称'),
    sa.Column('description', sa.String(length=255), nullable=True, comment='角色描述'),
    sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否激活'),
    sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='是否已删除'),
    sa.Column('id', advanced_alchemy.types.guid.GUID(length=16), nullable=False),
    sa.Column('sa_orm_sentinel', sa.Integer(), nullable=True),
    sa.Column('created_at', advanced_alchemy.types.datetime.DateTimeUTC(timezone=True), nullable=False),
    sa.Column('updated_at', advanced_alchemy.types.datetime.DateTimeUTC(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roles'))
    )
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)
    op.create_table('users',
    sa.Column('username', sa.String(length=50), nullable=False, comment='用户名'),
    sa.Column('email', sa.String(length=255), nullable=False, comment='邮箱'),
    sa.Column('phone', sa.String(length=20), nullable=True, comment='手机号'),
    sa.Column('password_hash', sa.String(length=255), nullable=False, comment='密码哈希'),
    sa.Column('nickname', sa.String(length=100), nullable=False, comment='昵称'),
    sa.Column('is_active', sa.Boolean(), nullable=False, comment='是否激活'),
    sa.Column('is_superuser', sa.Boolean(), nullable=False, comment='是否超级用户'),
    sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='是否已删除'),
    sa.Column('last_login', advanced_alchemy.types.datetime.DateTimeUTC(timezone=True), nullable=True, comment='最后登录时间'),
    sa.Column('id', advanced_alchemy.types.guid.GUID(length=16), nullable=False),
    sa.Column('sa_orm_sentinel', sa.Integer(), nullable=True),
    sa.Column('created_at', advanced_alchemy.types.datetime.DateTimeUTC(timezone=True), nullable=False),
    sa.Column('updated_at', advanced_alchemy.types.datetime.DateTimeUTC(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('audit_logs',
    sa.Column('user_id', advanced_alchemy.types.guid.GUID(length=16), nullable=True, comment='用户ID'),
    sa.Column('action', sa.String(length=50), nullable=False, comment='操作类型'),
    sa.Column('resource', sa.String(length=100), nullable=True, comment='资源类型'),
    sa.Column('resource_id', sa.String(length=100), nullable=True, comment='资源ID'),
    sa.Column('status', sa.String(length=20), nullable=False, comment='操作状态'),
    sa.Column('ip_address', sa.String(length=45), nullable=True, comment='IP地址'),
    sa.Column('user_agent', sa.String(length=500), nullable=True, comment='用户代理'),
    sa.Column('details', sa.Text(), nullable=True, comment='详细信息'),
    sa.Column('error_message', sa.Text(), nullable=True, comment='错误信息'),
    sa.Column('is_deleted', sa.Boolean(), nullable=False, comment='是否已删除'),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), nullable=False),
    sa.Column('created_at', advanced_alchemy.types.datetime.DateTimeUTC(timezone=True), nullable=False),
    sa.Column('updated_at', advanced_alchemy.types.datetime.DateTimeUTC(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_audit_logs_user_id_users')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_table('role_permissions',
    sa.Column('role_id', advanced_alchemy.types.guid.GUID(length=16), nullable=False),
    sa.Column('permission_id', advanced_alchemy.types.guid.GUID(length=16), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], name=op.f('fk_role_permissions_permission_id_permissions')),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_role_permissions_role_id_roles')),
    sa.PrimaryKeyConstraint('role_id', 'permission_id', name=op.f('pk_role_permissions'))
    )
    op.create_table('user_roles',
    sa.Column('user_id', advanced_alchemy.types.guid.GUID(length=16), nullable=False),
    sa.Column('role_id', advanced_alchemy.types.guid.GUID(length=16), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_user_roles_role_id_roles')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_roles_user_id_users')),
    sa.PrimaryKeyConstraint('user_id', 'role_id', name=op.f('pk_user_roles'))
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_roles')
    op.drop_table('role_permissions')
    op.drop_table('audit_logs')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_phone'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_table('roles')
    op.drop_index(op.f('ix_permissions_name'), table_name='permissions')
    op.drop_index(op.f('ix_permissions_code'), table_name='permissions')
    op.drop_table('permissions')
    # ### end Alembic commands ###
