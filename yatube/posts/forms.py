from django import forms
from .models import Post, Group, Comment


GROUP_LIST = Group.objects.values_list('id', 'title')


class PostForm(forms.ModelForm):
    text = forms.CharField(
        label='Текст публикации',
        widget=forms.Textarea,
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Название группы",
        required=False,

    )

    class Meta:
        model = Post
        fields = ('text', 'group', 'image',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if data == '':
            raise forms.ValidationError('Поле не может быть пустым')
        return data

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
