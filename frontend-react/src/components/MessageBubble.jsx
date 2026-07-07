import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { CodeSnippet } from './CodeSnippet';
import { Shield, DollarSign, GitBranch } from 'lucide-react';

export function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const mermaidRef = useRef(null);

  // Render Mermaid diagram
  useEffect(() => {
    if (message.diagram && mermaidRef.current) {
      import('mermaid').then((mermaid) => {
        mermaid.default.initialize({ 
          startOnLoad: false, 
          theme: 'dark',
          themeVariables: {
            darkMode: true,
            background: '#0a0a1a',
            primaryColor: '#10b981',
            primaryTextColor: '#e2e8f0',
            primaryBorderColor: '#10b981',
            lineColor: '#64748b',
            secondaryColor: '#1e293b',
            tertiaryColor: '#1e1e3a',
          }
        });
        const id = `mermaid-${Date.now()}`;
        mermaid.default.render(id, message.diagram).then(({ svg }) => {
          if (mermaidRef.current) {
            mermaidRef.current.innerHTML = svg;
          }
        }).catch(() => {});
      });
    }
  }, [message.diagram]);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`message-wrapper ${isUser ? 'user' : ''}`}
    >
      <div className={`message-bubble ${isUser ? 'user' : 'assistant'} ${message.isError ? 'error' : ''}`}>
        
        {/* Text content */}
        {message.text && (
          <div dangerouslySetInnerHTML={{ __html: message.text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>').replace(/\*(.*?)\*/g, '<em>$1</em>').replace(/\n/g, '<br/>') }} />
        )}

        {/* Code Snippets */}
        {message.code && Object.entries(message.code).map(([filename, content]) => (
          <CodeSnippet key={filename} filename={filename} content={content} />
        ))}

        {/* Architecture Diagram */}
        {message.diagram && (
          <div className="diagram-container">
            <div className="section-label"><GitBranch size={14} /> Architecture</div>
            <div ref={mermaidRef} className="mermaid-render" />
          </div>
        )}

        {/* Cost Estimate */}
        {message.costEstimate && (
          <div className="cost-container">
            <div className="section-label"><DollarSign size={14} /> Estimation de Coûts</div>
            <div className="cost-grid">
              {message.costEstimate.detail && Object.entries(message.costEstimate.detail).map(([key, val]) => (
                <div key={key} className="cost-row">
                  <span className="cost-key">{key}</span>
                  <span className="cost-val">{val}</span>
                </div>
              ))}
              <div className="cost-row total">
                <span className="cost-key">💰 Total mensuel</span>
                <span className="cost-val">{message.costEstimate.total_mensuel}$</span>
              </div>
              <div className="cost-row total">
                <span className="cost-key">📅 Total annuel</span>
                <span className="cost-val">{message.costEstimate.total_annuel}$</span>
              </div>
            </div>
          </div>
        )}

        {/* Compliance */}
        {message.compliance && message.compliance.length > 0 && (
          <div className="compliance-container">
            <div className="section-label"><Shield size={14} /> Conformité Sécurité</div>
            <div className="compliance-list">
              {message.compliance.map((rule, idx) => (
                <div key={idx} className={`compliance-row ${rule.status}`}>
                  <span className="compliance-icon">{rule.icon}</span>
                  <span className="compliance-msg">{rule.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </motion.div>
  );
}
