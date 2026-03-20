// components/SearchBar.jsx
import { useState } from 'react';
import { Search } from 'lucide-react';

const CUISINE_OPTIONS = [
  'All', 'American', 'Italian', 'French', 'Japanese', 'Thai',
  'Mediterranean', 'Greek', 'Burmese', 'Mexican', 'Indian', 'Chinese',
];

export default function SearchBar({ onSearch, initialValues = {} }) {
  const [keyword, setKeyword] = useState(initialValues.keyword || '');
  const [cuisine, setCuisine] = useState(initialValues.cuisine || '');
  const [city, setCity] = useState(initialValues.city || '');
  const [pricingTier, setPricingTier] = useState(initialValues.pricing_tier || '');

  const search = (overrides = {}) => {
    const filters = {
      keyword: keyword.trim(),
      cuisine: cuisine === 'All' ? '' : cuisine,
      city: city.trim(),
      pricing_tier: pricingTier ? parseInt(pricingTier) : '',
      ...overrides,
    };
    onSearch(filters);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    search();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="search-bar">
        <input
          type="text"
          className="form-input"
          placeholder="Search restaurants..."
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          id="search-keyword"
        />
        <button type="submit" className="btn btn-primary">
          <Search size={15} /> Search
        </button>
      </div>

      <div className="filters" style={{ marginTop: '16px' }}>
        <select
          className="filter-chip"
          value={cuisine}
          onChange={(e) => {
            const val = e.target.value;
            setCuisine(val);
            search({ cuisine: val === 'All' ? '' : val });
          }}
          style={{ background: 'var(--clr-bg-elevated)', border: '1px solid var(--clr-border)', color: 'var(--clr-text-secondary)', padding: '6px 16px', borderRadius: '9999px', fontSize: '0.8125rem' }}
          id="filter-cuisine"
        >
          <option value="">Cuisine</option>
          {CUISINE_OPTIONS.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <select
          className="filter-chip"
          value={pricingTier}
          onChange={(e) => {
            const val = e.target.value;
            setPricingTier(val);
            search({ pricing_tier: val ? parseInt(val) : '' });
          }}
          style={{ background: 'var(--clr-bg-elevated)', border: '1px solid var(--clr-border)', color: 'var(--clr-text-secondary)', padding: '6px 16px', borderRadius: '9999px', fontSize: '0.8125rem' }}
          id="filter-price"
        >
          <option value="">Price</option>
          <option value="1">$ (Budget)</option>
          <option value="2">$$ (Moderate)</option>
          <option value="3">$$$ (Upscale)</option>
          <option value="4">$$$$ (Fine Dining)</option>
        </select>

        <input
          type="text"
          className="filter-chip"
          placeholder="City..."
          value={city}
          onChange={(e) => setCity(e.target.value)}
          onBlur={() => search()}
          style={{ background: 'var(--clr-bg-elevated)', border: '1px solid var(--clr-border)', color: 'var(--clr-text-secondary)', padding: '6px 16px', borderRadius: '9999px', fontSize: '0.8125rem', width: '120px' }}
          id="filter-city"
        />
      </div>
    </form>
  );
}
