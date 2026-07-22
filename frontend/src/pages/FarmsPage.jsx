import { useEffect, useState } from 'react';
import { PlusCircle, LoaderCircle } from 'lucide-react';
import { createFarm, listFarms } from '../services/api';

export default function FarmsPage() {
  const [farms, setFarms] = useState([]);
  const [form, setForm] = useState({ name: '', address: '', location_lat: '', location_lon: '' });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const loadFarms = async () => {
    try {
      const response = await listFarms();
      setFarms(response.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to load farms.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFarms();
  }, []);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');

    try {
      await createFarm({
        name: form.name,
        address: form.address || null,
        location_lat: form.location_lat ? Number(form.location_lat) : null,
        location_lon: form.location_lon ? Number(form.location_lon) : null,
      });
      setForm({ name: '', address: '', location_lat: '', location_lon: '' });
      await loadFarms();
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to create farm.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">Farms</p>
          <h1>Manage your production sites</h1>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="content-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <div className="section-heading">
            <h2>Add farm</h2>
          </div>
          <label>
            Farm name
            <input name="name" value={form.name} onChange={handleChange} required />
          </label>
          <label>
            Address
            <input name="address" value={form.address} onChange={handleChange} />
          </label>
          <div className="inline-fields">
            <label>
              Latitude
              <input name="location_lat" type="number" step="0.0001" value={form.location_lat} onChange={handleChange} />
            </label>
            <label>
              Longitude
              <input name="location_lon" type="number" step="0.0001" value={form.location_lon} onChange={handleChange} />
            </label>
          </div>
          <button type="submit" className="primary-btn" disabled={submitting}>
            {submitting ? <LoaderCircle className="spinner" size={18} /> : <><PlusCircle size={18} /> Add farm</>}
          </button>
        </form>

        <section className="panel">
          <div className="section-heading">
            <h2>Your farms</h2>
          </div>
          {loading ? (
            <div className="loading-panel">Loading farms…</div>
          ) : farms.length ? (
            <div className="card-list">
              {farms.map((farm) => (
                <div key={farm.id} className="list-item">
                  <div>
                    <h3>{farm.name}</h3>
                    <p>{farm.address || 'Address not provided'}</p>
                  </div>
                  <span>{farm.location_lat ? `${farm.location_lat.toFixed(2)}, ${farm.location_lon.toFixed(2)}` : 'No coordinates'}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">No farms yet. Add one to begin organizing your fields.</div>
          )}
        </section>
      </div>
    </section>
  );
}
