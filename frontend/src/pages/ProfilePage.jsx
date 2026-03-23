// pages/ProfilePage.jsx — Profile + Preferences tabs
import { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { Pencil } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const LANGUAGE_OPTIONS = ['English', 'Spanish', 'French', 'Mandarin', 'Hindi', 'Arabic', 'Portuguese', 'Japanese', 'Korean', 'German', 'Italian', 'Punjabi', 'Tagalog', 'Vietnamese'];
const CUISINE_OPTIONS = ['Italian', 'American', 'French', 'Japanese', 'Thai', 'Mediterranean', 'Greek', 'Mexican', 'Indian', 'Chinese', 'Burmese', 'Korean'];
const DIETARY_OPTIONS = ['vegan', 'vegetarian', 'gluten-free', 'halal', 'kosher', 'dairy-free'];
const AMBIANCE_OPTIONS = ['romantic', 'outdoor', 'family-friendly', 'trendy', 'casual', 'fine-dining', 'live-music'];
const COUNTRY_OPTIONS = [
  'US', 'Canada', 'United Kingdom', 'Australia', 'Germany', 'France', 'Italy', 'Spain',
  'Japan', 'China', 'India', 'Brazil', 'Mexico', 'South Korea', 'Netherlands', 'Sweden',
  'Norway', 'Denmark', 'Switzerland', 'Singapore', 'New Zealand', 'South Africa',
  'Argentina', 'Chile', 'Portugal', 'Greece', 'Turkey', 'UAE', 'Saudi Arabia', 'Pakistan',
];

export default function ProfilePage() {
  const { user } = useAuth();
  const [tab, setTab] = useState('profile');

  // Avatar state
  const [avatarUrl, setAvatarUrl] = useState(null);
  const [avatarUploading, setAvatarUploading] = useState(false);
  const [avatarMsg, setAvatarMsg] = useState('');
  const avatarInputRef = useRef(null);

  // Profile state
  const [profile, setProfile] = useState({ name: '', phone: '', about_me: '', city: '', state: '', country: '', gender: '', languages: [] });
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
        languages: user.languages || [],
      });
      setAvatarUrl(user.profile_picture ? `${API_BASE}${user.profile_picture}` : null);
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

  const uploadAvatar = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setAvatarUploading(true);
    setAvatarMsg('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await api.post('/users/me/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setAvatarUrl(`${API_BASE}${res.data.profile_picture}`);
      setAvatarMsg('Photo updated!');
      setTimeout(() => setAvatarMsg(''), 3000);
    } catch (err) {
      setAvatarMsg(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setAvatarUploading(false);
    }
  };

  const initial = (user?.name || 'U').charAt(0).toUpperCase();

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: '720px' }}>
        {/* Header */}
        <div className="profile-header fade-in">
          <div style={{ position: 'relative', flexShrink: 0 }}>
            {avatarUrl ? (
              <img
                src={avatarUrl}
                alt="Profile"
                style={{ width: '80px', height: '80px', borderRadius: '50%', objectFit: 'cover', border: '2px solid var(--clr-border)' }}
                onError={() => setAvatarUrl(null)}
              />
            ) : (
              <div className="profile-avatar">{initial}</div>
            )}
            <button
              type="button"
              onClick={() => avatarInputRef.current?.click()}
              disabled={avatarUploading}
              title="Change profile photo"
              style={{ position: 'absolute', bottom: 0, right: 0, background: 'var(--clr-primary)', border: 'none', borderRadius: '50%', width: '24px', height: '24px', cursor: 'pointer', fontSize: '0.75rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff' }}
            >
              {avatarUploading ? '…' : <Pencil size={12} />}
            </button>
            <input ref={avatarInputRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={uploadAvatar} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem' }}>{user?.name}</h1>
            <p className="text-secondary">{user?.email}</p>
            <span className="badge badge-primary" style={{ marginTop: '4px' }}>{user?.role}</span>
            {avatarMsg && <p style={{ fontSize: '0.8125rem', marginTop: '4px', color: avatarMsg.includes('failed') || avatarMsg.includes('Failed') ? 'var(--clr-error)' : 'var(--clr-success)' }}>{avatarMsg}</p>}
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
                <label className="form-label">Email</label>
                <input className="form-input" value={user?.email || ''} readOnly style={{ opacity: 0.6, cursor: 'not-allowed' }} title="Email cannot be changed" />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Phone</label>
                <input className="form-input" value={profile.phone} onChange={(e) => setProfile((p) => ({ ...p, phone: e.target.value }))} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">About Me</label>
              <textarea className="form-textarea" value={profile.about_me} onChange={(e) => setProfile((p) => ({ ...p, about_me: e.target.value }))} rows={3} />
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">City</label>
                <input className="form-input" value={profile.city} onChange={(e) => setProfile((p) => ({ ...p, city: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">State (abbrev.)</label>
                <input className="form-input" maxLength={3} placeholder="e.g. CA" value={profile.state} onChange={(e) => setProfile((p) => ({ ...p, state: e.target.value.toUpperCase() }))} />
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div className="form-group">
                <label className="form-label">Country</label>
                <select className="form-select" value={profile.country} onChange={(e) => setProfile((p) => ({ ...p, country: e.target.value }))}>
                  <option value="">Select country</option>
                  {COUNTRY_OPTIONS.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
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
            <div className="form-group">
              <label className="form-label">Languages</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {LANGUAGE_OPTIONS.map((lang) => (
                  <button key={lang} type="button"
                    className={`filter-chip ${profile.languages?.includes(lang) ? 'active' : ''}`}
                    onClick={() => setProfile((p) => ({
                      ...p,
                      languages: p.languages?.includes(lang)
                        ? p.languages.filter((l) => l !== lang)
                        : [...(p.languages || []), lang],
                    }))}>
                    {profile.languages?.includes(lang) ? '✓ ' : ''}{lang}
                  </button>
                ))}
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
                    onClick={() => togglePrefArray('cuisine_preferences', c)}>
                    {prefs.cuisine_preferences?.includes(c) ? '✓ ' : ''}{c}
                  </button>
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
                    onClick={() => togglePrefArray('dietary_needs', d)}>
                    {prefs.dietary_needs?.includes(d) ? '✓ ' : ''}{d}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Ambiance</label>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                {AMBIANCE_OPTIONS.map((a) => (
                  <button key={a} type="button" className={`filter-chip ${prefs.ambiance_preferences?.includes(a) ? 'active' : ''}`}
                    onClick={() => togglePrefArray('ambiance_preferences', a)}>
                    {prefs.ambiance_preferences?.includes(a) ? '✓ ' : ''}{a}
                  </button>
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
