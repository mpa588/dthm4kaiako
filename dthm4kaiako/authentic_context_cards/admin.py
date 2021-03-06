"""Module for admin configuration for authentic context cards application."""

from django.contrib import admin
from authentic_context_cards.models import AchievementObjective


class AchievementObjectiveAdmin(admin.ModelAdmin):
    """Configuration for displaying achievement objectives in admin."""

    list_display = ('learning_area', 'level', 'component', 'strand', 'content')
    ordering = ('learning_area', 'level', 'component', 'strand')


admin.site.register(AchievementObjective, AchievementObjectiveAdmin)
