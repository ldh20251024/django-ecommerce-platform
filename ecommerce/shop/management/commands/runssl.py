import os
import ssl
from django.core.management.commands.runserver import Command as RunServer
from django.core.servers.basehttp import WSGIServer, WSGIRequestHandler
from django.core.wsgi import get_wsgi_application

# 自定义带 SSL 的 WSGI 服务器（修复 get_request 返回值问题）
class SSLWSGIServer(WSGIServer):
    def __init__(self, address, handler_cls, ssl_context):
        self.ssl_context = ssl_context
        self.https_environ = {  # 存储 HTTPS 标识环境变量
            'wsgi.url_scheme': 'https',
            'HTTP_X_FORWARDED_PROTO': 'https'
        }
        super().__init__(address, handler_cls)

    def server_bind(self):
        # 绑定端口后用 SSL 包装套接字
        super().server_bind()
        self.socket = self.ssl_context.wrap_socket(self.socket, server_side=True)

    def get_request(self):
        # 仅返回父类预期的 2 个值（request, client_address）
        request, client_address = super().get_request()
        return (request, client_address)

# 自定义请求处理器（注入 HTTPS 环境变量）
class SSLRequestHandler(WSGIRequestHandler):
    def get_environ(self):
        environ = super().get_environ()
        # 从服务器获取 HTTPS 标识并注入环境变量
        environ.update(self.server.https_environ)
        return environ

class Command(RunServer):
    def handle(self, *args, **options):
        # 1. 解析地址和端口
        addrport = args[0] if args else '127.0.0.1:8000'
        addr, _, port = addrport.partition(':')
        port = int(port) if port else 8000

        # 2. 定位证书文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        cert_file = os.path.join(project_root, 'local-ssl-cert.pem')
        key_file = os.path.join(project_root, 'local-ssl-key.pem')

        # 3. 验证证书存在
        if not os.path.exists(cert_file):
            raise FileNotFoundError(f"证书文件不存在：{cert_file}")
        if not os.path.exists(key_file):
            raise FileNotFoundError(f"私钥文件不存在：{key_file}")

        # 4. 创建 SSL 上下文
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile=cert_file, keyfile=key_file)

        # 5. 获取 Django WSGI 应用
        application = get_wsgi_application()

        # 6. 初始化服务器（使用自定义请求处理器）
        server = SSLWSGIServer((addr, port), SSLRequestHandler, ssl_context)
        server.set_app(application)

        # 7. 启动服务器
        self.stdout.write(f"HTTPS 服务器运行于：https://{addr}:{port}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.stdout.write("\n服务器已关闭")

    help = "启动 HTTPS 开发服务器（用法：python manage.py runssl [地址:端口]）"