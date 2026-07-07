import { useState, useRef, useEffect } from 'react';
import { Send, Bot } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { motion } from 'framer-motion';

export function ChatArea({ messages, onSendMessage, isTyping, apiStatus }) {
  const [input, setInput] = useState('');
  const endOfMessagesRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;
    onSendMessage(input.trim());
    setInput('');
  };

  return (
    <main className="chat-area">
      <header className="chat-header">
        <h1><Bot size={24} color="var(--accent-primary)" /> IaC Chatbot Assistant</h1>
        <div className="status-indicator">
          <div className={`status-dot ${apiStatus === 'ok' ? 'online' : 'offline'}`}></div>
          {apiStatus === 'ok' ? 'API Connectée' : 'API Hors Ligne'}
        </div>
      </header>

      <div className="messages-container">
        {/* Welcome Message */}
        <MessageBubble message={{
          role: 'assistant',
          text: 'Bonjour ! Je suis ton assistant Infrastructure as Code. Que souhaites-tu déployer aujourd\'hui ?\n\n*Exemple : "Je veux une VM Ubuntu 22.04 sur vSphere avec 4 CPU, 8 Go de RAM et 50 Go de disque" ou "Déploie un conteneur nginx sur OpenShift".*'
        }} />

        {/* Chat Messages */}
        {messages.map((msg, index) => (
          <MessageBubble key={index} message={msg} />
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="message-wrapper assistant"
          >
            <div className="message-bubble assistant">
              <div className="typing-dots">
                <motion.span animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0 }} />
                <motion.span animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.2 }} />
                <motion.span animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 0.6, delay: 0.4 }} />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      <div className="input-wrapper">
        <form className="input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            className="chat-input"
            placeholder="Décris l'infrastructure que tu souhaites déployer..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isTyping}
            autoFocus
          />
          <button type="submit" className="send-btn" disabled={!input.trim() || isTyping}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </main>
  );
}
