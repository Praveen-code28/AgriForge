import { Link } from 'react-router-dom';
import { Activity, CloudSun, Leaf, ShieldCheck, Sparkles, UploadCloud } from 'lucide-react';

const features = [
  {
    title: 'Fast disease detection',
    description: 'Upload a crop image and get instant disease insights backed by the AgriForge model.',
    icon: UploadCloud,
  },
  {
    title: 'Weather-aware guidance',
    description: 'Review spray timing, plant stress, and weather risk in one place.',
    icon: CloudSun,
  },
  {
    title: 'Actionable recommendations',
    description: 'Receive treatment guidance and keep a living history of every analysis.',
    icon: ShieldCheck,
  },
];

export default function LandingPage() {
  return (
    <section className="hero-section">
      <div className="hero-copy">
        <p className="eyebrow">AI-powered precision agriculture</p>
        <h1>Turn field observations into fast, reliable farm decisions.</h1>
        <p className="hero-description">
          AgriForge helps farmers detect crop disease, review treatment options, and understand weather risks from a single dashboard.
        </p>
        <div className="hero-actions">
          <Link to="/register" className="primary-btn large">Get started</Link>
          <Link to="/login" className="secondary-btn large">Sign in</Link>
        </div>
      </div>

      <div className="hero-card">
        <div className="hero-card-header">
          <Sparkles size={18} />
          <span>What you can do</span>
        </div>
        <div className="hero-metrics">
          <div className="metric-card">
            <Activity size={20} />
            <strong>Analysis</strong>
            <span>Upload images and get instant results.</span>
          </div>
          <div className="metric-card">
            <Leaf size={20} />
            <strong>Farm records</strong>
            <span>Organize farms and keep every prediction together.</span>
          </div>
        </div>
      </div>

      <div className="feature-grid">
        {features.map(({ title, description, icon: Icon }) => (
          <article key={title} className="panel feature-card">
            <Icon size={20} />
            <h3>{title}</h3>
            <p>{description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
