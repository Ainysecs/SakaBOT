import logging
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

logger = logging.getLogger('saka.keep_alive')

class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        self.do_HEAD()
        self.wfile.write("Saka is alive! 💅✨".encode('utf-8'))

    def log_message(self, format, *args):
        pass

def run_server():
    # Pega a porta exigida pelo Render, ou usa 8080 por padrão
    port = int(os.environ.get("PORT", 8080))
    
    try:
        server = ThreadingHTTPServer(('0.0.0.0', port), Handler)
        logger.info(f"🌐 Servidor Keep-Alive rodando suavemente na porta {port}...")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Falha ao iniciar o servidor Keep-Alive na porta {port}: {e}")

def keep_alive():
    t = Thread(target=run_server, daemon=True)
    t.start()
