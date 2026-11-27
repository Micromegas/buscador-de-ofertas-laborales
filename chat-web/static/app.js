const form = document.querySelector('#chat-form');
const input = document.querySelector('#message-input');
const messages = document.querySelector('#messages');
const typing = document.querySelector('#typing');
const sendButton = document.querySelector('#send-button');
const newChatButton = document.querySelector('#new-chat');
const sessionStorageKey = 'job-search-chat-session';

function makeSessionId() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function getSessionId() {
  let id = localStorage.getItem(sessionStorageKey);
  if (!id) {
    id = makeSessionId();
    localStorage.setItem(sessionStorageKey, id);
  }
  return id;
}

function scrollToLatest() {
  messages.scrollTop = messages.scrollHeight;
}

function addMessage(text, role, html = false, isError = false) {
  const article = document.createElement('article');
  article.className = `message ${role === 'user' ? 'user-message' : 'assistant-message'}${isError ? ' error-message' : ''}`;

  const avatar = document.createElement('div');
  avatar.className = 'message-avatar';
  avatar.setAttribute('aria-hidden', 'true');
  avatar.textContent = role === 'user' ? 'G' : '✦';

  const bubble = document.createElement('div');
  bubble.className = 'bubble markdown-body';
  if (html) bubble.innerHTML = text;
  else bubble.textContent = text;

  article.append(avatar, bubble);
  messages.append(article);
  scrollToLatest();
}

async function sendMessage(text) {
  addMessage(text, 'user');
  typing.classList.remove('hidden');
  sendButton.disabled = true;
  input.disabled = true;

  try {
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, sessionId: getSessionId() }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo completar la consulta.');
    addMessage(data.replyHtml || data.reply || 'El asistente respondió sin texto.', 'assistant', Boolean(data.replyHtml));
  } catch (error) {
    addMessage(error.message || 'Ocurrió un error al enviar el mensaje.', 'assistant', false, true);
  } finally {
    typing.classList.add('hidden');
    sendButton.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const text = input.value.trim();
  if (!text || sendButton.disabled) return;
  input.value = '';
  input.style.height = 'auto';
  sendMessage(text);
});

input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = `${Math.min(input.scrollHeight, 130)}px`;
});

input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll('.suggestion').forEach((button) => {
  button.addEventListener('click', () => {
    input.value = button.textContent;
    input.focus();
    input.style.height = 'auto';
    input.style.height = `${input.scrollHeight}px`;
  });
});

newChatButton.addEventListener('click', () => {
  localStorage.removeItem(sessionStorageKey);
  messages.replaceChildren();
  addMessage('Conversación nueva. ¿Qué puesto, país y modalidad querés buscar?', 'assistant');
  input.focus();
});
