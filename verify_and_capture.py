import subprocess, time, json, urllib.request, urllib.parse, socket, base64, os, sys, struct, io, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = tempfile.mkdtemp(prefix="edge_profile_")
BRAIN_DIR = r"C:\Users\user\.gemini\antigravity\brain\ad250e03-0542-46ea-a788-0b1c7bee0db7"

print(f"Starting Edge with user-data-dir: {USER_DATA}", flush=True)

proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9350",
    f"--user-data-dir={USER_DATA}",
    "--allow-file-access-from-files",
    "--disable-web-security",
    "--disable-gpu",
    "--window-size=1550,1050",
    "file:///C:/Users/user/.gemini/antigravity/scratch/student-teacher-timetable/test_runner.html"
])

try:
    req = None
    for attempt in range(30):
        try:
            req = urllib.request.urlopen("http://127.0.0.1:9350/json")
            if req:
                print(f"Connected to CDP on attempt {attempt+1}", flush=True)
                break
        except Exception:
            time.sleep(0.5)
    if not req:
        raise RuntimeError("Failed to connect to Edge CDP on port 9350 after 15s")
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

    # 1. Wait for test runner to complete all 17 tests
    print("Waiting for test runner execution...", flush=True)
    title_val = ""
    for sec in range(30):
        time.sleep(1.0)
        t_eval = cdp_call("Runtime.evaluate", {"expression": "document.title + ' | ' + (document.getElementById('passed-tests') ? document.getElementById('passed-tests').innerText : '') + '/' + (document.getElementById('total-tests') ? document.getElementById('total-tests').innerText : '')"})
        status_val = t_eval.get("result", {}).get("result", {}).get("value", "")
        print(f"Runner status ({sec+1}s): {status_val}", flush=True)
        if "17/17" in status_val:
            title_val = status_val
            break

    print(f"Final Test Runner Result: {title_val}", flush=True)

    # Capture 17/17 Benchmark Screenshot
    res1 = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data1 = base64.b64decode(res1["result"]["data"])
    out_path1 = os.path.join(BRAIN_DIR, "benchmark_17_pass.png")
    with open(out_path1, "wb") as f:
        f.write(img_data1)
    print(f"Saved Benchmark screenshot to {out_path1}", flush=True)

    # Scroll down to show tc17 details
    cdp_call("Runtime.evaluate", {"expression": "window.scrollTo(0, document.body.scrollHeight);"})
    time.sleep(0.5)
    res_sc = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_sc = base64.b64decode(res_sc["result"]["data"])
    out_path_sc = os.path.join(BRAIN_DIR, "benchmark_17_tc17_detail.png")
    with open(out_path_sc, "wb") as f:
        f.write(img_data_sc)
    print(f"Saved tc17 detail screenshot to {out_path_sc}", flush=True)

    # 2. Navigate to index.html Step 3 (행사 & 불가 시간 등록)
    print("Navigating to index.html Step 3...", flush=True)
    cdp_call("Page.navigate", {"url": "file:///C:/Users/user/.gemini/antigravity/scratch/student-teacher-timetable/index.html"})
    time.sleep(2.0)
    cdp_call("Runtime.evaluate", {"expression": "window.alert = () => {}; window.confirm = () => true;"})

    # Prepare custom stamp and view Step 3
    cdp_call("Runtime.evaluate", {"expression": """
        App.loadPreset('grade2', false);
        App.createCustomStamp({ type: 'meeting', subject: '연구부 협의회', pages: '실습실', teacher: '연구부장', colorKey: 'rose' });
        App.createCustomStamp({ type: 'lecture', subject: 'AI 디지털 교육', pages: '시청각실', teacher: '외부강사', colorKey: 'indigo' });
        App.setTab(3);
    """})
    time.sleep(1.0)
    res_s3 = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_s3 = base64.b64decode(res_s3["result"]["data"])
    out_path_s3 = os.path.join(BRAIN_DIR, "step3_event_grid_and_stamp_bar.png")
    with open(out_path_s3, "wb") as f:
        f.write(img_data_s3)
    print(f"Saved Step 3 Stamp Bar screenshot to {out_path_s3}", flush=True)

    # Open basic stamp colors modal
    cdp_call("Runtime.evaluate", {"expression": "App.openBasicStampColorModal();"})
    time.sleep(1.0)
    res_modal_basic = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_modal_basic = base64.b64decode(res_modal_basic["result"]["data"])
    out_path_modal_basic = os.path.join(BRAIN_DIR, "step3_basic_stamp_color_modal.png")
    with open(out_path_modal_basic, "wb") as f:
        f.write(img_data_modal_basic)
    print(f"Saved Basic Stamp Color Modal screenshot to {out_path_modal_basic}", flush=True)

    cdp_call("Runtime.evaluate", {"expression": "App.closeBasicStampColorModal();"})
    time.sleep(0.5)

    # Open custom stamp creation modal
    cdp_call("Runtime.evaluate", {"expression": "App.openCustomStampModal();"})
    time.sleep(1.0)
    res_modal_custom = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_modal_custom = base64.b64decode(res_modal_custom["result"]["data"])
    out_path_modal_custom = os.path.join(BRAIN_DIR, "step3_custom_stamp_create_modal.png")
    with open(out_path_modal_custom, "wb") as f:
        f.write(img_data_modal_custom)
    print(f"Saved Custom Stamp Create Modal screenshot to {out_path_modal_custom}", flush=True)

    cdp_call("Runtime.evaluate", {"expression": "App.closeCustomStampModal();"})
    time.sleep(0.5)

    # 3. Navigate to Step 4 Timetable (배당표)
    print("Navigating to index.html Step 4...", flush=True)
    cdp_call("Runtime.evaluate", {"expression": """
        App.runAutoAllocation(false);
        App.setTab(4);
    """})
    time.sleep(1.5)
    res_s4 = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_s4 = base64.b64decode(res_s4["result"]["data"])
    out_path_s4 = os.path.join(BRAIN_DIR, "step4_timetable_color_matching.png")
    with open(out_path_s4, "wb") as f:
        f.write(img_data_s4)
    print(f"Saved Step 4 Timetable Color Matching screenshot to {out_path_s4}", flush=True)

    s.close()
    print("All tasks and screenshots completed successfully!", flush=True)
finally:
    proc.kill()
