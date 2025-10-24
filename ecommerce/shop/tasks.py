# shop/tasks.py
from celery import shared_task
from .models import SearchQuery

@shared_task
def update_search_count(query_text):
    """异步更新搜索关键词的计数（避免阻塞搜索请求）"""
    # 用get_or_create+F表达式原子更新，避免并发问题
    query, created = SearchQuery.objects.get_or_create(query=query_text)
    if not created:
        from django.db.models import F
        query.count = F('count') + 1  # 原子操作，防止竞态条件
        query.save()
    return f"Updated search count for: {query_text}"