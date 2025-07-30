#!/usr/bin/env python3
"""
FastAPI server to connect the React frontend with the workflow engine.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import time
import uuid
from main import RedisSOPExecutor, MockRedis
from weather_dag import weather_dag

app = FastAPI(title="Workflow Engine API", version="1.0.0")

# Initialize Redis client
redis_client = MockRedis()

# Store active executors
active_executors = {}


class ProgressTrackingExecutor(RedisSOPExecutor):
    """Extended executor that tracks progress for the API"""

    def execute_node(self, node_id: str) -> str:
        """Execute a single node and update API status"""
        # Update workflow status before execution
        workflow_status['current_node'] = node_id
        workflow_status['node_statuses'][node_id] = {'status': 'running'}

        # Add log message
        workflow_status['messages'].append({
            'id': str(int(time.time() * 1000)),
            'type': 'system',
            'content': f'Executing node: {node_id}',
            'timestamp': int(time.time() * 1000)
        })

        # Execute the actual node
        result = super().execute_node(node_id)

        # Update status after execution
        if result == "OK":
            workflow_status['node_statuses'][node_id] = {
                'status': 'completed',
                'output': f'Node {node_id} completed successfully'
            }
        elif result == "WAIT":
            workflow_status['node_statuses'][node_id] = {
                'status': 'pending',
                'output': 'Waiting for user input'
            }
        else:
            workflow_status['node_statuses'][node_id] = {
                'status': 'error',
                'error': str(result)
            }

        return result


# Request models
class ExecuteRequest(BaseModel):
    input: str


# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://localhost:3000",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store workflow execution status
workflow_status = {
    'is_running': False,
    'current_node': None,
    'messages': [],
    'node_statuses': {},
    'conversation_id': None
}


def reset_workflow_status():
    """Reset the workflow status"""
    workflow_status['is_running'] = False
    workflow_status['current_node'] = None
    workflow_status['messages'] = []
    workflow_status['node_statuses'] = {}
    workflow_status['conversation_id'] = None


@app.get('/api/dag')
def get_dag():
    """Get the current DAG structure"""
    return weather_dag


@app.get('/api/status')
def get_status():
    """Get current workflow status"""
    return workflow_status


@app.post('/api/execute')
def execute_workflow_api(request: ExecuteRequest):
    """Execute workflow with user input"""

    if workflow_status['is_running']:
        raise HTTPException(status_code=400,
                            detail='Workflow is already running')

    user_input = request.input

    if not user_input:
        raise HTTPException(status_code=400, detail='Input is required')

    # Reset status
    reset_workflow_status()
    workflow_status['is_running'] = True

    # Add user message
    workflow_status['messages'].append({
        'id': str(int(time.time() * 1000)),
        'type': 'user',
        'content': user_input,
        'timestamp': int(time.time() * 1000)
    })

    # Add system message
    workflow_status['messages'].append({
        'id': str(int(time.time() * 1000) + 1),
        'type': 'system',
        'content': 'Starting workflow execution...',
        'timestamp': int(time.time() * 1000)
    })

    # Start workflow execution in background
    def run_workflow():
        try:
            # Create unique conversation ID
            conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
            workflow_status['conversation_id'] = conversation_id

            # Initialize executor with user input in context
            initial_context = {"user_query": user_input}
            executor = ProgressTrackingExecutor(
                sop=weather_dag,
                conversation_id=conversation_id,
                redis_client=redis_client,
                initial_context=initial_context)

            # Add user message to conversation history BEFORE starting execution
            executor.context.add_user_message(user_input)

            # Store executor for potential stop operations
            active_executors[conversation_id] = executor

            # Execute workflow
            result = executor.run()

            # Process final result
            if result.get("status") == "COMPLETED":
                # Extract the actual response from the workflow result
                final_response = result.get("data", {})
                content = "Workflow completed successfully!"

                # Try to get the activity advisor response
                if isinstance(final_response, dict):
                    action_outputs = final_response.get("action_outputs", [])
                    for output in action_outputs:
                        if output.get("node_id") == "activity-advisor":
                            advisor_output = output.get("output", {})
                            if isinstance(advisor_output, dict):
                                llm_response = advisor_output.get(
                                    "llm_response", {})
                                if isinstance(llm_response, dict):
                                    # Get the clean response from the LLM
                                    response_text = llm_response.get(
                                        "response", "")
                                    if response_text:
                                        content = response_text
                                    break

                # If no activity advisor response found, try to get weather info
                if content == "Workflow completed successfully!":
                    weather_info = ""
                    quote_info = ""
                    location_info = ""

                    # Get location from chat context
                    chat_context = final_response.get("chat_context", {})
                    location = chat_context.get("location", "")
                    if location:
                        location_info = f"📍 Location: {location}\n"

                    for output in action_outputs:
                        if output.get("node_id") == "weather-api":
                            weather_output = output.get("output", {})
                            if isinstance(weather_output,
                                          dict) and weather_output.get(
                                              "weather_found"):
                                location = weather_output.get("location", "")
                                temp = weather_output.get("temperature", "")
                                desc = weather_output.get("description", "")
                                weather_info = f"🌤️ Weather in {location}: {temp}°C, {desc}\n"

                        elif output.get("node_id") == "quote-api":
                            quote_output = output.get("output", {})
                            if isinstance(
                                    quote_output,
                                    dict) and quote_output.get("quote_found"):
                                quote = quote_output.get("quote", "")
                                author = quote_output.get("author", "")
                                quote_info = f'💭 "{quote}" - {author}\n'

                    if location_info or weather_info or quote_info:
                        content = f"{location_info}{weather_info}{quote_info}I've gathered information about your query!"

                workflow_status['messages'].append({
                    'id':
                    str(int(time.time() * 1000) + 100),
                    'type':
                    'assistant',
                    'content':
                    content,
                    'timestamp':
                    int(time.time() * 1000)
                })

            elif result.get("status") == "WAITING":
                workflow_status['messages'].append({
                    'id':
                    str(int(time.time() * 1000) + 50),
                    'type':
                    'system',
                    'content':
                    f'Workflow paused - waiting for input at node: {result.get("node_id")}',
                    'timestamp':
                    int(time.time() * 1000)
                })

            elif result.get("status") == "FAILED":
                workflow_status['messages'].append({
                    'id':
                    str(int(time.time() * 1000) + 200),
                    'type':
                    'system',
                    'content':
                    f'Workflow failed at node {result.get("failed_node")}: {result.get("error")}',
                    'timestamp':
                    int(time.time() * 1000)
                })

            workflow_status['is_running'] = False
            workflow_status['current_node'] = None

            # Clean up executor
            if conversation_id in active_executors:
                del active_executors[conversation_id]

        except (RuntimeError, ValueError, KeyError) as e:
            workflow_status['messages'].append({
                'id':
                str(int(time.time() * 1000) + 999),
                'type':
                'system',
                'content':
                f'Error: {str(e)}',
                'timestamp':
                int(time.time() * 1000)
            })
            workflow_status['is_running'] = False

    # Start execution thread
    thread = threading.Thread(target=run_workflow)
    thread.daemon = True
    thread.start()

    return {'message': 'Workflow execution started'}


if __name__ == '__main__':
    import uvicorn
    print("Starting FastAPI server...")
    print("React frontend should connect to: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
