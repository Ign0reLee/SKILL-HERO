#!/usr/bin/env python3
# Skill Hero — 라이브 서버. skill-hero.html 과 상태 JSON 을 HTTP 로 서빙한다.
# Claude 가 도는 곳(로컬이든 SSH 원격이든)에서 실행 → 로컬 브라우저로 접속(원격이면 VS Code 포트 포워딩).
#   python3 skill-hero-serve.py [PORT]      (기본 8777)
# 의존성 0 (파이썬 표준 라이브러리).
import http.server, os, sys, json

HERE  = os.path.dirname(os.path.abspath(__file__))
HTML  = os.path.join(HERE, "skill-hero.html")
STATE = os.environ.get("SKILL_HERO_STATE") or os.path.join(os.path.expanduser("~"), ".claude", "skill-hero-state.json")
PORT  = int(os.environ.get("SKILL_HERO_PORT") or (sys.argv[1] if len(sys.argv) > 1 else 8777))
IDLE  = json.dumps({"phase": "idle", "label": "대기 중...", "agents": [{"name": "main"}], "skills": [], "hp": 100},
                   ensure_ascii=False).encode("utf-8")

class H(http.server.BaseHTTPRequestHandler):
    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        p = self.path.split("?", 1)[0]
        if p in ("/", "/index.html", "/skill-hero.html"):
            try: self._send(open(HTML, "rb").read(), "text/html; charset=utf-8")
            except Exception: self.send_error(404)
        elif p == "/skill-hero-state.json":
            try: body = open(STATE, "rb").read()
            except Exception: body = IDLE
            self._send(body, "application/json; charset=utf-8")
        else:
            self.send_error(404)
    def log_message(self, *a): pass  # 조용히

if __name__ == "__main__":
    print("Skill Hero 서버: http://localhost:%d   (상태: %s)" % (PORT, STATE), flush=True)
    try:
        http.server.HTTPServer(("127.0.0.1", PORT), H).serve_forever()
    except OSError as e:
        print("포트 %d 사용 불가(이미 켜져 있을 수 있음): %s" % (PORT, e), flush=True)
