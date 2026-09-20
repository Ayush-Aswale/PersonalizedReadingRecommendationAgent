import { useState, useEffect } from 'react';
import { Bookmark, AlertCircle } from 'lucide-react';
import { api } from '../api';
import RecommendationCard from './RecommendationCard';

const FavoritesView = ({ userId, onActionComplete, showToast }) => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadFavorites = async () => {
    setLoading(true);
    const { data, error } = await api.getFavorites(userId);
    if (error) {
      showToast(error, 'error');
    } else {
      setFavorites(data || []);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadFavorites();
  }, [userId]);

  const handleCardAction = () => {
    onActionComplete();
    loadFavorites(); // Refresh local list just in case
  };

  if (loading) {
    return <div className="view-loading">Loading favorites...</div>;
  }

  if (favorites.length === 0) {
    return (
      <div className="empty-view">
        <Bookmark size={48} className="empty-icon" />
        <h2>No Favorites Yet</h2>
        <p>Books you mark as favorite will appear here.</p>
      </div>
    );
  }

  return (
    <div className="view-container">
      <h2>Your Favorite Books ({favorites.length})</h2>
      <div className="gallery-grid">
        {favorites.map((book) => (
          <RecommendationCard
            key={book.book_id}
            book={book}
            userId={userId}
            onActionComplete={handleCardAction}
            showToast={showToast}
          />
        ))}
      </div>
    </div>
  );
};

export default FavoritesView;
