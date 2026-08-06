from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "language", "notify_review_due")
    search_fields = ("user__username",)
    list_filter = ("language",)
