/* global $, bootbox */
let currentJobId = null;
let pollingTimer = null;
let platformsCache = [];

function csrfToken() {
  return $('[name=csrfmiddlewaretoken]').first().val();
}

function dialog(type, message, callback) {
  const titleMap = {
    info: 'Información',
    success: 'Operación completada',
    error: 'Error',
    warning: 'Advertencia',
    confirm: 'Confirmación',
  };
  if (typeof bootbox !== 'undefined') {
    if (type === 'confirm') {
      bootbox.confirm({
        title: titleMap.confirm,
        message,
        centerVertical: true,
        buttons: {
          confirm: { label: 'Sí', className: 'btn-primary' },
          cancel: { label: 'No', className: 'btn-outline-secondary' },
        },
        callback,
      });
      return;
    }
    bootbox.alert({
      title: titleMap[type] || titleMap.info,
      message,
      centerVertical: true,
      callback,
    });
    return;
  }
  if (type === 'confirm') {
    callback(window.confirm(message));
    return;
  }
  window.alert(message);
  if (callback) callback();
}

function logLine(message) {
  const $console = $('#console');
  $console.val(`${$console.val()}${message}\n`);
  $console.scrollTop($console[0].scrollHeight);
}

function setStatus(message, variant = 'info') {
  $('#app-status')
    .removeClass('text-bg-info text-bg-success text-bg-danger text-bg-warning text-bg-secondary')
    .addClass(`text-bg-${variant}`)
    .text(message);
}

function formToObject(form) {
  const data = {};
  $.each($(form).serializeArray(), (_index, field) => {
    data[field.name] = field.value;
  });
  $(form).find('input[type="checkbox"]').each((_index, input) => {
    data[input.name] = $(input).is(':checked');
  });
  return data;
}

function api(url, options = {}) {
  return $.ajax({
    url,
    method: options.method || 'GET',
    data: options.body || undefined,
    contentType: 'application/json',
    dataType: 'json',
    headers: { 'X-CSRFToken': csrfToken() },
  }).catch((xhr) => {
    const errorMessage = xhr.responseJSON?.error || xhr.statusText || `Error HTTP ${xhr.status}`;
    return $.Deferred().reject(new Error(errorMessage)).promise();
  });
}

function setFormsLocked(locked) {
  const selector = '#download-form input, #download-form select, #download-form textarea, #download-form button, #platform-form input, #platform-form select, #platform-form textarea, #platform-form button, #settings-form input, #settings-form select, #settings-form textarea, #settings-form button';
  $(selector).each((_index, control) => {
    if (control.id === 'download-button') {
      $(control).prop('disabled', false);
      return;
    }
    $(control).prop('disabled', locked);
  });
  $('#settings-panel, #platform-list').toggleClass('locked-panel', locked);
}

function markJobEnded(status, variant = 'secondary') {
  currentJobId = null;
  $('#download-button').text('Descargar').removeClass('btn-warning').addClass('btn-primary');
  setFormsLocked(false);
  setStatus(status, variant);
}

function refreshPlatformSelect() {
  const $select = $('#platform-select');
  $select.empty();
  platformsCache.forEach((platform) => {
    $('<option>').val(platform.id).text(platform.name).appendTo($select);
  });
}

function renderPlatformList() {
  const $list = $('#platform-list');
  $list.empty();
  if (!platformsCache.length) {
    $list.html('<p class="text-secondary mb-0">Aún no hay plataformas. Agrega una para habilitar descargas.</p>');
    return;
  }
  platformsCache.forEach((platform) => {
    const statusBadge = platform.terms_accepted
      ? '<span class="badge text-bg-success ms-2">términos OK</span>'
      : '<span class="badge text-bg-warning ms-2">faltan términos</span>';
    const $item = $(
      `<button type="button" class="list-group-item list-group-item-action platform-item" data-id="${platform.id}">
        <strong></strong>${statusBadge}<br>
        <span class="text-secondary"></span>
      </button>`,
    );
    $item.find('strong').text(platform.name);
    $item.find('.text-secondary').text(platform.connector_type);
    $item.on('click', () => {
      if (currentJobId) {
        logLine('[WARN] No se puede editar plataformas mientras una descarga está activa.');
        dialog('warning', 'No se puede editar plataformas mientras una descarga está activa. Primero cancela o espera a que termine.');
        return;
      }
      fillPlatformForm(platform);
      dialog('info', `Plataforma cargada para edición: <strong>${$('<div>').text(platform.name).html()}</strong>.`);
    });
    $list.append($item);
  });
}

