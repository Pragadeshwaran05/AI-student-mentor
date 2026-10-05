document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chatForm');
    const messageInput = document.getElementById('messageInput');
    const chatMessages = document.getElementById('chatMessages');
    const clearChatBtn = document.getElementById('clearChat');
    const suggestions = document.getElementById('suggestions');
    const aiMode = document.getElementById('aiMode');
    
    // Voice Elements
    const recordBtn = document.getElementById('recordBtn');
    const recordingIndicator = document.getElementById('recordingIndicator');
    const speechAnalysis = document.getElementById('speechAnalysis');
    
    // Conversation State
    let currentConversationId = null;
    
    // Marked configuration for markdown
    marked.setOptions({
        highlight: function(code, lang) {
            const language = hljs.getLanguage(lang) ? lang : 'plaintext';
            return hljs.highlight(code, { language }).value;
        }
    });
    
    // Auto-scroll to bottom
    const scrollToBottom = () => {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    };
    
    // Play TTS
    window.playAudio = async (text, btnElement) => {
        const icon = btnElement.querySelector('i');
        icon.className = 'fas fa-spinner fa-spin';
        
        try {
            const response = await fetch('/api/text-to-speech', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            const data = await response.json();
            
            if (response.ok && data.status === "success") {
                const audio = new Audio(data.audio_url);
                icon.className = 'fas fa-stop';
                
                audio.play();
                
                audio.onended = () => {
                    icon.className = 'fas fa-volume-up';
                };
                
                btnElement.onclick = () => {
                    audio.pause();
                    audio.currentTime = 0;
                    icon.className = 'fas fa-volume-up';
                    btnElement.onclick = () => window.playAudio(text, btnElement);
                };
            } else {
                icon.className = 'fas fa-volume-mute';
                console.error("TTS Error:", data.error);
            }
        } catch (e) {
            icon.className = 'fas fa-volume-mute';
            console.error("TTS Request Failed:", e);
        }
    };
    
    // Add a message to the chat UI
    const appendMessage = (text, sender, isHistory=false) => {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (sender === 'ai') {
            contentDiv.innerHTML = marked.parse(text);
            
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';
            
            const copyBtn = document.createElement('button');
            copyBtn.className = 'msg-action-btn';
            copyBtn.innerHTML = '<i class="fas fa-copy"></i>';
            copyBtn.title = 'Copy';
            copyBtn.onclick = () => { navigator.clipboard.writeText(text); copyBtn.innerHTML = '<i class="fas fa-check"></i>'; setTimeout(() => copyBtn.innerHTML = '<i class="fas fa-copy"></i>', 2000); };
            
            const ttsBtn = document.createElement('button');
            ttsBtn.className = 'msg-action-btn';
            ttsBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
            ttsBtn.title = 'Listen';
            
            // Clean text for TTS (remove markdown)
            const cleanText = text.replace(/[#*`_]/g, '');
            ttsBtn.onclick = function() { window.playAudio(cleanText, this); };
            
            actionsDiv.appendChild(copyBtn);
            actionsDiv.appendChild(ttsBtn);
            
            msgDiv.appendChild(contentDiv);
            msgDiv.appendChild(actionsDiv);
        } else {
            contentDiv.textContent = text;
            msgDiv.appendChild(contentDiv);
        }
        
        chatMessages.appendChild(msgDiv);
        
        if (!isHistory) {
            scrollToBottom();
        }
    };
    
    // Show typing
    const showTyping = () => {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai typing-message';
        typingDiv.id = 'typingIndicator';
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        
        typingDiv.appendChild(indicator);
        chatMessages.appendChild(typingDiv);
        scrollToBottom();
    };
    
    const hideTyping = () => {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) indicator.remove();
    };
    
    // Load conversation
    window.loadConversation = async (id, title) => {
        currentConversationId = id;
        document.getElementById('currentConvTitle').textContent = title;
        
        // Highlight active
        document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
        const activeEl = document.querySelector(`.conversation-item[data-id="${id}"]`);
        if (activeEl) activeEl.classList.add('active');
        
        // Clear chat
        chatMessages.innerHTML = '';
        if (suggestions) suggestions.style.display = 'none';
        
        try {
            const res = await fetch(`/api/conversations/${id}`);
            const data = await res.json();
            
            data.messages.forEach(msg => {
                appendMessage(msg.message, msg.sender, true);
            });
            scrollToBottom();
        } catch (e) {
            console.error("Failed to load conversation", e);
        }
    };
    
    // Delete conversation
    window.deleteConversation = async (id, event) => {
        event.stopPropagation();
        if(!confirm("Delete this conversation?")) return;
        
        try {
            const res = await fetch(`/api/conversations/${id}`, { method: 'DELETE' });
            if (res.ok) {
                const el = document.querySelector(`.conversation-item[data-id="${id}"]`);
                if (el) el.remove();
                
                if (currentConversationId === id) {
                    startNewChat();
                }
            }
        } catch(e) {
            console.error(e);
        }
    };
    
    // Setup click handlers for existing conversations
    document.querySelectorAll('.conversation-item').forEach(el => {
        el.addEventListener('click', (e) => {
            if (!e.target.closest('button')) {
                loadConversation(el.dataset.id, el.querySelector('.conv-title').textContent);
            }
        });
    });
    
    const startNewChat = () => {
        currentConversationId = null;
        document.getElementById('currentConvTitle').textContent = "New Conversation";
        document.querySelectorAll('.conversation-item').forEach(el => el.classList.remove('active'));
        
        chatMessages.innerHTML = `
            <div class="message ai">
                <div class="message-content">
                    Hello! I'm your AI Academic Mentor. How can I help you with your studies today?
                </div>
            </div>
        `;
        if (suggestions) suggestions.style.display = 'flex';
    };
    
    document.getElementById('newChatBtn')?.addEventListener('click', startNewChat);
    
    // Send message to server
    const sendMessage = async (message) => {
        if (!message.trim()) return;
        
        if (suggestions) suggestions.style.display = 'none';
        
        const mode = aiMode ? aiMode.value : 'Explain';
        appendMessage(message, 'user');
        messageInput.value = '';
        
        showTyping();
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message,
                    mode: mode,
                    conversation_id: currentConversationId
                })
            });
            
            const data = await response.json();
            hideTyping();
            
            if (response.ok) {
                appendMessage(data.message, 'ai');
                
                // If it was a new conversation, set the ID and reload sidebar ideally
                if (!currentConversationId && data.conversation_id) {
                    currentConversationId = data.conversation_id;
                    // Simply reload page to update sidebar for Phase 2 simplicity
                    // location.reload();
                }
            } else {
                appendMessage('Sorry, an error occurred. Please try again. ' + (data.error || ''), 'ai');
            }
        } catch (error) {
            hideTyping();
            appendMessage('Connection error. Please check your network.', 'ai');
        }
    };
    
    if (chatForm) {
        chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            sendMessage(messageInput.value);
        });
    }
    
    window.sendSuggestion = (text) => sendMessage(text);
    if (clearChatBtn) clearChatBtn.addEventListener('click', startNewChat);

    // --- Voice Recording Logic ---
    let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let recordStartTime;
    
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        recordBtn.addEventListener('click', async () => {
            if (isRecording) {
                // Stop recording
                mediaRecorder.stop();
                isRecording = false;
                recordBtn.classList.remove('recording');
                recordingIndicator.style.display = 'none';
                return;
            }
            
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = e => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = async () => {
                    const duration = Math.round((Date.now() - recordStartTime) / 1000);
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    
                    // Stop tracks to release mic
                    stream.getTracks().forEach(track => track.stop());
                    
                    // Show processing state
                    recordBtn.querySelector('i').className = 'fas fa-spinner fa-spin';
                    
                    const formData = new FormData();
                    formData.append('audio', audioBlob);
                    
                    try {
                        const res = await fetch('/api/speech-to-text', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const data = await res.json();
                        recordBtn.querySelector('i').className = 'fas fa-microphone';
                        
                        if (res.ok && data.status === 'success') {
                            messageInput.value = data.transcript;
                            
                            // Show analysis
                            document.getElementById('saDuration').textContent = `Duration: ${duration}s`;
                            document.getElementById('saWords').textContent = `Words: ${data.word_count}`;
                            speechAnalysis.style.display = 'block';
                            
                            // Optionally auto-send: sendMessage(data.transcript);
                        } else {
                            alert("Speech recognition failed: " + data.error);
                        }
                    } catch (e) {
                        recordBtn.querySelector('i').className = 'fas fa-microphone';
                        alert("Network error during speech recognition.");
                    }
                };
                
                mediaRecorder.start();
                isRecording = true;
                recordStartTime = Date.now();
                recordBtn.classList.add('recording');
                recordingIndicator.style.display = 'flex';
                speechAnalysis.style.display = 'none';
                
            } catch (e) {
                console.error("Mic access denied", e);
                alert("Microphone access denied. Please allow microphone access to use voice features.");
            }
        });
    } else {
        recordBtn.style.display = 'none'; // Not supported
    }
});
