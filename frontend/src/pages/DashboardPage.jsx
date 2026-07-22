import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertCircle, ArrowRight, Leaf, Microscope, Trees, TrendingUp } from 'lucide-react';
import { getPredictionHistory, listFarms, healthCheck } from '../services/api';

export default function DashboardPage() {
  const [farms, setFarms] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const load = async () => {
      try {
        const [farmsResponse, historyResponse, healthResponse] = await Promise.all([
          listFarms(),
          getPredictionHistory(1, 5),
          healthCheck(),
        ]);
        setFarms(farmsResponse.data || []);
        setHistory(historyResponse.data?.items || []);
        setHealth(healthResponse.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const latestAnalysis = history[0];

  const summary = useMemo(() => ({
    farms: farms.length,
    analyses: history.length,
    latest: latestAnalysis,
  }), [farms.length, history.length, latestAnalysis]);

  return (
    <section className="dashboard-page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h1>Farmer operations dashboard</h1>
        </div>
        <Link to="/analyze" className="primary-btn">Start new analysis</Link>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {loading ? (
        <div className="panel loading-panel">Loading dashboard…</div>
      ) : (
        <>
          <div className="stats-grid">
            <article className="panel stat-card">
              <div className="stat-icon green"><Trees size={20} /></div>
              <div>
                <h3>{summary.farms}</h3>
                <p>Registered farms</p>
              </div>
            </article>
            <article className="panel stat-card">
              <div className="stat-icon blue"><Microscope size={20} /></div>
              <div>
                <h3>{summary.analyses}</h3>
                <p>Recent analyses</p>
              </div>
            </article>
            <article className="panel stat-card">
              <div className="stat-icon amber"><TrendingUp size={20} /></div>
              <div>
                <h3>{health?.status || 'Unknown'}</h3>
                <p>Backend status</p>
              </div>
            </article>
          </div>

          <div className="content-grid">
            <section className="panel">
              <div className="section-heading">
                <h2>Latest analysis</h2>
                <Link to="/history">View all <ArrowRight size={16} /></Link>
              </div>
              {summary.latest ? (
                <div className="card-list">
                  <div className="list-item large">
                    <div>
                      <h3>{summary.latest.primary_disease || 'Disease review'}</h3>
                      <p>{summary.latest.primary_plant || 'Crop'} · {new Date(summary.latest.created_at).toLocaleString()}</p>
                    </div>
                    <span>{summary.latest.primary_confidence?.toFixed(1)}%</span>
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  <Leaf size={18} />
                  <p>No analyses yet. Upload your first crop image to get started.</p>
                </div>
              )}
            </section>

            <section className="panel">
              <div className="section-heading">
                <h2>Farms</h2>
                <Link to="/farms">Manage <ArrowRight size={16} /></Link>
              </div>
              {farms.length ? (
                <div className="card-list">
                  {farms.map((farm) => (
                    <div key={farm.id} className="list-item">
                      <div>
                        <h3>{farm.name}</h3>
                        <p>{farm.address || 'Location pending'}</p>
                      </div>
                      <span>{farm.location_lat ? `${farm.location_lat.toFixed(2)}, ${farm.location_lon.toFixed(2)}` : 'No coordinates'}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <AlertCircle size={18} />
                  <p>No farms yet. Create a farm to organize field analyses.</p>
                </div>
              )}
            </section>
          </div>
        </>
      )}
    </section>
  );
}