function loadPlatforms() {
  return api('/api/platforms/').then((payload) => {
    platformsCache = payload.platforms;
    refreshPlatformSelect();
    renderPlatformList();
  });
}

function fillPlatformForm(platform) {
  const form = $('#platform-form')[0];
  Object.entries(platform).forEach(([key, value]) => {
    const input = form.elements[key];
    if (!input) return;
    if (input.type === 'checkbox') $(input).prop('checked', Boolean(value));
    else $(input).val(value ?? '');
  });
  form.elements.api_key.value = '';
  form.elements.oauth_token.value = '';
}

function resetPlatformForm() {
  const form = $('#platform-form')[0];
  form.reset();
  $('#platform-id').val('');
  $(form.elements.enabled).prop('checked', true);
  $(form.elements.strict_license_mode).prop('checked', true);
  $(form.elements.supports_public_search).prop('checked', true);
  $(form.elements.supports_download).prop('checked', true);
  $(form.elements.rate_limit_seconds).val(30);
}

function resetSettingsForm() {
  const form = $('#settings-form')[0];
  form.reset();
  $(form.elements.theme).val('dark');
  $(form.elements.max_results).val(25);
  $(form.elements.allowed_extensions).val('jpg,jpeg,png,webp,gif');
  $(form.elements.clear_console_on_new_download).prop('checked', true);
  $(form.elements.safe_api_only_mode).prop('checked', true);
  $(form.elements.strict_license_mode).prop('checked', true);
  logLine('[INFO] Configuración del sistema restablecida en pantalla. Pulsa Guardar configuración para persistirla.');
  dialog('info', 'Configuración restablecida en pantalla. Pulsa <strong>Guardar configuración</strong> para persistirla.');
}

function requestCancellation() {
  dialog('confirm', '¿Seguro que quieres cancelar la descarga en curso?', (confirmed) => {
    if (!confirmed) return;
    api(`/api/download/${currentJobId}/cancel/`, { method: 'POST', body: '{}' })
      .then(() => {
        $('#download-button').text('Cancelando...');
        setStatus('Cancelando', 'warning');
        logLine('[WARN] Cancelación solicitada por el usuario.');
      })
      .catch((error) => {
        logLine(`[ERROR] ${error.message}`);
        dialog('error', error.message);
        markJobEnded('Error', 'danger');
      });
  });
}

function startDownload(event) {
  event.preventDefault();
  if (currentJobId) {
    requestCancellation();
    return;
  }
  $('#console').val('');
  const data = formToObject(event.currentTarget);
  if (data.nsfw_enabled && !data.birth_date) {
    const message = 'Debes indicar fecha de nacimiento para habilitar NSFW.';
    logLine(`[ERROR] ${message}`);
    dialog('error', message);
    return;
  }
  dialog('confirm', '¿Deseas iniciar la descarga con la configuración actual?', (confirmed) => {
    if (!confirmed) return;
    setFormsLocked(true);
    setStatus('Preparando', 'info');
    api('/api/download/start/', { method: 'POST', body: JSON.stringify(data) })
      .then((payload) => {
        currentJobId = payload.job.id;
        $('#download-button').text('Cancelar').removeClass('btn-primary').addClass('btn-warning');
        $('#job-summary').text('Descarga en curso').removeClass('text-bg-secondary').addClass('text-bg-info');
        setStatus('Descargando', 'info');
        logLine('[INFO] Descarga iniciada. Los formularios están bloqueados hasta finalizar o cancelar.');
        pollJob();
      })
      .catch((error) => {
        logLine(`[ERROR] ${error.message}`);
        dialog('error', error.message);
        markJobEnded('Error', 'danger');
      });
  });
}

