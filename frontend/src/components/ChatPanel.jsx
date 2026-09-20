import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';
import AgentTracePanel from './AgentTracePanel';
import { api } from '../api';

const ChatPanel = ({ userId, onRecommendationsUpdate, showToast }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! Tell me what you are in the mood to read today.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    const { data, error } = await api.chat(userId, userMsg.content);
    
    if (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, an error occurred connecting to the agent.' }]);
      showToast(error, 'error');
    } else if (data) {
      setMessages(prev => [
        ...prev, 
        { 
          role: 'assistant', 
          content: data.response,
          trace: data.trace 
        }
      ]);

      if (data.recommendations && data.recommendations.length > 0) {
        onRecommendationsUpdate(data.recommendations);
      }
    }
    
    setIsLoading(false);
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <Bot size={20} />
        <h2>Agent Chat</h2>
      </div>
      
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`message-wrapper ${m.role}`}>
            <div className="message-bubble">
              <div className="message-icon">
                {m.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
              </div>
              <div className="message-content">
                <p>{m.content}</p>
                {m.trace && m.trace.length > 0 && (
                  <AgentTracePanel trace={m.trace} />
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message-wrapper assistant">
            <div className="message-bubble">
              <Bot size={16} />
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask for a book recommendation..."
        />
        <button onClick={handleSend} disabled={isLoading || !input.trim()}>
          <Send size={18} />
        </button>
      </div>
    </div>
  );
};

export default ChatPanel;
