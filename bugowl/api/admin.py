from django.contrib import admin
from django.db import models


class DjangoMigrations(models.Model):
    id = models.AutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "django_migrations"
        app_label = "api"
        verbose_name = "Migration"
        verbose_name_plural = "Migrations"


class DjangoMigrationsAdmin(admin.ModelAdmin):
    list_display = ("app", "name", "applied")
    search_fields = ("app", "name")
    list_filter = ("app", "applied")
    ordering = ("-applied",)
    readonly_fields = ("id", "app", "name", "applied")


admin.site.register(DjangoMigrations, DjangoMigrationsAdmin)
