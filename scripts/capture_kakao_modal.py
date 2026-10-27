import subprocess, time, json, urllib.request, urllib.parse, socket, base64, os, sys, struct, io, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = tempfile.mkdtemp(prefix="edge_screenshot_")
OUT_DIR = r"c:\Users\user\Documents\GitHub\student-teacher-timetable"

proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9344",
    f"--user-data-dir={USER_DATA}",
    "--allow-file-access-from-files",
    "--disable-web-security",
    "--disable-gpu",
    "--window-size=1440,960",
    "file:///C:/Users/user/Documents/GitHub/student-teacher-timetable/index.html"
])

try:
    ws_url = None
    for _ in range(20):
        time.sleep(0.5)
        try:
            req = urllib.request.urlopen("http://127.0.0.1:9344/json")
            pages = json.loads(req.read().decode('utf-8'))
            for p in pages:
                if p.get("type") == "page":
                    ws_url = p.get("webSocketDebuggerUrl")
                    break
            if ws_url:
                break
        except Exception:
            pass

    if not ws_url:
        raise RuntimeError("Failed to connect to Edge CDP on port 9344")

    url_parts = urllib.parse.urlparse(ws_url)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((url_parts.hostname, url_parts.port))
    key = base64.b64encode(os.urandom(16)).decode('utf-8')
    s.sendall(f"GET {url_parts.path} HTTP/1.1\r\nHost: {url_parts.hostname}:{url_parts.port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n".encode('utf-8'))
    s.recv(4096)

    def send(obj):
        d = json.dumps(obj).encode('utf-8')
        f = bytearray([0x81, 0x80 | len(d)]) if len(d) <= 125 else bytearray([0x81, 0x80 | 126]) + struct.pack('>H', len(d))
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

    def eval_js(expr):
        msg_id = int(time.time() * 1000) % 100000
        send({"id": msg_id, "method": "Runtime.evaluate", "params": {"expression": expr, "returnByValue": True}})
        while True:
            r = recv_msg()
            if r and r.get("id") == msg_id:
                return r.get("result", {}).get("result", {}).get("value")

    def capture_screenshot(filename):
        send({"id": 777, "method": "Page.captureScreenshot", "params": {"format": "png"}})
        while True:
            r = recv_msg()
            if r and r.get("id") == 777:
                data = r.get("result", {}).get("data")
                if data:
                    out_path = os.path.join(OUT_DIR, filename)
                    with open(out_path, "wb") as f:
                        f.write(base64.b64decode(data))
                    print(f"Captured: {out_path}", flush=True)
                break

    time.sleep(2)
    eval_js("App.loadPreset('grade3', false); App.runAutoAllocation(false); App.setTab(4);")
    time.sleep(0.5)
    allocated_count = eval_js("Object.values(App.timetable || {}).filter(c => c && c.teacher).length")
    teacher_name = eval_js("App.teachers[0].name")
    print(f"Allocated teacher classes count: {allocated_count}, First teacher: {teacher_name}", flush=True)

    capture_screenshot("screenshot_tab4_buttons.png")

    eval_js(f"App.openKakaoScheduleModal('{teacher_name}');")
    time.sleep(0.5)
    eval_js("const el = document.getElementById('kakao-message-preview'); if (el) el.scrollTop = 420;")
    time.sleep(0.3)
    capture_screenshot("screenshot_kakao_modal_teacher_scrolled.png")

    eval_js("App.selectKakaoScheduleTeacher('all');")
    time.sleep(0.5)
    capture_screenshot("screenshot_kakao_modal_all.png")

finally:
    proc.kill()
