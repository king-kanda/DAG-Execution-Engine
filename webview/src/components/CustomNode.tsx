import { memo } from 'react'
import { Handle, Position, NodeProps } from '@xyflow/react'
import './CustomNode.css'

interface CustomNodeData {
  label: string
  description: string
  iconName: string
  color: string
  status: 'pending' | 'running' | 'completed' | 'error'
  output?: any
  error?: string
}

const getIconEmoji = (iconName: string) => {
  const icons: { [key: string]: string } = {
    'Zap': '⚡',
    'Brain': '🧠',
    'Cloud': '☁️',
    'Quote': '💭',
    'Component': '🔧'
  }
  return icons[iconName] || '📦'
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'running': return '#f59e0b'
    case 'completed': return '#10b981'
    case 'error': return '#ef4444'
    default: return '#6b7280'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'running': return '⚡'
    case 'completed': return '✅'
    case 'error': return '❌'
    default: return '⏳'
  }
}

const CustomNode = memo(({ data, id }: NodeProps<CustomNodeData>) => {
  const statusColor = getStatusColor(data.status)
  const statusIcon = getStatusIcon(data.status)
  const icon = getIconEmoji(data.iconName)

  return (
    <div className="custom-node" style={{ borderColor: statusColor }}>
      <Handle
        type="target"
        position={Position.Top}
        className="custom-handle"
      />
      
      <div className="node-header">
        <div className="node-icon" style={{ backgroundColor: data.color }}>
          {icon}
        </div>
        <div className="node-status">
          <span className="status-icon">{statusIcon}</span>
          <span className="status-text">{data.status}</span>
        </div>
      </div>
      
      <div className="node-content">
        <div className="node-label">{data.label}</div>
        <div className="node-description">{data.description}</div>
        
        {data.status === 'completed' && data.output && (
          <div className="node-output">
            <small>Output: {JSON.stringify(data.output).slice(0, 50)}...</small>
          </div>
        )}
        
        {data.status === 'error' && data.error && (
          <div className="node-error">
            <small>Error: {data.error}</small>
          </div>
        )}
      </div>
      
      <Handle
        type="source"
        position={Position.Bottom}
        className="custom-handle"
      />
    </div>
  )
})

CustomNode.displayName = 'CustomNode'

export default CustomNode
