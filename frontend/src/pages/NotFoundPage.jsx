// pages/NotFoundPage.jsx — 404 page
import { Link } from 'react-router-dom';
import { UtensilsCrossed, Home, Search } from 'lucide-react';

export default function NotFoundPage() {
  return (
    <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '70vh' }}>
      <div style={{ textAlign: 'center', maxWidth: '480px', padding: '0 var(--sp-lg)' }}>
        <div style={{ marginBottom: 'var(--sp-lg)', color: 'var(--clr-primary)' }}>
          <UtensilsCrossed size={72} strokeWidth={1.25} />
        </div>
        <h1 style={{ fontSize: '6rem', fontWeight: 800, lineHeight: 1, color: 'var(--clr-primary)', margin: 0 }}>404</h1>
        <h2 style={{ fontSize: '1.5rem', marginTop: 'var(--sp-sm)', marginBottom: 'var(--sp-sm)' }}>
          Page Not Found
        </h2>
        <p className="text-secondary" style={{ marginBottom: 'var(--sp-xl)', lineHeight: 1.6 }}>
          Looks like this table doesn&apos;t exist. The page you&apos;re looking for may have been moved or deleted.
        </p>
        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
          <Link to="/" className="btn btn-primary">
            <Home size={15} /> Go Home
          </Link>
          <Link to="/" className="btn btn-ghost">
            <Search size={15} /> Find Restaurants
          </Link>
        </div>
      </div>
    </div>
  );
}
