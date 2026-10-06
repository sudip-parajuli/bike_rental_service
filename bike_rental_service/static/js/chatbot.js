/* Public rental assistant: one request at a time, with useful failure messages. */
(() => {
  const toggle = document.getElementById('chatbotToggle');
  const panel = document.getElementById('chatbotWindow');
  const form = document.getElementById('chatbotForm');
  if (!form || !panel) return;
  const input = document.getElementById('chatbotInput');
  const messages = document.getElementById('chatbotMessages');
  const send = form.querySelector('button[type="submit"]');
  const fallback = 'The assistant is temporarily unavailable. Please contact EasyMoto on WhatsApp at +977 9851401903.';
  let pending = false;
  toggle.addEventListener('click', () => {
    panel.classList.toggle('active');
    toggle.setAttribute('aria-expanded', String(panel.classList.contains('active')));
    if (panel.classList.contains('active')) input.focus();
  });
  document.getElementById('closeChatBtn').addEventListener('click', () => {
    panel.classList.remove('active');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.focus();
  });
  function addMessage(text, isUser = false) {
    const div = document.createElement('div');
    div.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const message = input.value.trim();
    if (pending || !message || !form.reportValidity()) return;
    pending = true;
    send.disabled = true;
    addMessage(message, true);
    input.value = '';
    const loading = addMessage('Checking your question…');
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 20000);
    try {
      const response = await fetch(form.dataset.chatEndpoint, {
        method: 'POST', credentials: 'same-origin',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message}), signal: controller.signal,
      });
      if (response.status === 429) {
        loading.textContent = 'Please wait a minute before asking another question, or contact EasyMoto on WhatsApp at +977 9851401903.';
      } else {
        const data = await response.json();
        loading.textContent = typeof data.response === 'string' && data.response.trim() ? data.response : fallback;
      }
    } catch {
      loading.textContent = fallback;
    } finally {
      clearTimeout(timeout);
      pending = false;
      send.disabled = false;
      messages.scrollTop = messages.scrollHeight;
    }
  });
})();
