#!/usr/bin/env python3

import asyncio
import os

from browser_use.browser.profile import BrowserProfile
from browser_use.browser.session import BrowserSession


async def test_dvd_animation():
	"""Test the DVD screensaver animation issue"""

	print('=== DEBUG: Testing DVD Animation ===')

	# Check environment variables
	print(f'IS_IN_EVALS env var: {os.getenv("IS_IN_EVALS", "not set")}')

	# Import CONFIG after setting env
	from browser_use.config import CONFIG

	print(f'CONFIG.IS_IN_EVALS: {CONFIG.IS_IN_EVALS}')

	# Create browser session
	browser_session = BrowserSession(
		browser_profile=BrowserProfile(
			headless=False,  # Set to False to see the animation
			keep_alive=True,
		)
	)

	try:
		print('\n=== Starting browser session ===')
		await browser_session.start()

		print('\n=== Creating new tab ===')
		page = await browser_session.navigate('about:blank', new_tab=True)
		print(f'New tab created with URL: {page.url}')

		# Wait a bit to see the animation
		print('\n=== Waiting 5 seconds to observe animation ===')
		await asyncio.sleep(5)

		print('\n=== Creating another new tab ===')
		page2 = await browser_session.navigate('about:blank', new_tab=True)
		print(f'Second tab created with URL: {page2.url}')

		# Wait a bit more
		await asyncio.sleep(5)

	finally:
		print('\n=== Cleaning up ===')
		await browser_session.kill()


if __name__ == '__main__':
	asyncio.run(test_dvd_animation())
