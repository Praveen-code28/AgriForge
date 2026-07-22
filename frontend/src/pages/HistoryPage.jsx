import { useEffect, useState } from 'react';
import { History as HistoryIcon } from 'lucide-react';
import { getPredictionHistory, getPredictionReport } from '../services/api';

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedReport, setSelectedReport] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await getPredictionHistory(1, 20);
        setItems(response.data?.items || []);
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load history.');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const handleSelect = async (predictionId) => {
    try {
      const response = await getPredictionReport(predictionId);
      setSelectedReport(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load report details.');
    }
  };

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">History</p>
          <h1>Review past analyses</h1>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="content-grid wide-grid">
        <section className="panel">
          <div className="section-heading">
            <h2>Recent predictions</h2>
          </div>
          {loading ? (
            <div className="loading-panel">Loading history…</div>
          ) : items.length ? (
            <div className="card-list">
              {items.map((item) => (
                <button key={item.id} type="button" className="history-item" onClick={() => handleSelect(item.id)}>
                  <div>
                    <h3>{item.primary_disease}</h3>
                    <p>{item.primary_plant} · {new Date(item.created_at).toLocaleString()}</p>
                  </div>
                  <span>{item.primary_confidence?.toFixed(1)}%</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="empty-state"><HistoryIcon size={18} /> No history yet.</div>
          )}
        </section>

        <section className="panel">
          <div className="section-heading">
            <h2>Report details</h2>
          </div>
          {selectedReport ? (
            <div className="result-stack">
              <div className="result-card">
                <h3>Combined analysis</h3>
                <p>{selectedReport.combined?.summary || 'No summary available.'}</p>
              </div>
              <div className="result-card">
                <h3>Treatment</h3>
                <p>{selectedReport.treatment?.recommendation || 'No treatment available.'}</p>
              </div>
              <div className="result-card">
                <h3>Weather</h3>
                <p>{selectedReport.weather?.summary || 'No weather summary.'}</p>
              </div>
            </div>
          ) : (
            <div className="empty-state">Select an item to inspect its report.</div>
          )}
        </section>
      </div>
    </section>
  );
}
