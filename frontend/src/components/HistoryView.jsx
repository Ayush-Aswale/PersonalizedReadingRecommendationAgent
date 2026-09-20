import { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';
import { api } from '../api';

const HistoryView = ({ userId, showToast }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    setLoading(true);
    const { data, error } = await api.getHistory(userId);
    if (error) {
      showToast(error, 'error');
    } else {
      setHistory(data || []);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadHistory();
  }, [userId]);

  if (loading) {
    return <div className="view-loading">Loading history...</div>;
  }

  if (history.length === 0) {
    return (
      <div className="empty-view">
        <Clock size={48} className="empty-icon" />
        <h2>No Reading History</h2>
        <p>Books you mark as read will appear here.</p>
      </div>
    );
  }

  return (
    <div className="view-container">
      <h2>Your Reading History ({history.length})</h2>
      <div className="history-list">
        {history.map((record, i) => (
          <div key={i} className="history-item">
            <div className="history-details">
              <h4>{record.title}</h4>
              <p className="history-meta">
                Status: {record.status}
                {record.rated && ` • Rating: ${record.rated}/5`}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default HistoryView;
