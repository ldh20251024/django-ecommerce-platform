from django.core.paginator import EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg, Count,Case, When, IntegerField
from django.core.paginator import Paginator
from .models import Product, Category, SearchQuery
from .forms import ProductSearchForm, ProductFilterForm
import pypinyin
from django.core.cache import cache
from .tasks import  update_search_count
from django_ratelimit.decorators import ratelimit
from .forms import ReviewForm
from django.contrib import messages

# 限制单IP每分钟最多20次搜索请求
@ratelimit(key='ip', rate='20/m', method='GET', block=True)
def product_search(request):
    """商品搜索视图"""
    # products = Product.objects.filter(available=True)
    """优化后的搜索视图"""
    products = Product.objects.filter(available=True) \
        .select_related('category')
    search_form = ProductSearchForm(request.GET)
    filter_form = ProductFilterForm(request.GET)

    # 搜索处理
    query = request.GET.get('q', '').strip()
    if query:
        search_query, created = SearchQuery.objects.get_or_create(query = query)
        if created:
            search_query.save()
        else:
            search_query.count += 1
            search_query.save()
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(rating__icontains=query)
        ).distinct()

        # 搜索历史记录（存储在session中）
        search_history = request.session.get('search_history', [])
        if query not in search_history:
            search_history.insert(0, query)
            # 只保留最近10条记录
            search_history = search_history[:10]
            request.session['search_history'] = search_history

        # 记录热门搜索
        # 异步更新搜索计数（不阻塞当前请求）
        update_search_count.delay(query)  # 用delay()触发异步

    # 获取热门搜索词
    popular_searches = SearchQuery.objects.all()[:5]

    # 筛选处理
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        price_range = filter_form.cleaned_data.get('price_range')
        min_price = filter_form.cleaned_data.get('min_price')
        max_price = filter_form.cleaned_data.get('max_price')
        in_stock = filter_form.cleaned_data.get('in_stock')
        sort_by = filter_form.cleaned_data.get('sort_by') or '-created'
        min_rating = filter_form.cleaned_data.get('min_rating')
        if min_rating:
            products = products.filter(rating__gte=float(min_rating))

        # 分类筛选
        if category:
            products = products.filter(category=category)

        # 价格区间筛选
        if price_range:
            if price_range == '0-100':
                products = products.filter(price__gte=0, price__lte=100)
            elif price_range == '100-500':
                products = products.filter(price__gte=100, price__lte=500)
            elif price_range == '500-1000':
                products = products.filter(price__gte=500, price__lte=1000)
            elif price_range == '1000-5000':
                products = products.filter(price__gte=1000, price__lte=5000)
            elif price_range == '5000-':
                products = products.filter(price__gte=5000)

        # 自定义价格范围
        if min_price is not None:
            products = products.filter(price__gte=min_price)
        if max_price is not None:
            products = products.filter(price__lte=max_price)

        # 库存筛选
        if in_stock:
            products = products.filter(stock__gt=0)

        # 排序
        products = products.order_by(sort_by)

    # 分页
    paginator = Paginator(products, 12)  # 每页12个商品
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 1. 先查询所有有产品的分类，并包含产品数量（替代原category_count查询），返回的是查询集，
    # 并非实际数据，当迭代查询集（如for category in all_categories_with_count）、调用len()、切片等操作时，
    # 才会实际执行 SQL 查询，获取数据。
    # 关键：提前执行查询集，转为列表（仅执行1次联表查询）
    all_categories_with_count = list(  # 转为列表，触发SQL执行并加载到内存
        Category.objects.annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)
    )

    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'filter_form': filter_form,
        'query': query,
        'category_count': all_categories_with_count,
        # 'total_products': products.count(),
        # 关键优化：用paginator.count替代products.count()，复用已有的计数结果
        'total_products': paginator.count,
        'popular_searches': popular_searches,
    }

    # 智能建议
    if query and paginator.count == 0: # 用paginator.count替代products.count()
        # 改进的相似分类查询
        similar_categories = get_similar_categories(query, all_categories_with_count)
        # print(f"改进后的相似分类: {[cat.name for cat in similar_categories]}")
        from difflib import get_close_matches
        # 仅获取name字段，用values_list提升效率
        all_product_names = list(Product.objects.filter(
            available=True
        ).values_list('name', flat=True))  # 只返回name的列表，如['商品1', '商品2']

        # 可选：如果产品数量极多，可限制查询数量（如最近上架的1000个）
        # all_product_names = list(Product.objects.filter(
        #     available=True
        # ).order_by('-created')[:1000].values_list('name', flat=True))

        similar_terms = get_close_matches(query, all_product_names, n=3, cutoff=0.3)
        # print('similar_terms:', similar_terms)
        # 添加拼音转换建议
        pinyin_suggestions = get_pinyin_suggestions(query, all_product_names)
        similar_terms.extend(pinyin_suggestions)

        # 去重
        similar_terms = list(dict.fromkeys(similar_terms))[:5]  # 最多5个建议
        context.update({
            'similar_categories': similar_categories,
            'similar_terms': similar_terms,
        })

    return render(request, 'shop/product_search.html', context)


