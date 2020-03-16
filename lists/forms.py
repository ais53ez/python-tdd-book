from django import forms

from lists.models import Item
from lists.views import ERROR_EMPTY_ITEM


class ItemForm(forms.models.ModelForm):
    class Meta:
        model = Item
        fields = ('text',)
        widgets = {
            'text': forms.fields.TextInput(attrs={
                'placeholder': 'Enter a to-do item',
                'class': 'form-control input-lg',
            }),
        }
        error_messages = {
            'text': {'required': ERROR_EMPTY_ITEM}
        }

