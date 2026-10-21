#!/usr/bin/env python3
"""[제출] 카카오톡 공유 미리보기(OG) 캐시를 초기화하고 새 메타 정보를 출력한다.

  kakao_share_cache.py https://site [--check] [--profile P]

- developers.kakao.com/tool/debugger/sharing 에 URL을 넣고 '캐시 초기화' → '메타 정보 조회'.
- --check 면 초기화 없이 조회만 한다.
- 로그아웃이면 QR 로그인 페이지를 열고 QR을 잘라 저장한다. CHROME_DIRECT_TG_TOKEN/CHAT_ID 가 있으면 텔레그램으로도 보낸다.
  QR은 약 4분 40초 유효 → 270초마다 페이지를 새로 열어 새 QR을 낸다(최대 15분). 사람은 카톡 '스캔'만 한다.
- 카카오는 이 캐시 초기화를 API로 열어 두지 않아 화면 조작이다. 비밀번호는 쓰지 않는다(QR 전용).
함정:
- 로그인 판정은 location.hostname 으로 한다. QR 페이지 주소의 continue 파라미터에 developers.kakao.com 이 들어 있어 href로 보면 오판한다.
- 만료되면 '유효 시간이 만료되었습니다' 모달이 QR을 가린다 → 새로고침 버튼 대신 페이지를 다시 연다.
- 이 사이트에선 js_json 이 None 을 돌려준 적이 있어 run_js(IIFE)로 읽는다.
- QR 자르기 비율은 Chrome 창 크기에 따라 어긋날 수 있다. 잘린 그림이 이상하면 qr.png 원본을 보낸다.
Exit 0 = OK, 1 = 실패, 2 = 로그인 시간 초과(사람 몫).
"""
import os, sys, tempfile, time

from _common import Blocked, notify, parser, run, tab
import chromectl as c

DBG = 'https://developers.kakao.com/tool/debugger/sharing'
QR = 'https://accounts.kakao.com/qr_login/?continue=https%3A%2F%2Fdevelopers.kakao.com%2Flogin%3Fcontinue%3D%252Ftool%252Fdebugger%252Fsharing&lang=ko'
TMP = os.path.join(tempfile.gettempdir(), 'kakao-share')

ap = parser(__doc__)
ap.add_argument('site')
ap.add_argument('--check', action='store_true')
a = ap.parse_args()


def send_qr(t):
    c.goto(t, QR); time.sleep(6)
    full, crop = f'{TMP}/qr.png', f'{TMP}/qr_crop.png'
    c.shot(t, full)
    try:
        from PIL import Image
        im = Image.open(full); w, h = im.size
        im.crop((int(w * .41), int(h * .46), int(w * .59), int(h * .71))).save(crop)
    except Exception:
        crop = full
    sent = notify(f'카카오 디벨로퍼스 로그인 QR ({a.site} 공유 캐시) — 카톡 더보기 > 스캔', open(crop, 'rb').read())
    print(f'QR {crop} {time.strftime("%H:%M:%S")}{" (텔레그램 전송)" if sent else ""}', flush=True)


def host(t):
    return c.run_js(t, 'location.hostname')


def click(t, label):
    return c.run_js(t, "(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim().startsWith(%r));"
                       "if(!b)return 'NF';setTimeout(()=>b.click(),10);return 'ok'})()" % label)


def main():
    os.makedirs(TMP, exist_ok=True)
    with tab(DBG, a) as t:
        time.sleep(8)
        if host(t) != 'developers.kakao.com':
            send_qr(t); last = time.time()
            for _ in range(300):
                if host(t) == 'developers.kakao.com':
                    break
                if time.time() - last > 270:
                    send_qr(t); last = time.time()
                time.sleep(3)
            else:
                raise Blocked('LOGIN_TIMEOUT QR 스캔 안 됨')
            time.sleep(6)
        if not c.run_js(t, "!!document.querySelector('input[placeholder*=\"공유할 URL\"]')"):
            c.goto(t, DBG); time.sleep(8)
        c.run_js(t, "(()=>{const i=document.querySelector('input[placeholder*=\"공유할 URL\"]');"
                    "Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(i,%r);"
                    "i.dispatchEvent(new Event('input',{bubbles:true}));return 1})()" % a.site)
        time.sleep(1)
        cleared = ''
        if not a.check:
            if click(t, '캐시 초기화') == 'NF':
                raise RuntimeError('캐시 초기화 버튼 없음')
            time.sleep(5)
            x = c.run_js(t, 'document.body.innerText') or ''
            i = x.find('처리 결과'); cleared = x[i + 5:].split('\n')[0].strip() if i >= 0 else '?'
            print('reset:', cleared)
        click(t, '메타 정보 조회'); time.sleep(6)
        x = c.run_js(t, 'document.body.innerText') or ''
        i = x.find('OG(Open Graph)'); print(x[i:i + 700] if i >= 0 else x[:500])
        print('RESULT: OK', cleared or 'checked')


run(main, a, f"Chrome 프로필 '{a.profile}'에서 {DBG} 를 열어 '공유할 URL'에 {a.site} 를 넣고 "
             f"{'메타 정보 조회만' if a.check else '캐시 초기화 후 메타 정보 조회'} 해서 OG 정보를 출력. 로그인이 필요하면 LOGIN_REQUIRED로 멈춤.")
