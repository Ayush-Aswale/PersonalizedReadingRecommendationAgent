import { useState, useEffect } from 'react';
import Onboarding from './components/Onboarding';
import Layout from './components/Layout';
import ChatPanel from './components/ChatPanel';
import RecommendationGallery from './components/RecommendationGallery';
import FavoritesView from './components/FavoritesView';
import HistoryView from './components/HistoryView';
import ProfileEditModal from './components/ProfileEditModal';
import { api } from './api';
import './App.css';

function App() {
  const [userId, setUserId] = useState(null);
  const [users, setUsers] = useState([]);
  const [profile, setProfile] = useState(null);
  const [displayName, setDisplayName] = useState('');
  
  const [recommendations, setRecommendations] = useState([]);
  const [historyCount, setHistoryCount] = useState(0);
  const [favoritesCount, setFavoritesCount] = useState(0);
  
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard', 'favorites', 'history'
  
  // Toast state
  const [toast, setToast] = useState({ message: '', type: '', visible: false });

  const showToast = (message, type = 'info') => {
    setToast({ message, type, visible: true });
    setTimeout(() => setToast(prev => ({ ...prev, visible: false })), 3000);
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    if (userId) {
      loadUserData();
    }
  }, [userId]);

  const loadUserData = async () => {
    setProfile(null);
    setRecommendations([]);
    setHistoryCount(0);
    setFavoritesCount(0);
    setCurrentView('dashboard');
    
    await fetchProfile();
    await updateCounts();
  };

  const fetchUsers = async () => {
    setLoading(true);
    const { data, error } = await api.getUsers();
    if (error) {
      showToast(error, 'error');
    } else {
      setUsers(data || []);
      if (data && data.length > 0) {
        setUserId(data[0].user_id);
        setDisplayName(data[0].display_name);
      } else {
        setShowOnboarding(true);
      }
    }
    setLoading(false);
  };

  const fetchProfile = async () => {
    const { data, error } = await api.getProfile(userId);
    if (!error && data) {
      setProfile(data);
    }
  };

  const updateCounts = async () => {
    const [{ data: hData }, { data: fData }] = await Promise.all([
      api.getHistory(userId),
      api.getFavorites(userId)
    ]);
    if (hData) setHistoryCount(hData.length);
    if (fData) setFavoritesCount(fData.length);
  };

  const handleProfileCreated = (newUser) => {
    setUserId(newUser.user_id);
    setDisplayName(newUser.display_name);
    setShowOnboarding(false);
    fetchUsers();
  };

  const handleSwitchUser = (uid) => {
    if (uid === userId) return;
    const user = users.find(u => u.user_id === uid);
    setUserId(uid);
    setDisplayName(user?.display_name || uid);
  };

  const handleRecommendationsUpdate = (newRecs) => {
    if (newRecs && newRecs.length > 0) {
      setRecommendations(newRecs);
    }
  };

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner"></div>
        <p>Loading ReadRec.ai...</p>
      </div>
    );
  }

  if (showOnboarding || !userId) {
    return (
      <Onboarding
        onComplete={handleProfileCreated}
        onSkip={users.length > 0 ? () => {
          setShowOnboarding(false);
          setUserId(users[0].user_id);
          setDisplayName(users[0].display_name);
        } : null}
        showToast={showToast}
      />
    );
  }

  return (
    <>
      <Layout
        userId={userId}
        displayName={displayName}
        users={users}
        onSwitchUser={handleSwitchUser}
        onCreateNew={() => setShowOnboarding(true)}
        profile={profile}
        onEditProfile={() => setShowEditProfile(true)}
        onProfileUpdate={fetchProfile}
        historyCount={historyCount}
        favoritesCount={favoritesCount}
        currentView={currentView}
        onNavigate={setCurrentView}
        showToast={showToast}
      >
        <div className="dashboard-content">
          <div className="main-area">
            {currentView === 'dashboard' && (
              <RecommendationGallery
                recommendations={recommendations}
                userId={userId}
                onActionComplete={updateCounts}
                showToast={showToast}
              />
            )}
            {currentView === 'favorites' && (
              <FavoritesView
                userId={userId}
                onActionComplete={updateCounts}
                showToast={showToast}
              />
            )}
            {currentView === 'history' && (
              <HistoryView
                userId={userId}
                showToast={showToast}
              />
            )}
          </div>
          {currentView === 'dashboard' && (
            <div className="side-area">
              <ChatPanel
                userId={userId}
                onRecommendationsUpdate={handleRecommendationsUpdate}
                showToast={showToast}
              />
            </div>
          )}
        </div>
      </Layout>

      {showEditProfile && (
        <ProfileEditModal
          userId={userId}
          profile={profile}
          onSave={() => {
            setShowEditProfile(false);
            fetchProfile();
            showToast('Profile updated successfully', 'success');
          }}
          onClose={() => setShowEditProfile(false)}
          showToast={showToast}
        />
      )}

      {/* Global Toast */}
      {toast.visible && (
        <div className={`global-toast ${toast.type}`}>
          {toast.message}
        </div>
      )}
    </>
  );
}

export default App;
