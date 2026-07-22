import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, LoaderCircle } from 'lucide-react';
import { getCurrentUser, loginUser, registerUser } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function RegisterPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirmPassword: '' });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await registerUser({ full_name: form.full_name, email: form.email, password: form.password });
      const response = await loginUser({ email: form.email, password: form.password });
      const token = response.data.access_token;
      login(token, null);
      const userResponse = await getCurrentUser();
      login(token, userResponse.data);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to create your account right now.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="auth-section">
      <div className="panel auth-panel">
        <p className="eyebrow">Join AgriForge</p>
        <h1>Create your account</h1>
        <p className="auth-subtitle">Start tracking farms, uploading crop images, and reviewing diagnosis history.</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && <div className="error-banner">{error}</div>}

          <label>
            Full name
            <input type="text" name="full_name" value={form.full_name} onChange={handleChange} required />
          </label>

          <label>
            Email
            <input type="email" name="email" value={form.email} onChange={handleChange} required />
          </label>

          <label>
            Password
            <div className="password-input">
              <input
                type={showPassword ? 'text' : 'password'}
                name="password"
                value={form.password}
                onChange={handleChange}
                required
              />
              <button type="button" className="icon-btn" onClick={() => setShowPassword((current) => !current)}>
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </label>

          <label>
            Confirm password
            <input type="password" name="confirmPassword" value={form.confirmPassword} onChange={handleChange} required />
          </label>

          <button type="submit" className="primary-btn wide" disabled={loading}>
            {loading ? <LoaderCircle className="spinner" size={18} /> : 'Create account'}
          </button>
        </form>

        <p className="switch-copy">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </section>
  );
}
