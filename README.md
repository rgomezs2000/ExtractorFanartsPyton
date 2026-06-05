# Extractor Fanarts Python

Extractor Fanarts Python es una propuesta de aplicación de escritorio moderna basada en Python, Django y WebView para buscar, validar y descargar fanarts, artes, screenshots, siluetas y recursos visuales desde plataformas compatibles, siempre respetando APIs oficiales, permisos, términos de servicio, derechos de autor, privacidad, restricciones de edad y límites técnicos.

> Estado del proyecto: este documento define el alcance funcional, legal y técnico deseado. La implementación debe seguir estas reglas antes de agregar conectores o automatizaciones.

## Principios obligatorios

La aplicación debe priorizar cumplimiento legal, seguridad y respeto por creadores y plataformas. Por lo tanto, debe evitar explícitamente:

- Scraping masivo no autorizado.
- Saltar captchas de forma automática.
- Saltar bloqueos regionales automáticamente.
- Extraer contenido privado, de grupos cerrados, mensajes directos, cuentas protegidas o servidores sin autorización.
- Automatizar cuentas personales de Discord, Facebook, Instagram, X/Twitter, Threads u otras plataformas cerradas.
- Descargar contenido tras paywalls, suscripciones, exclusividades, compras o membresías.
- Ignorar términos de servicio, límites de API o políticas de robots/automatización.
- Redistribuir imágenes sin licencia o sin autorización.
- Crear datasets sin revisar derechos, licencias, consentimiento, contenido sensible y restricciones de uso.

## Arquitectura propuesta

La aplicación debe organizarse en módulos independientes:

```text
Aplicación de escritorio WebView
├── UI Django moderna
│   ├── Pestaña Descarga
│   ├── Pestaña Configuración
│   └── Consola visual de eventos
├── Backend Django
│   ├── Vistas locales
│   ├── API interna local
│   ├── Gestor de tareas cancelables
│   └── Validadores legales/técnicos
├── Conectores por plataforma
│   ├── APIs oficiales
│   ├── Autenticación bot/OAuth cuando aplique
│   ├── Límites de uso
│   └── Reglas por fuente
├── Motor de descarga
│   ├── Pausas entre solicitudes
│   ├── Control de duplicados
│   ├── Verificación de integridad
│   └── Comparación de hashes
└── Sistema de excepciones
    ├── Red
    ├── Permisos
    ├── Bloqueos regionales
    ├── Captchas
    ├── Términos de servicio
    └── Restricciones NSFW
```

## UI de escritorio WebView para Django

La interfaz debe ser una aplicación de escritorio que ejecute Django localmente y lo muestre en una ventana WebView moderna. El usuario no debería necesitar abrir manualmente una terminal.

Características esperadas:

- Ventana principal con diseño moderno.
- Backend local Django escuchando en `127.0.0.1`.
- WebView embebido para mostrar la UI.
- Interfaz basada en Bootstrap para formularios, pestañas, badges y paneles responsivos.
- AJAX con jQuery para plataformas, configuración, inicio/cancelación y estado de descargas.
- Diálogos Bootbox.js para mensajes informativos, errores, advertencias y confirmaciones.
- Consola visual integrada como panel global inferior para todo el sistema.
- Panel superior con pestañas funcionales para Descarga y Configuración.
- Botones de inicio, cancelación y limpieza dentro de la pestaña Descarga.
- Botones de guardar y restablecer configuración dentro de la pestaña Configuración.
- Bloqueo automático de campos de Descarga y Configuración mientras una descarga está activa, con desbloqueo al cancelar, finalizar o perder conexión con el trabajo.
- Selector de carpeta local mediante diálogo nativo cuando sea posible.
- Empaquetado futuro como ejecutable para escritorio.

## Pestaña Descarga

La pestaña de descarga debe contener el formulario principal.

### Campos principales

- **Categoría de ilustración**: combobox con opciones como:
  - Personajes.
  - Artista / estilo.
  - Concepto.
  - Ropa o accesorio.
  - Herramientas.
  - Fondos o entornos.
  - Poses.
  - Activos o propiedades.
  - Vehículos.
  - Objetos.
  - Acciones.
  - Animales.
