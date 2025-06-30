from browser_use.llm import ChatOpenAI, ChatGoogle
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
from pathlib import Path
import argparse
from browser_use import BrowserConfig, Browser, BrowserContextConfig
from browser_use.browser.profile import BrowserProfile, get_display_size
from browser_use.browser.session import BrowserSession
import uuid
from browser_use.browser.context import BrowserContext
from datetime import datetime
import os
# from browser_use.browser.utils.handle_network_requests import setup_network_monitoring
from browser_use.browser import BrowserProfile

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='UI Automation Agent')
    parser.add_argument('file_path', type=str, help='Path to the input txt file')
    return parser.parse_args()

def read_tasks(my_file_path):
    """
    Read tasks from a txt file where each line is a task.
    
    Returns:
        List of tasks
    """
    tasks = []
    file_path = Path(my_file_path)
    
    if not file_path.exists():
        print(f"Error: txt not found in the current directory")
        return tasks
        
    try:
        print(f"ALL TASKS:")
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    tasks.append(line)
                    print(f"\033[93m ▶▶ {line} ▶▶\033[0m")
        return tasks
    except Exception as e:
        print(f"Error reading baya.txt: {e}")
        return tasks

async def run_tasks(tasks: list[str]):
    """
    Run multiple tasks sequentially using the Agent.
    
    Args:
        tasks: List of tasks to execute
    """
    llm_openai = ChatOpenAI(model="gpt-4o")
    #llm_openai = ChatOpenAI(model="gpt-4.1-nano") #This model does not return "done" action and goes on about it.
    llm_google = ChatGoogle(model="gemini-2.5-flash")
    llm = llm_openai
    llm = llm_google


# Detect the screen size
    screen_size = get_display_size() or {"width": 1920, "height": 1080}  # fallback if detection fails
    # from browser_use.browser.types import ViewportSize
    # screen_size = ViewportSize(width=1920, height=1080)
    browser_profile = BrowserProfile(
        viewport=None,
        keep_alive=True,
        headless=False,
        disable_security=False,
        highlight_elements=False,
        record_video_dir="videos/",
        record_video_size=screen_size,
        window_size=screen_size,  # This will open the window maximized to the screen
        user_data_dir=str(Path.home() / ".config" / "browseruse" / "profiles" / f"profile_{uuid.uuid4()}"),
        # viewport_expansion=-1,
    )

    my_browser_session = BrowserSession(browser_profile=browser_profile)

    await my_browser_session.start()
    print("BugOwl: BROWSER OPENED ALREADY!\n Starting the tasks now....")

    # Load sensitive data from environment variables
    sensitive_data = {
        "baya_password": os.getenv("BAYA_PASSWORD"),
        "hubspot_email": os.getenv("HUBSPOT_EMAIL"),
        "hubspot_password": os.getenv("HUBSPOT_PASSWORD"),
    }

    print("BUGOWL: Running tasks ONE BY ONE")
    agent = None
    results = []
    count = 0
    for task in tasks:
        count = count + 1
        test_run_uuid = str(uuid.uuid4())
        if not agent:
            agent = Agent(
                        task=task,
                        task_id=test_run_uuid,
                        llm=llm,
                        browser_session=my_browser_session,
                        # page=page,
                        # browser=browser,
                        # browser_context=browser_context,
                        # browser_profile=browser_profile,
                        # browser_session=browser_session,
                        enable_memory=False,
                        save_conversation_path="logs/conversation",  # Save chat logs
                        use_vision=True,
                        sensitive_data=sensitive_data,
                        cloud_sync=None,
                        use_thinking=False,
            )
        else:
            agent.add_new_task(task)
        print(f"\033[94mBUGOWL: Executing Task #{count} ▶ : {task}\033[0m")
        history = await agent.run()
        output = '✅ SUCCESSFUL' if history.is_successful() else '❌ FAILED!'
        print(f"\033[94mBUGOWL: {task} : {output}\033[0m")
        res = (task, output)
        results.append(res)
        if not history.is_successful():
            # Take a screenshot of the failed state
            from browser_use.utils import save_failure_screenshot
            await save_failure_screenshot(my_browser_session, test_run_uuid)						
            break
    for res in results:
        print(f"\033[94m{res}\033[0m")
    await my_browser_session.close()
    if agent:
        await agent.close()

async def main():
    args = parse_args()
    file_path = Path(args.file_path)
    tasks = read_tasks(file_path)
    if not tasks:
        print("No tasks found in baya.txt")
        return
        
    print(f"Found {len(tasks)} tasks to execute")
    await run_tasks(tasks)

if __name__ == "__main__":
    asyncio.run(main())