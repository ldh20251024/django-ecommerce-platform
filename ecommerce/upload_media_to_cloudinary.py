import os
import cloudinary
from cloudinary.uploader import upload

# 配置Cloudinary（替换为你的凭证）
cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

# 本地media文件夹路径（替换为你的本地路径，如项目根目录下的media）
LOCAL_MEDIA_ROOT = "media/products/"
# 遍历本地media文件夹，上传所有文件
# 允许上传的文件扩展名（根据项目实际媒体类型调整）
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm']
# 目标子文件夹（例如：products、images）
TARGET_SUBFOLDER = "products"  # 修改此处为你的子文件夹名称
# 遍历本地media文件夹，仅上传允许的媒体文件
for root, dirs, files in os.walk(LOCAL_MEDIA_ROOT):
    for file in files:
        # 过滤文件扩展名
        if not any(file.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
            print(f"跳过非媒体文件：{file}")
            continue
        # 本地文件完整路径
        local_file_path = os.path.join(root, file)
        # 计算相对路径（相对于media文件夹）
        # 核心修改：替换反斜杠为正斜杠，确保public_id有效
        relative_path = os.path.relpath(local_file_path, LOCAL_MEDIA_ROOT).replace('\\', '/')
        # Cloudinary的目标路径
        # 构造Cloudinary的public_id（保持原有路径结构）
        public_id = f"{relative_path}"
        # 指定folder参数为完整路径（home/子文件夹）
        public_id_list = public_id.split("/")
        folder = f"{TARGET_SUBFOLDER}/{public_id_list[0]}/{public_id_list[1]}/{public_id_list[2]}"

        try:
            upload(
                local_file_path,
                public_id=public_id_list[3],
                folder=folder,  # 关键参数：指定完整文件夹路径
                resource_type="image"
            )
            print(f"上传成功：{public_id} → 存储于 {folder}")
        except Exception as e:
            print(f"上传失败：{str(e)}")
