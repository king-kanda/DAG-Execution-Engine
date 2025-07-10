const API_BASE_URL = 'http://localhost:8000';

export interface APIMessage {
  id: string;
  type: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
}

export interface NodeStatus {
  status: 'pending' | 'running' | 'completed' | 'error';
  output?: any;
  error?: string;
}

export interface WorkflowStatus {
  is_running: boolean;
  current_node: string | null;
  messages: APIMessage[];
  node_statuses: { [nodeId: string]: NodeStatus };
}

export const api = {
  async getDAG() {
    const response = await fetch(`${API_BASE_URL}/api/dag`);
    if (!response.ok) {
      throw new Error('Failed to fetch DAG');
    }
    return response.json();
  },

  async getStatus(): Promise<WorkflowStatus> {
    const response = await fetch(`${API_BASE_URL}/api/status`);
    if (!response.ok) {
      throw new Error('Failed to fetch status');
    }
    return response.json();
  },

  async executeWorkflow(input: string) {
    const response = await fetch(`${API_BASE_URL}/api/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ input }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to execute workflow');
    }
    
    return response.json();
  },

  async stopWorkflow() {
    const response = await fetch(`${API_BASE_URL}/api/stop`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error('Failed to stop workflow');
    }
    
    return response.json();
  },

  async resetWorkflow() {
    const response = await fetch(`${API_BASE_URL}/api/reset`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error('Failed to reset workflow');
    }
    
    return response.json();
  },
};