- **Nombre de la ilustración o búsqueda**: caja de texto.
- **Página o fuente**: selector de plataforma/conector autorizado.
- **Carpeta de descarga**: campo de ruta con selector de carpeta.
- **Habilitar NSFW / Rule34**: opción desactivada por defecto.
- **Fecha de nacimiento**: requerida únicamente si NSFW está habilitado.
- **Botón Limpiar**: limpia campos y consola cuando corresponda.
- **Botón Buscar / Cancelar**:
  - En reposo muestra `Buscar`.
  - Durante una descarga cambia a `Cancelar`.
  - Al cancelar, detiene nuevas solicitudes y cierra la tarea de forma segura.

### Validación NSFW y Rule34

La opción NSFW debe estar desactivada por defecto.

Reglas obligatorias:

- Si NSFW no está habilitado:
  - Saltar resultados NSFW.
  - Saltar Rule34.
  - Saltar contenido adulto, explícito o sensible.
  - Registrar en consola los descartes cuando sea útil.
- Si NSFW está habilitado:
  - Solicitar fecha de nacimiento.
  - Calcular la edad.
  - Si el usuario es menor de 18 años, mostrar un mensaje de bloqueo y no permitir descargas NSFW.
  - Si el usuario es mayor de 18 años, permitir conectores NSFW compatibles, siempre respetando términos, leyes y filtros de la fuente.

Mensaje recomendado para menores de edad:

```text
No puedes habilitar contenido NSFW porque eres menor de edad. Debes ser mayor de 18 años para continuar.
```

## Pestaña Configuración

La pestaña de configuración debe permitir administrar plataformas, credenciales, límites y comportamiento de descarga.

### Configuración de plataformas

Debe permitir agregar y configurar cada plataforma de forma individual:

- Nombre de plataforma.
- Tipo de conector.
- URL base o instancia cuando aplique.
- API key, token OAuth o credenciales bot autorizadas.
- Estado de autenticación.
- Botón para iniciar sesión cuando la plataforma lo permita oficialmente.
- Botón para cerrar sesión o revocar credenciales locales.
- Indicador de permisos disponibles.
- Indicador de si la plataforma permite búsqueda pública, descarga, metadatos o contenido NSFW.

### Reglas de autenticación

- Usar APIs oficiales cuando existan.
- Usar cuentas bot o aplicaciones registradas cuando la plataforma lo requiera.
- No automatizar cuentas personales en plataformas que lo prohíban.
- No usar self-bots.
- No guardar credenciales en texto plano.
- Permitir al usuario borrar tokens y sesiones.

### Configuración básica

- Carpeta de descarga predeterminada.
- Política de archivos existentes.
- Idioma de la interfaz.
- Tema claro/oscuro.
- Tamaño máximo por archivo.
- Tipos de archivo permitidos: `jpg`, `jpeg`, `png`, `webp`, `gif`, entre otros configurables.
- Cantidad máxima de resultados por búsqueda.
- Limpieza automática de consola al iniciar nueva descarga.

### Configuración avanzada

- Pausa entre solicitudes.
- Límite máximo de concurrencia.
- Número máximo de reintentos.
- Timeout de red.
- Validación de hashes.
- Validación de integridad de imagen.
- Registro detallado para diagnóstico.
- Modo seguro que solo use APIs oficiales.
- Modo estricto de licencias.
- Lista de dominios permitidos.
- Lista de dominios bloqueados.
- Exclusión de contenido sensible.
- Exclusión de contenido generado por IA, si la plataforma proporciona ese metadato.
- Exclusión de contenido sin licencia clara.
- Exportación de reporte de descargas con fuente, autor, licencia y URL original.

## Control de ritmo y no automatización abusiva

La aplicación debe tener una pausa entre solicitudes para evitar comportamiento abusivo.

Reglas recomendadas:

- Pausa predeterminada: 30 segundos entre solicitudes por plataforma.
- Nunca superar límites indicados por API o términos de servicio.
- Si la plataforma informa `rate limit`, pausar hasta que sea permitido continuar.
- No realizar scraping masivo.
- No ejecutar descargas paralelas agresivas.
- Permitir cancelación manual inmediata.

## Captchas

