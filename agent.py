from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
import csv
from pathlib import Path
import argparse
from browser_use import BrowserConfig, Browser, BrowserContextConfig
from browser_use.browser.context import BrowserContext
from datetime import datetime
import os
from browser_use.browser.utils.handle_network_requests import setup_network_monitoring

load_dotenv()

def parse_args():
    parser = argparse.ArgumentParser(description='UI Automation Agent')
    parser.add_argument('file_path', type=str, help='Path to the input CSV file')
    return parser.parse_args()

def read_tasks(my_file_path):
    """
    Read tasks from a csv file where each line is a task.
    
    Returns:
        List of tasks
    """
    tasks = []
    #my_file_path = "mmt.csv"
    #my_file_path = "baya.csv"
    file_path = Path(my_file_path)
    
    if not file_path.exists():
        print(f"Error: csv not found in the current directory")
        return tasks
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row:  # Skip empty lines
                    tasks.append(row[0].strip())
        return tasks
    except Exception as e:
        print(f"Error reading baya.csv: {e}")
        return tasks

async def run_tasks(tasks: list[str]):
    """
    Run multiple tasks sequentially using the Agent.
    
    Args:
        tasks: List of tasks to execute
    """
    llm = ChatOpenAI(model="gpt-4o")
    llm = ChatOpenAI(model="gpt-4.1-nano")

    run_together = True
    # tasks_list = []
    # if run_together:
        # for i in range(1, len(tasks) + 1):
        #     tasks[i-1] = f"STEP {i}: {tasks[i-1]}"
        # tasks_list = " \n\n ".join(tasks)
        # print(f"\n OUR task list: {tasks_list}")

# Basic configuration
    context_config = BrowserContextConfig(
        highlight_elements=False,
        save_recording_path="videos/",
        save_har_path="network_logs/",  # Add HAR recording
        window_width=1920,
        window_height=1080,
        viewport_expansion=-1,
        record_video_format="webm",  # Using webm as it's the most compressed and optimized format
        record_video_name="video_{timestamp}_{guid}.webm"  # Custom naming format with timestamp and GUID
    )

    config = BrowserConfig(
        headless=False,
        disable_security=False,
        context_config = context_config
    )
    browser = Browser(config=config)    
    browser_context = BrowserContext(browser=browser, config=context_config)
    
    # Get the page and maximize it
    page = await browser_context.get_current_page()
    
    # Setup network monitoring
    cleanup_task = await setup_network_monitoring(page)
    
    await page.evaluate("""
        () => {
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            }
        }
    """)
    
    print("BROWSER OPENED ALREADY!")
    # Load sensitive data from environment variables
    sensitive_data = {
        "baya_password": "Baya@1234",
        "hubspot_email": os.getenv("HUBSPOT_EMAIL"),
        "hubspot_password": os.getenv("HUBSPOT_PASSWORD"),
    }
    print(sensitive_data)
    if run_together:
        agent = Agent(
            tasks=tasks,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            enable_memory=True,
            save_conversation_path="logs/conversation",  # Save chat logs
            use_vision=True,
            sensitive_data=sensitive_data
        )
        history = await agent.run()
        output = '✅ SUCCESSFUL' if history.is_successful() else '❌ FAILED!'
        print(f"Running all tasks status : {output}")
        for t, s in agent.tasks_result:
            output = '✅ SUCCESSFUL' if s else '❌ FAILED!'
            print(f" TASK: {t} : {output} ")
    else:
        agent = None
        results = []
        count = 0
        for task in tasks:
            count = count + 1
            if not agent:
                agent = Agent(
                    task=task,
                    llm=llm,
                    browser=browser,
                    browser_context=browser_context,
                    enable_memory=True,
                    use_vision=True,
                    save_conversation_path="logs/conversation",  # Save chat logs
                    generate_gif=f"{datetime.now().timestamp}.gif"
                )
            else:
                is_final_task = True if count == len(task) else False
                agent.add_new_task(task, is_final_task=is_final_task)
            print(f"Executing task: {task}")
            history = await agent.run()
            output = '✅ SUCCESSFUL' if history.is_successful() else '❌ FAILED!'
            print(f"{task} : {output}")
            res = (task, output)
            results.append(res)
            if not history.is_successful():
                break
        for res in results:
            print(res)
    await browser_context.close()
    await agent.browser.close()
    await agent.close()

async def main():
    args = parse_args()
    file_path = Path(args.file_path)
    tasks = read_tasks(file_path)
    if not tasks:
        print("No tasks found in baya.csv")
        return
        
    print(f"Found {len(tasks)} tasks to execute")
    await run_tasks(tasks)

if __name__ == "__main__":
    asyncio.run(main())