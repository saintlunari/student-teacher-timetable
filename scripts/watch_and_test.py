"""
watch_and_test.py — 실시간 파일 감시 및 34대 벤치마크 자동 검증·진단 루프 (Harness Loop Engine)

동작 원리:
1. index.html의 파일 변경(Ctrl+S 저장)을 0.5초 주기로 감지합니다.
2. 파일이 수정되면 Microsoft Edge Headless CDP를 구동하여 34개 테스트를 고속 전수 실행합니다.
3. 실행 결과를 분석하여 마크다운 진단 리포트인 `TEST_STATUS.md`를 즉시 갱신합니다.
   - 통과 시: 🟢 34/34 ALL PASSED 초록불 상태 기록
   - 결함 발생 시: 🔴 실패 항목, 구체적 원인, 의심 위치, 복구 가이드를 상세 기록

사용법:
- 상시 감시 모드: python watch_and_test.py
- 1회성 즉시 검증: python watch_and_test.py --once
"""

import subprocess
import time
import json
import urllib.request
import urllib.parse
import tempfile
import socket
import base64
import os
import struct
import io
import sys
import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_FILE = os.path.join(BASE_DIR, "index.html")
TEST_RUNNER_FILE = os.path.join(BASE_DIR, "test_runner.html")
STATUS_FILE = os.path.join(BASE_DIR, "TEST_STATUS.md")

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def run_benchmark_cdp():
    """Headless Edge CDP를 이용하여 test_runner.html을 구동하고 34개 테스트 결과를 수집합니다."""
    user_data = tempfile.mkdtemp(prefix="edge_watch_")
    proc = subprocess.Popen([
        EDGE_PATH,
        "--headless=new",
        "--remote-debugging-port=9352",
        f"--user-data-dir={user_data}",
        "--allow-file-access-from-files",
        "--disable-web-security",
        "--no-first-run",
        "--no-default-browser-check",
        f"file:///{TEST_RUNNER_FILE.replace(os.sep, '/')}"
    ])

    try:
        ws_url = None
        for _ in range(20):
            time.sleep(0.5)
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
            raise RuntimeError("test_runner.html 페이지에 연결할 수 없습니다.")

        url_parts = urllib.parse.urlparse(ws_url)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((url_parts.hostname, url_parts.port))
        key = base64.b64encode(os.urandom(16)).decode("utf-8")
        s.sendall(
            f"GET {url_parts.path} HTTP/1.1\r\n"
            f"Host: {url_parts.hostname}:{url_parts.port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n".encode("utf-8")
        )
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
            b2 = head[1] & 0x7F
            if b2 == 126: length = struct.unpack(">H", s.recv(2))[0]
            elif b2 == 127: length = struct.unpack(">Q", s.recv(8))[0]
            else: length = b2
            payload = bytearray()
            while len(payload) < length:
                chunk = s.recv(length - len(payload))
                if not chunk: break
                payload.extend(chunk)
            return json.loads(payload.decode("utf-8", errors="ignore"))

        # Wait until all tests finish
        for _ in range(30):
            time.sleep(0.5)
            send({
                "id": 99,
                "method": "Runtime.evaluate",
                "params": {"expression": "typeof testCases !== 'undefined' && testCases.length > 0 && testCases.every(t => t.lastPass !== undefined)"}
            })
            res = recv_msg()
            if res and res.get("id") == 99 and res.get("result", {}).get("result", {}).get("value") is True:
                break

        # Fetch results
        send({
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {"expression": "JSON.stringify(testCases.map(t => ({id: t.id, title: t.title, pass: t.lastPass, msg: t.lastMsg})) )"}
        })

        while True:
            res = recv_msg()
            if res and res.get("id") == 1:
                result_obj = res.get("result", {}).get("result", {})
                if "value" in result_obj:
                    return json.loads(result_obj["value"])
                else:
                    raise RuntimeError(f"결과 수신 실패: {result_obj}")
    finally:
        proc.kill()


