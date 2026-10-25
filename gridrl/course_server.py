"""Local step-by-step coursework demo; all updates happen in Python."""
import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .course import Lesson, Settings

ROOT = Path(__file__).resolve().parents[1]


def serve(port=8767):
    lesson = Lesson()
    lock = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def send(self, obj, status=200, mime="application/json; charset=utf-8"):
            body = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/api/state":
                with lock: self.send(lesson.snapshot())
            elif path in ("/", "/course.js", "/course.css"):
                file = "index.html" if path == "/" else path[1:]
                mime = "text/html" if file.endswith("html") else "text/javascript" if file.endswith("js") else "text/css"
                self.send((ROOT/"course_dashboard"/file).read_bytes(), mime=mime+"; charset=utf-8")
            else: self.send({"error": "Not found"}, 404)
        def do_POST(self):
            nonlocal lesson
            if self.headers.get("Origin") not in (None, f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
                self.send({"error":"Cross-origin request rejected"},403)
                return
            try:
                length = int(self.headers.get("Content-Length",0))
                if not 0 < length <= 10000: raise ValueError("Invalid request size")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data,dict): raise ValueError("Expected object")
                with lock:
                    if self.path == "/api/reset": lesson = Lesson(Settings(**data))
                    elif self.path == "/api/step": lesson.advance(data.get("count",1))
                    else:
                        self.send({"error":"Not found"},404)
                        return
                    self.send(lesson.snapshot())
            except (ValueError, TypeError) as exc: self.send({"error":str(exc)},400)
    server=ThreadingHTTPServer(("127.0.0.1",port),Handler)
    print(f"Learning Machine demo: http://127.0.0.1:{port}",flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--port",type=int,default=8767)
    serve(parser.parse_args().port)
