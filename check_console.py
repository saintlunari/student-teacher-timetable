import subprocess, time, json, urllib.request, tempfile, urllib.parse, socket, base64, os, struct

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = tempfile.mkdtemp(prefix="edge_debug_console_")

proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9356",
    f"--user-data-dir={USER_DATA}",
    "--allow-file-access-from-files",
    "--disable-web-security",
    "file:///C:/Users/user/.gemini/antigravity/scratch/student-teacher-timetable/test_runner.html"
])

time.sleep(2)
try:
    req = urllib.request.urlopen("http://127.0.0.1:9356/json")
    pages = json.loads(req.read().decode("utf-8"))
    for p in pages:
        print("Page:", p.get("type"), p.get("url"))
    
    ws_url = pages[0]["webSocketDebuggerUrl"]
    for p in pages:
        if "test_runner.html" in p.get("url", ""):
            ws_url = p.get("webSocketDebuggerUrl")
            break

    url_parts = urllib.parse.urlparse(ws_url)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((url_parts.hostname, url_parts.port))
    key = base64.b64encode(os.urandom(16)).decode("utf-8")
    s.sendall(f"GET {url_parts.path} HTTP/1.1\r\nHost: {url_parts.hostname}:{url_parts.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode("utf-8"))
    s.recv(4096)
    
    def send(obj):
        d = json.dumps(obj).encode("utf-8")
        f = bytearray([0x81, 0x80 | len(d)]) if len(d) <= 125 else bytearray([0x81, 0x80 | 126]) + struct.pack(">H", len(d))
        mask = os.urandom(4)
        f.extend(mask)
        f.extend(b ^ mask[i % 4] for i, b in enumerate(d))
        s.sendall(f)

    def recv_msg():
        head = s.recv(2)
        if not head: return None
        b1, b2 = head[0], head[1]
        length = b2 & 0x7F
        if length == 126: length = struct.unpack(">H", s.recv(2))[0]
        elif length == 127: length = struct.unpack(">Q", s.recv(8))[0]
        payload = bytearray()
        while len(payload) < length:
            chunk = s.recv(length - len(payload))
            if not chunk: break
            payload.extend(chunk)
        return json.loads(payload.decode("utf-8", errors="ignore"))

    send({"id": 1, "method": "Log.enable"})
    send({"id": 2, "method": "Runtime.enable"})

    # Check iframe App directly
    send({"id": 3, "method": "Runtime.evaluate", "params": {"expression": "(() => { const f = document.getElementById('app-frame'); return { hasFrame: !!f, hasCW: !!(f && f.contentWindow), hasApp: !!(f && f.contentWindow && f.contentWindow.App), title: document.title, runnerStarted: typeof runnerStarted !== 'undefined' ? runnerStarted : null }; })()", "returnByValue": True}})
    
    for _ in range(15):
        msg = recv_msg()
        if msg:
            if msg.get("id") == 3:
                print("App frame check:", msg.get("result", {}).get("result", {}).get("value"))
            elif "entry" in msg.get("params", {}):
                print("Console Log:", msg["params"]["entry"])
            elif "exceptionDetails" in msg.get("params", {}):
                print("Exception:", msg["params"]["exceptionDetails"])
            elif "text" in msg.get("params", {}):
                print("Message:", msg["params"]["text"])
        time.sleep(0.2)
finally:
    proc.kill()