function pollJob() {
  if (!currentJobId) return;
  api(`/api/download/${currentJobId}/`)
    .then((payload) => {
      $('#console').val(payload.job.logs.join('\n'));
      $('#console').scrollTop($('#console')[0].scrollHeight);
      $('#job-summary')
        .text(`${payload.job.status} · descargados: ${payload.job.downloaded} · omitidos: ${payload.job.skipped} · errores: ${payload.job.errors}`)
        .removeClass('text-bg-secondary text-bg-info text-bg-success text-bg-danger text-bg-warning')
        .addClass(payload.job.status === 'failed' ? 'text-bg-danger' : 'text-bg-info');
      if (['finished', 'failed', 'cancelled'].includes(payload.job.status)) {
        const variant = payload.job.status === 'finished' ? 'success' : payload.job.status === 'failed' ? 'danger' : 'warning';
        markJobEnded(payload.job.status, variant);
        dialog(payload.job.status === 'failed' ? 'error' : 'info', `Proceso ${payload.job.status}.`);
        return;
      }
      pollingTimer = setTimeout(pollJob, 1000);
    })
    .catch((error) => {
      logLine(`[ERROR] Se perdió la conexión con el trabajo: ${error.message}`);
      $('#job-summary').text('Desconectado').removeClass('text-bg-secondary text-bg-info').addClass('text-bg-warning');
      dialog('warning', `Se perdió la conexión con el trabajo: ${error.message}`);
      markJobEnded('Desconectado', 'warning');
    });
}

function clearDownloadForm() {
  dialog('confirm', '¿Quieres limpiar el formulario de descarga y el log global?', (confirmed) => {
    if (!confirmed) return;
    $('#download-form')[0].reset();
    $('#birth-date-row').addClass('d-none');
    $('#console').val('');
    $('#job-summary').text('Sin descargas activas').removeClass('text-bg-info text-bg-success text-bg-danger text-bg-warning').addClass('text-bg-secondary');
    logLine('[INFO] Formulario de descarga limpiado.');
  });
}

function savePlatform(event) {
  event.preventDefault();
  api('/api/platforms/', { method: 'POST', body: JSON.stringify(formToObject(event.currentTarget)) })
    .then(() => {
      logLine('[INFO] Plataforma guardada.');
      dialog('success', 'Plataforma guardada correctamente.');
      resetPlatformForm();
      return loadPlatforms();
    })
    .catch((error) => {
      logLine(`[ERROR] ${error.message}`);
      dialog('error', error.message);
    });
}

function saveSettings(event) {
  event.preventDefault();
  api('/api/settings/', { method: 'POST', body: JSON.stringify(formToObject(event.currentTarget)) })
    .then(() => {
      logLine('[INFO] Configuración del sistema guardada.');
      dialog('success', 'Configuración del sistema guardada correctamente.');
    })
    .catch((error) => {
      logLine(`[ERROR] ${error.message}`);
      dialog('error', error.message);
    });
}

$(document).ready(() => {
  $('#nsfw-enabled').on('change', (event) => {
    $('#birth-date-row').toggleClass('d-none', !$(event.currentTarget).is(':checked'));
  });
  $('#clear-download-button').on('click', clearDownloadForm);
  $('#download-form').on('submit', startDownload);
  $('#platform-form').on('submit', savePlatform);
  $('#reset-platform-button').on('click', () => {
    resetPlatformForm();
    dialog('info', 'Formulario de plataforma restablecido.');
  });
  $('#reset-settings-button').on('click', resetSettingsForm);
  $('#settings-form').on('submit', saveSettings);

  loadPlatforms()
    .then(() => logLine('[INFO] Interfaz cargada con Bootstrap, jQuery AJAX y Bootbox.'))
    .catch((error) => {
      logLine(`[ERROR] ${error.message}`);
      dialog('error', error.message);
    });
  if (pollingTimer) clearTimeout(pollingTimer);
});
