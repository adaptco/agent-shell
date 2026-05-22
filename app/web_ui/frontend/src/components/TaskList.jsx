import React from 'react';

export default function TaskList({ tasks, apiUrl }) {
  if (!tasks || tasks.length === 0) {
    return (
      <div className="task-list">
        <h2>🎯 Sub-Agent Tasks</h2>
        <p>Generate tasks by orchestrating a knowledge graph</p>
      </div>
    );
  }

  return (
    <div className="task-list">
      <h2>🎯 Generated Sub-Agent Tasks ({tasks.length})</h2>
      <div className="tasks-container">
        {tasks.map((item, idx) => {
          const task = item.task;
          const contract = item.delegation_contract;
          return (
            <div key={task.task_id} className="task-card">
              <div className="task-header">
                <div className="task-number">Task {idx + 1}</div>
                <div className="task-priority">
                  Priority: {(task.priority * 100).toFixed(0)}%
                </div>
              </div>

              <div className="task-details">
                <div className="detail">
                  <span className="label">Assigned Agent:</span>
                  <span className="value">{task.assigned_subagent}</span>
                </div>

                <div className="detail">
                  <span className="label">Description:</span>
                  <p className="value task-description">{task.task_description}</p>
                </div>

                <div className="detail">
                  <span className="label">Expertise Cluster:</span>
                  <span className="value">{task.expertise_cluster_id}</span>
                </div>

                <div className="detail">
                  <span className="label">Estimated Steps:</span>
                  <span className="value">{task.estimated_steps}</span>
                </div>

                <div className="detail">
                  <span className="label">Context Tokens:</span>
                  <div className="tokens">
                    {task.context_tokens.map((token, i) => (
                      <span key={i} className="token">{token}</span>
                    ))}
                  </div>
                </div>

                {task.dependencies.length > 0 && (
                  <div className="detail">
                    <span className="label">Dependencies:</span>
                    <div className="dependencies">
                      {task.dependencies.map((dep, i) => (
                        <span key={i} className="dependency">{dep}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="delegation-contract">
                <details>
                  <summary>Delegation Contract</summary>
                  <pre className="contract-json">
                    {JSON.stringify(contract, null, 2)}
                  </pre>
                </details>
              </div>

              <div className="task-actions">
                <button className="btn btn-small">
                  📤 Dispatch to Agent
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
