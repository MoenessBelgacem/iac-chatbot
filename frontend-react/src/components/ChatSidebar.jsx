import { RefreshCw, Clock } from 'lucide-react';
import { motion } from 'framer-motion';

export function ChatSidebar({ history, onRefresh, onSelect, isLoading }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2><Clock size={18} /> Historique</h2>
        <button 
          className="icon-btn" 
          onClick={onRefresh}
          disabled={isLoading}
          title="Rafraîchir l'historique"
        >
          <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
        </button>
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
