import { BookOpen, User, Plus } from 'lucide-react';

const Header = ({ userId, displayName, users, onSwitchUser, onCreateNew }) => {
  return (
    <header className="app-header">
      <div className="header-brand">
        <BookOpen className="brand-icon" size={28} />
        <h1>ReadRec.ai</h1>
      </div>
      <div className="header-right">
        <div className="header-user">
          <User size={18} />
          <select
            value={userId}
            onChange={(e) => onSwitchUser(e.target.value)}
            className="user-select"
          >
            {users.map(u => (
              <option key={u.user_id} value={u.user_id}>
                {u.display_name}
              </option>
            ))}
          </select>
        </div>
        <button className="btn-new-user" onClick={onCreateNew} title="Create New Profile">
          <Plus size={18} /> New Profile
        </button>
      </div>
    </header>
  );
};

export default Header;
