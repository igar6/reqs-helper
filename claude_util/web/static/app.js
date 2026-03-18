/**
 * CTO Requirements Agent — Frontend WebSocket client
 */

// ── State ─────────────────────────────────────────────────────────────────
let ws = null;
let sessionId = null;
let currentPhase = 'CLARIFYING';
let downloadUrl = null;
let streamingMsg = null;       // current chat message div being streamed
let streamingBuf = '';         // accumulated chat stream text
let artifactBufs = {};         // artifact_id → accumulated text (raw)
let isGenerating = false;
let _serverErrorReceived = false;  // true if server sent a meaningful error before closing
let _reconnectTimer = null;
let pendingAttachments = [];   // [{type, name, data, media_type}]

const PHASE_ORDER = ['CLARIFYING', 'REFINING', 'GENERATING', 'DONE'];

// Marked.js options
const markedOpts = { breaks: true, gfm: true };

// ── Init ──────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  // Start with input disabled — enable only after session_created
  setSendEnabled(false);
  connect();
});

// ── WebSocket ─────────────────────────────────────────────────────────────
function connect() {
  clearTimeout(_reconnectTimer);
  _serverErrorReceived = false;

  const overlay = document.getElementById('connecting-overlay');
  overlay.querySelector('p').textContent = 'Connecting to CTO Agent…';
  overlay.classList.remove('hidden');

  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${location.host}/ws`);

  ws.onopen = () => {
    // Don't hide overlay yet — wait for session_created to confirm server is ready
  };

  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data);
      dispatch(msg);
    } catch (e) {
      console.error('Bad WS message:', e);
    }
  };

  ws.onclose = () => {
    setSendEnabled(false);
    if (_serverErrorReceived) {
      // A real error was shown — don't overwrite it with a generic toast
      return;
    }
    if (currentPhase === 'DONE') return;  // expected close

    // Unexpected close — show overlay with retry
    const overlay = document.getElementById('connecting-overlay');
    overlay.querySelector('p').textContent =
      'Connection lost — server may have stopped.';
    overlay.classList.remove('hidden');
    // Auto-retry after 3 seconds
    _reconnectTimer = setTimeout(() => {
      overlay.querySelector('p').textContent = 'Reconnecting…';
      connect();
    }, 3000);
  };

  ws.onerror = () => {
    // onerror always fires before onclose — let onclose handle UI
  };
}

// ── Message dispatcher ────────────────────────────────────────────────────
function dispatch(msg) {
  const { type, payload } = msg;

  switch (type) {
    case 'session_created':
      sessionId = payload.session_id;
      document.getElementById('model-badge').textContent = payload.model;
      // Hide overlay but keep input disabled until role is selected
      document.getElementById('connecting-overlay').classList.add('hidden');
      break;

    case 'role_selection':
      showRoleSelection(payload.prompt, payload.roles);
      break;

    case 'scope_selection':
      showScopeSelection(payload.prompt, payload.scopes);
      break;

    case 'ready':
      // Both role and scope set — enable input
      setSendEnabled(true);
      document.getElementById('chat-input').placeholder = 'Describe your idea or requirement…';
      document.getElementById('chat-input').focus();
      break;

    case 'phase_change':
      setPhase(payload.phase);
      break;

    case 'phase_progress':
      // Show "Question X of Y" in a subtle way
      if (payload.phase === 'CLARIFYING') {
        const badge = document.getElementById('model-badge');
        const orig = badge.textContent;
        badge.textContent = `Q ${payload.round}/${payload.max_rounds}`;
        setTimeout(() => { badge.textContent = orig; }, 3000);
      }
      break;

    // ── Chat streaming ──
    case 'chat_message':
      finishChatStream();
      appendChatMsg(payload.role, payload.content);
      break;

    case 'chat_stream_start':
      finishChatStream();
      streamingBuf = '';
      streamingMsg = appendChatMsg('assistant', '');
      streamingMsg.querySelector('.msg-bubble').classList.add('stream-cursor');
      break;

    case 'chat_stream_token':
      if (streamingMsg) {
        streamingBuf += payload.token;
        streamingMsg.querySelector('.msg-bubble').innerHTML =
          marked.parse(streamingBuf, markedOpts);
        streamingMsg.querySelector('.msg-bubble').classList.add('stream-cursor');
        scrollChatToBottom();
      }
      break;

    case 'chat_stream_end':
      finishChatStream();
      // Re-enable input so the user can continue the conversation
      if (currentPhase === 'CLARIFYING' || currentPhase === 'REFINING') {
        setSendEnabled(true);
        document.getElementById('chat-input').focus();
      }
      break;

    // ── Refined requirements ──
    case 'refined_requirements_start':
      streamingBuf = '';
      showRefinedPlaceholder(false);
      document.getElementById('refined-content').style.display = 'block';
      document.getElementById('refined-content').innerHTML = '';
      document.getElementById('refined-content').classList.add('stream-cursor');
      break;

    case 'refined_requirements_token':
      streamingBuf += payload.token;
      const rc = document.getElementById('refined-content');
      rc.innerHTML = marked.parse(streamingBuf, markedOpts);
      rc.classList.add('stream-cursor');
      break;

    case 'refined_requirements_end':
      {
        const rc2 = document.getElementById('refined-content');
        rc2.classList.remove('stream-cursor');
        rc2.innerHTML = marked.parse(streamingBuf, markedOpts);
        markTabDone('refined');
        // Show "Generate Artifacts" button and re-enable input for corrections
        document.getElementById('generate-btn').classList.add('visible');
        setSendEnabled(true);
        document.getElementById('chat-input').placeholder = 'Send a correction, or click Generate Artifacts…';
        streamingBuf = '';
      }
      break;

    // ── Artifact streaming ──
    case 'artifact_start':
      {
        const { artifact_id } = payload;
        artifactBufs[artifact_id] = '';
        markTabGenerating(artifact_id);
        clearPanePlaceholder(artifact_id, payload.title);
        // Auto-switch to Score tab when evaluation runs before refinement
        if (artifact_id === 'evaluation' && currentPhase !== 'GENERATING') {
          switchTabById('evaluation');
        }
        if (currentPhase === 'GENERATING') {
          isGenerating = true;
          setSendEnabled(false);
          document.getElementById('chat-input').placeholder = 'Describe your idea or requirement…';
          const genBtn = document.getElementById('generate-btn');
          genBtn.textContent = '⏹ Stop';
          genBtn.onclick = sendStop;
          genBtn.classList.add('stop');
          genBtn.classList.add('visible');
        }
      }
      break;

    case 'artifact_token':
      {
        const { artifact_id, token } = payload;
        artifactBufs[artifact_id] = (artifactBufs[artifact_id] || '') + token;
        const pane = document.getElementById(`pane-${artifact_id}`);
        if (pane) {
          let container = pane.querySelector('.artifact-rendered');
          if (!container) {
            container = document.createElement('div');
            container.className = 'artifact-rendered stream-cursor';
            pane.innerHTML = '';
            pane.appendChild(container);
          }
          container.innerHTML = marked.parse(artifactBufs[artifact_id], markedOpts);
          container.classList.add('stream-cursor');
        }
      }
      break;

    case 'artifact_complete':
      {
        const { artifact_id, full_text } = payload;
        artifactBufs[artifact_id] = full_text;
        const pane = document.getElementById(`pane-${artifact_id}`);
        if (pane) {
          let container = pane.querySelector('.artifact-rendered');
          if (!container) {
            container = document.createElement('div');
            container.className = 'artifact-rendered';
            pane.innerHTML = '';
            pane.appendChild(container);
          }
          container.classList.remove('stream-cursor');
          container.innerHTML = marked.parse(full_text, markedOpts);
        }
        markTabDone(artifact_id);
      }
      break;

    // ── Mermaid diagram ──
    case 'mermaid_ready':
      renderMermaid(payload.mermaid_code);
      break;

    // ── Generation paused between artifacts ──
    case 'generation_paused':
      {
        const { completed, total, next_title } = payload;
        isGenerating = false;
        // Re-enable input so the user can send a correction
        setSendEnabled(true);
        document.getElementById('chat-input').placeholder =
          'Send a correction to refine this artifact, or click Generate to continue…';
        document.getElementById('chat-input').focus();
        // Repurpose the generate button for the next step
        const genBtn = document.getElementById('generate-btn');
        genBtn.textContent = `⚡ Generate: ${next_title} (${completed + 1}/${total})`;
        genBtn.onclick = sendGenerateNext;
        genBtn.classList.remove('stop');
        genBtn.classList.add('visible');
        // Informational chat message
        appendChatMsg('assistant',
          `**${completed}/${total}** done. Send a correction to refine this artifact, or click **Generate** to continue.`);
      }
      break;

    // ── Generation stopped by user ──
    case 'generation_stopped':
      {
        isGenerating = false;
        markTabDone(payload.artifact_id);
        setSendEnabled(true);
        document.getElementById('chat-input').placeholder =
          'Send feedback to improve this artifact, or click Regenerate…';
        document.getElementById('chat-input').focus();
        const genBtn = document.getElementById('generate-btn');
        genBtn.textContent = '⟳ Regenerate';
        genBtn.onclick = sendGenerateNext;
        genBtn.classList.remove('stop');
        genBtn.classList.add('visible');
        appendChatMsg('assistant',
          'Stopped. Send feedback or click **Regenerate** to try again.');
      }
      break;

    // ── Markdown ready ──
    case 'markdown_ready':
      downloadUrl = payload.download_url;
      document.getElementById('download-btn').href = downloadUrl;
      document.getElementById('download-bar').classList.add('visible');
      isGenerating = false;
      setSendEnabled(true);
      document.getElementById('chat-input').placeholder = 'Send an update to regenerate artifacts…';
      // Switch to Score tab so user sees evaluation first
      switchTabById('evaluation');
      break;

    // ── Error ──
    case 'error':
      _serverErrorReceived = true;
      const errMsg = payload.message || 'An error occurred.';
      if (payload.code === 'no_api_key') {
        // Show a permanent banner — don't just toast
        const overlay = document.getElementById('connecting-overlay');
        overlay.querySelector('p').innerHTML =
          `<strong style="color:#ef4444">API key missing.</strong><br>` +
          `Set <code>OPENROUTER_API_KEY</code> in your <code>.env</code> file ` +
          `and restart the server.`;
        overlay.classList.remove('hidden');
      } else {
        showToast(errMsg);
        isGenerating = false;
        if (currentPhase !== 'DONE') setSendEnabled(true);
      }
      break;

    default:
      break;
  }
}

// ── Phase management ──────────────────────────────────────────────────────
function setPhase(phase) {
  currentPhase = phase;
  const steps = document.querySelectorAll('.phase-step');
  const phaseIdx = PHASE_ORDER.indexOf(phase);

  steps.forEach((el, i) => {
    el.classList.remove('active', 'done');
    if (i < phaseIdx) el.classList.add('done');
    else if (i === phaseIdx) el.classList.add('active');
  });

  if (phase === 'GENERATING') {
    setSendEnabled(false);
  } else if (phase === 'DONE') {
    setSendEnabled(true);
    document.getElementById('chat-input').placeholder = 'Send an update to regenerate artifacts…';
    const genBtn = document.getElementById('generate-btn');
    genBtn.classList.remove('visible', 'stop');
    genBtn.textContent = '⚡ Generate Artifacts';
    genBtn.onclick = sendGenerate;
  } else {
    setSendEnabled(true);
  }
}

// ── Chat helpers ──────────────────────────────────────────────────────────
function appendChatMsg(role, content) {
  const container = document.getElementById('chat-messages');

  // Remove typing indicator if present
  const existing = container.querySelector('.typing-indicator');
  if (existing) existing.parentElement?.remove();

  const div = document.createElement('div');
  div.className = `msg ${role}`;
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = content ? marked.parse(content, markedOpts) : '';
  div.appendChild(bubble);
  container.appendChild(div);
  scrollChatToBottom();
  return div;
}

function showTyping() {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.innerHTML = `<div class="msg-bubble"><div class="typing-indicator">
    <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
  </div></div>`;
  container.appendChild(div);
  scrollChatToBottom();
}

function finishChatStream() {
  if (streamingMsg) {
    const bubble = streamingMsg.querySelector('.msg-bubble');
    bubble.classList.remove('stream-cursor');
    if (streamingBuf) {
      bubble.innerHTML = marked.parse(streamingBuf, markedOpts);
    }
    streamingMsg = null;
    streamingBuf = '';
    scrollChatToBottom();
  }
}

function scrollChatToBottom() {
  const el = document.getElementById('chat-messages');
  el.scrollTop = el.scrollHeight;
}

// ── Tab management ────────────────────────────────────────────────────────
function switchTab(btn) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.artifact-pane').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');
  const pane = document.getElementById(`pane-${btn.dataset.pane}`);
  if (pane) pane.classList.add('active');
}

function switchTabById(paneId) {
  const btn = document.querySelector(`.tab-btn[data-pane="${paneId}"]`);
  if (btn) switchTab(btn);
}

function markTabGenerating(artifactId) {
  const btn = document.querySelector(`.tab-btn[data-pane="${artifactId}"]`);
  if (btn) {
    btn.classList.remove('done');
    btn.classList.add('generating');
  }
}

function markTabDone(artifactId) {
  const btn = document.querySelector(`.tab-btn[data-pane="${artifactId}"]`);
  if (btn) {
    btn.classList.remove('generating');
    btn.classList.add('done');
  }
}

function clearPanePlaceholder(artifactId, title) {
  const pane = document.getElementById(`pane-${artifactId}`);
  if (pane) {
    pane.innerHTML = `<div class="artifact-rendered stream-cursor"></div>`;
  }
}

function showRefinedPlaceholder(show) {
  document.getElementById('refined-placeholder').style.display = show ? 'flex' : 'none';
}

// ── Mermaid rendering ─────────────────────────────────────────────────────
async function renderMermaid(code) {
  // Render inside the Technical Design pane (Architecture Diagram section)
  const pane = document.getElementById('pane-technical_design');
  if (!pane) return;

  const wrapper = document.createElement('div');
  wrapper.className = 'mermaid-wrapper';
  wrapper.style.marginTop = '16px';

  try {
    if (window._mermaid) {
      const id = 'arch-' + Date.now();
      const { svg } = await window._mermaid.render(id, code);
      wrapper.innerHTML = svg;
    } else {
      wrapper.innerHTML = `<pre><code>${escapeHtml(code)}</code></pre>
        <p style="color:var(--muted);font-size:11px;margin-top:8px">
          (Mermaid renderer loading — reload to see diagram)</p>`;
    }
  } catch (e) {
    wrapper.innerHTML = `<p style="color:var(--amber);font-size:12px">Diagram render error — showing source:</p>
      <pre><code>${escapeHtml(code)}</code></pre>`;
  }

  // Append after existing text content
  const existing = pane.querySelector('.artifact-rendered');
  if (existing) {
    existing.appendChild(wrapper);
  } else {
    pane.appendChild(wrapper);
  }
}

// ── User actions ──────────────────────────────────────────────────────────
function sendMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text && pendingAttachments.length === 0) return;
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showToast('Not connected — wait for the server or refresh the page.');
    return;
  }
  if (currentPhase === 'GENERATING' && isGenerating) return;

  // Show user message with attachment names if any
  const displayText = text + (pendingAttachments.length
    ? '\n\n📎 ' + pendingAttachments.map(a => a.name).join(', ')
    : '');
  appendChatMsg('user', displayText || '📎 ' + pendingAttachments.map(a => a.name).join(', '));

  input.value = '';
  input.style.height = 'auto';
  setSendEnabled(false);
  showTyping();

  // Build payload — text attachments are inlined as context, images sent as multimodal
  let fullText = text;
  const imageAttachments = [];

  for (const a of pendingAttachments) {
    if (a.type === 'text') {
      fullText += `\n\n---\n**Attached file: ${a.name}**\n\`\`\`\n${a.text}\n\`\`\`\n---`;
    } else if (a.type === 'image') {
      imageAttachments.push({ type: 'image', name: a.name, data: a.data, media_type: a.media_type });
    }
  }

  const payload = { session_id: sessionId, text: fullText };
  if (imageAttachments.length > 0) {
    payload.attachments = imageAttachments;
  }

  ws.send(JSON.stringify({ type: 'user_message', payload }));

  // Clear attachments
  pendingAttachments = [];
  renderAttachmentPreview();
}

