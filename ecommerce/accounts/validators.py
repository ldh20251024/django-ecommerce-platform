# 正确导入 BaseValidator（在 django.core.validators 中）
from django.core.validators import BaseValidator
from django.core.exceptions import ValidationError


class UniquePasswordValidator(BaseValidator):
    def __init__(self, history_limit=5):
        self.history_limit = history_limit

    def validate(self, password, user=None):
        if not user:
            return  # 仅在用户修改密码时验证（用户已存在）

        # 示例逻辑：检查新密码是否在历史密码中（假设用户模型有 previous_passwords 字段）
        if hasattr(user, 'previous_passwords'):
            # 只检查最近 history_limit 次的密码
            recent_passwords = user.previous_passwords[-self.history_limit:]
            if password in recent_passwords:
                raise ValidationError(f"不能使用最近 {self.history_limit} 次使用过的密码")

    def get_help_text(self):
        return f"新密码不能是最近 {self.history_limit} 次使用过的密码"