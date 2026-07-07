import { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import hljs from 'highlight.js';
import 'highlight.js/styles/atom-one-dark.css';

export function CodeSnippet({ filename, content }) {
  const [copied, setCopied] = useState(false);
  const lang = filename.endsWith('.tf') ? 'terraform' : 'yaml';
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const highlightedCode = hljs.highlight(content, { language: lang }).value;

  return (
    <div className="code-wrapper">
      <div className="code-header">
        <span>{filename}</span>
        <button className="copy-btn" onClick={handleCopy}>
          {copied ? (
            <><Check size={14} /> Copié !</>
          ) : (
            <><Copy size={14} /> Copier</>
          )}
        </button>
      </div>
      <pre>
        <code 
          className={`hljs language-${lang}`}
          dangerouslySetInnerHTML={{ __html: highlightedCode }} 
        />
      </pre>
    </div>
  );
}