def get_similar_categories(query, all_categories_with_count, max_results=3):
    """
        智能查找相似分类（合并为1次查询，按优先级筛选）
        """
    if not query or len(query.strip()) < 1:
        return Category.objects.none()

    query = query.strip()
    priority_matches = []  # 存储(分类对象, 优先级)，优先级：10>20>30>40（数字越大优先级越高）

    try:
        # 预处理拼音和首字母（仅执行一次）
        pinyin_query = ''.join(pypinyin.lazy_pinyin(query)) if query else ''
        initials = ''.join([p[0] for p in pypinyin.lazy_pinyin(query) if p]) if query else ''
    except Exception as e:
        # print(f"拼音处理错误: {e}")
        pinyin_query = ''
        initials = ''

    # 构建基础查询条件（精确匹配 + 包含匹配）
    query_conditions = Q(
        Q(name__iexact=query) |
        Q(description__iexact=query) |
        Q(name__icontains=query) |
        Q(description__icontains=query)
    )

    # 动态添加拼音匹配条件（仅当拼音字符串长度≥2时）
    if pinyin_query and len(pinyin_query) >= 2:
        query_conditions |= Q(
            Q(name__icontains=pinyin_query) |
            Q(description__icontains=pinyin_query)
        )

        # 动态添加首字母匹配条件（仅当首字母字符串长度≥2时）
    if initials and len(initials) >= 2:
        query_conditions |= Q(
            Q(name__icontains=initials) |
            Q(description__icontains=initials)
        )

    # # 一次查询获取：匹配分类 + 备用随机分类
    # all_potential_data = Category.objects.filter(
    #     query_conditions |  # 匹配分类
    #     Q(id__in=Category.objects.order_by('?').values_list('id', flat=True)[:backup_random_count])  # 备用随机分类
    # ).distinct()
    #当前数据库版本不支持上面的limit和in同时存在的操作，改用下面的优化

    # # 1. 单独查询随机ID列表（这一步会执行1次查询，但无嵌套子查询）
    # random_ids = list(
    #     Category.objects.order_by('?').values_list('id', flat=True)[:backup_random_count]
    # )
    #
    # # 2. 主查询使用预先获取的random_ids，避免子查询中的LIMIT
    # all_potential_data = Category.objects.filter(
    #     query_conditions |  # 匹配分类
    #     Q(id__in=random_ids)  # 备用随机分类（使用预先获取的ID列表）
    # ).distinct()
    # 使用一次性查询好的所有有产品的分类all_categories_with_count，不用再进行上诉查询，避免重复查询

    # 分离“匹配分类”和“备用随机分类”（内存中处理）
    matching_categories = []
    backup_random_categories = []
    for category in all_categories_with_count:
        # 判断是否属于匹配分类
        is_match = (
            (category.name.lower() == query.lower()) or
            (category.description.lower() == query.lower()) or
            (query.lower() in category.name.lower()) or
            (query.lower() in category.description.lower()) or
            (pinyin_query and len(pinyin_query) >= 2 and (
            pinyin_query.lower() in category.name.lower() or pinyin_query.lower() in category.description.lower())) or
            (initials and len(initials) >= 2 and (
            initials.lower() in category.name.lower() or initials.lower() in category.description.lower()))
        )
        if is_match:
            matching_categories.append(category)
        else:
            backup_random_categories.append(category)  # 非匹配分类作为备用

    # 对匹配分类按优先级排序（内存中处理）
    for category in matching_categories:
        # 优先级1：精确匹配（最高）
        if (category.name.lower() == query.lower()) or (category.description.lower() == query.lower()):
            priority_matches.append((category, 10))
        # 优先级2：包含匹配（次之）
        elif (query.lower() in category.name.lower()) or (query.lower() in category.description.lower()):
            priority_matches.append((category, 20))
        # 优先级3：拼音匹配（较低）
        elif pinyin_query and len(pinyin_query) >= 2 and (
                pinyin_query.lower() in category.name.lower() or pinyin_query.lower() in category.description.lower()):
            priority_matches.append((category, 30))
        # 优先级4：首字母匹配（最低）
        elif initials and len(initials) >= 2 and (
                initials.lower() in category.name.lower() or initials.lower() in category.description.lower()):
            priority_matches.append((category, 40))

    # 按优先级排序（10>20>30>40），相同优先级按名称排序
    priority_matches.sort(key=lambda x: (x[1], x[0].name))
    # 提取分类对象，截取前max_results个
    result = [item[0] for item in priority_matches[:max_results]]

    # 结果不足时，从备用随机分类中补充（内存中处理）
    if len(result) < max_results:
        remaining = max_results - len(result)
        # 排除已在结果中的分类（避免重复）
        result_ids = [item.id for item in result]
        available_backups = [cat for cat in backup_random_categories if cat.id not in result_ids]
        # 取前remaining个补充
        result.extend(available_backups[:remaining])

    return result

    # """
    # 智能查找相似分类
    # """
    # if not query or len(query.strip()) < 1:
    #     return Category.objects.none()
    #
    # query = query.strip()
    #
    # # 方法1: 精确匹配
    # exact_matches = Category.objects.filter(
    #     Q(name__iexact=query) |
    #     Q(description__iexact=query)
    # )
    #
    # if exact_matches.exists():
    #     return exact_matches[:max_results]
    #
    # # 方法2: 包含匹配
    # contains_matches = Category.objects.filter(
    #     Q(name__icontains=query) |
    #     Q(description__icontains=query)
    # )
    #
    # if contains_matches.exists():
    #     return contains_matches[:max_results]
    #
    # # 方法3: 拼音匹配
    # try:
    #     pinyin_query = ''.join(pypinyin.lazy_pinyin(query))
    #     if len(pinyin_query) >= 2:
    #         pinyin_matches = Category.objects.filter(
    #             Q(name__icontains=pinyin_query) |
    #             Q(description__icontains=pinyin_query)
    #         )
    #         if pinyin_matches.exists():
    #             return pinyin_matches[:max_results]
    # except Exception as e:
    #     print(f"拼音匹配错误: {e}")
    #
    # # 方法4: 首字母匹配
    # try:
    #     initials = ''.join([p[0] for p in pypinyin.lazy_pinyin(query) if p])
    #     if len(initials) >= 2:
    #         initials_matches = Category.objects.filter(
    #             Q(name__icontains=initials) |
    #             Q(description__icontains=initials)
    #         )
    #         if initials_matches.exists():
    #             return initials_matches[:max_results]
    # except Exception as e:
    #     print(f"首字母匹配错误: {e}")
    #
    # # 方法5: 返回一些随机分类作为备选
    # return Category.objects.all().order_by('?')[:max_results]


