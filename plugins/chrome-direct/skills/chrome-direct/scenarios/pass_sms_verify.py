#!/usr/bin/env python3
"""[제출] 한국 휴대폰 본인확인 표준창(cert.mobile-ok.com 등, PASS) 문자(SMS) 인증.

  pass_sms_verify.py send [--match mobile-ok]   → 통신사·이름·생년월일·성별·번호까지 넣고, 보안문자 그림을 저장하고 멈춤
  pass_sms_verify.py send --captcha 123456      → 보안문자를 넣고 문자 발송
  pass_sms_verify.py code 123456 [--match ..]   → 폰에 온 인증번호 입력·확인
  pass_sms_verify.py extend                     → 남은 시간 연장

- 사전 조건: 본인확인 창이 이미 열려 있어야 한다(사이트의 '휴대폰 인증' 버튼으로 연다). --match 는 그 탭 주소의 일부.
- 값은 ~/.chrome-direct/info.json(또는 $CHROME_DIRECT_INFO)에서 읽고 출력하지 않는다. 필요한 키:
    {"name": "홍길동", "birth": "1990-01-31", "phone": "010-1234-5678", "gender_digit": "1",
     "carrier": "skt", "mvno": true}
  gender_digit = 주민번호 뒷자리 첫 숫자. carrier = skt|kt|lgu, mvno = 알뜰폰이면 true.
- 보안문자는 그림을 CAPTCHA_PNG 로 저장하고 멈춘다 → 읽어서 `send --captcha <값>` 으로 다시 부른다.
  틀려도 자동 재시도하지 않는다(새 그림을 다시 저장하고 멈춤). 단계마다 다음 칸이 나타나는 방식이라 다시 불러도 이미 채운 칸은 건너뛴다.
- 사람 몫은 폰에 온 인증번호 6자리뿐이다. 창을 오래 두면 '유효시간 만료' → 사이트에서 다시 연다.
- 왜 화면 조작인가: 본인확인은 공개 API가 없다. 칸은 keyup이 있어야 '다음'이 나타나고, 버튼은 press(포인터 이벤트)만 먹는다.
- 검증 범위: SKT 알뜰폰 + mobile-ok/siren24 창에서 send·code 성공. 다른 통신사 버튼 선택자는 같은 규칙(data-telco)으로 짰지만 미검증.
"""
import argparse, base64, os, re, sys, tempfile, time

from _common import personal_info
import chromectl as c

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("cmd", choices=["send", "code", "extend"])
ap.add_argument("value", nargs="?")
ap.add_argument("--captcha")
ap.add_argument("--match", default="cert.mobile-ok.com")
a = ap.parse_args()
CAPTCHA_PNG = os.path.join(tempfile.gettempdir(), "pass-captcha.png")
SETV = """(e,v)=>{e.focus();Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set.call(e,v);
  for(const k of ["input","change","keydown","keyup"])e.dispatchEvent(k.startsWith("key")?new KeyboardEvent(k,{key:"1",bubbles:true}):new Event(k,{bubbles:true}));return e.value.length}"""


def put(t, pick, v):
    """보이는 input 중 pick(JS 식, e 변수)에 맞는 첫 칸에 값을 넣는다. 이미 차 있으면 건너뛴다. 값은 출력하지 않는다."""
    return c.run_js(t, f"""(()=>{{const e=[...document.querySelectorAll("input")].filter(e=>e.offsetParent).find(e=>{pick});
      if(!e)return "NOTFOUND";if(e.value)return "SKIP";return ({SETV})(e,{v!r})}})()""")


def nxt(t):
    c.press(t, text="다음")
    time.sleep(2)


def info_values():
    i = personal_info()
    miss = [k for k in ("name", "birth", "phone", "gender_digit", "carrier") if not i.get(k)]
    if miss:
        sys.exit(f"RESULT: FAILED info.json 에 {', '.join(miss)} 없음 (~/.chrome-direct/info.json)")
    y, m, d = re.fullmatch(r"(\d{4})-?(\d{2})-?(\d{2})", str(i["birth"])).groups()
    return (i["name"], y[2:] + m + d, re.sub(r"\D", "", str(i["phone"])), str(i["gender_digit"]),
            str(i["carrier"]).lower(), bool(i.get("mvno")))


