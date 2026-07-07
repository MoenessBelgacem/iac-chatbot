import { useState, useEffect } from 'react';
import { ChatSidebar } from './components/ChatSidebar';
import { ChatArea } from './components/ChatArea';
import './App.css';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [history, setHistory] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [apiStatus, setApiStatus] = useState('checking');
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  useEffect(() => {
    checkHealth();
    loadHistory();
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/health`);
      const data = await res.json();
      setApiStatus(data.api === 'ok' && data.ollama === 'ok' ? 'ok' : 'error');
    } catch {
      setApiStatus('error');
    }
  };

  const loadHistory = async () => {
    setIsLoadingHistory(true);
    try {
      const res = await fetch(`${API_URL}/history?limit=20`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data);
      }
    } catch (e) {
      console.error('Failed to load history', e);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const handleSendMessage = async (text) => {
    // Add user message
    setMessages(prev => [...prev, { role: 'user', text }]);
    setIsTyping(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId })
      });
      
      const data = await response.json();
      
      if (data.session_id) {
        setSessionId(data.session_id);
      }

      if (data.success) {
        if (data.needs_clarification) {
          // Assistant asks a follow-up question
          setMessages(prev => [...prev, { role: 'assistant', text: data.message }]);
        } else {
          // Generation successful — include all new data
          const assistantMsg = { 
            role: 'assistant', 
            text: data.message,
            code: data.generation?.contenu || 
                  (data.generations ? Object.assign({}, ...data.generations.map(g => g.contenu || {})) : null),
            diagram: data.diagram || null,
            costEstimate: data.cost_estimate || null,
            compliance: data.compliance || null,
            stackName: data.stack_name || null,
          };
          setMessages(prev => [...prev, assistantMsg]);
          setSessionId(null); // Reset session after success
          loadHistory(); // Refresh history
        }
      } else {
        // Error handling
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          text: `❌ ${data.error}`,
          isError: true
        }]);
        setSessionId(null);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        text: '❌ Erreur de connexion à l\'API. Assure-toi que le backend tourne.',
        isError: true
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSelectHistory = (prompt) => {
    if (!isTyping) {
      handleSendMessage(prompt);
    }
  };

  return (
    <div className="app-container glass-panel">
      <ChatSidebar 
        history={history} 
        onRefresh={loadHistory} 
        isLoading={isLoadingHistory}
        onSelect={handleSelectHistory}
      />
      <ChatArea 
        messages={messages} 
        onSendMessage={handleSendMessage} 
        isTyping={isTyping} 
        apiStatus={apiStatus}
      />
    </div>
  );
}

export default App;
