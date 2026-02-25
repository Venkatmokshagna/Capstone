/**
 * Samaj Health Suraksha — Floating Chatbot Widget
 * Rule-based, read-only support assistant.
 * Informational only — NOT a medical diagnosis tool.
 */
(function () {
    'use strict';

    // ── Inject CSS ──────────────────────────────────────────────────
    const style = document.createElement('style');
    style.textContent = `
    #shs-chat-fab {
        position: fixed; bottom: 28px; right: 28px; z-index: 9999;
        width: 58px; height: 58px; border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: #fff; border: none; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 6px 24px rgba(99,102,241,0.45);
        transition: transform 0.3s cubic-bezier(0.34,1.56,0.64,1), box-shadow 0.3s;
        font-size: 1.5rem;
    }
    #shs-chat-fab:hover { transform: scale(1.13); box-shadow: 0 10px 32px rgba(99,102,241,0.55); }
    #shs-chat-fab .fab-badge {
        position: absolute; top: -4px; right: -4px;
        width: 18px; height: 18px; border-radius: 50%;
        background: #ef4444; border: 2px solid #fff;
        animation: pulseBadge 2s ease-out infinite;
    }
    @keyframes pulseBadge {
        0%,100% { box-shadow: 0 0 0 0 rgba(239,68,68,0.5); }
        50%      { box-shadow: 0 0 0 7px rgba(239,68,68,0); }
    }

    #shs-chat-panel {
        position: fixed; bottom: 98px; right: 28px; z-index: 9998;
        width: 360px; max-height: 540px;
        background: rgba(255,255,255,0.97);
        backdrop-filter: blur(18px);
        border: 1px solid rgba(99,102,241,0.18);
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(99,102,241,0.18);
        display: flex; flex-direction: column;
        transform-origin: bottom right;
        transform: scale(0);
        opacity: 0;
        transition: transform 0.35s cubic-bezier(0.34,1.56,0.64,1), opacity 0.25s ease;
        overflow: hidden;
    }
    #shs-chat-panel.open { transform: scale(1); opacity: 1; }

    .shs-chat-header {
        display: flex; align-items: center; justify-content: space-between;
        padding: 14px 18px;
        background: linear-gradient(135deg, #6366f1, #a855f7);
        color: #fff;
    }
    .shs-chat-header .shs-title {
        display: flex; align-items: center; gap: 10px;
        font-weight: 700; font-size: 0.95rem;
    }
    .shs-chat-header .shs-avatar {
        width: 32px; height: 32px; border-radius: 50%;
        background: rgba(255,255,255,0.2);
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem;
    }
    .shs-chat-header button {
        background: none; border: none; color: #fff;
        cursor: pointer; font-size: 1.1rem; padding: 4px;
        border-radius: 6px; transition: background 0.2s;
    }
    .shs-chat-header button:hover { background: rgba(255,255,255,0.15); }

    .shs-disclaimer {
        padding: 7px 14px;
        background: #fef9c3;
        border-bottom: 1px solid #fde68a;
        font-size: 0.7rem; color: #92400e;
        font-weight: 600;
    }

    .shs-messages {
        flex: 1; overflow-y: auto; padding: 14px;
        display: flex; flex-direction: column; gap: 10px;
        scroll-behavior: smooth;
    }
    .shs-messages::-webkit-scrollbar { width: 4px; }
    .shs-messages::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.25); border-radius: 4px; }

    .shs-msg {
        max-width: 88%; padding: 10px 13px;
        border-radius: 14px; font-size: 0.82rem;
        line-height: 1.5; white-space: pre-wrap;
        animation: msgIn 0.28s cubic-bezier(0.22,1,0.36,1);
    }
    @keyframes msgIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
    .shs-msg.bot {
        background: linear-gradient(135deg,#f0f4ff,#f5f0ff);
        border: 1px solid rgba(99,102,241,0.12);
        color: #1e1b4b; align-self: flex-start;
        border-bottom-left-radius: 4px;
    }
    .shs-msg.user {
        background: linear-gradient(135deg,#6366f1,#a855f7);
        color: #fff; align-self: flex-end;
        border-bottom-right-radius: 4px;
    }

    .shs-typing {
        display: flex; align-items: center; gap: 5px;
        padding: 8px 12px; align-self: flex-start;
        background: #f0f4ff; border-radius: 14px;
        border-bottom-left-radius: 4px;
        border: 1px solid rgba(99,102,241,0.12);
    }
    .shs-typing span {
        width: 7px; height: 7px; border-radius: 50%;
        background: #6366f1; display: inline-block;
        animation: typingBounce 1.1s ease-in-out infinite;
    }
    .shs-typing span:nth-child(2) { animation-delay: 0.18s; }
    .shs-typing span:nth-child(3) { animation-delay: 0.36s; }
    @keyframes typingBounce {
        0%,80%,100% { transform: translateY(0); }
        40%          { transform: translateY(-7px); }
    }

    .shs-input-row {
        display: flex; gap: 8px;
        padding: 12px 14px;
        border-top: 1px solid rgba(99,102,241,0.1);
        background: rgba(255,255,255,0.5);
    }
    #shs-chat-input {
        flex: 1; padding: 9px 13px;
        border: 1.5px solid rgba(99,102,241,0.2);
        border-radius: 12px; font-size: 0.82rem; outline: none;
        transition: border-color 0.2s;
        font-family: inherit;
        background: #f9f9ff;
        color: #1e1b4b;
    }
    #shs-chat-input:focus { border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.1); }
    #shs-send-btn {
        padding: 9px 15px; border: none; border-radius: 12px;
        background: linear-gradient(135deg,#6366f1,#a855f7);
        color: #fff; cursor: pointer; font-size: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    #shs-send-btn:hover { transform: scale(1.07); box-shadow: 0 4px 14px rgba(99,102,241,0.4); }
    #shs-send-btn:active { transform: scale(0.96); }

    .shs-quick-chips {
        display: flex; flex-wrap: wrap; gap: 6px; padding: 0 14px 10px;
    }
    .shs-chip {
        padding: 4px 11px; border: 1.5px solid rgba(99,102,241,0.25);
        border-radius: 20px; font-size: 0.72rem; color: #4f46e5;
        background: #f0f4ff; cursor: pointer; transition: all 0.2s;
        font-weight: 600;
    }
    .shs-chip:hover { background: #e0e7ff; border-color: #6366f1; transform: scale(1.04); }

    @media (max-width: 480px) {
        #shs-chat-panel { width: calc(100vw - 20px); right: 10px; }
        #shs-chat-fab   { right: 16px; bottom: 16px; }
    }
    `;
    document.head.appendChild(style);

    // ── Build DOM ───────────────────────────────────────────────────
    const fab = document.createElement('button');
    fab.id = 'shs-chat-fab';
    fab.setAttribute('aria-label', 'Open Health Assistant');
    fab.innerHTML = '💬 <span class="fab-badge" title="Online"></span>';

    const panel = document.createElement('div');
    panel.id = 'shs-chat-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', 'Health Support Chatbot');
    panel.innerHTML = `
        <div class="shs-chat-header">
            <div class="shs-title">
                <div class="shs-avatar">🤖</div>
                <div>
                    <div>Health Assistant</div>
                    <div style="font-size:0.68rem;opacity:0.8;font-weight:400">Samaj Health Suraksha • Support Bot</div>
                </div>
            </div>
            <button id="shs-close-btn" aria-label="Close chat">✕</button>
        </div>
        <div class="shs-disclaimer">
            ℹ️ Informational assistant only — not a medical diagnosis tool. Always consult a health professional.
        </div>
        <div class="shs-messages" id="shs-messages"></div>
        <div class="shs-quick-chips" id="shs-chips">
            <button class="shs-chip" data-q="What is cholera?">Cholera</button>
            <button class="shs-chip" data-q="How to boil water safely?">Boil water</button>
            <button class="shs-chip" data-q="What are symptoms of water-borne diseases?">Symptoms</button>
            <button class="shs-chip" data-q="How to prevent water-borne diseases?">Prevention</button>
            <button class="shs-chip" data-q="How many reports recorded?">Report stats</button>
            <button class="shs-chip" data-q="Which village has highest risk?">Risk status</button>
        </div>
        <div class="shs-input-row">
            <input id="shs-chat-input" type="text" placeholder="Ask about water safety, diseases…" maxlength="500" autocomplete="off" />
            <button id="shs-send-btn" aria-label="Send">➤</button>
        </div>
    `;

    document.body.appendChild(fab);
    document.body.appendChild(panel);

    // ── State ───────────────────────────────────────────────────────
    let isOpen = false;
    let isTyping = false;
    const messagesEl = panel.querySelector('#shs-messages');

    function togglePanel() {
        isOpen = !isOpen;
        panel.classList.toggle('open', isOpen);
        fab.innerHTML = isOpen ? '✕' : '💬 <span class="fab-badge"></span>';
        if (isOpen && messagesEl.children.length === 0) {
            appendMessage('bot',
                "👋 Hello! I'm your Samaj Health Suraksha Support Assistant.\n\n" +
                "I can help with:\n• 💧 Water-borne diseases\n• 🩺 Symptoms & prevention\n" +
                "• 📊 System statistics\n• 🔐 How to use the system\n\n" +
                "⚠️ I provide information only — not medical diagnosis.\n\n" +
                "Try one of the quick buttons below or type your question!"
            );
        }
        if (isOpen) panel.querySelector('#shs-chat-input').focus();
    }

    function appendMessage(role, text) {
        const d = document.createElement('div');
        d.className = `shs-msg ${role}`;
        // Render **bold** markdown
        d.innerHTML = text
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>');
        messagesEl.appendChild(d);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function showTyping() {
        if (isTyping) return;
        isTyping = true;
        const t = document.createElement('div');
        t.className = 'shs-typing'; t.id = 'shs-typing-indicator';
        t.innerHTML = '<span></span><span></span><span></span>';
        messagesEl.appendChild(t);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function hideTyping() {
        const t = document.getElementById('shs-typing-indicator');
        if (t) t.remove();
        isTyping = false;
    }

    async function sendMessage(text) {
        const msg = text.trim();
        if (!msg) return;

        const input = panel.querySelector('#shs-chat-input');
        input.value = '';

        // Hide chips after first real message
        const chips = document.getElementById('shs-chips');
        if (chips) chips.style.display = 'none';

        appendMessage('user', msg);
        showTyping();

        // Simulate slight delay for natural feel
        await new Promise(r => setTimeout(r, 700 + Math.random() * 400));

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg })
            });
            const data = await res.json();
            hideTyping();
            appendMessage('bot', data.reply || "Sorry, I couldn't get a response. Please try again.");
        } catch (e) {
            hideTyping();
            appendMessage('bot',
                "⚠️ I'm having trouble connecting right now.\n" +
                "Please check your connection or contact your health administrator.");
        }
    }

    // ── Event Listeners ─────────────────────────────────────────────
    fab.addEventListener('click', togglePanel);
    panel.querySelector('#shs-close-btn').addEventListener('click', togglePanel);

    panel.querySelector('#shs-send-btn').addEventListener('click', () => {
        sendMessage(panel.querySelector('#shs-chat-input').value);
    });

    panel.querySelector('#shs-chat-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(e.target.value);
        }
    });

    panel.querySelectorAll('.shs-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            sendMessage(chip.dataset.q);
        });
    });

    // Close on backdrop click
    document.addEventListener('click', (e) => {
        if (isOpen && !panel.contains(e.target) && e.target !== fab) {
            togglePanel();
        }
    });

})();
