import { useState } from 'react';
import { X } from 'lucide-react';
import { api } from '../api';

const GENRE_OPTIONS = [
  'Science Fiction', 'Fantasy', 'Mystery', 'Thriller', 'Romance',
  'Horror', 'Historical Fiction', 'Literary Fiction', 'Non-Fiction',
  'Biography', 'Self-Help', 'Philosophy', 'Poetry', 'Adventure', 'Humor'
];

const ProfileEditModal = ({ userId, profile, onSave, onClose, showToast }) => {
  const [formData, setFormData] = useState({
    favorite_genres: profile?.favorite_genres || '',
    favorite_authors: profile?.favorite_authors || '',
    reading_level: profile?.reading_level || 'medium',
    preferred_length: profile?.preferred_length || 'medium',
    current_mood: profile?.current_mood || '',
  });
  const [saving, setSaving] = useState(false);

  const genreList = formData.favorite_genres
    ? formData.favorite_genres.split(',').map(g => g.trim()).filter(Boolean)
    : [];

  const toggleGenre = (genre) => {
    const updated = genreList.includes(genre)
      ? genreList.filter(g => g !== genre)
      : [...genreList, genre];
    setFormData({ ...formData, favorite_genres: updated.join(', ') });
  };

  const handleSave = async () => {
    setSaving(true);
    const { error } = await api.updateProfile(userId, formData);
    
    if (error) {
      if (showToast) showToast(error, 'error');
    } else {
      onSave();
    }
    
    setSaving(false);
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="edit-modal" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}><X size={24} /></button>
        <h2>Edit Profile</h2>
        
        <div className="edit-section">
          <label>Favorite Genres</label>
          <div className="genre-chips compact">
            {GENRE_OPTIONS.map(genre => (
              <button
                key={genre}
                className={`genre-chip ${genreList.includes(genre) ? 'selected' : ''}`}
                onClick={() => toggleGenre(genre)}
              >
                {genre}
              </button>
            ))}
          </div>
        </div>

        <div className="edit-section">
          <label>Favorite Authors</label>
          <input
            type="text"
            className="onboarding-input"
            value={formData.favorite_authors}
            onChange={(e) => setFormData({ ...formData, favorite_authors: e.target.value })}
            placeholder="e.g. Stephen King, J.K. Rowling..."
          />
        </div>

        <div className="edit-section">
          <label>Reading Level</label>
          <div className="option-row">
            {['easy', 'medium', 'hard'].map(v => (
              <button
                key={v}
                className={`option-pill ${formData.reading_level === v ? 'selected' : ''}`}
                onClick={() => setFormData({ ...formData, reading_level: v })}
              >
                {v === 'easy' ? 'Beginner' : v === 'medium' ? 'Intermediate' : 'Advanced'}
              </button>
            ))}
          </div>
        </div>

        <div className="edit-section">
          <label>Preferred Length</label>
          <div className="option-row">
            {['short', 'medium', 'long'].map(v => (
              <button
                key={v}
                className={`option-pill ${formData.preferred_length === v ? 'selected' : ''}`}
                onClick={() => setFormData({ ...formData, preferred_length: v })}
              >
                {v.charAt(0).toUpperCase() + v.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="edit-section">
          <label>Current Mood</label>
          <select
            value={formData.current_mood}
            onChange={(e) => setFormData({ ...formData, current_mood: e.target.value })}
            className="onboarding-input"
          >
            <option value="">Select mood...</option>
            <option value="adventurous">🗺️ Adventurous</option>
            <option value="relaxed">🌿 Relaxed</option>
            <option value="curious">🔬 Curious</option>
            <option value="romantic">💕 Romantic</option>
            <option value="dark">🌑 Dark</option>
            <option value="inspired">✨ Inspired</option>
          </select>
        </div>

        <div className="edit-actions">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProfileEditModal;
