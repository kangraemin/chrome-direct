#!/usr/bin/env python3
"""[로그인] 이 Chrome 프로필의 네이버 로그인 확인 → 로그아웃이면 비밀번호 없이 로그인을 띄운다.
지식iN·카페·네이버폼·네이버 로그인 공공사이트 작업 전에 먼저 돌린다.

  naver_login.py                      # 상태만: exit 0 IN, 2 LOGGED_OUT
  naver_login.py --qr --notify        # QR을 텔레그램(CHROME_DIRECT_TG_*)으로 보냄. 로그인되면 확인 메시지
  naver_login.py --qr [--out q.png]   # QR 로그인 띄우고 QR png + 앱에서 고를 숫자 출력, 로그인될 때까지 대기
  naver_login.py --otp 12345678       # 일회용 번호(네이버 앱 설정 > 로그인 아이디 관리 > 더보기)로 로그인

- 비밀번호는 쓰지 않는다(값 없음, 추측 금지). '로그인 상태 유지'를 켜서 다음 로그아웃을 줄인다.
- QR: 네이버 앱 검색창 옆 렌즈 → QR 스캔 → 앱에 뜬 숫자 중 출력된 숫자 선택. QR은 3분마다 바뀌어 --rounds번 새로 띄운다.
  사용자가 맥 앞에 없으면 png를 폰으로 보내 다른 화면에 띄워 스캔하게 하거나 --otp를 쓴다.
- 일회용 번호 로그인은 네이버가 '종료 예정'이라 공지했다(2026-10 화면 문구). 막히면 QR로.
Exit 0 = 로그인됨, 2 = 로그아웃/시간 초과(사람 몫).
"""
import base64, os, tempfile, time
from pathlib import Path

from _common import Blocked, emit, js, notify, parser, poll, run, tab
import chromectl as c

ap = parser(__doc__)
ap.add_argument("--qr", action="store_true")
ap.add_argument("--otp")
ap.add_argument("--out", default=os.path.join(tempfile.gettempdir(), "naver-qr.png"))
ap.add_argument("--notify", action="store_true", help="QR·숫자·결과를 텔레그램(CHROME_DIRECT_TG_TOKEN/CHAT_ID)으로 보냄")
ap.add_argument("--rounds", type=int, default=3, help="QR 새로 띄우는 횟수(1회 약 3분)")
a = ap.parse_args()

LOGIN = "https://nid.naver.com/nidlogin.login?mode=form&url=https%3A%2F%2Fwww.naver.com"
STATE = r"""const u=location.href;
  if (/nid\.naver\.com\/nidlogin/.test(u)) return {state:'LOGGED_OUT'};
  if (/nid\.naver\.com\/user2\/help\/myInfo/.test(u) && document.body && document.body.innerText.length>50) return {state:'IN'};
  return null;"""


def tg(text, photo=None):
    if a.notify and not notify(text, photo):
        print("TG_SKIP CHROME_DIRECT_TG_TOKEN/CHAT_ID 없음 또는 전송 실패", flush=True)


def big_png(raw):
    try:
        from PIL import Image
        import io
        im = Image.open(io.BytesIO(raw)).convert("L").resize((800, 800), Image.NEAREST)
        buf = io.BytesIO(); im.save(buf, "PNG"); return buf.getvalue()
    except Exception:
        return raw


def status(tid):
    c.goto(tid, "https://nid.naver.com/user2/help/myInfo?lang=ko_KR")
    time.sleep(2)
    return poll(tid, STATE, 20)


def logged_in_after(tid, secs):
    end = time.time() + secs
    while time.time() < end:
        time.sleep(3)
        try:
            u = js(tid, "return location.href")
        except Exception:
            continue
        if "nid.naver.com/nidlogin" not in u:
            return True
    return False


def keep_login(tid):
    js(tid, r"""const k=document.querySelector('#nvlong,[name=nvlong]'); if(k&&!k.checked){k.click();} return !!k""")


def main():
    with tab("https://nid.naver.com/user2/help/myInfo?lang=ko_KR", a) as tid:
        time.sleep(2)
        st = poll(tid, STATE, 25)
        st["profile"] = a.profile
        if st["state"] == "IN":
            emit(st, "OK", "네이버 로그인됨")
            return
        if not (a.qr or a.otp):
            emit(st, "LOGGED_OUT", "--qr 또는 --otp <번호>로 다시 실행")
            raise Blocked("LOGGED_OUT")
        c.goto(tid, LOGIN)
        time.sleep(3)
        keep_login(tid)
        if a.otp:
            js(tid, "document.querySelector('#onetime_login').click(); return 1")
            poll(tid, "return document.querySelector('#OnetimeCode') ? 1 : null", 15)
            js(tid, r"""const i=document.querySelector('#OnetimeCode');
              Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(i, %r);
              i.dispatchEvent(new Event('input',{bubbles:true})); return 1""" % a.otp.strip())
            js(tid, "document.getElementById('otnlog.login').click(); return 1")
            ok = logged_in_after(tid, 20) and status(tid)["state"] == "IN"
            emit({"profile": a.profile}, "OK" if ok else "OTP_FAIL", "" if ok else "번호가 틀렸거나 만료(1회용, 몇 분 유효)")
            if not ok:
                raise Blocked("OTP_FAIL")
            return
        for r in range(a.rounds):
            js(tid, "document.querySelector('#qrcode_login').click(); return 1")
            q = poll(tid, r"""const i=document.querySelector('#qrImage'); if(!i||!i.src.startsWith('data:')) return null;
              const m=document.body.innerText.match(/QR Code\s*\n\s*(\d{1,3})/); return {src:i.src, num:m?m[1]:''}""", 20)
            png = big_png(base64.b64decode(q["src"].split(",", 1)[1].strip()))
            Path(a.out).write_bytes(png)
            tg(f"네이버 로그인: 앱 렌즈로 QR 스캔 → 숫자 {q['num']} 선택 (3분, {r + 1}/{a.rounds})", png)
            print(f"QR {a.out} NUMBER {q['num']} ROUND {r + 1}/{a.rounds}", flush=True)
            if logged_in_after(tid, 175):
                ok = status(tid)["state"] == "IN"
                emit({"profile": a.profile}, "OK" if ok else "UNCONFIRMED", "QR 로그인")
                tg("네이버 로그인 확인됨 — 작업 이어서 함" if ok else "네이버 로그인 확인 안 됨")
                if ok:
                    return
                raise Blocked("UNCONFIRMED")
            c.goto(tid, LOGIN)
            time.sleep(3)
            keep_login(tid)
        emit({"profile": a.profile}, "TIMEOUT", "QR 스캔 안 됨")
        tg("네이버 QR 시간 초과 — 필요하면 다시 띄울게요")
        raise Blocked("QR_TIMEOUT")


run(main, a, f"Chrome 프로필 '{a.profile}'에서 https://nid.naver.com/user2/help/myInfo 를 열어 네이버 로그인 여부만 확인해 IN/LOGGED_OUT 출력. 비밀번호 입력·로그인 시도 금지.")
