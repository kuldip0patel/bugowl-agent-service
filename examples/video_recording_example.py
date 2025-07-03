import asyncio

from dotenv import load_dotenv

try:
	from langchain_openai import ChatOpenAI  # type: ignore[import-untyped]
except ImportError:
	ChatOpenAI = None  # type: ignore

from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig

try:
	from browser_use.browser.utils.video_recorder import (  # type: ignore[import-untyped]
		LiveStreamer,
		VideoRecorder,
		capture_screen,
	)
except ImportError:
	LiveStreamer = None  # type: ignore
	VideoRecorder = None  # type: ignore
	capture_screen = None  # type: ignore

load_dotenv()


async def on_step_start(browser_state, _agent_output, _step_number):
	"""Callback function that runs at the start of each step"""
	# Get the current page
	page = await browser_state.get_current_page()
	if page and capture_screen is not None:
		# Capture the screen
		frame = await capture_screen(page)  # type: ignore

		# Save video for this action
		video_recorder.add_frame(frame)

		# If streaming is enabled, add frame to stream
		if streamer:
			streamer.add_frame(frame)


async def main():
	# Check for required dependencies
	if ChatOpenAI is None:
		raise ImportError('langchain_openai is required for this example. Install with: pip install langchain_openai')
	if VideoRecorder is None:
		raise ImportError('OpenCV is required for video recording. Install with: pip install opencv-python')

	# Initialize video recording
	global video_recorder, streamer
	video_recorder = VideoRecorder(save_dir='videos/', width=1920, height=1080, fps=30)  # type: ignore

	# Initialize streaming (optional)
	streamer = LiveStreamer(stream_url='rtmp://your-streaming-server/live/stream', width=1920, height=1080, fps=30)  # type: ignore

	# Configure browser
	context_config = BrowserContextConfig(
		window_width=1920,
		window_height=1080,
		save_recording_path='videos/',  # For continuous recording  # type: ignore[call-arg]
		record_video_format='webm',  # type: ignore[call-arg]
		record_video_name='full_session_{timestamp}.webm',  # type: ignore[call-arg]
	)

	browser = Browser(config=BrowserConfig(headless=False, new_context_config=context_config))  # type: ignore[call-arg]

	# Initialize LLM
	llm = ChatOpenAI(model='gpt-4')  # type: ignore

	# Create agent with video recording
	agent = Agent(
		task="Go to google.com and search for 'browser automation'",
		llm=llm,  # type: ignore[arg-type]
		browser=browser,  # type: ignore[call-arg]
		register_new_step_callback=on_step_start,
	)

	try:
		# Start recording
		video_recorder.start_recording(0)
		if streamer:
			streamer.start_streaming()

		# Run the agent
		_history = await agent.run()

	finally:
		# Stop recording
		video_recorder.stop_recording()
		if streamer:
			streamer.stop_streaming()

		# Close browser
		await browser.close()


if __name__ == '__main__':
	asyncio.run(main())