function sendGenerate() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  document.getElementById('generate-btn').classList.remove('visible');
  setSendEnabled(false);
  ws.send(JSON.stringify({ type: 'generate', payload: { session_id: sessionId } }));
}

function sendStop() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(JSON.stringify({ type: 'stop_artifact', payload: { session_id: sessionId } }));
}

function sendGenerateNext() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;
  const genBtn = document.getElementById('generate-btn');
  genBtn.classList.remove('visible');
  genBtn.textContent = '⚡ Generate Artifacts';
  genBtn.onclick = sendGenerate;
  setSendEnabled(false);
  ws.send(JSON.stringify({ type: 'generate_next', payload: { session_id: sessionId } }));
}

function handleKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function newChat() {
  if (ws) ws.close();
  window.location.reload();
}

function setSendEnabled(enabled) {
  const btn = document.getElementById('send-btn');
  const input = document.getElementById('chat-input');
  btn.disabled = !enabled;
  input.disabled = !enabled;
}

// ── Utilities ─────────────────────────────────────────────────────────────
function showToast(message) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 5000);
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// ── Role selection ────────────────────────────────────────────────────────
function showRoleSelection(prompt, roles) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.id = 'role-selection-msg';

  const buttonsHtml = roles.map(r =>
    `<button class="role-btn" onclick="selectRole('${escapeHtml(r)}')">${escapeHtml(r)}</button>`
  ).join('');

  div.innerHTML = `
    <div class="msg-bubble">
      <p>${escapeHtml(prompt)}</p>
      <div class="role-btn-group">${buttonsHtml}</div>
    </div>`;
  container.appendChild(div);
  scrollChatToBottom();
}

