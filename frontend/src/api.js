/**
 * Centralized API client to ensure precise matching with Flask API contracts.
 * Matches endpoints in `api/app.py`.
 */

const API_BASE = '/api';

// Helper to handle standard response parsing
const request = async (url, options = {}) => {
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    // Handle non-JSON responses gracefully (e.g. 500 errors)
    let data;
    const text = await res.text();
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      data = { error: 'Invalid server response' };
    }

    if (!res.ok) {
      return { data: null, error: data.error || `HTTP ${res.status}` };
    }
    
    return { data, error: null };
  } catch (err) {
    return { data: null, error: err.message || 'Network error' };
  }
};

export const api = {
  // Users
  getUsers: () => request(`${API_BASE}/users`),
  createUser: (profileData) => request(`${API_BASE}/users`, {
    method: 'POST',
    body: JSON.stringify(profileData),
  }),

  // Profile
  getProfile: (userId) => request(`${API_BASE}/profile/${userId}`),
  updateProfile: (userId, updates) => request(`${API_BASE}/profile/${userId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  }),

  // Chat/Agent
  chat: (userId, message) => request(`${API_BASE}/chat`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, message }),
  }),

  // Books
  getBookDetails: (bookId) => request(`${API_BASE}/books/${bookId}`),

  // History
  getHistory: (userId) => request(`${API_BASE}/history/${userId}`),
  markAsRead: (userId, bookId, rating = null) => request(`${API_BASE}/mark-read`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, book_id: bookId, rating }),
  }),

  // Favorites
  getFavorites: (userId) => request(`${API_BASE}/favorites/${userId}`),
  addFavorite: (userId, bookId) => request(`${API_BASE}/favorites`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, book_id: bookId }),
  }),

  // Feedback
  addFeedback: (userId, bookId, sentiment, reason = null) => request(`${API_BASE}/feedback`, {
    method: 'POST',
    body: JSON.stringify({ user_id: userId, book_id: bookId, sentiment, reason }),
  }),
};
