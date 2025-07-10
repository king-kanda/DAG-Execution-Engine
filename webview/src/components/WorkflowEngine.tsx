import { useState, useCallback } from 'react'
import { ReactFlow, MiniMap, Controls, Background } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import DAGVisualization from './DAGVisualization'
import ChatInterface from './ChatInterface'
import { weatherDAG } from '../data/weatherDAG'
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

    // Simulate workflow execution
    const systemMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'system',
      content: 'Starting workflow execution...',
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, systemMessage])

    // TODO: Replace with actual API call to your Python backend
    // For now, we'll simulate the workflow execution
    await simulateWorkflowExecution(content)
    
    setIsExecuting(false)
  }, [])

  const simulateWorkflowExecution = async (userInput: string) => {
    const nodes = weatherDAG.nodes.map(n => n.id)
    
    // Simulate node execution with delays
    for (const nodeId of nodes) {
      setNodeStatuses(prev => ({
        ...prev,
        [nodeId]: { status: 'running' }
      }))
      
      const logMessage: Message = {
        id: Date.now().toString(),
        type: 'system',
        content: `Executing node: ${nodeId}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, logMessage])
      
      // Simulate processing time
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setNodeStatuses(prev => ({
        ...prev,
        [nodeId]: { 
          status: 'completed',
          output: `Output from ${nodeId}`
        }
      }))
    }
    
    // Final response
    const finalMessage: Message = {
      id: Date.now().toString(),
      type: 'assistant',
      content: `Based on your query "${userInput}", here's what I found:\n\n🌤️ The weather looks great for outdoor activities!\n🚶‍♂️ I recommend taking a walk or having a picnic.\n💭 "The best time to plant a tree was 20 years ago. The second best time is now." - Chinese Proverb`,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, finalMessage])
  }

  return (
    <div className="workflow-engine">
      <div className="workflow-main">
        <div className="dag-panel">
          <div className="panel-header">
            <h3>Workflow DAG</h3>
            <div className="dag-controls">
              <button 
                className="btn btn-primary"
                onClick={() => setNodeStatuses({})}
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