function selectRole(role) {
  const selMsg = document.getElementById('role-selection-msg');
  if (selMsg) {
    selMsg.querySelector('.msg-bubble').innerHTML =
      `<p>Select your role:</p><p><strong>${escapeHtml(role)}</strong></p>`;
  }
  appendChatMsg('user', role);
  // Don't show typing or enable input — wait for scope_selection then ready
  ws.send(JSON.stringify({ type: 'set_role', payload: { role } }));
}

// ── Scope selection ───────────────────────────────────────────────────────
function showScopeSelection(prompt, scopes) {
  finishChatStream();
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg assistant';
  div.id = 'scope-selection-msg';

  const buttonsHtml = scopes.map(s =>
    `<button class="role-btn" onclick="selectScope('${escapeHtml(s)}')">${escapeHtml(s)}</button>`
  ).join('');

  div.innerHTML = `
    <div class="msg-bubble">
      <p>${escapeHtml(prompt)}</p>
      <div class="role-btn-group">${buttonsHtml}</div>
    </div>`;
  container.appendChild(div);
  scrollChatToBottom();
}

function selectScope(scope) {
  const selMsg = document.getElementById('scope-selection-msg');
  if (selMsg) {
    selMsg.querySelector('.msg-bubble').innerHTML =
      `<p>Scope:</p><p><strong>${escapeHtml(scope)}</strong></p>`;
  }
  appendChatMsg('user', scope);
  showTyping();
  ws.send(JSON.stringify({ type: 'set_scope', payload: { scope } }));
}

