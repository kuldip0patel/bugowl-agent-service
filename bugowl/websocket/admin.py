# Register your models here.

from django.contrib import admin

from .models import PlayGround


@admin.register(PlayGround)
class PlayGroundAdmin(admin.ModelAdmin):
	"""
	Admin interface for PlayGround model.
	"""

	list_display = ('id', 'playground_uuid', 'data', 'created_at', 'updated_at')
	search_fields = ('playground_uuid',)
