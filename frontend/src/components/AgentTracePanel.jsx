import { useState } from 'react';
import { ChevronDown, ChevronRight, Activity, Terminal } from 'lucide-react';

const AgentTracePanel = ({ trace }) => {
  const [expanded, setExpanded] = useState(false);

  if (!trace || trace.length === 0) return null;

  return (
    <div className="agent-trace-panel">
      <button 
        className="trace-toggle" 
        onClick={() => setExpanded(!expanded)}
      >
        <Activity size={14} />
        <span>Agent Activity ({trace.length} tool calls)</span>
        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      
      {expanded && (
        <div className="trace-content">
          {trace.map((t, idx) => (
            <div key={idx} className="trace-item">
              <div className="trace-header">
                <Terminal size={12} />
                <span className="tool-name">{t.tool}</span>
                <span className={`status-badge ${t.status}`}>{t.status}</span>
              </div>
              <div className="trace-body">
                {t.input && <div className="trace-data"><strong>Input:</strong> <code>{t.input}</code></div>}
                {t.result && <div className="trace-data"><strong>Result:</strong> <code>{t.result}</code></div>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AgentTracePanel;
