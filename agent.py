from langchain_openai import ChatOpenAI
from browser_use import Agent
import asyncio
from dotenv import load_dotenv
import csv
from pathlib import Path
import argparse
load_dotenv()
from browser_use import BrowserConfig, Browser, BrowserContextConfig
from browser_use.browser.context import BrowserContext


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

    run_together = False
    tasks_list = []
    if run_together:
        for i in range(1, len(tasks) + 1):
            tasks[i-1] = f"STEP {i}: {tasks[i-1]}"

        tasks_list = " \n\n ".join(tasks)
        print(f"\n OUR task list: {tasks_list}")

# Basic configuration
    context_config = BrowserContextConfig( 
    highlight_elements=False,
    save_recording_path="videos/",
    window_width=1920,  # or your desired width
    window_height=1080,  # or your desired height
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
    await page.evaluate("""
        () => {
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            }
        }
    """)
    
    print("BROWSER OPENED ALREADY?")
    if run_together:
        agent = Agent(
            task=tasks_list,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            enable_memory=True,
            save_conversation_path="logs/conversation",  # Save chat logs
            use_vision=True
        )
        history = await agent.run()
        output = '✅ SUCCESSFUL' if history.is_successful() else '❌ FAILED!'
        print(f"Running all tasks status : {output}")
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