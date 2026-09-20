import Header from './Header';
import Sidebar from './Sidebar';

const Layout = ({ 
  children, 
  userId, 
  displayName, 
  users, 
  onSwitchUser, 
  onCreateNew, 
  profile, 
  onEditProfile, 
  onProfileUpdate, 
  historyCount, 
  favoritesCount,
  currentView,
  onNavigate,
  showToast
}) => {
  return (
    <div className="layout-container">
      <Header
        userId={userId}
        displayName={displayName}
        users={users}
        onSwitchUser={onSwitchUser}
        onCreateNew={onCreateNew}
      />
      <div className="layout-body">
        <Sidebar
          userId={userId}
          displayName={displayName}
          profile={profile}
          onEditProfile={onEditProfile}
          onProfileUpdate={onProfileUpdate}
          historyCount={historyCount}
          favoritesCount={favoritesCount}
          currentView={currentView}
          onNavigate={onNavigate}
          showToast={showToast}
        />
        <main className="layout-main">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
