# django-ecommerce-platform
基于 Django 的电商平台，含搜索优化、购物车、订单管理、支付集成、退款、商品管理、支付记录查询等功能
# Django 电商平台

## 项目简介
基于 Django 5.2 开发的全栈电商系统，解决传统电商「搜索慢、筛选体验差、库存超卖」等痛点，支持商品浏览、多条件搜索、购物车、订单管理等核心功能。

## 技术栈
- 后端：Django 5.2 + PostGreSQL + Redis（缓存）+ Cloudinary（云存储）
- 前端：HTML5 + CSS3 + JavaScript + Bootstrap
- 部署：Render（在线演示：https://django-ecommerce-demo.onrender.com）
- 性能优化：
- 1、运用django-silk性能分析工具，记录 Django 应用中每一次请求的代码执行耗时、函数调用链路、数据库查询效率等详细性能数据，
- 帮助定位性能瓶颈，并且通过prefetch_related、select_related、SQL聚合查询等措施解决N+1查询与重复查询等性能问题；
- 2、运用Redis缓存热门商品。减少频繁请求数据库的损耗
- 安全加固：
- 1、密码加密加固：注册时自动加密明文密码
- 2、配置信息非硬编码：重要的配置信息均从环境变量获取，避免硬编码。防止泄露
- 3、启用https保障网络数据传输的安全与可信度，解决 HTTP 协议 “明文传输、无身份验证、数据易篡改” 的三大安全缺陷

## 核心功能
1. **商品模块**：分类导航、商品详情、用户评论
2. **搜索优化**：多条件筛选（价格/评分/库存/分类）、排序（首字母/价格/评分/上架时间）、相似分类推荐、智能搜索建议、搜索历史、热门搜索
3. **购物车**：添加/删除/更新数量、库存锁避免超卖
4. **订单系统**：创建订单、已支付订单退款、未支付订单删除、订单状态显示
5. **用户中心**：注册/登录、收获地址管理、修改密码、订单管理

## 本地运行步骤
1. 克隆仓库：`git clone git@github.com:ldh20251024/django-ecommerce-platform.git`
2. 进入目录：`cd django-ecommerce-platform`
3. 创建虚拟环境：`python -m venv venv`
4. 激活虚拟环境：  
   - Windows：`venv\Scripts\activate`  
   - macOS/Linux：`source venv/bin/activate`
5. 安装依赖：`pip install -r requirements.txt`
6. 配置数据库：修改 `settings.py` 中的 `DATABASES` 为本地 MySQL/PostGreSQL 信息
7. 迁移数据库：`python manage.py makemigrations && python manage.py migrate`
8. 启动服务：`python manage.py runserver`
9. 访问：http://127.0.0.1:8000

## 技术亮点
- **数据库优化**：通过 prefetch_related 预加载关联数据，搜索页响应时间从 283ms 降至 12ms
- **缓存策略**：Redis 缓存热门商品数据，高并发场景 QPS 提升 3 倍
- **用户体验**：URL 参数保留筛选状态，分页不重置条件；搜索无结果时提供相似推荐

## 在线演示
https://django-ecommerce-demo.onrender.com（可注册新用户测试核心功能）
