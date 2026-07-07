const API_URL = 'http://127.0.0.1:8000';
let currentSessionId = null;

// DOM Elements
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const chatContainer = document.getElementById('chat-container');
const typingIndicator = document.getElementById('typing-indicator');
const historyList = document.getElementById('history-list');
const refreshHistoryBtn = document.getElementById('refresh-history-btn');
const statusDot = document.querySelector('.status-dot');
const statusText = document.querySelector('.status-indicator').lastChild;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadHistory();
    // Set up syntax highlighting
    hljs.configure({ ignoreUnescapedHTML: true });
});

// --- API Calls ---
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        if (data.api === 'ok' && data.ollama === 'ok') {
            setOnlineStatus(true);
        } else {
            setOnlineStatus(false, 'Ollama non joignable');
        }
    } catch (error) {
        setOnlineStatus(false, 'API hors ligne');
    }
}

async function sendMessageToApi(message) {
    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Error sending message:', error);
        return {
            success: false,
            error: "Erreur de connexion à l'API. Assure-toi que le backend tourne."
        };
    }
}

async function fetchHistory() {
    try {
        const response = await fetch(`${API_URL}/history?limit=20`);
        if (!response.ok) throw new Error('Failed to fetch history');
        return await response.json();
    } catch (error) {
        console.error('Error fetching history:', error);
        return [];
    }
}

// --- UI Updates ---
function setOnlineStatus(isOnline, text = 'Ollama & API Connectés') {
    if (isOnline) {
        statusDot.className = 'status-dot online';
        statusText.textContent = ' ' + text;
    } else {
        statusDot.className = 'status-dot error';
        statusText.textContent = ' ' + text;
    }
}

function appendMessage(role, content, isError = false) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message ${isError ? 'error-message' : ''}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Convert newlines to <br> for simple text content
    if (typeof content === 'string' && !content.includes('<div class="code-container">')) {
        contentDiv.innerHTML = content.replace(/\n/g, '<br>');
    } else {
        contentDiv.innerHTML = content;
    }
    
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function buildSuccessMessage(data) {
    let html = `${data.message}<br><br>`;
    
    // Add code snippets if generation was successful
    if (data.generation && data.generation.contenu) {
        for (const [filename, content] of Object.entries(data.generation.contenu)) {
            const lang = filename.endsWith('.tf') ? 'terraform' : 'yaml';
            const escapedContent = content.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            
            html += `
                <div class="code-container">
                    <div class="code-header">
                        <span>${filename}</span>
                        <button class="copy-btn" onclick="copyCode(this)">Copier</button>
                    </div>
                    <pre><code class="language-${lang}">${escapedContent}</code></pre>
                </div>
            `;
        }
    }
    return html;
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function setTyping(isTyping) {
    typingIndicator.style.display = isTyping ? 'flex' : 'none';
    userInput.disabled = isTyping;
    sendBtn.disabled = isTyping;
    if (!isTyping) userInput.focus();
    scrollToBottom();
}

async function loadHistory() {
    historyList.innerHTML = '<div class="loading-spinner" style="text-align:center; padding:20px; color:var(--text-muted);">Chargement...</div>';
    const history = await fetchHistory();
    
    historyList.innerHTML = '';
    
    if (history.length === 0) {
        historyList.innerHTML = '<div style="text-align:center; padding:20px; color:var(--text-muted); font-size:0.9rem;">Aucun historique récent.</div>';
        return;
    }
    
    history.forEach(entry => {
        const date = new Date(entry.timestamp).toLocaleString('fr-FR', {
            month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
        
        let statusClass = 'success';
        let statusLabel = 'Généré';
        if (entry.statut === 'error') { statusClass = 'error'; statusLabel = 'Erreur'; }
        if (entry.statut === 'clarification') { statusClass = 'clarification'; statusLabel = 'Incomplet'; }
        
        const item = document.createElement('div');
        item.className = 'history-item';
        item.innerHTML = `
            <div class="prompt" title="${entry.prompt}">${entry.prompt}</div>
            <div class="meta">
                <span>${date}</span>
                <span class="status-badge ${statusClass}">${statusLabel}</span>
            </div>
        `;
        
        // When clicking history item, we could load it (not fully implemented yet, just visual for now)
        item.addEventListener('click', () => {
            userInput.value = entry.prompt;
            userInput.focus();
        });
        
        historyList.appendChild(item);
    });
}

// --- Event Listeners ---
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    // Display user message
    appendMessage('user', message);
    userInput.value = '';
    
    // Show typing indicator
    setTyping(true);

    // Call API
    const response = await sendMessageToApi(message);
    
    // Hide typing indicator
    setTyping(false);

    // Update Session ID
    if (response.session_id) {
        currentSessionId = response.session_id;
    }

    // Display Assistant Response
    if (response.success) {
        if (response.needs_clarification) {
            // NLU multi-turn prompt
            appendMessage('assistant', response.message);
        } else {
            // Successful generation
            const successHtml = buildSuccessMessage(response);
            appendMessage('assistant', successHtml);
            
            // Apply syntax highlighting to new code blocks
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
            
            // Clear session after successful generation
            currentSessionId = null;
            
            // Refresh history
            loadHistory();
        }
    } else {
        // Error
        appendMessage('assistant', `❌ ${response.error}`, true);
        // Clear session on hard error to avoid getting stuck
        currentSessionId = null;
    }
});

refreshHistoryBtn.addEventListener('click', loadHistory);

// Utility for copy buttons
window.copyCode = function(button) {
    const pre = button.parentElement.nextElementSibling;
    const code = pre.querySelector('code').innerText;
    
    navigator.clipboard.writeText(code).then(() => {
        const originalText = button.innerText;
        button.innerText = 'Copié !';
        setTimeout(() => {
            button.innerText = originalText;
        }, 2000);
    });
};
