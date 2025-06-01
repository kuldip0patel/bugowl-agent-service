import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from browser_use import Agent
from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig
from browser_use.utils.video_recorder import VideoRecorder, LiveStreamer, capture_screen

load_dotenv()

async def on_step_start(browser_state, agent_output, step_number):
    """Callback function that runs at the start of each step"""
    # Get the current page
    page = await browser_state.get_current_page()
    if page:
        # Capture the screen
        frame = await capture_screen(page)
        
        # Save video for this action
        video_recorder.add_frame(frame)
        
        # If streaming is enabled, add frame to stream
        if streamer:
            streamer.add_frame(frame)

async def main():
    # Initialize video recording
    global video_recorder, streamer
    video_recorder = VideoRecorder(
        save_dir="videos/",
        width=1920,
        height=1080,
        fps=30
    )
    
    # Initialize streaming (optional)
    streamer = LiveStreamer(
        stream_url="rtmp://your-streaming-server/live/stream",
        width=1920,
        height=1080,
        fps=30
    )
    
    # Configure browser
    context_config = BrowserContextConfig(
        window_width=1920,
        window_height=1080,
        save_recording_path="videos/",  # For continuous recording
        record_video_format="webm",
        record_video_name="full_session_{timestamp}.webm"
    )
    
    browser = Browser(config=BrowserConfig(
        headless=False,
        new_context_config=context_config
    ))
    
    # Initialize LLM
    llm = ChatOpenAI(model="gpt-4")
    
    # Create agent with video recording
    agent = Agent(
        task="Go to google.com and search for 'browser automation'",
        llm=llm,
        browser=browser,
        register_new_step_callback=on_step_start
    )
    
    try:
        # Start recording
        video_recorder.start_recording(0)
        if streamer:
            streamer.start_streaming()
        
        # Run the agent
        history = await agent.run()
        
    finally:
        # Stop recording
        video_recorder.stop_recording()
        if streamer:
            streamer.stop_streaming()
        
        # Close browser
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main()) 