"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: log_compression.py
@DateTime: 2025/07/08
@Docs: 日志压缩和归档功能
"""

import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.dao.operation_log import OperationLogDAO
from app.utils.logger import logger


class LogCompressor:
    """日志压缩器"""

    def __init__(self):
        self.operation_log_dao = OperationLogDAO()
        self.archive_dir = Path("logs/archive")
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    async def compress_old_logs(self, days_to_keep: int = 30) -> dict[str, Any]:
        """压缩旧日志"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            result = {
                "operation_logs": {"compressed": 0, "deleted": 0, "size_saved": 0},
                "total_size_saved": 0,
                "archive_files": [],
            }

            # 压缩操作日志
            operation_result = await self._compress_operation_logs(cutoff_date)
            result["operation_logs"] = operation_result

            # 计算总大小节省
            result["total_size_saved"] = result["operation_logs"]["size_saved"]

            logger.info(f"日志压缩完成，节省空间: {result['total_size_saved']} 字节")
            return result

        except Exception as e:
            logger.error(f"压缩日志失败: {e}")
            return {"error": str(e)}

    async def _compress_operation_logs(self, cutoff_date: datetime) -> dict[str, Any]:
        """压缩操作日志"""
        try:
            # 获取需要压缩的日志
            old_logs = await self.operation_log_dao.get_by_date_range(datetime.min, cutoff_date)

            if not old_logs:
                return {"compressed": 0, "deleted": 0, "size_saved": 0}

            # 按月分组压缩
            logs_by_month = {}
            for log in old_logs:
                month_key = log.created_at.strftime("%Y-%m")
                if month_key not in logs_by_month:
                    logs_by_month[month_key] = []
                logs_by_month[month_key].append(log)

            compressed_count = 0
            size_saved = 0

            for month, month_logs in logs_by_month.items():
                # 创建压缩文件
                archive_file = self.archive_dir / f"operation_logs_{month}.json.gz"

                # 转换为可序列化的格式
                log_data = []
                for log in month_logs:
                    log_dict = {
                        "id": str(log.id),
                        "user_id": str(log.user_id),
                        "module": log.module,
                        "action": log.action,
                        "resource_id": log.resource_id,
                        "resource_type": log.resource_type,
                        "method": log.method,
                        "path": log.path,
                        "ip_address": log.ip_address,
                        "response_code": log.response_code,
                        "response_time": log.response_time,
                        "description": log.description,
                        "created_at": log.created_at.isoformat(),
                        "updated_at": log.updated_at.isoformat(),
                    }
                    log_data.append(log_dict)

                # 压缩写入文件
                json_data = json.dumps(log_data, ensure_ascii=False, indent=2)
                original_size = len(json_data.encode("utf-8"))

                with gzip.open(archive_file, "wt", encoding="utf-8") as f:
                    f.write(json_data)

                compressed_size = archive_file.stat().st_size
                size_saved += original_size - compressed_size
                compressed_count += len(month_logs)

                logger.info(f"压缩操作日志: {month}, {len(month_logs)} 条记录")

            # 删除已压缩的原始日志
            log_ids = [log.id for log in old_logs]
            deleted_count = await self._soft_delete_logs("operation_log", log_ids)

            return {"compressed": compressed_count, "deleted": deleted_count, "size_saved": size_saved}

        except Exception as e:
            logger.error(f"压缩操作日志失败: {e}")
            return {"compressed": 0, "deleted": 0, "size_saved": 0}

    async def _soft_delete_logs(self, table_type: str, log_ids: list) -> int:
        """批量软删除日志记录"""
        try:
            if not log_ids:
                return 0

            total_deleted = 0
            batch_size = 1000  # 每批次处理1000条记录

            for i in range(0, len(log_ids), batch_size):
                batch_ids = log_ids[i : i + batch_size]

                if table_type == "operation_log":
                    # 使用批量软删除方法
                    deleted_count = await self.operation_log_dao.soft_delete_by_ids(batch_ids)
                    total_deleted += deleted_count
                    logger.debug(f"批量软删除操作日志: {deleted_count}/{len(batch_ids)} 条")

            logger.info(f"批量软删除 {table_type} 完成: {total_deleted}/{len(log_ids)} 条")
            return total_deleted

        except Exception as e:
            logger.error(f"批量软删除日志失败: {e}")
            return 0

    async def restore_compressed_logs(self, archive_file: str) -> dict[str, Any]:
        """恢复压缩的日志"""
        try:
            archive_path = self.archive_dir / archive_file
            if not archive_path.exists():
                return {"error": "归档文件不存在"}

            # 读取压缩文件
            with gzip.open(archive_path, "rt", encoding="utf-8") as f:
                log_data = json.load(f)

            # 确定日志类型
            if "operation_logs_" in archive_file:
                # 恢复操作日志
                restored_count = await self._restore_operation_logs(log_data)
            else:
                return {"error": "未知的归档文件类型"}

            return {"restored": restored_count, "total_records": len(log_data)}

        except Exception as e:
            logger.error(f"恢复压缩日志失败: {e}")
            return {"error": str(e)}

    async def _restore_operation_logs(self, log_data: list) -> int:
        """批量恢复操作日志"""
        if not log_data:
            return 0

        try:
            batch_size = 500  # 每批次处理500条记录
            total_restored = 0

            for i in range(0, len(log_data), batch_size):
                batch_data = log_data[i : i + batch_size]

                # 准备批量创建的数据
                bulk_data = []
                for log_dict in batch_data:
                    try:
                        # 转换数据格式
                        create_data = {
                            "user_id": log_dict["user_id"],
                            "module": log_dict["module"],
                            "action": log_dict["action"],
                            "resource_id": log_dict.get("resource_id"),
                            "resource_type": log_dict.get("resource_type"),
                            "method": log_dict["method"],
                            "path": log_dict["path"],
                            "ip_address": log_dict["ip_address"],
                            "response_code": log_dict["response_code"],
                            "response_time": log_dict["response_time"],
                            "description": log_dict.get("description"),
                        }
                        bulk_data.append(create_data)
                    except Exception as e:
                        logger.warning(f"跳过无效的操作日志记录: {e}")
                        continue

                # 批量创建
                if bulk_data:
                    created_logs = await self.operation_log_dao.bulk_create(bulk_data)
                    batch_restored = len(created_logs)
                    total_restored += batch_restored
                    logger.debug(f"批量恢复操作日志: {batch_restored}/{len(bulk_data)} 条")

            logger.info(f"批量恢复操作日志完成: {total_restored}/{len(log_data)} 条")
            return total_restored

        except Exception as e:
            logger.error(f"批量恢复操作日志失败: {e}")
            return 0

    def get_archive_files(self) -> list[dict[str, Any]]:
        """获取归档文件列表"""
        try:
            archive_files = []
            for file_path in self.archive_dir.glob("*.json.gz"):
                file_info = {
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "created_at": datetime.fromtimestamp(file_path.stat().st_ctime),
                    "type": "operation_log",
                }
                archive_files.append(file_info)

            return sorted(archive_files, key=lambda x: x["created_at"], reverse=True)
        except Exception as e:
            logger.error(f"获取归档文件列表失败: {e}")
            return []


# 全局日志压缩器实例
_log_compressor = LogCompressor()


def get_log_compressor() -> LogCompressor:
    """获取全局日志压缩器"""
    return _log_compressor


async def compress_old_logs(days_to_keep: int = 30) -> dict[str, Any]:
    """压缩旧日志的便捷函数"""
    return await _log_compressor.compress_old_logs(days_to_keep)
