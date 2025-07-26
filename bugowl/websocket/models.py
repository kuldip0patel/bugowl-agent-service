from django.db import models

# Create your models here.


class PlayGround(models.Model):
	"""
	Model to represent a playground for agents.
	"""

	playground_uuid = models.UUIDField(unique=True)
	data = models.JSONField()  # JSON field to store playground data
	run_by = models.JSONField()
	business = models.IntegerField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f'{self.id} - {self.playground_uuid}'  # type: ignore
