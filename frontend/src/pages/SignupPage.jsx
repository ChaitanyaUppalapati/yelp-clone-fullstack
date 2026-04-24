// pages/SignupPage.jsx
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { registerUser, clearError } from '../store/authSlice';

const COUNTRY_OPTIONS = [
  'US', 'Canada', 'United Kingdom', 'Australia', 'Germany', 'France', 'Italy', 'Spain',
  'Japan', 'China', 'India', 'Brazil', 'Mexico', 'South Korea', 'Netherlands', 'Sweden',
  'Norway', 'Denmark', 'Switzerland', 'Singapore', 'New Zealand', 'South Africa',
  'Argentina', 'Chile', 'Portugal', 'Greece', 'Turkey', 'UAE', 'Saudi Arabia', 'Pakistan',
];

export default function SignupPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading, error: reduxError } = useSelector((state) => state.auth);

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'user',
    phone: '',
    city: '',
    state: '',
    country: 'US',
  });
  // Client-side validation lives in local state so it doesn't collide with the
  // async Redux error (which is cleared on mount/unmount).
  const [localError, setLocalError] = useState('');

  useEffect(() => {
    dispatch(clearError());
    return () => { dispatch(clearError()); };
  }, [dispatch]);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLocalError('');

    if (form.password !== form.confirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }
    if (form.password.length < 8) {
      setLocalError('Password must be at least 8 characters.');
      return;
    }

    const result = await dispatch(registerUser({
      name: form.name,
      email: form.email,
      password: form.password,
      role: form.role,
      phone: form.phone || undefined,
      city: form.city || undefined,
      state: form.state || undefined,
      country: form.country || undefined,
    }));
    if (registerUser.fulfilled.match(result)) {
      navigate('/login');
    }
  };

  const error = localError || reduxError;

  return (
    <div className="auth-page">
      <div className="auth-card fade-in-up" style={{ maxWidth: '500px' }}>
        <h1>Join YelpClone</h1>
        <p className="auth-subtitle">Create an account to find and review restaurants</p>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="signup-name">Full Name</label>
            <input id="signup-name" type="text" className="form-input" placeholder="Jane Doe"
              value={form.name} onChange={update('name')} required autoFocus />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-email">Email</label>
            <input id="signup-email" type="email" className="form-input" placeholder="you@example.com"
              value={form.email} onChange={update('email')} required />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="signup-password">Password</label>
              <input id="signup-password" type="password" className="form-input" placeholder="Min 8 characters"
                value={form.password} onChange={update('password')} required />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="signup-confirm">Confirm Password</label>
              <input id="signup-confirm" type="password" className="form-input" placeholder="Re-enter"
                value={form.confirmPassword} onChange={update('confirmPassword')} required />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-role">I am a…</label>
            <select id="signup-role" className="form-select" value={form.role} onChange={update('role')}>
              <option value="user">Restaurant Lover (User)</option>
              <option value="owner">Restaurant Owner</option>
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="signup-city">City</label>
              <input id="signup-city" type="text" className="form-input" placeholder="San Francisco"
                value={form.city} onChange={update('city')} />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="signup-state">State</label>
              <input id="signup-state" type="text" className="form-input" placeholder="CA"
                value={form.state} onChange={update('state')} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-country">Country</label>
            <select id="signup-country" className="form-select" value={form.country} onChange={update('country')}>
              <option value="">Select country</option>
              {COUNTRY_OPTIONS.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="signup-phone">Phone (optional)</label>
            <input id="signup-phone" type="tel" className="form-input" placeholder="(555) 123-4567"
              value={form.phone} onChange={update('phone')} />
          </div>

          <button type="submit" className="btn btn-primary btn-lg" disabled={loading}
            style={{ width: '100%', marginTop: '8px' }} id="signup-submit">
            {loading ? 'Creating Account…' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-divider">or</div>

        <p style={{ textAlign: 'center', color: 'var(--clr-text-secondary)', fontSize: '0.9375rem' }}>
          Already have an account? <Link to="/login" style={{ fontWeight: 600 }}>Log in</Link>
        </p>
      </div>
    </div>
  );
}
