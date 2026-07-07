import { RefreshCw, Clock, FileDown, Layers } from 'lucide-react';
import { motion } from 'framer-motion';

const API_URL = 'http://127.0.0.1:8000';

export function ChatSidebar({ history, onRefresh, onSelect, isLoading }) {
  
  const downloadPDF = async () => {
    try {
      const res = await fetch(`${API_URL}/report/pdf`);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'iac-chatbot-report.pdf';
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error('Failed to download PDF', e);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2><Clock size={18} /> Historique</h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button 
            className="icon-btn" 
            onClick={downloadPDF}
            title="Télécharger le rapport PDF"
          >
            <FileDown size={18} />
          </button>
          <button 
            className="icon-btn" 
            onClick={onRefresh}
            disabled={isLoading}
            title="Rafraîchir l'historique"
          >
            <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
          </button>
        </div>
      </div>

      {/* Stacks Shortcuts */}
      <div className="stacks-section">
        <div className="section-label-sidebar"><Layers size={14} /> Stacks Rapides</div>
        <div className="stacks-grid">
          {[
            { id: 'wordpress', label: '🌐 WordPress', cmd: 'Déploie une stack WordPress' },
            { id: 'lamp', label: '💡 LAMP', cmd: 'Déploie une stack LAMP' },
            { id: 'monitoring', label: '📊 Monitoring', cmd: 'Déploie une stack monitoring' },
            { id: 'cache', label: '⚡ Cache', cmd: 'Déploie une stack cache nginx' },
            { id: 'elk', label: '🔍 ELK', cmd: 'Déploie une stack ELK' },
          ].map(s => (
            <button key={s.id} className="stack-btn" onClick={() => onSelect(s.cmd)} title={s.cmd}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="history-list">
        {history.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '2rem', fontSize: '0.9rem' }}>
            Aucun historique récent.
          </div>
        ) : (
          history.map((entry, index) => {
            const date = new Date(entry.timestamp).toLocaleString('fr-FR', {
              month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            });
            
            let statusClass = 'status-success';
            let statusLabel = 'Généré';
            if (entry.statut === 'error') { statusClass = 'status-error'; statusLabel = 'Erreur'; }
            if (entry.statut === 'clarification') { statusClass = 'status-clarification'; statusLabel = 'Incomplet'; }

            return (
              <motion.div 
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                key={entry.id} 
                className="history-item"
                onClick={() => onSelect(entry.prompt)}
              >
                <div className="history-prompt" title={entry.prompt}>{entry.prompt}</div>
                <div className="history-meta">
                  <span>{date}</span>
                  <span className={`status-badge ${statusClass}`}>{statusLabel}</span>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </aside>
  );
}
