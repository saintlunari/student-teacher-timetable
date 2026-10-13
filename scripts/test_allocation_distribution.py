import subprocess, time, json, urllib.request, urllib.parse, socket, base64, os, struct, tempfile

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = tempfile.mkdtemp(prefix="edge_test_dist_")
proc = subprocess.Popen([
    EDGE_PATH, "--headless=new", "--remote-debugging-port=9355", f"--user-data-dir={USER_DATA}",
    "--allow-file-access-from-files", "--disable-web-security",
    "file:///C:/Users/user/Documents/GitHub/student-teacher-timetable/index.html"
])
time.sleep(2.5)

try:
    req = urllib.request.urlopen("http://127.0.0.1:9355/json")
    pages = json.loads(req.read().decode('utf-8'))
    ws = pages[0]['webSocketDebuggerUrl']
    url_parts = urllib.parse.urlparse(ws)
    s = socket.socket()
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
    def cdp(method, params=None):
        cur_id[0] += 1
        cid = cur_id[0]
        msg = {"id": cid, "method": method}
        if params: msg["params"] = params
        send(msg)
        while True:
            res = recv_msg()
            if res and res.get("id") == cid:
                return res

    cdp("Runtime.enable")

    js_code = """
    (() => {
        try {
            App.loadPreset('grade3', false);
            App.runAutoAllocation(false);

            const tt = App.timetable;
            const weekCounts = [0, 0, 0, 0];
            let day18Count = 0, day19Count = 0;
            let unassignedCount = 0;
            const teacherHours = {};
            App.teachers.forEach(t => teacherHours[t.name] = 0);

            Object.keys(tt).forEach(k => {
                const cell = tt[k];
                if (cell && cell.subject && !cell.isLocked) {
                    const [d, p] = k.split('-').map(Number);
                    const w = Math.floor(d / 5);
                    if (w < 4) weekCounts[w]++;
                    if (d === 18) day18Count++;
                    if (d === 19) day19Count++;
                    if (!cell.teacher || cell.teacher.trim() === '') unassignedCount++;
                    else teacherHours[cell.teacher] = (teacherHours[cell.teacher] || 0) + 1;
                }
            });

            // Also check Grade 2
            App.loadPreset('grade2', false);
            App.runAutoAllocation(false);
            const g2tt = App.timetable;
            const g2weekCounts = [0, 0];
            let g2day8Count = 0, g2day9Count = 0;
            let g2unassignedCount = 0;
            const g2teacherHours = {};
            App.teachers.forEach(t => g2teacherHours[t.name] = 0);

            Object.keys(g2tt).forEach(k => {
                const cell = g2tt[k];
                if (cell && cell.subject && !cell.isLocked) {
                    const [d, p] = k.split('-').map(Number);
                    const w = Math.floor(d / 5);
                    if (w < 2) g2weekCounts[w]++;
                    if (d === 8) g2day8Count++;
                    if (d === 9) g2day9Count++;
                    if (!cell.teacher || cell.teacher.trim() === '') g2unassignedCount++;
                    else g2teacherHours[cell.teacher] = (g2teacherHours[cell.teacher] || 0) + 1;
                }
            });

            return {
                grade3: { weekCounts, day18Count, day19Count, unassignedCount, teacherHours },
                grade2: { g2weekCounts, g2day8Count, g2day9Count, g2unassignedCount, g2teacherHours }
            };
        } catch(err) {
            return { error: err.message, stack: err.stack };
        }
    })()
    """

    res = cdp("Runtime.evaluate", {"expression": js_code, "returnByValue": True})
    print("res:", res)
    val = res.get("result", {}).get("value")
    print(json.dumps(val, indent=2, ensure_ascii=False))

finally:
    proc.kill()
