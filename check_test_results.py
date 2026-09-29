import subprocess, time, json, urllib.request, tempfile, urllib.parse, socket, base64, os, struct, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = tempfile.mkdtemp(prefix="edge_debug_")

proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9352",
    f"--user-data-dir={USER_DATA}",
    "--allow-file-access-from-files",
    "--disable-web-security",
    "file:///C:/Users/user/Documents/GitHub/student-teacher-timetable/test_runner.html"
])

time.sleep(5)
try:
    req = urllib.request.urlopen("http://127.0.0.1:9352/json")
    pages = json.loads(req.read().decode("utf-8"))
    ws_url = None
    for p in pages:
        if p.get("type") == "page" and "test_runner.html" in p.get("url", ""):
            ws_url = p.get("webSocketDebuggerUrl")
            break
    if not ws_url:
        for p in pages:
            if p.get("type") == "page":
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

    send({"id": 1, "method": "Runtime.evaluate", "params": {"expression": "JSON.stringify(testCases.map(t => ({id: t.id, pass: t.lastPass, msg: t.lastMsg})))"}})
    while True:
        res = recv_msg()
        if res and res.get("id") == 1:
            print("Evaluation res:", res)
            result_obj = res.get("result", {}).get("result", {})
            if "value" in result_obj:
                val = json.loads(result_obj["value"])
                for item in val:
                    status = "PASS" if item["pass"] else "FAIL"
                    print(f"{item['id']}: {status} -> {item['msg']}")
            else:
                print("No value in result_obj:", result_obj)
            break
finally:
    proc.kill()
