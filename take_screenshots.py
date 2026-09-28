import subprocess, time, json, urllib.request, urllib.parse, socket, base64, os, sys, struct, io, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = tempfile.mkdtemp(prefix="edge_profile_")
BRAIN_DIR = r"C:\Users\user\.gemini\antigravity\brain\ad250e03-0542-46ea-a788-0b1c7bee0db7"

print(f"Starting Edge with user-data-dir: {USER_DATA}", flush=True)

proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9337",
    f"--user-data-dir={USER_DATA}",
    "--allow-file-access-from-files",
    "--disable-web-security",
    "--disable-gpu",
    "--window-size=1400,950",
    "file:///C:/Users/user/.gemini/antigravity/scratch/student-teacher-timetable/test_runner.html"
])

try:
    req = None
    for attempt in range(30):
        try:
            req = urllib.request.urlopen("http://127.0.0.1:9337/json")
            if req:
                print(f"Connected to CDP on attempt {attempt+1}", flush=True)
                break
        except Exception:
            time.sleep(0.5)
    if not req:
        raise RuntimeError("Failed to connect to Edge CDP on port 9337 after 15s")
    pages = json.loads(req.read().decode('utf-8'))
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

    print(f"Target WebSocket URL: {ws_url}", flush=True)
    url_parts = urllib.parse.urlparse(ws_url)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(10.0)
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

    cur_id = [0]
    def cdp_call(method, params=None):
        cur_id[0] += 1
        cid = cur_id[0]
        msg = {"id": cid, "method": method}
        if params: msg["params"] = params
        send(msg)
        while True:
            res = recv_msg()
            if res and res.get("id") == cid:
                return res

    cdp_call("Page.enable")
    cdp_call("Runtime.enable")

    # 1. Wait for test runner to complete all 10 tests
    print("Waiting 4s for test runner execution...", flush=True)
    time.sleep(4.0)
    title_eval = cdp_call("Runtime.evaluate", {"expression": "document.title"})
    title_val = title_eval.get("result", {}).get("value", "")
    print(f"Test Runner Result Title: {title_val}", flush=True)

    # Capture 10/10 Benchmark Screenshot
    res1 = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data1 = base64.b64decode(res1["result"]["data"])
    out_path1 = os.path.join(BRAIN_DIR, "benchmark_10_pass.png")
    with open(out_path1, "wb") as f:
        f.write(img_data1)
    print(f"Saved Benchmark screenshot to {out_path1}", flush=True)

    # 2. Navigate to index.html to test Step 4 Smart Swap & Deletion UI
    print("Navigating to index.html...", flush=True)
    cdp_call("Page.navigate", {"url": "file:///C:/Users/user/.gemini/antigravity/scratch/student-teacher-timetable/index.html"})
    time.sleep(2.0)

    # Load grade2 preset and navigate to Tab 4
    cdp_call("Runtime.evaluate", {"expression": "App.loadPreset('grade2', false); App.setTab(4);"})
    time.sleep(0.8)

    # Click an allocated lesson cell to activate Smart Swap guide
    cdp_call("Runtime.evaluate", {"expression": """
        const k = Object.keys(App.timetable).find(key => App.timetable[key] && App.timetable[key].subject && !App.timetable[key].isLocked);
        if (k) App.onCellClick(k);
    """})
    time.sleep(0.8)

    res2 = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data2 = base64.b64decode(res2["result"]["data"])
    out_path2 = os.path.join(BRAIN_DIR, "step4_smart_swap_guide.png")
    with open(out_path2, "wb") as f:
        f.write(img_data2)
    print(f"Saved Smart Swap Guide screenshot to {out_path2}", flush=True)

    # 3. Synchronize config metadata and view personal deadline calendar
    print("Testing config metadata sync and personal calendar...", flush=True)
    cdp_call("Runtime.evaluate", {"expression": """
        App.clearSwapSelection();
        document.getElementById('cfg-school').value = '국립공주교육대학교부설초등학교';
        document.getElementById('cfg-gradeClass').value = '2학년 2반';
        document.getElementById('cfg-teacherName').value = '홍길동 지도교사';
        App.onConfigChange();
        App.setTeacherFilter(App.teachers[0].name);
        const panel = document.getElementById('personal-deadline-panel');
        if (panel) panel.scrollIntoView({ behavior: 'instant' });
    """})
    time.sleep(0.8)

    res3 = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data3 = base64.b64decode(res3["result"]["data"])
    out_path3 = os.path.join(BRAIN_DIR, "step4_calendar_sync.png")
    with open(out_path3, "wb") as f:
        f.write(img_data3)
    print(f"Saved Calendar Sync screenshot to {out_path3}", flush=True)

    s.close()
    print("All tasks completed successfully!", flush=True)
finally:
    proc.kill()
