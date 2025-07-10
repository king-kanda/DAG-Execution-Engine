import { useState, useRef, useEffect } from 'react'
import type { Message } from './WorkflowEngine.js'
import './ChatInterface.css'

interface ChatInterfaceProps {
  messages: Message[]
  onSendMessage: (content: string) => void
  isExecuting: boolean
}

const ChatInterface = ({ messages, onSendMessage, isExecuting }: ChatInterfaceProps) => {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isExecuting) {
      onSendMessage(input.trim())
      setInput('')
    }
  }

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'user': return '👤'
      case 'assistant': return '🤖'
      case 'system': return '⚙️'
      default: return '💬'
    }
  }

  return (
    <div className="chat-interface">
      <div className="messages-container">
        <div className="messages">
          {messages.map((message) => (
            <div key={message.id} className={`message message-${message.type}`}>
              <div className="message-header">
                <span className="message-icon">{getMessageIcon(message.type)}</span>
                <span className="message-type">{message.type}</span>
                <span className="message-timestamp">{formatTimestamp(message.timestamp)}</span>
              </div>
              <div className="message-content">{message.content}</div>
            </div>
          ))}
          
          {isExecuting && (
            <div className="typing-indicator">
              <div className="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="typing-text">Processing workflow...</span>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
      </div>
      
      <form onSubmit={handleSubmit} className="input-form">
        <div className="input-container">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about weather in any location..."
            disabled={isExecuting}
            className="message-input"
          />
          <button 
            type="submit" 
            disabled={!input.trim() || isExecuting}
            className="send-button"
          >
            {isExecuting ? '⏳' : '🚀'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default ChatInterface