La aplicación no debe resolver captchas automáticamente.

Reglas obligatorias:

- Si aparece un captcha, pausar el proceso.
- Mostrar al usuario que se requiere validación manual.
- Permitir que el usuario complete el captcha manualmente si la plataforma lo permite.
- Si no se puede continuar de forma autorizada, detener la descarga y registrar el error.

Mensaje recomendado:

```text
La plataforma requiere una verificación captcha. Resuélvela manualmente para continuar o cancela la descarga.
```

## Validación legal y de licencias

Antes de descargar o guardar un recurso, el conector debe intentar revisar metadatos disponibles:

- Autor o propietario.
- URL original.
- Licencia.
- Restricciones de uso.
- Si es contenido público o privado.
- Si es contenido gratuito o de pago.
- Si pertenece a paywall, membresía, exclusividad o suscripción.
- Si permite descarga.
- Si permite redistribución.
- Si es NSFW o sensible.

Si la licencia o el permiso no son claros, el modo estricto debe bloquear la descarga o pedir confirmación explícita.

## Política de archivos existentes e integridad

La política deseada es:

- Si el archivo no existe, se guarda.
- Si el archivo existe y está íntegro, se salta.
- Si el archivo existe pero está corrupto, se sobrescribe.
- Si el archivo existe y el hash remoto/local indica diferencia, se puede sobrescribir según configuración.
- Si se descarga un archivo parcial, se debe usar un nombre temporal y renombrarlo solo al completar la descarga.

Para robustez:

- Calcular hash local cuando sea posible.
- Usar hash remoto si la API lo proporciona.
- Validar cabeceras `Content-Length` y tipo MIME.
- Intentar abrir la imagen con una librería de validación antes de marcarla como completada.
- Registrar duplicados detectados.

## Excepciones y errores

La aplicación debe capturar y mostrar errores en la consola visual, detener la descarga cuando el error sea crítico y dejar trazabilidad suficiente para diagnóstico.

### Errores de red

- Sin conexión a Internet.
- DNS no resuelto.
- Timeout.
- Conexión rechazada.
- SSL inválido.
- Proxy incorrecto.
- VPN caída.
- Respuesta incompleta.

### Errores HTTP/API

- `400 Bad Request`.
- `401 Unauthorized`.
- `403 Forbidden`.
- `404 Not Found`.
- `408 Request Timeout`.
- `409 Conflict`.
- `410 Gone`.
- `429 Too Many Requests`.
- `451 Unavailable For Legal Reasons`.
- `500 Internal Server Error`.
- `502 Bad Gateway`.
- `503 Service Unavailable`.
- `504 Gateway Timeout`.

### Errores legales o de permisos

- Términos de servicio no aceptados.
- Plataforma sin API oficial compatible.
- Contenido privado.
- Contenido de pago.
- Contenido exclusivo.
- Contenido sin licencia clara.
- Contenido con redistribución prohibida.
- Contenido bloqueado por edad.
- Contenido NSFW con usuario menor de edad.
- Cuenta bot sin permisos suficientes.
- Token inválido o expirado.

### Errores por bloqueo regional

- Bloqueo por país.
- Código HTTP `451`.
- Código HTTP `403` con indicios de restricción regional.
- Redirección a página de bloqueo.
- Respuesta de proveedor indicando restricción geográfica.

La aplicación puede permitir continuar si el usuario ya usa una VPN legítima y la plataforma permite el acceso, pero no debe saltar bloqueos regionales automáticamente.

### Errores de archivo

- Carpeta destino inexistente.
- Permiso denegado al escribir.
- Espacio insuficiente.
- Nombre de archivo inválido.
- Archivo corrupto.
- Hash no coincide.
- Tipo MIME no permitido.
- Extensión no permitida.

### Errores de proceso

- Descarga cancelada por usuario.
- Tarea en segundo plano fallida.
- Conector no configurado.
- Plataforma deshabilitada.
- Límite diario alcanzado.
- Captcha requerido.

## Consola visual

La consola dentro de la UI debe mostrar eventos importantes:

