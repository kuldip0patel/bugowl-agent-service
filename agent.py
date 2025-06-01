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
from datetime import datetime
import json
import os

# Global variables for network monitoring
request_map = {}  # Store requests to match with responses
MAX_REQUEST_AGE = 30  # Maximum age of requests in seconds

async def cleanup_old_requests():
    while True:
        current_time = datetime.now()
        # Remove requests older than MAX_REQUEST_AGE seconds
        keys_to_remove = []
        for request_id, request_data in request_map.items():
            request_time = datetime.fromisoformat(request_data["timestamp"])
            if (current_time - request_time).total_seconds() > MAX_REQUEST_AGE:
                keys_to_remove.append(request_id)
        
        for key in keys_to_remove:
            print(f"🧹 Cleaning up old request: {request_map[key]['method']} {request_map[key]['url']}")
            del request_map[key]
        
        await asyncio.sleep(5)  # Check every 5 seconds

async def handle_route(route):
    request = route.request
    # Create a unique ID using method, URL, and request headers that should be consistent
    request_id = f"{request.method}_{request.url}_{hash(frozenset(request.headers.items()))}"
    #print(f"📤 Request: {request.method} {request.url}")
    
    request_data = {
        "request_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "method": request.method,
        "url": request.url,
        "headers": dict(request.headers),
        "post_data": None,  # Initialize as None
        "response": None  # Initialize response as None
    }
    
    # Safely handle POST data
    if request.method == "POST":
        try:
            # Try to get post data as text
            post_data = request.post_data
            request_data["post_data"] = post_data
        except UnicodeDecodeError:
            # If it's binary data, store it as base64
            try:
                post_data = request.post_data_buffer
                if post_data:
                    request_data["post_data"] = {
                        "type": "binary",
                        "size": len(post_data),
                        "content_type": request.headers.get("content-type", "application/octet-stream")
                    }
            except Exception as e:
                request_data["post_data"] = {
                    "error": f"Failed to process post data: {str(e)}"
                }
    
    # Store request data for later matching with response
    request_map[request_id] = request_data
    
    # Continue the request
    await route.continue_()

async def handle_response(response):
    request = response.request
    # Use the same ID generation logic as in handle_route
    request_id = f"{request.method}_{request.url}_{hash(frozenset(request.headers.items()))}"
    #print(f"📥 Response: {response.status} {request.method} {request.url}")
    
    # Find the matching request data
    request_data = request_map.get(request_id)
    if request_data:
        try:
            response_data = {
                "status": response.status,
                "status_text": response.status_text,
                "headers": dict(response.headers),
                "body": None
            }
            
            """ Skipping to store response body for now"""
            # # Try to get response body
            # try:
            #     # Try to get response as text
            #     response_data["body"] = await response.text()
            # except UnicodeDecodeError:
            #     # If it's binary data, store metadata
            #     try:
            #         body = await response.body()
            #         if body:
            #             response_data["body"] = {
            #                 "type": "binary",
            #                 "size": len(body),
            #                 "content_type": response.headers.get("content-type", "application/octet-stream")
            #             }
            #     except Exception as e:
            #         response_data["body"] = {
            #             "error": f"Failed to process response body: {str(e)}"
            #         }
            
            request_data["response"] = response_data
            
            # Save to file
            with open("network_logs/requests.json", "a") as f:
                f.write(json.dumps(request_data) + "\n")
            
            # Clean up the request from the map
            del request_map[request_id]
            #print(f"✅ Saved request/response pair for {request.method} {request.url}")
            
        except Exception as e:
            request_data["response"] = {
                "error": f"Failed to process response: {str(e)}"
            }
            print(f"❌ Error processing response for {request.method} {request.url}: {str(e)}")
    else:
        print(f"⚠️ No matching request found for response: {request.method} {request.url}")

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
    
    # Start the cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_requests())
    
    # Create network_logs directory if it doesn't exist
    os.makedirs("network_logs", exist_ok=True)
    
    # Monitor all network requests and responses
    await page.route("**/*", handle_route)
    
    # Register response handler with proper async handling
    page.on("response", lambda response: asyncio.create_task(handle_response(response)))
    
    await page.evaluate("""
        () => {
            if (document.documentElement.requestFullscreen) {
                document.documentElement.requestFullscreen();
            }
        }
    """)
    
    print("BROWSER OPENED ALREADY!")
    sensitive_data = {"baya_password": "Baya@1234", "peerlist_email": "kul.iitk@gmail.com"}
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