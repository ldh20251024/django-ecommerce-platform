# management/commands/convert_to_cloudinary_ids.py
from django.core.management.base import BaseCommand
from shop.models import Product
import cloudinary.uploader
from urllib.parse import urlparse
import os


class Command(BaseCommand):
    help = '将本地文件路径转换为 Cloudinary public_id'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行，不实际执行转换',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write("开始转换本地路径为 Cloudinary public_id...")

        products = Product.objects.all()
        converted_count = 0
        error_count = 0

        for product in products:
            if product.image:
                current_value = str(product.image)

                # 检查是否是本地路径格式（包含日期路径）
                if self.is_local_path_format(current_value):
                    self.stdout.write(f"发现本地路径: {product.name} -> {current_value}")

                    if not dry_run:
                        success = self.convert_to_cloudinary_id(product)
                        if success:
                            converted_count += 1
                        else:
                            error_count += 1
                    else:
                        converted_count += 1
                else:
                    self.stdout.write(f"✅ 已是 Cloudinary 格式: {product.name} -> {current_value}")

        if dry_run:
            self.stdout.write(f"试运行: 将转换 {converted_count} 个图片")
        else:
            self.stdout.write(self.style.SUCCESS(
                f"转换完成: {converted_count} 成功, {error_count} 失败"
            ))

    def is_local_path_format(self, value):
        """检查是否是本地文件路径格式"""
        # 检查是否包含日期路径模式 (YYYY/MM/DD/)
        if any(f'/2025/{str(i).zfill(2)}/' in value for i in range(1, 13)):
            return True
        # 检查是否包含中文文件名（本地路径特征）
        if any(char in value for char in ['哈尔滨', '镇海', '怨仇', '花园宝宝']):
            return True
        return False

    def convert_to_cloudinary_id(self, product):
        """将本地路径转换为 Cloudinary public_id"""
        try:
            # 获取当前图片的 Cloudinary URL（如果已经上传了）
            current_url = product.image.url

            # 从 URL 中提取真正的 public_id
            true_public_id = self.extract_true_public_id(current_url)

            if true_public_id:
                # 直接更新为真正的 public_id
                product.image = true_public_id
                product.save()

                self.stdout.write(f"✅ 转换成功: {product.name} -> {true_public_id}")
                return True
            else:
                # 如果无法提取，重新上传
                return self.reupload_to_cloudinary(product)

        except Exception as e:
            self.stderr.write(f"❌ 转换失败 {product.name}: {e}")
            return False

    def extract_true_public_id(self, url):
        """从 Cloudinary URL 中提取真正的 public_id"""
        try:
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')

            # Cloudinary URL 格式: /image/upload/v1234567/folder/filename.jpg
            if 'upload' in path_parts:
                upload_index = path_parts.index('upload')

                # 跳过版本号（如果存在）
                if upload_index + 1 < len(path_parts) and path_parts[upload_index + 1].startswith('v'):
                    public_id_parts = path_parts[upload_index + 2:]
                else:
                    public_id_parts = path_parts[upload_index + 1:]

                public_id = '/'.join(public_id_parts)

                # 移除文件扩展名
                public_id = os.path.splitext(public_id)[0]

                return public_id

        except Exception as e:
            self.stderr.write(f"❌ 提取 public_id 失败: {e}")

        return None

    def reupload_to_cloudinary(self, product):
        """重新上传图片到 Cloudinary"""
        try:
            # 获取当前图片 URL
            current_url = product.image.url

            # 生成新的 public_id（基于产品名称和ID）
            new_public_id = f"product_{product.id}_{product.name}"
            # 移除特殊字符
            new_public_id = ''.join(c if c.isalnum() or c in '_-' else '_' for c in new_public_id)

            # 上传到 Cloudinary
            upload_result = cloudinary.uploader.upload(
                current_url,
                folder="products/",
                public_id=new_public_id,
                overwrite=True,
                resource_type="image"
            )

            # 更新为新的 public_id
            product.image = upload_result['public_id']
            product.save()

            self.stdout.write(f"✅ 重新上传成功: {product.name} -> {upload_result['public_id']}")
            return True

        except Exception as e:
            self.stderr.write(f"❌ 重新上传失败 {product.name}: {e}")
            return False