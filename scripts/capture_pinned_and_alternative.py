import subprocess, time, json, urllib.request, urllib.parse, socket, base64, os, sys, struct, io, tempfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = tempfile.mkdtemp(prefix="edge_profile_")
ARTIFACT_DIR = r"C:\Users\user\.gemini\antigravity\brain\85611002-e183-4087-81af-826373524762"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

print(f"Starting Edge with user-data-dir: {USER_DATA}", flush=True)

proc = subprocess.Popen([
    EDGE_PATH,
    "--headless=new",
    "--remote-debugging-port=9360",
    f"--user-data-dir={USER_DATA}",
    "--allow-file-access-from-files",
    "--disable-web-security",
    "--disable-gpu",
    "--window-size=1600,1100",
    "file:///C:/Users/user/Documents/GitHub/student-teacher-timetable/index.html"
])

try:
    req = None
    for attempt in range(30):
        try:
            req = urllib.request.urlopen("http://127.0.0.1:9360/json")
            if req:
                print(f"Connected to CDP on attempt {attempt+1}", flush=True)
                break
        except Exception:
            time.sleep(0.5)
    if not req:
        raise RuntimeError("Failed to connect to Edge CDP on port 9360 after 15s")
    pages = json.loads(req.read().decode('utf-8'))
    ws_url = None
    for p in pages:
        if p.get("type") == "page" and "index.html" in p.get("url", ""):
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
        for i, b in enumerate(d):
            f.append(b ^ mask[i % 4])
        s.sendall(f)

    def recv():
        hdr = s.recv(2)
        if not hdr: return None
        l = hdr[1] & 0x7f
        if l == 126: l = struct.unpack('>H', s.recv(2))[0]
        elif l == 127: l = struct.unpack('>Q', s.recv(8))[0]
        payload = bytearray()
        while len(payload) < l:
            c = s.recv(l - len(payload))
            if not c: break
            payload.extend(c)
        return json.loads(payload.decode('utf-8', errors='ignore'))

    def call(m, p={}):
        cid = int(time.time()*1000) % 10000000
        send({"id": cid, "method": m, "params": p})
        while True:
            r = recv()
            if r and r.get("id") == cid: return r

    time.sleep(2)

    # 1. Load grade3 preset, run auto allocation, switch to tab 4, pin 3 classes
    script1 = """
    (() => {
        window.alert = () => {};
        window.confirm = () => true;
        App.loadPreset('grade3', false);
        App.runAutoAllocation(false);
        App.setTab(4);

        // Find 3 valid teaching classes to pin (e.g. from week 1 and week 2)
        const keys = Object.keys(App.timetable).filter(k => {
            const c = App.timetable[k];
            return c && !c.isLocked && c.subject;
        });

        if (keys.length >= 3) {
            App.toggleCellPin(keys[0]);
            App.toggleCellPin(keys[2]);
            App.toggleCellPin(keys[4]);
        }
        return {
            pinnedCount: Object.keys(App.timetable).filter(k => App.timetable[k] && App.timetable[k].isPinned).length,
            pinnedKeys: [keys[0], keys[2], keys[4]]
        };
    })()
    """
    res1 = call("Runtime.evaluate", {"expression": script1, "returnByValue": True})
    print("Pinned classes setup:", res1.get("result", {}).get("value"), flush=True)

    time.sleep(1)

    # Capture 1: Pinned classes view
    shot1 = call("Page.captureScreenshot", {"format": "png"})
    png_data1 = base64.b64decode(shot1["result"]["data"])
    p1 = os.path.join(ARTIFACT_DIR, "verified_pinned_classes.png")
    with open(p1, "wb") as f:
        f.write(png_data1)
    print(f"Captured: {p1} ({len(png_data1)} bytes)", flush=True)

    # 2. Run alternative allocation
    script2 = """
    (() => {
        window.alert = () => {};
        window.confirm = () => true;

        const prevKeys = Object.keys(App.timetable).filter(k => App.timetable[k] && App.timetable[k].isPinned);
        const prevData = prevKeys.map(k => ({
            key: k,
            sub: App.timetable[k].subject,
            lesson: App.timetable[k].lesson,
            teacher: App.timetable[k].teacher
        }));

        App.runAlternativeAllocation();

        const afterData = prevKeys.map(k => ({
            key: k,
            sub: App.timetable[k].subject,
            lesson: App.timetable[k].lesson,
            teacher: App.timetable[k].teacher,
            isPinned: App.timetable[k].isPinned
        }));

        return {
            prev: prevData,
            after: afterData,
            preserved: prevData.every((item, i) => 
                item.sub === afterData[i].sub && 
                String(item.lesson) === String(afterData[i].lesson) && 
                item.teacher === afterData[i].teacher && 
                afterData[i].isPinned
            )
        };
    })()
    """
    res2 = call("Runtime.evaluate", {"expression": script2, "returnByValue": True})
    print("Alternative allocation result:", res2.get("result", {}).get("value"), flush=True)

    time.sleep(1)

    # Capture 2: Alternative allocation view
    shot2 = call("Page.captureScreenshot", {"format": "png"})
    png_data2 = base64.b64decode(shot2["result"]["data"])
    p2 = os.path.join(ARTIFACT_DIR, "verified_alternative_allocation.png")
    with open(p2, "wb") as f:
        f.write(png_data2)
    print(f"Captured: {p2} ({len(png_data2)} bytes)", flush=True)

finally:
    proc.terminate()
    print("Completed screenshot capture successfully.", flush=True)
