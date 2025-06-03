"""all network requests of playwright will be handled here"""
import asyncio
import json
import os
from datetime import datetime

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
            #print(f"🧹 Cleaning up old request: {request_map[key]['method']} {request_map[key]['url']}")
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
            #print(f"❌ Error processing response for {request.method} {request.url}: {str(e)}")
    else:
        error_msg = f"⚠️ No matching request found for response: {request.method} {request.url}"
        #print(error_msg)

async def setup_network_monitoring(page):
    """Setup network monitoring for a page"""
    # Create network_logs directory if it doesn't exist
    os.makedirs("network_logs", exist_ok=True)
    
    # Start the cleanup task
    cleanup_task = asyncio.create_task(cleanup_old_requests())
    
    # Monitor all network requests and responses
    await page.route("**/*", handle_route)
    page.on("response", lambda response: asyncio.create_task(handle_response(response)))
    
    return cleanup_task