```text
[INFO] Iniciando búsqueda.
[INFO] Fuente seleccionada: Danbooru.
[INFO] Pausa configurada: 30 segundos.
[WARN] Resultado omitido por licencia no clara.
[WARN] Resultado omitido por contenido NSFW deshabilitado.
[ERROR] La fuente devolvió 451: posible bloqueo regional.
[INFO] Descarga cancelada por el usuario.
```

La consola debe limpiarse:

- Al iniciar una nueva descarga.
- Al cerrar el programa.
- Al pulsar el botón limpiar, si el usuario así lo decide.

## Plataformas y conectores

Cada plataforma debe implementarse como conector independiente, con reglas explícitas.

Ejemplos de reglas por tipo:

- **Boorus**: usar API pública si existe, respetar ratings, tags y límites.
- **Mastodon**: usar API de la instancia, respetar privacidad de publicaciones.
- **Tumblr**: usar API oficial cuando aplique.
- **DeviantArt**: usar API oficial o endpoints permitidos.
- **Discord**: solo bots autorizados en servidores donde el bot tenga permisos; nunca self-bots ni cuentas personales automatizadas.
- **Facebook / Instagram / Threads / X**: solo APIs oficiales y permisos concedidos; no automatizar cuentas personales ni extraer contenido privado.
- **Wikis**: preferir APIs tipo MediaWiki y respetar licencias de archivos.
- **Civitai**: respetar filtros, licencias, contenido sensible y términos.
- **Rule34/NSFW**: deshabilitado por defecto, requiere validación de edad y filtros estrictos.

## Licencia

El archivo `LICENSE` contiene la licencia del repositorio. Actualmente el proyecto está publicado bajo Unlicense, que libera el software al dominio público en jurisdicciones que lo reconocen.

Esta licencia aplica al código del proyecto, pero no otorga derechos sobre imágenes, fanarts, screenshots, personajes, marcas, obras audiovisuales o contenido descargado desde terceros. Cada recurso descargado conserva sus propios derechos, licencias y restricciones de uso.

## Próximos pasos sugeridos

1. Crear el esqueleto Django.
2. Crear la ventana WebView.
3. Implementar la pestaña Descarga.
4. Implementar la pestaña Configuración.
5. Implementar sistema de logs.
6. Implementar gestor de tareas cancelables.
7. Implementar validadores legales/técnicos.
8. Implementar conectores seguros empezando por fuentes con API pública clara.
9. Agregar pruebas unitarias para validación NSFW, edad, archivos corruptos, hashes y errores de red.
10. Documentar cada conector con sus términos, permisos y límites.

## Código incluido en esta versión

Esta versión ya incluye una base funcional del proyecto:

- Proyecto Django en `extractor_fanarts/`.
- App principal en `core/`.
- Modelos para plataformas, credenciales locales y configuración.
- UI WebView/Django con pestañas de descarga y configuración.
- Endpoints JSON para plataformas, configuración, inicio, cancelación y estado de descargas.
- Servicios de cumplimiento para NSFW, edad, licencias, privacidad, paywalls y términos.
- Gestor de descargas en segundo plano con cancelación y consola.
- Conector inicial de URL manual autorizada.
- Registro de conectores placeholder para plataformas que requieren API oficial o implementación específica.
- Helpers de hashes, integridad de imagen y política de sobrescritura/salto.
- Pruebas unitarias para validación de edad, archivos corruptos, mensajes HTTP y endpoints básicos.

## Instalación local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Luego abre `http://127.0.0.1:8000/`.

## Ejecutar como escritorio WebView

```bash
python desktop.py
```

El launcher ejecuta migraciones, inicia Django localmente en `127.0.0.1:8765` y abre una ventana WebView si `pywebview` está instalado. Si WebView no está disponible, abre el navegador predeterminado. La UI carga Bootstrap, jQuery y Bootbox.js desde CDN; para distribución offline conviene empaquetar esas librerías como archivos estáticos locales.

## Ejecutar pruebas

```bash
python manage.py test
```

## Limitaciones actuales

La base funcional no implementa scraping de plataformas cerradas ni descarga masiva. Solo incluye un conector inicial de URL manual autorizada y deja conectores de plataformas como placeholders hasta revisar e implementar cada API oficial, permisos, términos, filtros NSFW y licencias.