def get_pinyin_suggestions(query, product_names, max_suggestions=3):
    """获取拼音相关的建议 - 改进版本"""
    suggestions = []

    try:
        # 将查询词转换为拼音
        query_pinyin = ''.join(pypinyin.lazy_pinyin(query))


        # 查找商品名称拼音中包含查询词拼音的商品
        for name in product_names:
            try:
                name_pinyin = ''.join(pypinyin.lazy_pinyin(name))
                if query_pinyin in name_pinyin and name not in suggestions:
                    suggestions.append(name)
                    if len(suggestions) >= max_suggestions:
                        break
            except:
                continue



    except Exception as e:
        print(f"拼音建议错误: {e}")

    return suggestions[:max_suggestions]


def simple_chinese_to_pinyin(text):
    """简单的中文转拼音函数（实际项目中建议使用pypinyin库）"""
    # 这是一个简化的版本，实际项目中应该使用专业的拼音转换库
    pinyin_dict = {
        '蛤': 'ha', '哈': 'ha',
        '和': 'he', '合': 'he',
        '胡': 'hu', '湖': 'hu',
        '马': 'ma', '妈': 'ma',
        '李': 'li', '里': 'li',
        '张': 'zhang', '章': 'zhang',
        '王': 'wang', '网': 'wang',
        # 可以添加更多映射...
    }

    if text in pinyin_dict:
        return pinyin_dict[text]

    # 对于多字符，只处理第一个字符
    if len(text) > 0:
        first_char = text[0]
        return pinyin_dict.get(first_char, text)

    return text

