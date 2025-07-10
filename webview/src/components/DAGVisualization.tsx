import { useCallback, useMemo } from 'react'
import {
  ReactFlow,
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode
} from '@xyflow/react'
import CustomNode from './CustomNode'
import { NodeStatus } from './WorkflowEngine'
import './DAGVisualization.css'

interface DAGVisualizationProps {
  dag: {
    nodes: any[]
    edges: any[]
  }
  nodeStatuses: NodeStatus
}

const nodeTypes = {
  FlowNode: CustomNode,
}

const DAGVisualization = ({ dag, nodeStatuses }: DAGVisualizationProps) => {
  // Convert DAG nodes to React Flow format
  const initialNodes: Node[] = useMemo(() => {
    return dag.nodes.map(node => ({
      id: node.id,
      type: 'FlowNode',
      position: node.position,
      data: {
        ...node.data,
        status: nodeStatuses[node.id]?.status || 'pending',
        output: nodeStatuses[node.id]?.output,
        error: nodeStatuses[node.id]?.error
      }
    }))
  }, [dag.nodes, nodeStatuses])

  // Convert DAG edges to React Flow format
  const initialEdges: Edge[] = useMemo(() => {
    return dag.edges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: false,
      style: {
        stroke: '#6b7280',
        strokeWidth: 2
      }
    }))
  }, [dag.edges])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  // Update nodes when statuses change
  useMemo(() => {
    setNodes(nodes => 
      nodes.map(node => ({
        ...node,
        data: {
          ...node.data,
          status: nodeStatuses[node.id]?.status || 'pending',
          output: nodeStatuses[node.id]?.output,
          error: nodeStatuses[node.id]?.error
        }
      }))
    )
  }, [nodeStatuses, setNodes])

  return (
    <div className="dag-visualization">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#374151" gap={20} />
        <Controls 
          style={{
            button: {
              backgroundColor: '#374151',
              color: '#f9fafb',
              border: '1px solid #6b7280'
            }
          }}
        />
        <MiniMap 
          style={{
            backgroundColor: '#1f2937',
          }}
          nodeColor={(node) => {
            const status = node.data?.status || 'pending'
            switch (status) {
              case 'running': return '#f59e0b'
              case 'completed': return '#10b981'
              case 'error': return '#ef4444'
              default: return '#6b7280'
            }
          }}
        />
      </ReactFlow>
    </div>
  )
}

export default DAGVisualization
