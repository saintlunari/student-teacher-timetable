import subprocess, time, json, urllib.request, tempfile, urllib.parse, socket, base64, os, struct

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = tempfile.mkdtemp(prefix="edge_scroll_")
BRAIN_DIR = r"C:\Users\user\.gemini\antigravity\brain\ad250e03-0542-46ea-a788-0b1c7bee0db7"

proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9358",
    f"--user-data-dir={USER_DATA}",
    "--allow-file-access-from-files",
    "--disable-web-security",
    "--window-size=1550,1050",
    "file:///C:/Users/user/.gemini/antigravity/scratch/student-teacher-timetable/test_runner.html"
])

time.sleep(2)
try:
    req = urllib.request.urlopen("http://127.0.0.1:9358/json")
    pages = json.loads(req.read().decode("utf-8"))
    ws_url = None
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

    cid = [0]
    def cdp_call(method, params=None):
        cid[0] += 1
        msg = {"id": cid[0], "method": method}
        if params: msg["params"] = params
        send(msg)
        while True:
            res = recv_msg()
            if res and res.get("id") == cid[0]:
                return res

    cdp_call("Page.enable")
    cdp_call("Runtime.enable")

    time.sleep(6) # wait for all tests to run
    # Scroll to bottom
    cdp_call("Runtime.evaluate", {"expression": "window.scrollTo(0, document.body.scrollHeight);"})
    time.sleep(1)

    shot = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data = base64.b64decode(shot["result"]["data"])
    out_file = os.path.join(BRAIN_DIR, "benchmark_16_tc16_detail.png")
    with open(out_file, "wb") as f:
        f.write(img_data)
    print(f"Saved tc16 detail screenshot: {out_file}")
finally:
    proc.kill()
