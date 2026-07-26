from django.contrib import admin
from django import forms

from .models import Post


class PostAdminForm(forms.ModelForm):
    body = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'rich-blog-editor'}),
        help_text=(
            'Use the editor toolbar to add images, embedded videos, audio, '
            'links, tables, and formatted sections.'
        ),
    )

    class Meta:
        model = Post
        fields = '__all__'

    class Media:
        css = {
            'all': ('css/blog-editor.css',)
        }
        js = (
            'js/blog-editor.js',
        )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('title', 'slug', 'display_author', 'published', 'created_at')
    list_filter = ('published', 'created_at', 'author')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    @admin.display(description='Author')
    def display_author(self, obj):
        return obj.get_author_display_name()
