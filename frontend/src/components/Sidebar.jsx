import { Bookmark, Clock, User as UserIcon, Edit, Search } from 'lucide-react';
import { api } from '../api';

const Sidebar = ({ 
  userId, 
  displayName, 
  profile, 
  onEditProfile, 
  onProfileUpdate, 
  historyCount, 
  favoritesCount,
  currentView,
  onNavigate,
  showToast
}) => {
  const handleMoodChange = async (e) => {
    const mood = e.target.value;
    if (mood) {
      const { error } = await api.updateProfile(userId, { current_mood: mood });
      if (error) {
        showToast(error, 'error');
      } else {
        onProfileUpdate();
        showToast('Mood updated successfully', 'success');
      }
    }
  };

  return (
    <aside className="sidebar">
      {/* Profile Summary Card */}
      <div className="sidebar-section profile-card">
        <div className="profile-header">
          <div className="profile-avatar">
            {(displayName || 'U').charAt(0).toUpperCase()}
          </div>
          <div>
            <h2>{displayName || userId}</h2>
            <span className="profile-id">{userId}</span>
          </div>
        </div>

        <div className="profile-details">
          <div className="profile-tag-row">
            {profile?.favorite_genres
              ? profile.favorite_genres.split(',').slice(0, 3).map(g => (
                  <span key={g.trim()} className="profile-tag">{g.trim()}</span>
                ))
              : <span className="profile-tag muted">No genres set</span>
            }
          </div>
          <p><strong>Level:</strong> {profile?.reading_level || 'Not set'}</p>
          <p><strong>Length:</strong> {profile?.preferred_length || 'Not set'}</p>
          {profile?.current_mood && (
            <p><strong>Mood:</strong> {profile.current_mood}</p>
          )}
          <button className="btn-secondary edit-btn" onClick={onEditProfile}>
            <Edit size={14} /> Edit Profile
          </button>
        </div>
      </div>

      {/* Mood Picker */}
      <div className="sidebar-section mood-picker">
        <h3>Current Mood</h3>
        <select onChange={handleMoodChange} value={profile?.current_mood || ""}>
          <option value="">Select mood...</option>
          <option value="adventurous">🗺️ Adventurous</option>
          <option value="relaxed">🌿 Relaxed</option>
          <option value="curious">🔬 Curious</option>
          <option value="romantic">💕 Romantic</option>
          <option value="dark">🌑 Dark</option>
          <option value="inspired">✨ Inspired</option>
        </select>
      </div>

      {/* Navigation */}
      <div className="sidebar-section nav-links">
        <div 
          className={`nav-item ${currentView === 'dashboard' ? 'active' : ''}`}
          onClick={() => onNavigate('dashboard')}
        >
          <Search size={18} />
          <span>Recommendations</span>
        </div>
        <div 
          className={`nav-item ${currentView === 'favorites' ? 'active' : ''}`}
          onClick={() => onNavigate('favorites')}
        >
          <Bookmark size={18} />
          <span>Favorites ({favoritesCount})</span>
        </div>
        <div 
          className={`nav-item ${currentView === 'history' ? 'active' : ''}`}
          onClick={() => onNavigate('history')}
        >
          <Clock size={18} />
          <span>History ({historyCount})</span>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