def main():
    if not c.ref(a.match):
        sys.exit(f"RESULT: FAILED '{a.match}' 탭 없음 — 사이트에서 휴대폰 인증 창을 먼저 연다")
    t = a.match
    if a.cmd == "extend":
        c.press(t, text="시간연장")
        print("RESULT: EXTENDED")
        return
    if a.cmd == "code":
        if not re.fullmatch(r"\d{6}", a.value or ""):
            sys.exit("usage: code <6자리>")
        print(put(t, 'e.placeholder=="인증번호"', a.value))
        time.sleep(0.5)
        # 확인 버튼은 press가 안 먹고 DOM click만 먹는다
        c.run_js(t, """setTimeout(()=>[...document.querySelectorAll("button,a")].filter(b=>b.offsetParent)
          .find(b=>["확인","다음"].includes(b.innerText.trim())).click(),10);1""")
        time.sleep(4)
        try:
            body = c.page_text(t)
        except RuntimeError:
            body = "(창 닫힘 — 원래 사이트로 결과 넘김. 사이트 쪽 인증 상태를 따로 확인)"
        print(body[:300])
        print("RESULT:", "FAILED" if re.search(r"일치하지|만료|오류", body) else "DONE")
        return
    name, birth6, phone, gender, carrier, mvno = info_values()
    if "통신사를" in c.page_text(t):
        # 알뜰폰 버튼은 li.tel_item.save 안에 있다(siren24 창은 data-telco가 없어 첫 save 버튼)
        sel = (f"li.tel_item.save button[data-telco={carrier}],li.tel_item.save button" if mvno
               else f"li.tel_item:not(.save) button[data-telco={carrier}]")
        c.press(t, sel=sel)
        time.sleep(2)
    if "인증방법을" in c.page_text(t):
        c.press(t, text="문자(SMS) 인증")
        time.sleep(1)
        # mobile-ok: user_agree_checkbox / siren24(서울평가정보): check_txt
        c.press(t, sel="label[for=user_agree_checkbox],label[for=check_txt]")
        time.sleep(1)
        nxt(t)
    if "이름을" in c.page_text(t):
        put(t, 'e.name=="userName_sms"||e.id=="userName"', name)
        time.sleep(0.5)
        nxt(t)
    if "생년월일/성별" in c.page_text(t):
        put(t, 'e.placeholder=="생년월일 6자리"', birth6)
        time.sleep(0.5)
        put(t, 'e.type=="tel"&&!e.placeholder', gender)
        time.sleep(1.5)
    if "휴대폰번호를" in c.page_text(t):
        put(t, 'e.name=="mobileNo_sms"||e.id=="mobileNo"', phone)
        time.sleep(1.5)
    if "보안문자를" in c.page_text(t):
        if not a.captcha:
            # mobile-ok는 data URL, siren24는 같은 출처 jsp 이미지(#simpleCaptchaImg) → 이미 뜬 그림을 캔버스로 뽑는다(다시 받으면 글자가 바뀜)
            src = c.run_js(t, """(()=>{const d=[...document.querySelectorAll("img")].find(i=>i.src.startsWith("data:"));if(d)return d.src;
              const i=document.getElementById("simpleCaptchaImg"),k=document.createElement("canvas");k.width=i.naturalWidth;k.height=i.naturalHeight;
              k.getContext("2d").drawImage(i,0,0);return k.toDataURL("image/png")})()""", 30)
            open(CAPTCHA_PNG, "wb").write(base64.b64decode(src.split(",", 1)[1]))
            print(f"RESULT: CAPTCHA {CAPTCHA_PNG} — 읽어서 send --captcha <값>")
            return
        put(t, 'e.placeholder=="보안문자"||e.id=="captchaInput"', a.captcha)
        time.sleep(1)
        nxt(t)
        time.sleep(1)
    body = c.page_text(t)
    if "인증번호 6자리" in body:
        print("RESULT: SMS_SENT — 폰에 온 6자리를 code 로")
    else:
        print(body[:300])
        print("RESULT: FAILED")


main()
