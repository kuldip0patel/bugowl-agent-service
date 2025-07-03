"""
Test script to verify the enhanced button click functionality
that provides detailed context about page changes after clicking.
"""

import asyncio
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from browser_use.agent.views import ActionModel
from browser_use.browser import BrowserProfile, BrowserSession
from browser_use.controller.service import Controller
from browser_use.controller.views import ClickElementAction


async def test_enhanced_click():
	"""Test the enhanced click functionality with a simple HTML page"""

	# Create a simple HTML page for testing
	test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Test Page</h1>
        <button id="btn1" onclick="changeContent()">Click Me</button>
        <button id="btn2" onclick="navigateAway()">Navigate Away</button>
        <button id="btn3" onclick="openNewTab()">Open New Tab</button>
        <div id="content">Original content</div>
        
        <script>
            function changeContent() {
                document.getElementById('content').innerHTML = 'Content changed!';
                document.getElementById('btn1').innerHTML = 'Changed!';
            }
            
            function navigateAway() {
                window.location.href = 'data:text/html,<h1>New Page</h1>';
            }
            
            function openNewTab() {
                window.open('data:text/html,<h1>New Tab</h1>', '_blank');
            }
        </script>
    </body>
    </html>
    """

	# Create browser session
	browser_session = BrowserSession(
		browser_profile=BrowserProfile(
			headless=True,  # Run headless for testing
			window_size={'width': 1280, 'height': 720},
		)
	)

	try:
		await browser_session.start()

		# Navigate to the test HTML
		page = await browser_session.get_current_page()
		await page.goto(f'data:text/html,{test_html}')
		await asyncio.sleep(1)  # Wait for page to load

		# Get initial state
		state = await browser_session.get_state_summary(cache_clickable_elements_hashes=True)
		print(f'Initial page title: {state.title}')
		print(f'Initial URL: {state.url}')
		print(f'Initial elements count: {len(state.selector_map) if state.selector_map else 0}')

		# Print available elements
		if state.selector_map:
			print('\nAvailable elements:')
			for index, element in state.selector_map.items():
				element_text = element.get_all_text_till_next_clickable_element(max_depth=2)
				print(f"  [{index}] {element.tag_name}: '{element_text}'")

		# Create controller
		controller = Controller()

		# Test 1: Click button that changes content (should detect element change)
		print('\n=== Test 1: Click button that changes content ===')
		if state.selector_map and len(state.selector_map) > 0:
			# Find the first button (should be "Click Me")
			button_index = None
			for index, element in state.selector_map.items():
				if element.tag_name.lower() == 'button':
					element_text = element.get_all_text_till_next_clickable_element(max_depth=2)
					if 'Click Me' in element_text:
						button_index = index
						break

			if button_index is not None:
				# Create a proper action model for click_element_by_index
				class ClickActionModel(ActionModel):
					click_element_by_index: ClickElementAction | None = None

				click_action = ClickActionModel(click_element_by_index=ClickElementAction(index=button_index))
				result = await controller.act(click_action, browser_session)
				print(f'Result: {result.extracted_content}')
				print(f'Success: {result.success}')
				print(f'Error: {result.error}')
			else:
				print("Could not find 'Click Me' button")

		# Wait a moment and refresh state
		await asyncio.sleep(1)

		# Test 2: Click button that navigates away (should detect URL change)
		print('\n=== Test 2: Click button that navigates away ===')
		state = await browser_session.get_state_summary(cache_clickable_elements_hashes=True)
		if state.selector_map:
			# Find the navigate button
			button_index = None
			for index, element in state.selector_map.items():
				if element.tag_name.lower() == 'button':
					element_text = element.get_all_text_till_next_clickable_element(max_depth=2)
					if 'Navigate Away' in element_text:
						button_index = index
						break

			if button_index is not None:
				# Create a proper action model for click_element_by_index
				class ClickActionModel2(ActionModel):
					click_element_by_index: ClickElementAction | None = None

				click_action = ClickActionModel2(click_element_by_index=ClickElementAction(index=button_index))
				result = await controller.act(click_action, browser_session)
				print(f'Result: {result.extracted_content}')
				print(f'Success: {result.success}')
				print(f'Error: {result.error}')
			else:
				print("Could not find 'Navigate Away' button")

		print('\n=== Test completed ===')

	except Exception as e:
		print(f'Test failed with error: {e}')
		import traceback

		traceback.print_exc()
	finally:
		await browser_session.stop()


if __name__ == '__main__':
	asyncio.run(test_enhanced_click())
