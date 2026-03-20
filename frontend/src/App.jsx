// App.jsx — Chaitanya (Frontend)
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ChatWidget from './components/ChatWidget';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import ExplorePage from './pages/ExplorePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import ProfilePage from './pages/ProfilePage';
import RestaurantDetailPage from './pages/RestaurantDetailPage';
import WriteReviewPage from './pages/WriteReviewPage';
import AddRestaurantPage from './pages/AddRestaurantPage';
import FavoritesPage from './pages/FavoritesPage';
import OwnerDashboardPage from './pages/OwnerDashboardPage';
import OwnerManagePage from './pages/OwnerManagePage';
import HistoryPage from './pages/HistoryPage';
import NotFoundPage from './pages/NotFoundPage';

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<ExplorePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/restaurants/:id" element={<RestaurantDetailPage />} />

        {/* Protected routes */}
        <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
        <Route path="/restaurants/:id/review" element={<ProtectedRoute><WriteReviewPage /></ProtectedRoute>} />
        <Route path="/add-restaurant" element={<ProtectedRoute><AddRestaurantPage /></ProtectedRoute>} />
        <Route path="/favorites" element={<ProtectedRoute><FavoritesPage /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />

        {/* Owner-only routes */}
        <Route path="/owner/dashboard" element={<ProtectedRoute ownerOnly><OwnerDashboardPage /></ProtectedRoute>} />
        <Route path="/owner/manage/:id" element={<ProtectedRoute ownerOnly><OwnerManagePage /></ProtectedRoute>} />

        {/* 404 */}
        <Route path="*" element={<NotFoundPage />} />
      </Routes>

      <ChatWidget />
    </>
  );
}

export default App;
