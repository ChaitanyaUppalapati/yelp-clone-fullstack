// components/Navbar.jsx
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UtensilsCrossed, Heart, ClipboardList, BarChart2 } from 'lucide-react';

export default function Navbar() {
  const { isAuthenticated, isOwner, user, logout } = useAuth();
  const location = useLocation();

  const isActive = (path) => location.pathname === path ? 'navbar-link active' : 'navbar-link';

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="navbar-logo"><UtensilsCrossed size={20} /> Yelp</Link>

        <div className="navbar-links">
          <Link to="/" className={isActive('/')}>Explore</Link>

          {isAuthenticated ? (
            <>
              <Link to="/add-restaurant" className={isActive('/add-restaurant')}>
                + Add Restaurant
              </Link>
              <Link to="/favorites" className={isActive('/favorites')}>
                <Heart size={14} /> Favorites
              </Link>
              <Link to="/history" className={isActive('/history')}>
                <ClipboardList size={14} /> History
              </Link>
              <Link to="/profile" className={isActive('/profile')}>
                {user?.name || 'Profile'}
              </Link>
              {isOwner && (
                <Link to="/owner/dashboard" className={isActive('/owner/dashboard')}>
                  <BarChart2 size={14} /> Dashboard
                </Link>
              )}
              <button onClick={logout} className="navbar-link" style={{ cursor: 'pointer' }}>
                Logout
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className={isActive('/login')}>Log In</Link>
              <Link to="/signup" className="btn btn-primary btn-sm">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
