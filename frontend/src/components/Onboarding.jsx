import { useState } from 'react';
import { BookOpen, Sparkles, ChevronRight } from 'lucide-react';
import { api } from '../api';

const GENRE_OPTIONS = [
  'Science Fiction', 'Fantasy', 'Mystery', 'Thriller', 'Romance',
  'Horror', 'Historical Fiction', 'Literary Fiction', 'Non-Fiction',
  'Biography', 'Self-Help', 'Philosophy', 'Poetry', 'Adventure', 'Humor'
];

const MOOD_OPTIONS = [
  { value: 'adventurous', label: '🗺️ Adventurous', desc: 'I want excitement and discovery' },
  { value: 'relaxed', label: '🌿 Relaxed', desc: 'Something easy and calming' },
  { value: 'curious', label: '🔬 Curious', desc: 'Teach me something new' },
  { value: 'romantic', label: '💕 Romantic', desc: 'I\'m in a love-story mood' },
  { value: 'dark', label: '🌑 Dark', desc: 'Give me something intense' },
  { value: 'inspired', label: '✨ Inspired', desc: 'I want to feel motivated' },
];

const Onboarding = ({ onComplete, onSkip, showToast }) => {
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({
    display_name: '',
    favorite_genres: [],
    favorite_authors: '',
    reading_level: '',
    preferred_length: '',
    current_mood: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const toggleGenre = (genre) => {
    setFormData(prev => ({
      ...prev,
      favorite_genres: prev.favorite_genres.includes(genre)
        ? prev.favorite_genres.filter(g => g !== genre)
        : [...prev.favorite_genres, genre]
    }));
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError('');
    
    const { data, error } = await api.createUser({
      display_name: formData.display_name,
      favorite_genres: formData.favorite_genres.join(', '),
      favorite_authors: formData.favorite_authors,
      reading_level: formData.reading_level,
      preferred_length: formData.preferred_length,
      current_mood: formData.current_mood,
    });
    
    if (error) {
      setError(error);
      if (showToast) showToast(error, 'error');
    } else {
      onComplete(data);
    }
    
    setSubmitting(false);
  };

  const canProceed = () => {
    switch (step) {
      case 0: return formData.display_name.trim().length >= 2;
      case 1: return formData.favorite_genres.length >= 1;
      case 2: return formData.reading_level !== '';
      case 3: return formData.preferred_length !== '';
      case 4: return true; // mood is optional
      default: return true;
    }
  };

  const steps = [
    // Step 0: Name
    <div className="onboarding-step" key="name">
      <h2>What should we call you?</h2>
      <p className="step-desc">Your name personalizes the reading experience.</p>
      <input
        type="text"
        className="onboarding-input"
        placeholder="Enter your name..."
        value={formData.display_name}
        onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
        autoFocus
      />
    </div>,

    // Step 1: Genres
    <div className="onboarding-step" key="genres">
      <h2>Pick your favorite genres</h2>
      <p className="step-desc">Select one or more genres you enjoy reading.</p>
      <div className="genre-chips">
        {GENRE_OPTIONS.map(genre => (
          <button
            key={genre}
            className={`genre-chip ${formData.favorite_genres.includes(genre) ? 'selected' : ''}`}
            onClick={() => toggleGenre(genre)}
          >
            {genre}
          </button>
        ))}
      </div>
    </div>,

    // Step 2: Reading level
    <div className="onboarding-step" key="level">
      <h2>What's your reading level?</h2>
      <p className="step-desc">This helps us match book complexity to your comfort.</p>
      <div className="option-cards">
        {[
          { value: 'easy', label: 'Beginner', desc: 'Light, accessible reads' },
          { value: 'medium', label: 'Intermediate', desc: 'Standard complexity' },
          { value: 'hard', label: 'Advanced', desc: 'Dense, challenging texts' },
        ].map(opt => (
          <button
            key={opt.value}
            className={`option-card ${formData.reading_level === opt.value ? 'selected' : ''}`}
            onClick={() => setFormData({ ...formData, reading_level: opt.value })}
          >
            <strong>{opt.label}</strong>
            <span>{opt.desc}</span>
          </button>
        ))}
      </div>
    </div>,

    // Step 3: Preferred length
    <div className="onboarding-step" key="length">
      <h2>How long do you like your books?</h2>
      <p className="step-desc">We'll prioritize books that fit your preference.</p>
      <div className="option-cards">
        {[
          { value: 'short', label: 'Short', desc: 'Under 200 pages' },
          { value: 'medium', label: 'Medium', desc: '200–400 pages' },
          { value: 'long', label: 'Long', desc: 'Over 400 pages' },
        ].map(opt => (
          <button
            key={opt.value}
            className={`option-card ${formData.preferred_length === opt.value ? 'selected' : ''}`}
            onClick={() => setFormData({ ...formData, preferred_length: opt.value })}
          >
            <strong>{opt.label}</strong>
            <span>{opt.desc}</span>
          </button>
        ))}
      </div>
    </div>,

    // Step 4: Mood + Authors
    <div className="onboarding-step" key="mood">
      <h2>What's your current reading mood?</h2>
      <p className="step-desc">This fine-tunes your first set of recommendations.</p>
      <div className="mood-cards">
        {MOOD_OPTIONS.map(mood => (
          <button
            key={mood.value}
            className={`mood-card ${formData.current_mood === mood.value ? 'selected' : ''}`}
            onClick={() => setFormData({ ...formData, current_mood: mood.value })}
          >
            <span className="mood-label">{mood.label}</span>
            <span className="mood-desc">{mood.desc}</span>
          </button>
        ))}
      </div>
      <div className="authors-field">
        <label>Favorite authors (optional)</label>
        <input
          type="text"
          className="onboarding-input"
          placeholder="e.g. Brandon Sanderson, Agatha Christie..."
          value={formData.favorite_authors}
          onChange={(e) => setFormData({ ...formData, favorite_authors: e.target.value })}
        />
      </div>
    </div>,
  ];

  return (
    <div className="onboarding-container">
      <div className="onboarding-card">
        <div className="onboarding-header">
          <BookOpen size={36} className="onboarding-logo" />
          <h1>ReadRec.ai</h1>
          <p className="onboarding-tagline">
            <Sparkles size={14} /> Personalized AI-Powered Reading Recommendations
          </p>
        </div>

        {/* Progress Indicator */}
        <div className="progress-bar">
          {steps.map((_, i) => (
            <div key={i} className={`progress-dot ${i <= step ? 'active' : ''} ${i === step ? 'current' : ''}`} />
          ))}
        </div>

        <div className="step-container">
          {steps[step]}
        </div>

        {error && <div className="onboarding-error">{error}</div>}

        <div className="onboarding-actions">
          {step > 0 && (
            <button className="btn-secondary" onClick={() => setStep(step - 1)}>
              Back
            </button>
          )}
          {onSkip && step === 0 && (
            <button className="btn-secondary" onClick={onSkip}>
              Use Existing Profile
            </button>
          )}
          <div style={{ flex: 1 }} />
          {step < steps.length - 1 ? (
            <button
              className="btn-primary btn-next"
              disabled={!canProceed()}
              onClick={() => setStep(step + 1)}
            >
              Next <ChevronRight size={18} />
            </button>
          ) : (
            <button
              className="btn-primary btn-create"
              disabled={submitting}
              onClick={handleSubmit}
            >
              {submitting ? 'Creating...' : '🚀 Create My Profile'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Onboarding;
