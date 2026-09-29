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

    # 1. Wait for test runner to complete all 16 tests
    print("Waiting for test runner execution...", flush=True)
    title_val = ""
    for sec in range(25):
        time.sleep(1.0)
        t_eval = cdp_call("Runtime.evaluate", {"expression": "document.title + ' | ' + (document.getElementById('passed-tests') ? document.getElementById('passed-tests').innerText : '') + '/' + (document.getElementById('total-tests') ? document.getElementById('total-tests').innerText : '')"})
        status_val = t_eval.get("result", {}).get("result", {}).get("value", "")
        print(f"Runner status ({sec+1}s): {status_val}", flush=True)
        if "16/16" in status_val:
            title_val = status_val
            break

    print(f"Final Test Runner Result: {title_val}", flush=True)

    # Capture 16/16 Benchmark Screenshot
    res1 = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data1 = base64.b64decode(res1["result"]["data"])
    out_path1 = os.path.join(BRAIN_DIR, "benchmark_16_pass.png")
    with open(out_path1, "wb") as f:
        f.write(img_data1)
    print(f"Saved Benchmark screenshot to {out_path1}", flush=True)

    # Scroll down to show tc16 details
    cdp_call("Runtime.evaluate", {"expression": "window.scrollTo(0, document.body.scrollHeight);"})
    time.sleep(0.5)
    res_sc = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_sc = base64.b64decode(res_sc["result"]["data"])
    out_path_sc = os.path.join(BRAIN_DIR, "benchmark_16_tc16_detail.png")
    with open(out_path_sc, "wb") as f:
        f.write(img_data_sc)
    print(f"Saved tc16 detail screenshot to {out_path_sc}", flush=True)

    # 2. Navigate to index.html Step 2 to show Curriculum Database Modal
    print("Navigating to index.html Step 2...", flush=True)
    cdp_call("Page.navigate", {"url": "file:///C:/Users/user/.gemini/antigravity/scratch/student-teacher-timetable/index.html"})
    time.sleep(2.0)
    cdp_call("Runtime.evaluate", {"expression": "window.alert = () => {}; window.confirm = () => true;"})

    # Open modal, select Grade 3 Math (수학 64차시)
    cdp_call("Runtime.evaluate", {"expression": "App.setTab(2); App.openCurriculumDbModal(); App.setCurriculumDbGrade(3); App.setCurriculumDbSubject('수학');"})
    time.sleep(1.0)
    res_math = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_math = base64.b64decode(res_math["result"]["data"])
    out_path_math = os.path.join(BRAIN_DIR, "step2_curriculum_db_grade3_math.png")
    with open(out_path_math, "wb") as f:
        f.write(img_data_math)
    print(f"Saved Grade 3 Math DB Modal screenshot to {out_path_math}", flush=True)

    # Switch to Art (미술 30차시)
    cdp_call("Runtime.evaluate", {"expression": "App.setCurriculumDbSubject('미술');"})
    time.sleep(1.0)
    res_art = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_art = base64.b64decode(res_art["result"]["data"])
    out_path_art = os.path.join(BRAIN_DIR, "step2_curriculum_db_grade3_art.png")
    with open(out_path_art, "wb") as f:
        f.write(img_data_art)
    print(f"Saved Grade 3 Art DB Modal screenshot to {out_path_art}", flush=True)

    # Switch to Music (음악 34차시)
    cdp_call("Runtime.evaluate", {"expression": "App.setCurriculumDbSubject('음악');"})
    time.sleep(1.0)
    res_music = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_music = base64.b64decode(res_music["result"]["data"])
    out_path_music = os.path.join(BRAIN_DIR, "step2_curriculum_db_grade3_music.png")
    with open(out_path_music, "wb") as f:
        f.write(img_data_music)
    print(f"Saved Grade 3 Music DB Modal screenshot to {out_path_music}", flush=True)

    # Switch to Social Studies (사회 45차시)
    cdp_call("Runtime.evaluate", {"expression": "App.setCurriculumDbSubject('사회');"})
    time.sleep(1.0)
    res_soc = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_soc = base64.b64decode(res_soc["result"]["data"])
    out_path_soc = os.path.join(BRAIN_DIR, "step2_curriculum_db_grade3_social.png")
    with open(out_path_soc, "wb") as f:
        f.write(img_data_soc)
    print(f"Saved Grade 3 Social Studies DB Modal screenshot to {out_path_soc}", flush=True)

    # Switch to PE (체육 53차시)
    cdp_call("Runtime.evaluate", {"expression": "App.setCurriculumDbSubject('체육');"})
    time.sleep(1.0)
    res_pe = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_pe = base64.b64decode(res_pe["result"]["data"])
    out_path_pe = os.path.join(BRAIN_DIR, "step2_curriculum_db_grade3_pe.png")
    with open(out_path_pe, "wb") as f:
        f.write(img_data_pe)
    print(f"Saved Grade 3 PE DB Modal screenshot to {out_path_pe}", flush=True)

    # Switch to Science (과학 48차시)
    cdp_call("Runtime.evaluate", {"expression": "App.setCurriculumDbSubject('과학');"})
    time.sleep(1.0)
    res_sci = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_sci = base64.b64decode(res_sci["result"]["data"])
    out_path_sci = os.path.join(BRAIN_DIR, "step2_curriculum_db_grade3_science.png")
    with open(out_path_sci, "wb") as f:
        f.write(img_data_sci)
    print(f"Saved Grade 3 Science DB Modal screenshot to {out_path_sci}", flush=True)

    # Switch to English (영어 31차시)
    cdp_call("Runtime.evaluate", {"expression": "App.setCurriculumDbSubject('영어');"})
    time.sleep(1.0)
    res_eng = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_eng = base64.b64decode(res_eng["result"]["data"])
    out_path_eng = os.path.join(BRAIN_DIR, "step2_curriculum_db_grade3_english.png")
    with open(out_path_eng, "wb") as f:
        f.write(img_data_eng)
    print(f"Saved Grade 3 English DB Modal screenshot to {out_path_eng}", flush=True)

    # Switch to Korean (국어 102차시)
    cdp_call("Runtime.evaluate", {"expression": "App.setCurriculumDbSubject('국어');"})
    time.sleep(1.0)
    res_kor = cdp_call("Page.captureScreenshot", {"format": "png"})
    img_data_kor = base64.b64decode(res_kor["result"]["data"])
    out_path_kor = os.path.join(BRAIN_DIR, "step2_curriculum_db_grade3.png")
    with open(out_path_kor, "wb") as f:
        f.write(img_data_kor)
    print(f"Saved Grade 3 Korean DB Modal screenshot to {out_path_kor}", flush=True)

    # Close modal
    cdp_call("Runtime.evaluate", {"expression": "App.closeCurriculumDbModal();"})
    time.sleep(0.5)

    s.close()
    print("All tasks and screenshots completed successfully!", flush=True)
finally:
    proc.kill()
