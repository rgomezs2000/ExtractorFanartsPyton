"""Desktop launcher for the Django WebView application."""
import importlib.util
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from wsgiref.simple_server import make_server

HOST = "127.0.0.1"
PORT = 8765


def run_django_server() -> None:
    """Run Django in-process for the desktop WebView."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "extractor_fanarts.settings")
    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
    with make_server(HOST, PORT, application) as server:
        server.serve_forever()


def open_window(url: str) -> None:
    """Open a native WebView when available, otherwise fall back to a browser."""
    if importlib.util.find_spec("webview"):
        import webview

        webview.create_window("Extractor Fanarts Python", url, width=1280, height=840)
        webview.start()
        return
    webbrowser.open(url)
    print(f"pywebview no está instalado; abre la app en {url}")


def main() -> None:
    """Start the local server and open the desktop shell."""
    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)
    subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], check=True)
    thread = threading.Thread(target=run_django_server, daemon=True)
    thread.start()
    time.sleep(1)
    open_window(f"http://{HOST}:{PORT}/")


if __name__ == "__main__":
    main()
