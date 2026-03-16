// pages/ProfilePage.jsx — Profile + Preferences tabs
import { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';

const CUISINE_OPTIONS = ['Italian', 'American', 'French', 'Japanese', 'Thai', 'Mediterranean', 'Greek', 'Mexican', 'Indian', 'Chinese', 'Burmese', 'Korean'];
const DIETARY_OPTIONS = ['vegan', 'vegetarian', 'gluten-free', 'halal', 'kosher', 'dairy-free'];
const AMBIANCE_OPTIONS = ['romantic', 'outdoor', 'family-friendly', 'trendy', 'casual', 'fine-dining', 'live-music'];

export default function ProfilePage() {
  const { user } = useAuth();
  const [tab, setTab] = useState('profile');

  // Profile state
  const [profile, setProfile] = useState({ name: '', phone: '', about_me: '', city: '', state: '', country: '', gender: '' });
  const [profileMsg, setProfileMsg] = useState('');
  const [profileLoading, setProfileLoading] = useState(false);

  // Preferences state
  const [prefs, setPrefs] = useState({
    cuisine_preferences: [], price_range: null, preferred_locations: [],
    search_radius: 10, dietary_needs: [], ambiance_preferences: [], sort_preference: 'rating',
  });
  const [prefsExist, setPrefsExist] = useState(false);
  const [prefsMsg, setPrefsMsg] = useState('');
  const [prefsLoading, setPrefsLoading] = useState(false);

  useEffect(() => {
    if (user) {
      setProfile({
        name: user.name || '', phone: user.phone || '', about_me: user.about_me || '',
        city: user.city || '', state: user.state || '', country: user.country || 'US', gender: user.gender || '',
      });
    }
    // Fetch preferences
    api.get('/users/me/preferences')
      .then((res) => { setPrefs(res.data); setPrefsExist(true); })
      .catch(() => setPrefsExist(false));
  }, [user]);

  const saveProfile = async (e) => {
    e.preventDefault();
    setProfileLoading(true);
    try {
      await api.put('/users/me', profile);
      setProfileMsg('Profile updated!');
      setTimeout(() => setProfileMsg(''), 3000);
    } catch { setProfileMsg('Failed to update.'); }
    finally { setProfileLoading(false); }
  };

  const savePrefs = async (e) => {
    e.preventDefault();
    setPrefsLoading(true);
    try {
      if (prefsExist) {
        await api.put('/users/me/preferences', prefs);
      } else {
        await api.post('/users/me/preferences', prefs);
        setPrefsExist(true);
      }
      setPrefsMsg('Preferences saved!');
      setTimeout(() => setPrefsMsg(''), 3000);
    } catch { setPrefsMsg('Failed to save.'); }
    finally { setPrefsLoading(false); }
  };

  const togglePrefArray = (field, val) => {
    setPrefs((p) => ({
      ...p,
      [field]: p[field]?.includes(val) ? p[field].filter((v) => v !== val) : [...(p[field] || []), val],
    }));
  };

  const initial = (user?.name || 'U').charAt(0).toUpperCase();

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: '720px' }}>
        {/* Header */}
        <div className="profile-header fade-in">
          <div className="profile-avatar">{initial}</div>
          <div>
            <h1 style={{ fontSize: '1.5rem' }}>{user?.name}</h1>
            <p className="text-secondary">{user?.email}</p>
            <span className="badge badge-primary" style={{ marginTop: '4px' }}>{user?.role}</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs">
          <button className={`tab ${tab === 'profile' ? 'active' : ''}`} onClick={() => setTab('profile')}>Profile</button>
          <button className={`tab ${tab === 'preferences' ? 'active' : ''}`} onClick={() => setTab('preferences')}>Preferences</button>
        </div>

        {/* Profile Tab */}
        {tab === 'profile' && (
          <form onSubmit={saveProfile} className="fade-in">
            {profileMsg && <div className={`alert ${profileMsg.includes('Failed') ? 'alert-error' : 'alert-success'}`}>{profileMsg}</div>}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Name</label>
                <input className="form-input" value={profile.name} onChange={(e) => setProfile((p) => ({ ...p, name: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Phone</label>
                <input className="form-input" value={profile.phone} onChange={(e) => setProfile((p) => ({ ...p, phone: e.target.value }))} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">About Me</label>
              <textarea className="form-textarea" value={profile.about_me} onChange={(e) => setProfile((p) => ({ ...p, about_me: e.target.value }))} rows={3} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">City</label>
                <input className="form-input" value={profile.city} onChange={(e) => setProfile((p) => ({ ...p, city: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">State</label>
                <input className="form-input" value={profile.state} onChange={(e) => setProfile((p) => ({ ...p, state: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Gender</label>
                <select className="form-select" value={profile.gender} onChange={(e) => setProfile((p) => ({ ...p, gender: e.target.value }))}>
                  <option value="">Prefer not to say</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="non-binary">Non-binary</option>
                </select>
              </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={profileLoading} style={{ marginTop: '8px' }}>
              {profileLoading ? 'Saving…' : 'Save Profile'}
            </button>
          </form>
        )}

        {/* Preferences Tab */}
        {tab === 'preferences' && (
          <form onSubmit={savePrefs} className="fade-in">
            {prefsMsg && <div className={`alert ${prefsMsg.includes('Failed') ? 'alert-error' : 'alert-success'}`}>{prefsMsg}</div>}

            <div className="form-group">
              <label className="form-label">Cuisine Preferences</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {CUISINE_OPTIONS.map((c) => (
                  <button key={c} type="button" className={`filter-chip ${prefs.cuisine_preferences?.includes(c) ? 'active' : ''}`}
                    onClick={() => togglePrefArray('cuisine_preferences', c)}>{c}</button>
                ))}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Price Range</label>
                <select className="form-select" value={prefs.price_range || ''} onChange={(e) => setPrefs((p) => ({ ...p, price_range: parseInt(e.target.value) || null }))}>
                  <option value="">Any</option>
                  <option value="1">$ Budget</option>
                  <option value="2">$$ Moderate</option>
                  <option value="3">$$$ Upscale</option>
                  <option value="4">$$$$ Fine Dining</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Sort By</label>
                <select className="form-select" value={prefs.sort_preference} onChange={(e) => setPrefs((p) => ({ ...p, sort_preference: e.target.value }))}>
                  <option value="rating">Rating</option>
                  <option value="distance">Distance</option>
                  <option value="price_asc">Price ↑</option>
                  <option value="price_desc">Price ↓</option>
                  <option value="most_reviewed">Most Reviewed</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Dietary Needs</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {DIETARY_OPTIONS.map((d) => (
                  <button key={d} type="button" className={`filter-chip ${prefs.dietary_needs?.includes(d) ? 'active' : ''}`}
                    onClick={() => togglePrefArray('dietary_needs', d)}>{d}</button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Ambiance</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {AMBIANCE_OPTIONS.map((a) => (
                  <button key={a} type="button" className={`filter-chip ${prefs.ambiance_preferences?.includes(a) ? 'active' : ''}`}
                    onClick={() => togglePrefArray('ambiance_preferences', a)}>{a}</button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Search Radius (miles)</label>
              <input type="number" className="form-input" style={{ maxWidth: '120px' }} value={prefs.search_radius || 10}
                onChange={(e) => setPrefs((p) => ({ ...p, search_radius: parseFloat(e.target.value) }))} min="1" max="100" />
            </div>

            <button type="submit" className="btn btn-primary" disabled={prefsLoading} style={{ marginTop: '8px' }}>
              {prefsLoading ? 'Saving…' : 'Save Preferences'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