def update_test_status_report(results):
    """결과 리스트를 기반으로 TEST_STATUS.md 문서를 자동 생성합니다."""
    total = len(results)
    passed = sum(1 for r in results if r.get("pass"))
    failed = total - passed
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    is_all_passed = (failed == 0)

    lines = []
    if is_all_passed:
        lines.append(f"# 🟢 [PASS] 하네스 벤치마크 검증 완벽 통과 ({passed}/{total})")
        lines.append(f"> **검증 일시**: `{now_str}` | **전체 테스트**: `{total}개` 전원 정상 통과 | **결함**: `0건`")
        lines.append("")
        lines.append("🎉 **축하합니다! 모든 핵심 불변성 규칙(Hard Invariants)이 100% 무결성을 만족하고 있습니다.**")
        lines.append("- 차시 순서성 역전 0건 (Zero Lesson Inversion)")
        lines.append("- 잠긴 행사 및 불가 시간 보호 100% (Hard-Lock Invariant)")
        lines.append("- 실습생 시수 공평성 오차 1시간 이내 균등 (Fairness)")
        lines.append("- 압축 차시 및 교생인증/대표수업 스케줄링 무결성 보존")
    else:
        lines.append(f"# 🔴 [ALERT] 하네스 벤치마크 결함 감지 ({passed}/{total} 통과, {failed}건 실패)")
        lines.append(f"> **검증 일시**: `{now_str}` | **통과**: `{passed}` | **실패**: `{failed}`")
        lines.append("")
        lines.append("## 🚨 실패한 테스트 상세 내역 (자가 치유 가이드)")
        for r in results:
            if not r.get("pass"):
                lines.append(f"### ❌ `{r['id']}`: {r.get('title', '테스트')}")
                lines.append(f"- **실패 원인**: `{r.get('msg', '원인 미상')}`")
                lines.append(f"- **조치 권고사항**: `index.html` 내 관련 로직(솔버 정렬, 쿼터 제약, 이벤트 렌더링)을 점검하세요.")
                lines.append("")

    lines.append("")
    lines.append("## 📋 전체 34대 벤치마크 테스트 항목 현황")
    lines.append("| ID | 상태 | 테스트 제목 | 검증 결과 메시지 |")
    lines.append("| :--- | :---: | :--- | :--- |")
    for r in results:
        status_icon = "✅ PASS" if r.get("pass") else "❌ FAIL"
        lines.append(f"| `{r['id']}` | **{status_icon}** | {r.get('title', '')} | {r.get('msg', '')} |")

    report_content = "\n".join(lines) + "\n"

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"[{now_str}] 검증 완료: {passed}/{total} 통과 -> '{STATUS_FILE}' 갱신 완료")


def main():
    once_mode = ("--once" in sys.argv)

    print("=================================================================")
    print(" 🔄 교생 수업 배당표 하네스 루프 엔지니어링 (Watch & Test Engine)")
    print("=================================================================")
    print(f"• 감시 대상: {INDEX_FILE}")
    print(f"• 테스트 러너: {TEST_RUNNER_FILE}")
    print(f"• 진단 보고서: {STATUS_FILE}")
    print(f"• 모드: {'1회성 즉시 검증' if once_mode else '상시 파일 감시 (저장 시 자동 검증)'}")
    print("-----------------------------------------------------------------")

    last_mtime = os.path.getmtime(INDEX_FILE) if os.path.exists(INDEX_FILE) else 0

    # Initial Run
    print("▶ 1차 전체 벤치마크 테스트 구동 중...", flush=True)
    try:
        results = run_benchmark_cdp()
        update_test_status_report(results)
    except Exception as e:
        print(f"❌ 검증 실행 중 오류 발생: {e}")

    if once_mode:
        print("1회성 검증이 완료되었습니다. 종료합니다.")
        return

    print("\n👀 파일을 감시 중입니다. index.html을 수정하고 저장(Ctrl+S)하면 자동으로 테스트가 실행됩니다. (종료: Ctrl+C)\n")
    try:
        while True:
            time.sleep(0.5)
            if os.path.exists(INDEX_FILE):
                cur_mtime = os.path.getmtime(INDEX_FILE)
                if cur_mtime != last_mtime:
                    last_mtime = cur_mtime
                    print(f"\n[변경 감지] index.html 파일 저장이 감지되었습니다 ({datetime.datetime.now().strftime('%H:%M:%S')})")
                    print("▶ 34대 벤치마크 자동 검증 시작...", flush=True)
                    try:
                        results = run_benchmark_cdp()
                        update_test_status_report(results)
                    except Exception as e:
                        print(f"❌ 검증 실행 중 오류 발생: {e}")
    except KeyboardInterrupt:
        print("\n파일 감시가 중단되었습니다.")


if __name__ == "__main__":
    main()
