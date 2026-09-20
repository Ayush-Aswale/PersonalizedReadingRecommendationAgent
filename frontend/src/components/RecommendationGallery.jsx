import RecommendationCard from './RecommendationCard';
import { BookMarked } from 'lucide-react';

const RecommendationGallery = ({ recommendations, userId, onActionComplete }) => {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="empty-gallery">
        <BookMarked size={48} className="empty-icon" />
        <h2>No Recommendations Yet</h2>
        <p>Chat with the agent to get personalized reading suggestions!</p>
      </div>
    );
  }

  return (
    <div className="recommendation-gallery">
      <h2>Recommended For You</h2>
      <div className="gallery-grid">
        {recommendations.map((book) => (
          <RecommendationCard 
            key={book.book_id} 
            book={book} 
            userId={userId}
            onActionComplete={onActionComplete}
          />
        ))}
      </div>
    </div>
  );
};

export default RecommendationGallery;
