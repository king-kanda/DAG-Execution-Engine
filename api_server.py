#!/usr/bin/env python3
"""
FastAPI server to connect the React frontend with the workflow engine.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
import time
from typing import Dict, List, Any, Optional
from weather_dag import weather_dag
from main import RedisSOPExecutor, MockRedis

app = FastAPI(title="Workflow Engine API", version="1.0.0")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store workflow execution status
workflow_status = {
    'is_running': False,
    'current_node': None,
    'messages': [],
    'node_statuses': {}
}


def reset_workflow_status():
    """Reset the workflow status"""
    global workflow_status
    workflow_status = {
        'is_running': False,
        'current_node': None,
        'messages': [],
        'node_statuses': {}
    }


@app.route('/api/dag', methods=['GET'])
def get_dag():
    """Get the current DAG structure"""
    return jsonify(weather_dag)


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current workflow status"""
    return jsonify(workflow_status)


@app.route('/api/execute', methods=['POST'])
def execute_workflow_api():
    """Execute workflow with user input"""
    global workflow_status

    if workflow_status['is_running']:
        return jsonify({'error': 'Workflow is already running'}), 400

    data = request.get_json()
    user_input = data.get('input', '')

    if not user_input:
        return jsonify({'error': 'Input is required'}), 400

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
            # Simulate workflow execution (replace with actual execution)
            nodes = [node['id'] for node in weather_dag['nodes']]

            for i, node_id in enumerate(nodes):
                if not workflow_status['is_running']:
                    break

                workflow_status['current_node'] = node_id
                workflow_status['node_statuses'][node_id] = {
                    'status': 'running'
                }

                # Add log message
                workflow_status['messages'].append({
                    'id':
                    str(int(time.time() * 1000) + i + 2),
                    'type':
                    'system',
                    'content':
                    f'Executing node: {node_id}',
                    'timestamp':
                    int(time.time() * 1000)
                })

                # Simulate processing time
                time.sleep(1)

                workflow_status['node_statuses'][node_id] = {
                    'status': 'completed',
                    'output': f'Output from {node_id}'
                }

            # Add final response
            workflow_status['messages'].append({
                'id':
                str(int(time.time() * 1000) + 100),
                'type':
                'assistant',
                'content':
                f'Based on your query "{user_input}", here\'s what I found:\\n\\n🌤️ The weather looks great for outdoor activities!\\n🚶‍♂️ I recommend taking a walk or having a picnic.\\n💭 "The best time to plant a tree was 20 years ago. The second best time is now." - Chinese Proverb',
                'timestamp':
                int(time.time() * 1000)
            })

            workflow_status['is_running'] = False
            workflow_status['current_node'] = None

        except Exception as e:
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

    return jsonify({'message': 'Workflow execution started'})


@app.route('/api/stop', methods=['POST'])
def stop_workflow():
    """Stop workflow execution"""
    global workflow_status
    workflow_status['is_running'] = False
    workflow_status['current_node'] = None

    workflow_status['messages'].append({
        'id': str(int(time.time() * 1000)),
        'type': 'system',
        'content': 'Workflow execution stopped by user',
        'timestamp': int(time.time() * 1000)
    })

    return jsonify({'message': 'Workflow stopped'})


@app.route('/api/reset', methods=['POST'])
def reset_workflow():
    """Reset workflow state"""
    reset_workflow_status()
    return jsonify({'message': 'Workflow reset'})


if __name__ == '__main__':
    print("Starting Flask API server...")
    print("React frontend should connect to: http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
