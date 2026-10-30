import subprocess, time, json, urllib.request, tempfile, urllib.parse, socket, base64, os, struct, io, sys, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATUS_FILE = os.path.join(BASE_DIR, "TEST_STATUS.md")
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

LEDGER_SECTION = """
---

## 🗂️ 누적 오류 및 회귀 방지 관리 대장 (Cumulative Error & Regression Ledger)
| 오류 ID | 발견 일자 | 오류 현상 요약 | 근본 원인 (Root Cause) | 조치 내역 및 코드 위치 | 연동 테스트 |
| :--- | :---: | :--- | :--- | :--- | :---: |
| **`ERR-01`** | 2026-10-12 | 이동가능(초록색) 슬롯으로 이동 시 잠긴 행사 침범 경고 오탐지 | 강의/참관 슬롯의 강사명(`teacher`)을 실습생 수업 중복으로 잘못 집계 | `runFullDiagnostic` 및 `executeSwap`에서 `this.teachers`에 등록된 실습생 이름만 검사하도록 필터링 | `tc15` |
| **`ERR-02`** | 2026-10-15 | 통합교과(바생·슬생·즐생·즐생(놀이)) 주제별 차시 배치 시 역전 오류 발생 | 통합교과는 주제 중심 모듈형 수업으로 차시 번호 역전이 허용되어야 하나 일반 교과와 동일하게 검사 | `isIntegratedSubject(sub)` 헬퍼 도입 후 `detectTimetableErrors`, `runFullDiagnostic`, `highlightSwapTargets`에서 역전 검사 예외 처리 | `tc28` |
| **`ERR-03`** | 2026-10-20 | 자동 배당 완료 후 Step 1에서 실습생 이름 변경 시 배당표 미반영 | `timetable`, `events`, `morningDuty`, `fullDayTeaching`, `curriculum`에 이전 교생 이름이 그대로 잔류 | `renameTeacherCascade(oldName, newName)` 구현으로 전 상태 객체 및 DOM/모달 100% 연쇄 갱신 | `tc30` |
| **`ERR-04`** | 2026-10-22 | 동일 요일 동일 교생/동일 교과 중복 배정 및 교과서 페이지 역전 미탐지 | 솔버 비용 함수에 일일 동일 교생·교과 하드 페널티 부족 및 차시 번호만 비교하고 페이지(`pages`) 선후 미비교 | 솔버에 일일 중복 금지 제약 추가 및 `parsePageNum` 기반 교과서 페이지 역전 탐지 추가 | `tc31` |
| **`ERR-05`** | 2026-10-30 | 다단원 과목(예: 수학 `98~101쪽 8/10` → 다음 단원 `110~111쪽 2/8`) 선택 시 모든 슬롯이 `🚫불가`로 표시됨 | `highlightSwapTargets`의 `isOrderValid`가 교과서 쪽수(`pages`) 대신 단순 차시 번호(`2 < 8`)만 비교하여 이후 슬롯을 전부 역전으로 차단 | `isOrderValid`에서 쪽수(`pNum`, `cPageNum`)가 존재하면 쪽수 선후 관계를 우선 비교하도록 `detectTimetableErrors`와 판정 기준 100% 통일 | `tc37` |
| **`ERR-06`** | 2026-10-30 | 동일 쪽수 범위(예: 국어 `78~83쪽` 본책 `6/15` & 국어활동 `5/15`) 수업 간 오류 오탐지 및 동일 과목 1:1 교환(`12-1 수학 8/10` ↔ `11-2 수학 7/10`) 허용 버그 | 1) `pPrev >= pNext` 조건으로 인해 동일 쪽수 내 차시 차이가 오류/불가로 판정됨, 2) `isOrderValid`가 교환 대상 두 셀(`sourceKey`, `key`)을 모두 제외하여 동일 과목 두 셀 간 상대 순서를 미검증 | 1) 동일 쪽수 범위 내 차시 병행 허용(`isPageInversion && prev.lessonNum > next.lessonNum`), 2) 1:1 교환 시 동일 과목 간 상대적 쪽수·차시 순서(`pairSafe`) 검증 추가 | `tc37` |
| **`ERR-07`** | 2026-10-30 | Step 2에서 과목 필터(예: `즐생`) 적용 중 백업 저장 시 원본 진도표 앞쪽(`0..N`)이 덮어써짐 | `renderCurriculumTable`에서 필터링된 행에 원본 배열 인덱스를 보존하지 않고 `syncCurriculumFromDOM`이 화면 행 순서(`0..N`)로 덮어씀 | `tr.dataset.idx = idx`로 원본 인덱스를 바인딩하여 정확히 동기화하고, `loadJsonBackup` 시 `timetable`의 `curriculumId`를 기준으로 손상된 진도표 자동 복원 | `tc37` |
"""

def update_test_status_md(results):
    total = len(results)
    passed = sum(1 for r in results if r.get("pass"))
    failed = total - passed
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    if failed == 0:
        lines.append(f"# 🟢 하네스 벤치마크 100% 무결성 달성 ({passed}/{total} 전원 통과)")
        lines.append(f"> **검증 일시**: `{now_str}` | **통과**: `{passed}` | **실패**: `0` (100% PASS)")
    else:
        lines.append(f"# 🔴 [ALERT] 하네스 벤치마크 결함 감지 ({passed}/{total} 통과, {failed}건 실패)")
        lines.append(f"> **검증 일시**: `{now_str}` | **통과**: `{passed}` | **실패**: `{failed}`")
        lines.append("")
        lines.append("## 🚨 실패한 테스트 상세 내역")
        for r in results:
            if not r.get("pass"):
                lines.append(f"- ❌ **`{r['id']}` ({r.get('title', '')})**: `{r.get('msg', '')}`")
    lines.append("")
    lines.append(f"## 📋 전체 {total}대 벤치마크 테스트 항목 현황")
    lines.append("| ID | 상태 | 테스트 제목 | 검증 결과 메시지 |")
    lines.append("| :--- | :---: | :--- | :--- |")
    for r in results:
        status_icon = "✅ PASS" if r.get("pass") else "❌ FAIL"
        lines.append(f"| `{r['id']}` | **{status_icon}** | {r.get('title', '')} | {r.get('msg', '')} |")
    lines.append(LEDGER_SECTION.rstrip())
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

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

    send({"id": 1, "method": "Runtime.evaluate", "params": {"expression": "JSON.stringify(testCases.map(t => ({id: t.id, title: t.title, pass: t.lastPass, msg: t.lastMsg})))"}})
    while True:
        res = recv_msg()
        if res and res.get("id") == 1:
            result_obj = res.get("result", {}).get("result", {})
            if "value" in result_obj:
                val = json.loads(result_obj["value"])
                update_test_status_md(val)
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