def category_products(request, category_slug):
    """分类商品页面"""
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category, available=True)

    # 使用相同的筛选逻辑
    filter_form = ProductFilterForm(request.GET)
    filter_form.fields['category'].initial = category

    if filter_form.is_valid():
        price_range = filter_form.cleaned_data.get('price_range')
        min_price = filter_form.cleaned_data.get('min_price')
        max_price = filter_form.cleaned_data.get('max_price')
        in_stock = filter_form.cleaned_data.get('in_stock')
        sort_by = filter_form.cleaned_data.get('sort_by') or '-created'

        # 价格区间筛选
        if price_range:
            if price_range == '0-100':
                products = products.filter(price__gte=0, price__lte=100)
            elif price_range == '100-500':
                products = products.filter(price__gte=100, price__lte=500)
            elif price_range == '500-1000':
                products = products.filter(price__gte=500, price__lte=1000)
            elif price_range == '1000-5000':
                products = products.filter(price__gte=1000, price__lte=5000)
            elif price_range == '5000-':
                products = products.filter(price__gte=5000)

        # 自定义价格范围
        if min_price is not None:
            products = products.filter(price__gte=min_price)
        if max_price is not None:
            products = products.filter(price__lte=max_price)

        # 库存筛选
        if in_stock:
            products = products.filter(stock__gt=0)

        # 排序
        products = products.order_by(sort_by)

    # 分页
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category,
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_products': products.count(),
    }

    return render(request, 'shop/category_products.html', context)

def clear_search_history(request):
    """清除搜索历史"""
    if 'search_history' in request.session:
        del request.session['search_history']
    return redirect('shop:product_search')

def product_list(request, category_slug=None):
    category = None
    # categories = Category.objects.all()

    # 缓存分类列表（24小时过期）
    cache_key = 'shop:categories'
    categories = cache.get(cache_key)
    if not categories:
        categories = list(Category.objects.all())  # 转为列表避免ORM查询集缓存问题
        cache.set(cache_key, categories, 60 * 60 * 24)  # 24小时

    # 优化：用select_related关联category，避免循环查询分类信息
    products = Product.objects.filter(available=True).select_related('category')

    # 添加基本的筛选和排序
    sort_by = request.GET.get('sort_by', '-created')

    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug)
            products = products.filter(category=category)
        except (Category.DoesNotExist, ValueError):
            pass

    # 排序
    if sort_by in ['price', '-price', 'name', '-created', '-sales', 'rating']:
        products = products.order_by(sort_by)
    else:
        products = products.order_by('-created')

    # 优化查询：使用select_related但不使用only/defer
    products = products.select_related('category')

    # 分页
    paginator = Paginator(products, 12)  # 每页12个商品
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'shop/product/list.html', {
        'category': category,
        'categories': categories,
        'products': products
    })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    # 优化：用prefetch_related加载关联的评论（避免N+1）
    # 获取产品评论，按时间倒序排列
    # reviews = product.reviews.all().order_by('-created')
    # 关键优化：使用 select_related('user') 预加载评论关联的用户数据
    reviews = product.reviews.select_related('user').order_by('-created')  # 新增 select_related
    # 关键优化：一次聚合查询获取所有星级的数量
    rating_aggregates = product.reviews.aggregate(
        total=Count('id'),  # 总评论数
        # 分别计算5-1星的数量
        star5=Count(Case(When(rating=5, then=1), output_field=IntegerField())),
        star4=Count(Case(When(rating=4, then=1), output_field=IntegerField())),
        star3=Count(Case(When(rating=3, then=1), output_field=IntegerField())),
        star2=Count(Case(When(rating=2, then=1), output_field=IntegerField())),
        star1=Count(Case(When(rating=1, then=1), output_field=IntegerField())),
    )

    # 构造评分统计字典
    rating_stats = {
        'average': product.rating,
        'count': rating_aggregates['total'],  # 总评论数
        'distribution': {
            '5': rating_aggregates['star5'],
            '4': rating_aggregates['star4'],
            '3': rating_aggregates['star3'],
            '2': rating_aggregates['star2'],
            '1': rating_aggregates['star1'],
        }
    }

    # 处理评论提交
    review_form = ReviewForm()
    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(data=request.POST)
        if review_form.is_valid():
            # 检查用户是否已评论过该产品
            if reviews.filter(user=request.user).exists():
                messages.warning(request, '您已经评论过该商品')
            else:
                new_review = review_form.save(commit=False)
                new_review.product = product
                new_review.user = request.user
                new_review.save()

                # 更新产品评分
                avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg']
                product.rating = round(avg_rating, 1)
                product.save()

                messages.success(request, '您的评论已提交成功！')
                return redirect('shop:product_detail', id=product.id, slug=product.slug)

    context = {
        'product': product,
        'reviews': reviews,
        'review_form': review_form,
        'rating_stats': rating_stats,
    }
    return render(request, 'shop/product/detail.html', context)