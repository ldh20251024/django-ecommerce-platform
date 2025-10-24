from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """获取字典中的值"""
    return dictionary.get(key)

@register.filter
def add_class(field, css):
    """为表单字段添加CSS类"""
    return field.as_widget(attrs={"class": css})

@register.simple_tag
def remove_param(request, *param_names):
    """
    移除指定参数的URL
    使用方式: {% remove_param request 'param1' 'param2' %}
    """
    params = request.GET.copy()
    for param_name in param_names:
        if param_name in params:
            del params[param_name]
    return params.urlencode()


@register.simple_tag
def get_price_range_display(form, price_range):
    """
    获取价格范围的显示文本
    """
    if not price_range:
        return ""

    price_ranges = dict(form.fields['price_range'].choices)
    return price_ranges.get(price_range, "")


@register.simple_tag
def get_sort_by_display(form, sort_by):
    """
    获取排序方式的显示文本
    """
    if not sort_by:
        return ""

    sort_choices = dict(form.fields['sort_by'].choices)
    return sort_choices.get(sort_by, "")