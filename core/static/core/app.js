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

function setFormsLocked(locked) {
  const controls = $$('#download-form input, #download-form select, #download-form textarea, #download-form button, #platform-form input, #platform-form select, #platform-form textarea, #platform-form button, #settings-form input, #settings-form select, #settings-form textarea, #settings-form button');
  controls.forEach((control) => {
    if (control.id === 'download-button') {
      control.disabled = false;
      return;
    }
    control.disabled = locked;
  });
  $('#settings-panel').classList.toggle('locked-panel', locked);
  $('#platform-list').classList.toggle('locked-panel', locked);
}

function markJobEnded(status) {
  currentJobId = null;
  $('#download-button').textContent = 'Descargar';
  setFormsLocked(false);
  setStatus(status);
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
    item.addEventListener('click', () => {
      if (currentJobId) {
        logLine('[WARN] No se puede editar plataformas mientras una descarga está activa.');
        return;
      }
      fillPlatformForm(platform);
    });
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

function resetSettingsForm() {
  const form = $('#settings-form');
  form.reset();
  form.elements.theme.value = 'dark';
  form.elements.max_results.value = 25;
  form.elements.allowed_extensions.value = 'jpg,jpeg,png,webp,gif';
  form.elements.clear_console_on_new_download.checked = true;
  form.elements.safe_api_only_mode.checked = true;
  form.elements.strict_license_mode.checked = true;
  logLine('[INFO] Configuración del sistema restablecida en pantalla. Pulsa Guardar configuración para persistirla.');
}

async function startDownload(event) {
  event.preventDefault();
  if (currentJobId) {
    try {
      await api(`/api/download/${currentJobId}/cancel/`, { method: 'POST', body: '{}' });
      $('#download-button').textContent = 'Cancelando...';
      setStatus('Cancelando');
    } catch (error) {
      logLine(`[ERROR] ${error.message}`);
      markJobEnded('Error');
    }
    return;
  }
  consoleBox.value = '';
  const data = formToObject(event.currentTarget);
  if (data.nsfw_enabled && !data.birth_date) {
    logLine('[ERROR] Debes indicar fecha de nacimiento para habilitar NSFW.');
    return;
  }
  try {
    setFormsLocked(true);
    const payload = await api('/api/download/start/', { method: 'POST', body: JSON.stringify(data) });
    currentJobId = payload.job.id;
    $('#download-button').textContent = 'Cancelar';
    $('#job-summary').textContent = 'Descarga en curso';
    setStatus('Descargando');
    pollJob();
  } catch (error) {
    logLine(`[ERROR] ${error.message}`);
    markJobEnded('Error');
  }
}

async function pollJob() {
  if (!currentJobId) return;
  try {
    const payload = await api(`/api/download/${currentJobId}/`);
    consoleBox.value = payload.job.logs.join('\n');
    consoleBox.scrollTop = consoleBox.scrollHeight;
    $('#job-summary').textContent = `${payload.job.status} · descargados: ${payload.job.downloaded} · omitidos: ${payload.job.skipped} · errores: ${payload.job.errors}`;
    if (['finished', 'failed', 'cancelled'].includes(payload.job.status)) {
      markJobEnded(payload.job.status);
      return;
    }
    pollingTimer = setTimeout(pollJob, 1000);
  } catch (error) {
    logLine(`[ERROR] Se perdió la conexión con el trabajo: ${error.message}`);
    $('#job-summary').textContent = 'Desconectado';
    markJobEnded('Desconectado');
  }
}

$$('.tab').forEach((button) => button.addEventListener('click', () => switchTab(button)));
$('#nsfw-enabled').addEventListener('change', (event) => {
  $('#birth-date-row').classList.toggle('hidden', !event.target.checked);
});
$('#clear-download-button').addEventListener('click', () => {
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
$('#reset-settings-button').addEventListener('click', resetSettingsForm);
$('#settings-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await api('/api/settings/', { method: 'POST', body: JSON.stringify(formToObject(event.currentTarget)) });
    logLine('[INFO] Configuración del sistema guardada.');
  } catch (error) {
    logLine(`[ERROR] ${error.message}`);
  }
});

loadPlatforms().catch((error) => logLine(`[ERROR] ${error.message}`));
if (pollingTimer) clearTimeout(pollingTimer);
