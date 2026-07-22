import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, LoaderCircle, UploadCloud } from 'lucide-react';
import { aiReport, analyzeWeather, completeAnalysis, getSupportedCrops, predictYield } from '../services/api';

const initialForm = {
  crop: 'tomato',
  disease: 'late_blight',
  confidence: '0.88',
  address: '',
  lat: '',
  lon: '',
  farm_id: '',
};

export default function AnalyzePage() {
  const [form, setForm] = useState(initialForm);
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState('');
  const [crops, setCrops] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [yieldResult, setYieldResult] = useState(null);

  useEffect(() => {
    const loadMeta = async () => {
      try {
        const response = await getSupportedCrops();
        const cropList = response.data?.crops || [];
        setCrops(cropList);
        if (cropList[0]) {
          setForm((current) => ({ ...current, crop: cropList[0].crop }));
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Unable to load crop metadata.');
      } finally {
        setLoading(false);
      }
    };

    loadMeta();
  }, []);

  const selectedCrop = useMemo(() => crops.find((item) => item.crop === form.crop) || null, [crops, form.crop]);

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
      const [analysisResponse, weatherResponse, yieldResponse] = await Promise.all([
        completeAnalysis(submitData),
        analyzeWeather({
          crop: form.crop,
          disease: form.disease,
          confidence: Number(form.confidence || 0.8),
          lat: form.lat ? Number(form.lat) : null,
          lon: form.lon ? Number(form.lon) : null,
          address: form.address || null,
        }),
        predictYield({
          crop: form.crop,
          soil_ph: 6.2,
          nitrogen: 120,
          phosphorus: 45,
          potassium: 180,
        }),
      ]);

      const reportResponse = await aiReport(submitData);
      setResult({ analysis: analysisResponse.data, weather: weatherResponse.data, report: reportResponse.data });
      setYieldResult(yieldResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <section className="page-stack">
      <div className="page-header">
        <div>
          <p className="eyebrow">AI analysis</p>
          <h1>Upload a crop image and review insights</h1>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading ? (
        <div className="panel loading-panel">Loading crop support data…</div>
      ) : (
        <div className="content-grid wide-grid">
          <form className="panel form-panel" onSubmit={handleSubmit}>
            <div className="section-heading">
              <h2>Analysis form</h2>
            </div>

            <label>
              Crop
              <select name="crop" value={form.crop} onChange={handleChange}>
                {crops.map((crop) => (
                  <option key={crop.crop} value={crop.crop}>{crop.crop}</option>
                ))}
              </select>
            </label>

            <label>
              Disease
              <input name="disease" value={form.disease} onChange={handleChange} required />
            </label>

            <label>
              Confidence
              <input name="confidence" type="number" min="0" max="1" step="0.01" value={form.confidence} onChange={handleChange} required />
            </label>

            <label>
              Address
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
                  <h3>Primary disease</h3>
                  <p>{result.analysis?.disease?.primary_disease || 'Pending'}</p>
                  <span>Confidence: {result.analysis?.disease?.primary_confidence?.toFixed(2) || 'n/a'}</span>
                </div>
                <div className="result-card">
                  <h3>Treatment</h3>
                  <p>{result.analysis?.treatment?.recommendation || 'No recommendation available.'}</p>
                </div>
                <div className="result-card">
                  <h3>Weather</h3>
                  <p>{result.weather?.summary || 'Weather analysis unavailable.'}</p>
                </div>
                {yieldResult && (
                  <div className="result-card">
                    <h3>Yield outlook</h3>
                    <p>{yieldResult.estimated_yield} t/ha · {yieldResult.risk_assessment}</p>
                    <span>Confidence: {yieldResult.confidence}%</span>
                  </div>
                )}
                {selectedCrop && (
                  <div className="result-card">
                    <h3>Supported diseases</h3>
                    <p>{selectedCrop.diseases.join(', ')}</p>
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
      )}
    </section>
  );
}
