import { motion } from 'framer-motion';
import { CodeSnippet } from './CodeSnippet';

export function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  
  return (
    <motion.div 
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`message-wrapper ${isUser ? 'user' : ''}`}
    >
      <div className={`message-bubble ${isUser ? 'user' : 'assistant'} ${message.isError ? 'error' : ''}`}>
        
        {/* Rendering standard text (converting \n to <br/>) */}
        {message.text && (
          <div dangerouslySetInnerHTML={{ __html: message.text.replace(/\n/g, '<br/>') }} />
        )}

        {/* Rendering Code Snippets if any */}
        {message.code && Object.entries(message.code).map(([filename, content]) => (
          <CodeSnippet key={filename} filename={filename} content={content} />
        ))}

      </div>
    </motion.div>
  );
}
