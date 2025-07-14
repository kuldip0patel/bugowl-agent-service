#!/usr/bin/env python3

import asyncio
import uuid
from pathlib import Path

from dotenv import load_dotenv

from browser_use.browser import BrowserProfile
from browser_use.browser.profile import get_display_size
from browser_use.browser.session import BrowserSession

load_dotenv()


def get_chrome_args_for_automation():
	"""Get Chrome arguments optimized for web automation without prompts"""
	return [
		# Disable password manager and autofill prompts
		'--disable-password-manager-reauthentication',
		'--disable-features=PasswordManager,AutofillServerCommunication',
		'--disable-save-password-bubble',
		# Disable other common prompts and notifications
		'--disable-notifications',
		'--disable-infobars',
		'--disable-translate',
		'--disable-popup-blocking',
		'--disable-default-apps',
		'--disable-extensions-http-throttling',
		# Disable location and media prompts
		'--disable-geolocation',
		'--disable-media-stream',
		'--use-fake-ui-for-media-stream',
		'--use-fake-device-for-media-stream',
		# Additional stability flags
		'--no-first-run',
		'--no-default-browser-check',
		'--disable-backgrounding-occluded-windows',
		'--disable-renderer-backgrounding',
		'--disable-background-timer-throttling',
	]


async def test_agent_style_browser():
	"""Test browser session creation like in agent.py"""

	print('=== Testing Agent-Style Browser Creation ===')

	# Detect the screen size
	screen_size = get_display_size() or {'width': 1920, 'height': 1080}

	browser_profile = BrowserProfile(
		viewport=None,
		keep_alive=True,
		headless=False,
		disable_security=False,
		highlight_elements=False,
		record_video_dir='videos/',
		record_video_size=screen_size,
		window_size=screen_size,
		user_data_dir=str(Path.home() / '.config' / 'browseruse' / 'profiles' / f'profile_{uuid.uuid4()}'),
		args=get_chrome_args_for_automation(),
	)

	my_browser_session = BrowserSession(browser_profile=browser_profile)

	try:
		print('\n=== Starting browser session (like agent.py) ===')
		await my_browser_session.start()

		print('\n=== Creating new tab (new addition) ===')
		await my_browser_session.navigate('about:blank', new_tab=True)

		print('BugOwl: BROWSER OPENED ALREADY! Starting the tasks now....')

		# Wait to observe
		await asyncio.sleep(10)

	finally:
		await my_browser_session.close()


if __name__ == '__main__':
	asyncio.run(test_agent_style_browser())
