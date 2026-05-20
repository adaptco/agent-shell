import React, { useState } from 'react';

export default function AnalysisPanel({ apiUrl }) {
  const [text, setText] = useState('');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleAnalyze = async () => {
    if (!text.trim()) return;

    setLoading(true);
    try {
      const response = await fetch(`${apiUrl}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          context: 'manual_analysis'
        })
      });

      const result = await response.json();
      if (result.status === 'success') {
        setAnalysis(result);
      }
    } catch (error) {
      alert('Error analyzing text: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analysis-panel">
      <h2>🔍 Semantic Analysis</h2>

      <div className="analysis-input">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter text to analyze for semantic tokens and domain classification..."
          rows="8"
        />
        <button
          onClick={handleAnalyze}
          disabled={loading || !text.trim()}
          className="btn btn-primary"
        >
          {loading ? 'Analyzing...' : '🔍 Analyze'}
        </button>
      </div>

      {analysis && (
        <div className="analysis-results">
          <div className="result-section">
            <h3>Domain Classification</h3>
            <div className="domain-scores">
              {Object.entries(analysis.domains)
                .sort((a, b) => b[1] - a[1])
                .filter(([_, score]) => score > 0)
                .map(([domain, score]) => (
                  <div key={domain} className="domain-score">
                    <span className="domain-name">{domain}</span>
                    <div className="score-bar">
                      <div
                        className="score-fill"
                        style={{ width: `${score * 100}%` }}
                      />
                    </div>
                    <span className="score-value">{(score * 100).toFixed(1)}%</span>
                  </div>
                ))}
            </div>
          </div>

          <div className="result-section">
            <h3>Extracted Tokens ({analysis.token_count})</h3>
            <div className="tokens-list">
              {analysis.tokens.map((token, idx) => (
                <div key={idx} className="token-item">
                  <div className="token-text">{token.text}</div>
                  <div className="token-meta">
                    <span className="tf">TF: {token.term_frequency.toFixed(3)}</span>
                    <span className="context">{token.context.substring(0, 50)}...</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
