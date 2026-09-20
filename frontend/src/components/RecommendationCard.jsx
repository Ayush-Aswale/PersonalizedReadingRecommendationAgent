import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Heart, CheckCircle, Info } from 'lucide-react';
import BookDetailDrawer from './BookDetailDrawer';
import { api } from '../api';

const RecommendationCard = ({ book, userId, onActionComplete, showToast }) => {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [loadingAction, setLoadingAction] = useState(null); // 'like', 'dislike', 'favorite', 'read'
  
  // Local state to prevent duplicate actions in the same session
  const [hasLiked, setHasLiked] = useState(false);
  const [hasDisliked, setHasDisliked] = useState(false);
  const [hasFavorited, setHasFavorited] = useState(false);
  const [hasRead, setHasRead] = useState(false);

  const handleFeedback = async (sentiment) => {
    if (loadingAction || (sentiment === 'like' && hasLiked) || (sentiment === 'dislike' && hasDisliked)) return;
    
    setLoadingAction(sentiment);
    const { error } = await api.addFeedback(userId, book.book_id, sentiment);
    
    if (error) {
      showToast(error, 'error');
    } else {
      if (sentiment === 'like') {
        setHasLiked(true);
        setHasDisliked(false);
      } else {
        setHasDisliked(true);
        setHasLiked(false);
      }
      showToast(`Book marked as ${sentiment}`, 'success');
      onActionComplete();
    }
    setLoadingAction(null);
  };

  const handleFavorite = async () => {
    if (loadingAction || hasFavorited) return;
    
    setLoadingAction('favorite');
    const { error } = await api.addFavorite(userId, book.book_id);
    
    if (error) {
      showToast(error, 'error');
    } else {
      setHasFavorited(true);
      showToast('Added to favorites', 'success');
      onActionComplete();
    }
    setLoadingAction(null);
  };

  const handleMarkRead = async () => {
    if (loadingAction || hasRead) return;
    
    setLoadingAction('read');
    const { error } = await api.markAsRead(userId, book.book_id, 5); // default 5 rating
    
    if (error) {
      showToast(error, 'error');
    } else {
      setHasRead(true);
      showToast('Marked as read', 'success');
      onActionComplete();
    }
    setLoadingAction(null);
  };

  return (
    <>
      <div className="recommendation-card">
        <div className="card-header">
          <h3>{book.title}</h3>
          <p className="author">by {book.author}</p>
        </div>
        <div className="card-meta">
          <span className="badge genre">{book.genre}</span>
          <span className="badge rating">★ {book.avg_rating}</span>
          <span className="badge pages">{book.pages} pages</span>
        </div>
        
        {book.match_reasons && (
          <div className="match-reasons">
            <p><strong>Why it matches:</strong> {book.match_reasons}</p>
          </div>
        )}
        
        <div className="card-actions">
          <button 
            onClick={() => handleFeedback('like')} 
            title="Like"
            disabled={loadingAction === 'like' || hasLiked}
            className={hasLiked ? 'active' : ''}
          >
            <ThumbsUp size={16} />
          </button>
          <button 
            onClick={() => handleFeedback('dislike')} 
            title="Dislike"
            disabled={loadingAction === 'dislike' || hasDisliked}
            className={hasDisliked ? 'active' : ''}
          >
            <ThumbsDown size={16} />
          </button>
          <button 
            onClick={handleFavorite} 
            title="Favorite"
            disabled={loadingAction === 'favorite' || hasFavorited}
            className={hasFavorited ? 'active' : ''}
          >
            <Heart size={16} />
          </button>
          <button 
            onClick={handleMarkRead} 
            title="Mark as Read"
            disabled={loadingAction === 'read' || hasRead}
            className={hasRead ? 'active' : ''}
          >
            <CheckCircle size={16} />
          </button>
          <button onClick={() => setDrawerOpen(true)} className="btn-details">
            <Info size={16} /> Details
          </button>
        </div>
      </div>
      
      {drawerOpen && (
        <BookDetailDrawer 
          bookId={book.book_id} 
          onClose={() => setDrawerOpen(false)} 
        />
      )}
    </>
  );
};

export default RecommendationCard;