// ── File attachment ───────────────────────────────────────────────────────
async function handleFileSelect(event) {
  const files = Array.from(event.target.files);
  event.target.value = '';  // reset so same file can be reselected

  for (const file of files) {
    const isImage = file.type.startsWith('image/');

    if (isImage) {
      const data = await readFileAsBase64(file);
      pendingAttachments.push({
        type: 'image',
        name: file.name,
        media_type: file.type,
        data,
      });
    } else {
      // Read as text for text/markdown/csv; skip binary formats with a notice
      try {
        const text = await readFileAsText(file);
        // For text attachments, we inline them as context in the message text
        pendingAttachments.push({
          type: 'text',
          name: file.name,
          media_type: file.type,
          text,
        });
      } catch {
        showToast(`Could not read ${file.name} — only text files are supported.`);
      }
    }
  }

  renderAttachmentPreview();
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      // result is "data:<type>;base64,<data>" — strip prefix
      const b64 = reader.result.split(',')[1];
      resolve(b64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsText(file);
  });
}

function renderAttachmentPreview() {
  const preview = document.getElementById('attachment-preview');
  if (!preview) return;
  if (pendingAttachments.length === 0) {
    preview.innerHTML = '';
    return;
  }
  preview.innerHTML = pendingAttachments.map((a, i) => `
    <span class="attachment-chip">
      ${a.type === 'image' ? '🖼' : '📄'} ${escapeHtml(a.name)}
      <button onclick="removeAttachment(${i})" title="Remove">×</button>
    </span>`).join('');
}

function removeAttachment(index) {
  pendingAttachments.splice(index, 1);
  renderAttachmentPreview();
}
