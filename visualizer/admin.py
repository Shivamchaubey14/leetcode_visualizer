from django.contrib import admin
from .models import Problem

@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ['leetcode_id', 'title', 'difficulty', 'category', 'created_at']
    list_filter = ['difficulty', 'category']
    search_fields = ['title', 'leetcode_id']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['leetcode_id']