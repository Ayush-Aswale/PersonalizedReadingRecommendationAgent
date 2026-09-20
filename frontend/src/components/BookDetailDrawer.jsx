import { useState, useEffect } from 'react';
import { X, Book } from 'lucide-react';
import { api } from '../api';

const BookDetailDrawer = ({ bookId, onClose }) => {
  const [bookDetails, setBookDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetails = async () => {
      setLoading(true);
      const { data, error } = await api.getBookDetails(bookId);
      if (!error && data) {
        setBookDetails(data);
      } else {
        setBookDetails(null);
      }
      setLoading(false);
    };
    fetchDetails();
  }, [bookId]);

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}><X size={24} /></button>
        
        {loading ? (
          <div className="drawer-loading">Loading details...</div>
        ) : bookDetails ? (
          <div className="book-full-details">
            <div className="drawer-header">
              <Book size={32} />
              <h2>{bookDetails.title}</h2>
              <h3>by {bookDetails.author}</h3>
            </div>
            
            <div className="drawer-meta">
              <p><strong>Genre:</strong> {bookDetails.genre}</p>
              <p><strong>Pages:</strong> {bookDetails.pages}</p>
              <p><strong>Rating:</strong> {bookDetails.avg_rating} / 5</p>
              <p><strong>Year:</strong> {bookDetails.published_year}</p>
            </div>
            
            <div className="drawer-description">
              <h4>Description</h4>
              <p>{bookDetails.description}</p>
            </div>
          </div>
        ) : (
          <div className="drawer-error">Could not load book details.</div>
        )}
      </div>
    </div>
  );
};

export default BookDetailDrawer;
