from django.contrib import admin
from .models import Answer, Category, Quiz, Question, Option, Attempt
from django.contrib.auth.models import User

class OptionInline(admin.TabularInline):
    model = Option
    extra = 2  # minimum 2 options
    max_num = 4

class QuestionAdmin(admin.ModelAdmin):
    inlines = [OptionInline]
    search_fields = ('user__username', 'quiz__title')

class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    list_filter = ('category',)
    search_fields = ('user__username', 'quiz__title')

class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'total', 'completed_at')
    list_filter = ('quiz', 'user')
    search_fields = ('user__username', 'quiz__title')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option')

admin.site.register(Category)
admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Answer, AnswerAdmin)

