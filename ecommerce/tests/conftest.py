import pytest
from .factories import UserFactory

@pytest.fixture
def authenticated_client(client):
    """返回已认证的测试客户端"""
    user = UserFactory()
    client.force_login(user)
    return client

@pytest.fixture
def category():
    """返回测试分类"""
    from .factories import CategoryFactory
    return CategoryFactory()

@pytest.fixture
def product(category):
    """返回测试商品"""
    from .factories import ProductFactory
    return ProductFactory(category=category)