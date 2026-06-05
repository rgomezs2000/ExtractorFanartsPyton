const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const consoleBox = $('#console');
let currentJobId = null;
let pollingTimer = null;
let platformsCache = [];

function csrfToken() {
  return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function logLine(message) {
  consoleBox.value += `${message}\n`;
  consoleBox.scrollTop = consoleBox.scrollHeight;
}

function setStatus(message) {
  $('#app-status').textContent = message;
}

function formToObject(form) {
  const data = {};
  new FormData(form).forEach((value, key) => { data[key] = value; });
  form.querySelectorAll('input[type="checkbox"]').forEach((input) => { data[input.name] = input.checked; });
  return data;
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken() },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `Error HTTP ${response.status}`);
  }
  return payload;
}

function switchTab(button) {
  $$('.tab').forEach((tab) => tab.classList.remove('active'));
  $$('.panel').forEach((panel) => panel.classList.remove('active'));
  button.classList.add('active');
  $(`#${button.dataset.tab}`).classList.add('active');
}

async function loadPlatforms() {
  const payload = await api('/api/platforms/');
  platformsCache = payload.platforms;
  const select = $('#platform-select');
  select.innerHTML = '';
  platformsCache.forEach((platform) => {
    const option = document.createElement('option');
    option.value = platform.id;
    option.textContent = platform.name;
    select.appendChild(option);
  });
  const list = $('#platform-list');
  list.innerHTML = '';
  if (!platformsCache.length) {
    list.innerHTML = '<p class="muted">Aún no hay plataformas. Agrega una para habilitar descargas.</p>';
    return;
  }
  platformsCache.forEach((platform) => {
    const item = document.createElement('article');
    item.className = 'platform-item';
    item.dataset.id = platform.id;
    item.innerHTML = `<strong>${platform.name}</strong><span>${platform.connector_type} · ${platform.terms_accepted ? 'términos aceptados' : 'faltan términos'}</span>`;
    item.addEventListener('click', () => fillPlatformForm(platform));
    list.appendChild(item);
  });
}

function fillPlatformForm(platform) {
  const form = $('#platform-form');
  Object.entries(platform).forEach(([key, value]) => {
    const input = form.elements[key];
    if (!input) return;
    if (input.type === 'checkbox') input.checked = Boolean(value);
    else input.value = value ?? '';
  });
  form.elements.api_key.value = '';
  form.elements.oauth_token.value = '';
}

function resetPlatformForm() {
  $('#platform-form').reset();
  $('#platform-id').value = '';
  $('#platform-form').elements.enabled.checked = true;
  $('#platform-form').elements.strict_license_mode.checked = true;
  $('#platform-form').elements.supports_public_search.checked = true;
  $('#platform-form').elements.supports_download.checked = true;
  $('#platform-form').elements.rate_limit_seconds.value = 30;
}

async function startDownload(event) {
  event.preventDefault();
  if (currentJobId) {
    await api(`/api/download/${currentJobId}/cancel/`, { method: 'POST', body: '{}' });
    return;
  }
  consoleBox.value = '';
  const data = formToObject(event.currentTarget);
  if (data.nsfw_enabled && !data.birth_date) {
    logLine('[ERROR] Debes indicar fecha de nacimiento para habilitar NSFW.');
    return;
  }
  try {
    const payload = await api('/api/download/start/', { method: 'POST', body: JSON.stringify(data) });
    currentJobId = payload.job.id;
    $('#search-button').textContent = 'Cancelar';
    $('#job-summary').textContent = 'Descarga en curso';
    setStatus('Descargando');
    pollJob();
  } catch (error) {
    logLine(`[ERROR] ${error.message}`);
    setStatus('Error');
  }
}

async function pollJob() {
  if (!currentJobId) return;
  const payload = await api(`/api/download/${currentJobId}/`);
  consoleBox.value = payload.job.logs.join('\n');
  consoleBox.scrollTop = consoleBox.scrollHeight;
  $('#job-summary').textContent = `${payload.job.status} · descargados: ${payload.job.downloaded} · omitidos: ${payload.job.skipped} · errores: ${payload.job.errors}`;
  if (['finished', 'failed', 'cancelled'].includes(payload.job.status)) {
    currentJobId = null;
    $('#search-button').textContent = 'Buscar';
    setStatus(payload.job.status);
    return;
  }
  pollingTimer = setTimeout(pollJob, 1000);
}

$$('.tab').forEach((button) => button.addEventListener('click', () => switchTab(button)));
$('#nsfw-enabled').addEventListener('change', (event) => {
  $('#birth-date-row').classList.toggle('hidden', !event.target.checked);
});
$('#clear-button').addEventListener('click', () => {
  $('#download-form').reset();
  $('#birth-date-row').classList.add('hidden');
  consoleBox.value = '';
  $('#job-summary').textContent = 'Sin descargas activas';
});
$('#download-form').addEventListener('submit', startDownload);
$('#platform-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await api('/api/platforms/', { method: 'POST', body: JSON.stringify(formToObject(event.currentTarget)) });
    logLine('[INFO] Plataforma guardada.');
    resetPlatformForm();
    await loadPlatforms();
  } catch (error) {
    logLine(`[ERROR] ${error.message}`);
  }
});
$('#reset-platform-button').addEventListener('click', resetPlatformForm);
$('#settings-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  await api('/api/settings/', { method: 'POST', body: JSON.stringify(formToObject(event.currentTarget)) });
  logLine('[INFO] Configuración guardada.');
});

loadPlatforms().catch((error) => logLine(`[ERROR] ${error.message}`));
if (pollingTimer) clearTimeout(pollingTimer);
