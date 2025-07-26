from rest_framework import serializers

from .models import PlayGround


class PlayGroundSerializer(serializers.ModelSerializer):
	class Meta:
		model = PlayGround
		fields = ['id', 'playground_uuid', 'data', 'run_by', 'business', 'created_at', 'updated_at']
		read_only_fields = ['id', 'created_at', 'updated_at']
