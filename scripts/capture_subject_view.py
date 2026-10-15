import subprocess, time, json, urllib.request, urllib.parse, socket, base64, os, sys, struct, io, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = tempfile.mkdtemp(prefix="edge_profile_subj_")
BRAIN_DIR = r"C:\Users\user\.gemini\antigravity\brain\85611002-e183-4087-81af-826373524762"

os.makedirs(BRAIN_DIR, exist_ok=True)

proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9462",
    f"--user-data-dir={USER_DATA}",
    "--allow-file-access-from-files",
    "--disable-web-security",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-gpu",
    "--window-size=1650,1200",
    "file:///C:/Users/user/Documents/GitHub/student-teacher-timetable/index.html"
])

try:
    ws_url = None
    for attempt in range(20):
        time.sleep(1.0)
        try:
            req = urllib.request.urlopen("http://127.0.0.1:9462/json")
            pages = json.loads(req.read().decode('utf-8'))
            for p in pages:
                if p.get("type") == "page" and "index.html" in p.get("url", ""):
                    ws_url = p.get("webSocketDebuggerUrl")
                    break
            if ws_url:
                break
        except Exception:
            pass

    if not ws_url:
        raise RuntimeError("Failed to connect to Edge CDP on port 9462 after 20s")

    url_parts = urllib.parse.urlparse(ws_url)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15.0)
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
        if length == 126: length = struct.unpack('>H', s.recv(2))[0]
        elif length == 127: length = struct.unpack('>Q', s.recv(8))[0]
        payload = bytearray()
        while len(payload) < length:
            chunk = s.recv(length - len(payload))
            if not chunk: break
            payload.extend(chunk)
        return json.loads(payload.decode('utf-8', errors='ignore'))

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

    for _ in range(15):
        eval_res = cdp_call("Runtime.evaluate", {"expression": "typeof App !== 'undefined' && App !== null"})
        if eval_res.get("result", {}).get("result", {}).get("value") is True:
            break
        time.sleep(0.5)

    cdp_call("Runtime.evaluate", {
        "expression": """
          window.alert = () => {};
          window.confirm = () => true;
          App.loadPreset('grade2', false);
          App.runAutoAllocation(false);
          App.setTab(4);
          App.setSubjectFilter('국어');
        """
    })
    time.sleep(0.8)

    # Scroll to the personalized deadline panel for Korean
    cdp_call("Runtime.evaluate", {
        "expression": """
          const el = document.getElementById('personal-deadline-panel');
          if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
        """
    })
    time.sleep(0.5)

    shot = cdp_call("Page.captureScreenshot", {"format": "png"})
    if "result" in shot and "data" in shot["result"]:
        p = os.path.join(BRAIN_DIR, "verified_subject_view_korean.png")
        with open(p, "wb") as f:
            f.write(base64.b64decode(shot["result"]["data"]))
        print(f"Captured: {p}", flush=True)

    s.close()
finally:
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except Exception:
        proc.kill()
