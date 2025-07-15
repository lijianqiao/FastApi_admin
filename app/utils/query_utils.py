"""
@Author: li
@Email: lijianqiao2906@live.com
@FileName: query_utils.py
@DateTime: 2025/07/15
@Docs: 将 API 查询参数转换为 ORM 过滤器的工具.
"""

from tortoise.expressions import Q


def list_query_to_orm_filters(
    query: dict,
    search_fields: list[str] | None = None,
    model_fields: set | None = None,
) -> tuple[dict, dict]:
    """
    将类似 ListQueryRequest 的字典转换为 ORM 过滤器.

    Args:
        query: 查询参数字典.
        search_fields: 一份模型字段列表，用于搜索'关键词'.
        model_fields: 一组有效的模型字段可用于过滤.

    Returns:
        一个包含 (model_filters, dao_params) 的元组.
    """
    model_filters = {}
    dao_params = {}
    q_filters = []

    # 处理关键词搜索
    keyword = query.pop("keyword", None)
    if keyword and search_fields:
        keyword_q = Q()
        for field in search_fields:
            keyword_q |= Q(**{f"{field}__icontains": keyword})
        q_filters.append(keyword_q)

    # 处理日期范围
    if "start_date" in query and query["start_date"]:
        model_filters["created_at__gte"] = query.pop("start_date")
    if "end_date" in query and query["end_date"]:
        model_filters["created_at__lte"] = query.pop("end_date")

    # 处理软删除参数
    if "include_deleted" in query:
        dao_params["include_deleted"] = query.pop("include_deleted")

    # 将剩余的有效模型字段添加到过滤器中
    if model_fields:
        for key, value in query.items():
            if key in model_fields and value is not None:
                model_filters[key] = value

    # 合并Q对象（如果有的话）
    if q_filters:
        model_filters["q_objects"] = q_filters

    return model_filters, dao_params
