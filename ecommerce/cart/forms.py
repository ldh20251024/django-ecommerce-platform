from django import forms

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]

class CartAddProductForm(forms.Form):
    # quantity 字段使用 TypedChoiceField，选择范围是1-20
    # 当单个商品数量超过20后,会重新显示为1,因为超出范围的数值不被接受,会显示为初始值
    # quantity = forms.TypedChoiceField(
    #     choices=PRODUCT_QUANTITY_CHOICES,
    #     coerce=int,
    #     label='数量'
    # )

    # 改进:将选择框更改为输入数字字段
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label='数量',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 80px;',
            'min': '1'
        })
    )
    update = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.HiddenInput
    )