from django import template
from django.utils.html import escape
import re

register = template.Library()


@register.filter
def highlight(text, query):
    """
    在文本中高亮显示查询关键词
    """
    if not query or not text:
        return text

    # 确保文本是字符串
    text = str(text)

    # 转义HTML字符
    text = escape(text)

    try:
        # 使用正则表达式进行不区分大小写的替换
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        highlighted = pattern.sub(
            lambda match: f'<mark class="bg-warning">{match.group()}</mark>',
            text
        )
        return highlighted
    except re.error:
        # 如果正则表达式有问题，返回原文本
        return text


@register.filter
def truncatewords_html(text, num_words):
    """
    截断HTML文本的单词数量，但保持HTML标签完整
    """
    from django.utils.text import Truncator
    from django.utils.html import strip_tags

    if not text:
        return ""

    # 先去除HTML标签计算纯文本字数
    plain_text = strip_tags(text)
    truncated = Truncator(plain_text).words(num_words, truncate=' ...')

    return truncated