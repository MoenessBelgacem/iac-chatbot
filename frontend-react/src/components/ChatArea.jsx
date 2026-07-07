import { useState, useRef, useEffect } from 'react';
import { Send, Bot, Mic, MicOff } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { motion } from 'framer-motion';

export function ChatArea({ messages, onSendMessage, isTyping, apiStatus }) {
  const [input, setInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const endOfMessagesRef = useRef(null);
  const recognitionRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.lang = 'fr-FR';
      recognition.interimResults = true;
      recognition.continuous = false;

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setInput(transcript);
        
        // If final result, auto-send
        if (event.results[0].isFinal) {
          setIsListening(false);
        }
      };

      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);

      recognitionRef.current = recognition;
    }
  }, []);

  const toggleVoice = () => {
    if (!recognitionRef.current) return;
    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setInput('');
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

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
          text: 'Bonjour ! Je suis ton assistant Infrastructure as Code. 🚀\n\n*Exemples de commandes :*\n• "Déploie une VM Ubuntu sur vSphere avec 4 CPU"\n• "Conteneur nginx sur OpenShift"\n• "Déploie une stack WordPress"\n• "Supprime la dernière ressource"\n\n🎤 *Tu peux aussi me parler avec le bouton micro !*'
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
            placeholder={isListening ? "🎤 Je t'écoute..." : "Décris l'infrastructure à déployer..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isTyping}
            autoFocus
          />
          {recognitionRef.current && (
            <button 
              type="button" 
              className={`voice-btn ${isListening ? 'listening' : ''}`}
              onClick={toggleVoice}
              disabled={isTyping}
              title={isListening ? 'Arrêter l\'écoute' : 'Commande vocale'}
            >
              {isListening ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
          )}
          <button type="submit" className="send-btn" disabled={!input.trim() || isTyping}>
            <Send size={18} />
          </button>
        </form>
      </div>
    </main>
  );
}
