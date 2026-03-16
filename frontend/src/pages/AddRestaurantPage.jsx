// pages/AddRestaurantPage.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

const DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
const AMENITY_OPTIONS = ['wifi', 'parking', 'outdoor_seating', 'reservations', 'wheelchair_accessible', 'bar', 'live_music', 'takeout', 'delivery', 'valet_parking'];

export default function AddRestaurantPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: '', cuisine_type: '', description: '',
    address_line: '', city: '', state: '', zip_code: '', country: 'US',
    phone: '', website: '', email: '',
    pricing_tier: 2,
    amenities: [],
  });
  const [hours, setHours] = useState(
    Object.fromEntries(DAYS.map((d) => [d, '']))
  );
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const toggleAmenity = (amenity) => {
    setForm((f) => ({
      ...f,
      amenities: f.amenities.includes(amenity)
        ? f.amenities.filter((a) => a !== amenity)
        : [...f.amenities, amenity],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) { setError('Restaurant name is required.'); return; }
    setLoading(true);
    setError('');
    try {
      const payload = {
        ...form,
        pricing_tier: parseInt(form.pricing_tier),
        hours_of_operation: Object.fromEntries(
          DAYS.map((d) => [d, hours[d] || 'closed'])
        ),
      };
      // Remove empty strings
      Object.keys(payload).forEach((k) => {
        if (payload[k] === '') payload[k] = undefined;
      });
      const res = await api.post('/restaurants/', payload);
      navigate(`/restaurants/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to add restaurant.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: '720px' }}>
        <div className="fade-in-up">
          <h1 style={{ marginBottom: 'var(--sp-xs)' }}>Add a Restaurant</h1>
          <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)' }}>Share a great spot with the community</p>

          {error && <div className="alert alert-error">{error}</div>}

          <form onSubmit={handleSubmit}>
            {/* Basic Info */}
            <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
              <div className="card-body">
                <h3 style={{ marginBottom: 'var(--sp-md)', fontSize: '1rem' }}>Basic Info</h3>
                <div className="form-group">
                  <label className="form-label" htmlFor="r-name">Restaurant Name *</label>
                  <input id="r-name" className="form-input" placeholder="e.g. Bella Italia" value={form.name} onChange={update('name')} required />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="r-cuisine">Cuisine Type</label>
                    <input id="r-cuisine" className="form-input" placeholder="e.g. Italian" value={form.cuisine_type} onChange={update('cuisine_type')} />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="r-pricing">Price Range</label>
                    <select id="r-pricing" className="form-select" value={form.pricing_tier} onChange={update('pricing_tier')}>
                      <option value={1}>$ — Budget</option>
                      <option value={2}>$$ — Moderate</option>
                      <option value={3}>$$$ — Upscale</option>
                      <option value={4}>$$$$ — Fine Dining</option>
                    </select>
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label" htmlFor="r-desc">Description</label>
                  <textarea id="r-desc" className="form-textarea" placeholder="Tell people about this place…" value={form.description} onChange={update('description')} rows={3} />
                </div>
              </div>
            </div>

            {/* Location */}
            <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
              <div className="card-body">
                <h3 style={{ marginBottom: 'var(--sp-md)', fontSize: '1rem' }}>Location & Contact</h3>
                <div className="form-group">
                  <label className="form-label" htmlFor="r-address">Address</label>
                  <input id="r-address" className="form-input" placeholder="123 Main St" value={form.address_line} onChange={update('address_line')} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="r-city">City</label>
                    <input id="r-city" className="form-input" placeholder="San Francisco" value={form.city} onChange={update('city')} />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="r-state">State</label>
                    <input id="r-state" className="form-input" placeholder="CA" value={form.state} onChange={update('state')} />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="r-zip">ZIP</label>
                    <input id="r-zip" className="form-input" placeholder="94102" value={form.zip_code} onChange={update('zip_code')} />
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div className="form-group">
                    <label className="form-label" htmlFor="r-phone">Phone</label>
                    <input id="r-phone" className="form-input" placeholder="(415) 555-0123" value={form.phone} onChange={update('phone')} />
                  </div>
                  <div className="form-group">
                    <label className="form-label" htmlFor="r-website">Website</label>
                    <input id="r-website" className="form-input" placeholder="https://…" value={form.website} onChange={update('website')} />
                  </div>
                </div>
              </div>
            </div>

            {/* Hours */}
            <div className="card" style={{ marginBottom: 'var(--sp-lg)' }}>
              <div className="card-body">
                <h3 style={{ marginBottom: 'var(--sp-md)', fontSize: '1rem' }}>Hours of Operation</h3>
                <div style={{ display: 'grid', gap: '8px' }}>
                  {DAYS.map((day) => (
                    <div key={day} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span style={{ width: '80px', textTransform: 'capitalize', fontWeight: 500, fontSize: '0.875rem' }}>{day}</span>
                      <input
                        className="form-input"
                        placeholder="e.g. 11:00-22:00 or closed"
                        value={hours[day]}
                        onChange={(e) => setHours((h) => ({ ...h, [day]: e.target.value }))}
                        style={{ padding: '8px 12px', fontSize: '0.875rem' }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Amenities */}
            <div className="card" style={{ marginBottom: 'var(--sp-xl)' }}>
              <div className="card-body">
                <h3 style={{ marginBottom: 'var(--sp-md)', fontSize: '1rem' }}>Amenities</h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {AMENITY_OPTIONS.map((a) => (
                    <button
                      key={a}
                      type="button"
                      className={`filter-chip ${form.amenities.includes(a) ? 'active' : ''}`}
                      onClick={() => toggleAmenity(a)}
                    >
                      {a.replace(/_/g, ' ')}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 'var(--sp-md)' }}>
              <button type="submit" className="btn btn-primary btn-lg" disabled={loading} id="add-restaurant-submit">
                {loading ? 'Saving…' : '🏪 Add Restaurant'}
              </button>
              <button type="button" className="btn btn-ghost btn-lg" onClick={() => navigate(-1)}>Cancel</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
