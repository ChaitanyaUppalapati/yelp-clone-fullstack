// pages/OwnerManagePage.jsx — Edit restaurant details
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { Save } from 'lucide-react';

const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];

export default function OwnerManagePage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [form, setForm] = useState(null);
  const [hours, setHours] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    api.get(`/restaurants/${id}`)
      .then((res) => {
        const r = res.data;
        setForm({
          name: r.name || '', cuisine_type: r.cuisine_type || '', description: r.description || '',
          address_line: r.address_line || '', city: r.city || '', state: r.state || '',
          zip_code: r.zip_code || '', phone: r.phone || '', website: r.website || '',
          email: r.email || '', pricing_tier: r.pricing_tier || 2,
        });
        setHours(r.hours_of_operation || {});
      })
      .catch(() => setMsg('Failed to load restaurant.'))
      .finally(() => setLoading(false));
  }, [id]);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMsg('');
    try {
      await api.put(`/owner/restaurants/${id}`, {
        ...form,
        pricing_tier: parseInt(form.pricing_tier),
        hours_of_operation: hours,
      });
      setMsg('Restaurant updated!');
      setTimeout(() => setMsg(''), 3000);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setMsg(Array.isArray(detail) ? detail.map((e) => e.msg).join(', ') : detail || 'Failed to update.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="page loading-center"><div className="spinner"></div></div>;
  if (!form) return <div className="page container"><div className="alert alert-error">{msg || 'Not found'}</div></div>;

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: '720px' }}>
        <div className="fade-in-up">
          <h1 style={{ marginBottom: 'var(--sp-xs)' }}>Manage Restaurant</h1>
          <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)' }}>Update your restaurant's information</p>

          {msg && <div className={`alert ${msg.includes('Failed') ? 'alert-error' : 'alert-success'}`}>{msg}</div>}

          <form onSubmit={handleSubmit}>
            <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
              <div className="card-body">
                <h3 style={{ marginBottom: 'var(--sp-md)', fontSize: '1rem' }}>Basic Info</h3>
                <div className="form-group">
                  <label className="form-label">Name</label>
                  <input className="form-input" value={form.name} onChange={update('name')} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">Cuisine</label>
                    <input className="form-input" value={form.cuisine_type} onChange={update('cuisine_type')} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Price Range</label>
                    <select className="form-select" value={form.pricing_tier} onChange={update('pricing_tier')}>
                      <option value={1}>$</option><option value={2}>$$</option>
                      <option value={3}>$$$</option><option value={4}>$$$$</option>
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea className="form-textarea" value={form.description} onChange={update('description')} rows={3} />
                </div>
              </div>
            </div>

            <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
              <div className="card-body">
                <h3 style={{ marginBottom: 'var(--sp-md)', fontSize: '1rem' }}>Location & Contact</h3>
                <div className="form-group">
                  <label className="form-label">Address</label>
                  <input className="form-input" value={form.address_line} onChange={update('address_line')} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">City</label>
                    <input className="form-input" value={form.city} onChange={update('city')} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">State</label>
                    <input className="form-input" value={form.state} onChange={update('state')} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">ZIP</label>
                    <input className="form-input" value={form.zip_code} onChange={update('zip_code')} />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label">Phone</label>
                    <input className="form-input" value={form.phone} onChange={update('phone')} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Website</label>
                    <input className="form-input" value={form.website} onChange={update('website')} />
                  </div>
                </div>
              </div>
            </div>

            <div className="card" style={{ marginBottom: 'var(--sp-xl)' }}>
              <div className="card-body">
                <h3 style={{ marginBottom: 'var(--sp-md)', fontSize: '1rem' }}>Hours</h3>
                <div style={{ display: 'grid', gap: '8px' }}>
                  {DAYS.map((day) => (
                    <div key={day} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ width: '80px', textTransform: 'capitalize', fontWeight: 500, fontSize: '0.875rem' }}>{day}</span>
                      <input className="form-input" placeholder="e.g. 11:00-22:00" value={hours[day] || ''}
                        onChange={(e) => setHours((h) => ({ ...h, [day]: e.target.value }))}
                        style={{ padding: '8px 12px', fontSize: '0.875rem' }} />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 'var(--sp-md)' }}>
              <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
                {saving ? 'Saving…' : <><Save size={15} /> Save Changes</>}
              </button>
              <button type="button" className="btn btn-ghost btn-lg" onClick={() => navigate('/owner/dashboard')}>Back</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
