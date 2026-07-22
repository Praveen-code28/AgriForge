import { useEffect, useState } from 'react';
import { AlertCircle, LoaderCircle, UploadCloud } from 'lucide-react';
import { aiReport, predictYield } from '../services/api';

const initialForm = {
  address: '',
  lat: '',
  lon: '',
  farm_id: '',
};

export default function AnalyzePage() {
  const [form, setForm] = useState(initialForm);
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [yieldResult, setYieldResult] = useState(null);
  const [locationStatus, setLocationStatus] = useState('Requesting location…');

  useEffect(() => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setLocationStatus('Location unavailable in this browser.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toString();
        const lon = position.coords.longitude.toString();
        setForm((current) => ({ ...current, lat, lon }));
        setLocationStatus('Location detected');
      },
      (geoError) => {
        let message = 'Location unavailable. You can still continue with address fallback.';
        if (geoError.code === 1) {
          message = 'Location permission denied. You can continue with address fallback.';
        } else if (geoError.code === 2) {
          message = 'Location unavailable. You can continue with address fallback.';
        } else if (geoError.code === 3) {
          message = 'Location request timed out. You can continue with address fallback.';
        }
        setLocationStatus(message);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }, []);

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setImage(file);
    setPreview(URL.createObjectURL(file));
  };

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!image) {
      setError('Please upload an image before running analysis.');
      return;
    }
    setSubmitting(true);
    setError('');
    setResult(null);
    setYieldResult(null);

    const submitData = new FormData();
    submitData.append('image', image);
    if (form.lat) {
      submitData.append('lat', form.lat);
    }
    if (form.lon) {
      submitData.append('lon', form.lon);
    }
    if (form.address) {
      submitData.append('address', form.address);
    }
    if (form.farm_id) {
      submitData.append('farm_id', form.farm_id);
    }

    try {
      const response = await aiReport(submitData);
      const crop = response.data?.combined?.crop || 'tomato';
      const yieldResponse = await predictYield({
        crop,
        soil_ph: 6.2,
        nitrogen: 120,
        phosphorus: 45,
        potassium: 180,
      });

      setResult({ report: response.data });
      setYieldResult(yieldResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const aiSummary = result?.report?.ai_report;
  const detectedDisease = aiSummary?.disease?.name || result?.report?.combined?.disease || 'Pending';
  const weatherImpact = aiSummary?.weather?.impact || result?.report?.weather?.weather_analysis?.risk || 'Weather analysis unavailable.';
  const riskLevel = aiSummary?.risk?.level || 'UNKNOWN';

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">AI analysis</p>
          <h1>Upload a crop image and review insights</h1>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="content-grid wide-grid">
        <form className="panel form-panel" onSubmit={handleSubmit}>
          <div className="section-heading">
            <h2>Analysis form</h2>
          </div>

          <div className="result-card" style={{ padding: '0.75rem 1rem', marginBottom: '1rem' }}>
            <strong>{locationStatus}</strong>
          </div>

          <label>
            Address (optional fallback)
            <input name="address" value={form.address} onChange={handleChange} />
          </label>

          <div className="inline-fields">
            <label>
              Latitude
              <input name="lat" type="number" step="0.0001" value={form.lat} onChange={handleChange} />
            </label>
            <label>
              Longitude
              <input name="lon" type="number" step="0.0001" value={form.lon} onChange={handleChange} />
            </label>
          </div>

          <label>
            Farm ID
            <input name="farm_id" type="number" value={form.farm_id} onChange={handleChange} />
          </label>

          <label className="upload-box">
            <span>Upload image</span>
            <input type="file" accept="image/*" onChange={handleFileChange} />
            {preview ? <img src={preview} alt="Upload preview" className="preview-image" /> : <UploadCloud size={40} />}
          </label>

          <button type="submit" className="primary-btn" disabled={submitting}>
            {submitting ? <LoaderCircle className="spinner" size={18} /> : 'Run analysis'}
          </button>
        </form>

        <div className="panel result-panel">
          <div className="section-heading">
            <h2>Results</h2>
          </div>
          {result ? (
            <div className="result-stack">
              <div className="result-card">
                <h3>Detected problem</h3>
                <p>{detectedDisease}</p>
              </div>
              <div className="result-card">
                <h3>Weather impact</h3>
                <p>{weatherImpact}</p>
              </div>
              <div className="result-card">
                <h3>Risk level</h3>
                <p>{riskLevel}</p>
              </div>
              <div className="result-card">
                <h3>Recommended treatment</h3>
                <p>
                  {(aiSummary?.treatment?.immediate_actions || []).join(' • ') || result?.report?.treatment?.farmer_advice || 'No recommendation available.'}
                </p>
              </div>
              <div className="result-card">
                <h3>Prevention & maintenance</h3>
                <p>
                  {(aiSummary?.treatment?.preventive_measures || aiSummary?.maintenance || []).join(' • ') || 'Keep field observations regular and follow local guidance.'}
                </p>
              </div>
              <div className="result-card">
                <h3>What happens if untreated</h3>
                <p>{aiSummary?.if_untreated || 'Please consult a local agricultural extension officer immediately.'}</p>
              </div>
              {yieldResult && (
                <div className="result-card">
                  <h3>Yield outlook</h3>
                  <p>{yieldResult.estimated_yield} t/ha · {yieldResult.risk_assessment}</p>
                </div>
              )}
              {aiSummary?.sources?.length > 0 && (
                <div className="result-card">
                  <h3>Market insight</h3>
                  <p>Trusted references were included for this recommendation.</p>
                </div>
              )}
            </div>
          ) : (
            <div className="empty-state">
              <AlertCircle size={18} />
              <p>Results will appear here after analysis completes.</p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
