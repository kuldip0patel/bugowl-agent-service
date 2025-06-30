import json
import logging

import requests
from django.conf import settings


class SlackHandler(logging.Handler):
	"""
	Custom logging handler that sends error logs to Slack.
	"""

	def __init__(self, webhook_url, channel, username, icon_emoji):
		super().__init__()
		self.webhook_url = webhook_url
		self.channel = channel
		self.username = username
		self.icon_emoji = icon_emoji

	def emit(self, record):
		try:
			# Only send to Slack if it's an error or higher AND has exc_info=True
			if record.levelno < logging.ERROR:
				return

			# Check if exc_info is present (indicating a traceback)
			if not hasattr(record, 'exc_info') or record.exc_info is None:
				return

			# Get the formatted message
			msg = self.format(record)

			# Prepare the Slack message
			payload = {
				'channel': self.channel,
				'username': self.username,
				'icon_emoji': self.icon_emoji,
				'text': f'*Error in {settings.ENV} ENV*',
				'attachments': [
					{
						'color': '#FF0000',
						'blocks': [{'type': 'section', 'text': {'type': 'mrkdwn', 'text': f'*Error Message:*\n{msg}'}}],
					}
				],
			}

			# Send to Slack
			response = requests.post(self.webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})

			# Raise an exception if the request failed
			response.raise_for_status()

		except Exception as e:
			# If there's an error sending to Slack, log it to console
			print(f'Failed to send log to Slack: {str(e)}')
