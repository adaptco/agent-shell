import React, { useEffect, useState } from 'react';

export default function GraphVisualizer({ graphId, apiUrl }) {
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadGraph();
  }, [graphId]);

  const loadGraph = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/graphs/${graphId}`);
      const data = await response.json();
      setGraph(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading graph...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!graph) return <div className="error">Graph not found</div>;

  return (
    <div className="graph-visualizer">
      <div className="graph-stats">
        <div className="stat">
          <span className="stat-label">Nodes:</span>
          <span className="stat-value">{graph.node_count}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Edges:</span>
          <span className="stat-value">{graph.edge_count}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Clusters:</span>
          <span className="stat-value">{graph.clusters.length}</span>
        </div>
      </div>

      <div className="nodes-container">
        <h3>Expertise Clusters</h3>
        <div className="nodes-list">
          {graph.nodes.map((node) => (
            <div key={node.id} className="node">
              <div className="node-label">{node.label}</div>
              <div className="node-meta">
                <span className="confidence">Confidence: {(node.confidence * 100).toFixed(0)}%</span>
                <span className="tokens">Tokens: {node.token_count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="edges-container">
        <h3>Relationships</h3>
        <div className="edges-list">
          {graph.edges.length > 0 ? (
            graph.edges.map((edge, idx) => (
              <div key={idx} className="edge">
                <span className="edge-source">{edge.source}</span>
                <span className="edge-arrow">→</span>
                <span className="edge-target">{edge.target}</span>
              </div>
            ))
          ) : (
            <p>No relationships</p>
          )}
        </div>
      </div>

      <svg className="graph-canvas" width="100%" height="400">
        <text x="50%" y="50%" textAnchor="middle" dy="0.3em" fill="#999">
          Graph visualization (D3.js integration coming soon)
        </text>
      </svg>
    </div>
  );
}
