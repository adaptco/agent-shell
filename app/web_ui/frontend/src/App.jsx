import React, { useState, useEffect } from 'react';
import './App.css';
import DocumentUpload from './components/DocumentUpload';
import GraphVisualizer from './components/GraphVisualizer';
import TaskList from './components/TaskList';
import AnalysisPanel from './components/AnalysisPanel';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [documents, setDocuments] = useState([]);
  const [graphs, setGraphs] = useState([]);
  const [selectedGraphId, setSelectedGraphId] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const API_URL = 'http://127.0.0.1:8001';

  useEffect(() => {
    loadDocuments();
    loadGraphs();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await fetch(`${API_URL}/api/documents`);
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  const loadGraphs = async () => {
    try {
      const response = await fetch(`${API_URL}/api/graphs`);
      const data = await response.json();
      setGraphs(data.graphs || []);
    } catch (error) {
      console.error('Error loading graphs:', error);
    }
  };

  const handleDocumentUploaded = async (filename) => {
    setMessage(`Document uploaded: ${filename}`);
    await loadDocuments();
    setTimeout(() => setMessage(''), 3000);
  };

  const handleCreateGraph = async () => {
    if (documents.length === 0) {
      setMessage('Please upload at least one document first');
      return;
    }

    setLoading(true);
    try {
      const documentMap = {};
      for (const doc of documents) {
        const response = await fetch(`${API_URL}/api/documents/${doc.filename}`);
        const data = await response.json();
        documentMap[doc.filename] = data.content;
      }

      const response = await fetch(`${API_URL}/api/graph/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          documents: documentMap,
          graph_id: `graph_${Date.now()}`
        })
      });

      const result = await response.json();
      if (result.status === 'success') {
        setMessage(`Graph created: ${result.node_count} nodes, ${result.edge_count} edges`);
        setSelectedGraphId(result.graph_id);
        await loadGraphs();
      }
    } catch (error) {
      setMessage(`Error creating graph: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleOrchestrate = async () => {
    if (!selectedGraphId) {
      setMessage('Please create or select a graph first');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/orchestrate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          graph_id: selectedGraphId,
          parent_task: 'Build software from requirements',
          parent_task_id: `parent_${Date.now()}`
        })
      });

      const result = await response.json();
      if (result.status === 'success') {
        setTasks(result.tasks || []);
        setMessage(`Generated ${result.task_count} sub-agent tasks`);
        setActiveTab('tasks');
      }
    } catch (error) {
      setMessage(`Error generating tasks: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🧠 Knowledge Graph Agent Orchestrator</h1>
        <p>Upload requirements → Create semantic graph → Assign sub-agents</p>
      </header>

      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}

      <div className="tabs">
        <button
          className={`tab-button ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          📄 Documents
        </button>
        <button
          className={`tab-button ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          📊 Graph
        </button>
        <button
          className={`tab-button ${activeTab === 'tasks' ? 'active' : ''}`}
          onClick={() => setActiveTab('tasks')}
        >
          🎯 Tasks
        </button>
        <button
          className={`tab-button ${activeTab === 'analyze' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyze')}
        >
          🔍 Analyze
        </button>
      </div>

      <div className="content">
        {activeTab === 'upload' && (
          <div className="tab-content">
            <DocumentUpload onUploaded={handleDocumentUploaded} apiUrl={API_URL} />
            <div className="document-list">
              <h2>Uploaded Documents ({documents.length})</h2>
              {documents.length > 0 ? (
                <ul>
                  {documents.map((doc) => (
                    <li key={doc.filename}>
                      {doc.filename} ({(doc.size / 1024).toFixed(2)} KB)
                    </li>
                  ))}
                </ul>
              ) : (
                <p>No documents uploaded yet</p>
              )}
            </div>
            <div className="action-buttons">
              <button
                onClick={handleCreateGraph}
                disabled={loading || documents.length === 0}
                className="btn btn-primary"
              >
                {loading ? 'Creating Graph...' : '✨ Create Knowledge Graph'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'graph' && (
          <div className="tab-content">
            <div className="graph-selector">
              <h2>Available Graphs</h2>
              {graphs.length > 0 ? (
                <div className="graph-list">
                  {graphs.map((graph) => (
                    <div
                      key={graph.graph_id}
                      className={`graph-item ${selectedGraphId === graph.graph_id ? 'selected' : ''}`}
                      onClick={() => setSelectedGraphId(graph.graph_id)}
                    >
                      <h3>{graph.graph_id}</h3>
                      <p>
                        {graph.node_count} nodes | {graph.edge_count} edges | {graph.cluster_count} clusters
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p>No graphs created yet</p>
              )}
            </div>

            {selectedGraphId && (
              <div className="graph-display">
                <h2>Graph: {selectedGraphId}</h2>
                <GraphVisualizer graphId={selectedGraphId} apiUrl={API_URL} />
              </div>
            )}

            <div className="action-buttons">
              <button
                onClick={handleOrchestrate}
                disabled={loading || !selectedGraphId}
                className="btn btn-primary"
              >
                {loading ? 'Generating Tasks...' : '🚀 Generate Sub-Agent Tasks'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'tasks' && (
          <div className="tab-content">
            <TaskList tasks={tasks} apiUrl={API_URL} />
          </div>
        )}

        {activeTab === 'analyze' && (
          <div className="tab-content">
            <AnalysisPanel apiUrl={API_URL} />
          </div>
        )}
      </div>

      <footer className="App-footer">
        <p>Knowledge Graph MCP System | Orchestrating Multi-Agent Workflows</p>
      </footer>
    </div>
  );
}

export default App;
