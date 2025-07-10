import { useState, useCallback } from 'react'
import DAGVisualization from './DAGVisualization.js'
import ChatInterface from './ChatInterface.js'
import { weatherDAG } from '../data/weatherDAG.js'
import { api } from '../services/api.js'
import './WorkflowEngine.css'

export interface Message {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

export interface NodeStatus {
  [nodeId: string]: {
    status: 'pending' | 'running' | 'completed' | 'error'
    output?: any
    error?: string
  }
}

const WorkflowEngine = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'system',
      content: 'Welcome to the Weather & Activity Advisor! Ask me about the weather in any location.',
      timestamp: new Date()
    }
  ])
  
  const [nodeStatuses, setNodeStatuses] = useState<NodeStatus>({})
  const [isExecuting, setIsExecuting] = useState(false)

  const handleSendMessage = useCallback(async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsExecuting(true)

    try {
      // Execute workflow via API
      await api.executeWorkflow(content)
      
      // Start polling for status updates
      pollForUpdates()
    } catch (error) {
      const errorMessage: Message = {
        id: Date.now().toString(),
        type: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
      setIsExecuting(false)
    }
  }, [])

  const pollForUpdates = useCallback(async () => {
    try {
      const status = await api.getStatus()
      
      // Convert API timestamps to Date objects and update messages
      const convertedMessages = status.messages.map(msg => ({
        ...msg,
        timestamp: new Date(msg.timestamp)
      }))
      
      setMessages(convertedMessages)
      setNodeStatuses(status.node_statuses)
      setIsExecuting(status.is_running)
      
      // Continue polling if workflow is running
      if (status.is_running) {
        setTimeout(pollForUpdates, 1000)
      }
    } catch (error) {
      console.error('Failed to poll status:', error)
      setIsExecuting(false)
    }
  }, [])

  const handleReset = useCallback(async () => {
    try {
      await api.resetWorkflow()
      setNodeStatuses({})
      setMessages([
        {
          id: '1',
          type: 'system',
          content: 'Welcome to the Weather & Activity Advisor! Ask me about the weather in any location.',
          timestamp: new Date()
        }
      ])
    } catch (error) {
      console.error('Failed to reset workflow:', error)
    }
  }, [])

  return (
    <div className="workflow-engine">
      <div className="workflow-main">
        <div className="dag-panel">
          <div className="panel-header">
            <h3>Workflow DAG</h3>
            <div className="dag-controls">
              <button 
                className="btn btn-primary"
                onClick={handleReset}
                disabled={isExecuting}
              >
                Reset
              </button>
            </div>
          </div>
          <DAGVisualization 
            dag={weatherDAG} 
            nodeStatuses={nodeStatuses}
          />
        </div>
        
        <div className="chat-panel">
          <div className="panel-header">
            <h3>Chat Interface</h3>
            <div className="status-indicator">
              <div className={`status-dot ${isExecuting ? 'running' : 'idle'}`}></div>
              <span>{isExecuting ? 'Executing...' : 'Ready'}</span>
            </div>
          </div>
          <ChatInterface
            messages={messages}
            onSendMessage={handleSendMessage}
            isExecuting={isExecuting}
          />
        </div>
      </div>
    </div>
  )
}

export default WorkflowEngine
