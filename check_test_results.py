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
    "--no-first-run",
    "--no-default-browser-check",
    "file:///C:/Users/user/Documents/GitHub/student-teacher-timetable/test_runner.html"
])

try:
    ws_url = None
    for _ in range(15):
        time.sleep(1)
        try:
            req = urllib.request.urlopen("http://127.0.0.1:9352/json")
            pages = json.loads(req.read().decode("utf-8"))
            for p in pages:
                if p.get("type") == "page" and "test_runner.html" in p.get("url", ""):
                    ws_url = p.get("webSocketDebuggerUrl")
                    break
            if ws_url:
                break
        except Exception:
            pass
    
    if not ws_url:
        raise RuntimeError("Could not find test_runner.html page in Edge")
    
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

    # Wait until all tests have completed
    for _ in range(20):
        time.sleep(0.5)
        send({"id": 99, "method": "Runtime.evaluate", "params": {"expression": "typeof testCases !== 'undefined' && testCases.length > 0 && testCases.every(t => t.lastPass !== undefined)"}})
        res = recv_msg()
        if res and res.get("id") == 99 and res.get("result", {}).get("result", {}).get("value") is True:
            break

    send({"id": 1, "method": "Runtime.evaluate", "params": {"expression": "JSON.stringify(testCases.map(t => ({id: t.id, pass: t.lastPass, msg: t.lastMsg})))"}})
    while True:
        res = recv_msg()
        if res and res.get("id") == 1:
            result_obj = res.get("result", {}).get("result", {})
            if "value" in result_obj:
                val = json.loads(result_obj["value"])
                passed = sum(1 for item in val if item.get("pass"))
                print(f"Total: {passed}/{len(val)} passed")
                for item in val:
                    status = "PASS" if item.get("pass") else "FAIL"
                    print(f"{item['id']}: {status} -> {item.get('msg')}")
            else:
                print("No value in result_obj:", result_obj)
            break
finally:
    proc.kill()
