import os
from PIL import Image

# 图片存放目录（根据实际路径修改）
MEDIA_DIR = os.path.join(os.path.dirname(__file__), 'media', 'products')

def optimize_image(image_path, quality=80):
    """处理透明通道，压缩图片并保存"""
    try:
        with Image.open(image_path) as img:
            # 处理 RGBA 透明图片（JPEG 不支持透明，用白色背景填充）
            if img.mode in ('RGBA', 'LA'):
                # 创建白色背景的图片（尺寸与原图一致）
                background = Image.new(img.mode[:-1], img.size, (255, 255, 255))  # 白色背景
                # 将透明图片合成到白色背景上
                background.paste(img, img.split()[-1])  # 用原图的 alpha 通道作为遮罩
                img = background.convert('RGB')  # 转为 RGB 模式（适合 JPEG）
            elif img.mode != 'RGB':
                # 其他模式直接转为 RGB
                img = img.convert('RGB')

            # 保存压缩后的图片（覆盖原文件）
            img.save(image_path, format='JPEG', quality=quality, optimize=True)
            print(f"优化完成: {image_path}")
    except Exception as e:
        print(f"处理失败 {image_path}: {e}")

# 遍历目录下所有图片文件
for root, dirs, files in os.walk(MEDIA_DIR):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            image_path = os.path.join(root, file)
            optimize_image(image_path)