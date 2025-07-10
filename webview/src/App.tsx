import { useState } from 'react'
import WorkflowEngine from './components/WorkflowEngine'
import './App.css'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Workflow Engine</h1>
        <p>DAG Visualization & Chat Interface</p>
      </header>
      <WorkflowEngine />
    </div>
  )
}

export default App
