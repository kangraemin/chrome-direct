---
name: chrome-direct
description: Run repeated web actions in the user's real Mac Chrome without an LLM, using AppleScript + JS scenario scripts (Gmail search and verification codes, Google Forms read/fill, Notion page export, generic page keyword check, Google account check). Use this before asking the user to do a login or lookup step in the browser, when the user is already signed in to the site in Chrome.
---

# chrome-direct

`scenarios/`의 스크립트는 `chromectl.py`(AppleScript `execute javascript` + cliclick)로 실제 Chrome의 **새 탭**을 조작하고, 끝나면 그 탭을 닫는다.

```
python3 ${CLAUDE_SKILL_DIR}/scenarios/<scenario>.py ... [--profile "Default"] [--no-fallback] [--keep-tab]
```

- 출력은 JSON 한 덩어리와 마지막 줄 `RESULT: <STATUS> ...`다.
- 종료 코드는 0 성공, 1 실패, 2 막힘(로그인 필요·이미 제출·잠금)이다.
- 2는 사용자에게 이유를 그대로 전한다.

## 사전 조건
- macOS, Google Chrome, Python 3.9 이상.
- 처음 쓰기 전, 또는 어떤 스크립트든 종료코드 2와 권한·"Apple Events" 안내가 나오면 먼저 `python3 ${CLAUDE_SKILL_DIR}/chromectl.py setup`을 돌린다.
  - 필수 설정(cliclick, 자동화·손쉬운 사용 권한, Chrome 'Apple Events의 자바스크립트 허용')을 점검하고 켤 수 있는 건 바로 켠다. `READY`면 끝.
  - `TODO` 줄은 사람 몫이다(권한 창 '허용', 열어 둔 설정 화면에서 켜기). 사람이 할 일은 기다리는 명령을 돌리기 **전에** 먼저 사용자에게 말한다 — 너는 명령이 끝나야 출력을 보므로 기다리는 중에는 전할 수 없다.
  - 'Apple Events의 자바스크립트 허용'은 setup이 진짜 마우스로 그 항목 위에 올린 뒤 눌러 자동으로 켠다(System Events click은 Chrome이 무시). 설정은 프로필마다 따로다.
  - `TODO js`로 끝나면(자동 클릭 실패): 먼저 사용자에게 "곧 Chrome '보기 > 개발자 정보' 메뉴가 펼쳐집니다. 선택된 'Apple Events의 자바스크립트 허용'을 반드시 눌러 주세요"라고 말한 뒤 `chromectl.py setup --wait-js`를 백그라운드로 돌린다(메뉴를 펼치고 최대 120초 기다림). 끝나면 결과를 보고한다.
  - 메뉴가 펼쳐진 동안 Chrome은 Apple Events에 답하지 않는다(다른 명령이 시간 초과).
- 조작할 사이트에는 해당 Chrome 프로필로 미리 로그인해 둔다.

## 설정(환경변수, 모두 선택)
- `CHROME_DIRECT_PROFILE`: 기본 Chrome 프로필 폴더 이름(기본 `Default`, `chrome://version`의 프로필 경로 끝에서 확인).
- `CHROME_DIRECT_GOOGLE_ACCOUNT`: Gmail 시나리오와 `google_relogin`이 쓸 Google 계정.
- `CHROME_DIRECT_INFO`: 폼 자동 입력에 쓸 개인정보 JSON 경로(기본 `~/.chrome-direct/info.json`). 본인확인용 키: `name` `birth` `phone` `gender_digit` `carrier` `mvno`. 값은 출력하지 않는다.
- `CHROME_DIRECT_TG_TOKEN` / `CHROME_DIRECT_TG_CHAT_ID`: 있으면 로그인 QR을 텔레그램으로 보낸다(선택).
- `CHROME_DIRECT_CODEX_SCRIPT`: Codex 폴백 래퍼 스크립트 경로(선택, 아래 참고).

## 시나리오

| 스크립트 | 하는 일 | 종류 |
|---|---|---|
| `google_account.py [--expect me@gmail.com]` | 이 프로필에 로그인된 Google 계정 확인 | 읽기 |
| `gmail_search.py "<검색어>" [--limit N] [--open N] [--proof x.pdf]` | Gmail 검색 결과 목록, N번째 메일 열어 읽기 | 읽기 |
| `gmail_code.py "<검색어>" [--newer 20m] [--link 패턴]` | 최근 메일에서 인증번호(`CODE n`) 또는 링크(`LINK url`) 뽑기 | 읽기 |
| `gform_read.py <url> [--skeleton answers.json]` | 구글폼 구조(질문·필수·선택지) 덤프 | 읽기 |
| `gform_fill.py <url> answers.json [--submit --lock-id 이름]` | 구글폼 채우기, `--submit`이 있을 때만 제출 | 제출 |
| `page_check.py <url> --kw a --kw b [--name]` | 아무 페이지에서 키워드가 든 줄과 링크 뽑기 | 읽기 |
| `notion_export.py <page_id> <out_dir>` | 노션 페이지 트리를 로컬 마크다운으로 내보내기(로그인된 탭의 내부 API 사용) | 읽기 |
| `naver_login.py [--qr --notify] [--otp N]` | 네이버 로그인 확인(exit 0 IN, 2 LOGGED_OUT). `--qr --notify`면 QR+고를 숫자를 텔레그램으로 보내고 스캔될 때까지 대기(3분×3회). 비밀번호 안 씀. 백그라운드로 돌리고 `RESULT: OK`가 나오면 다음 단계로 | 로그인 |
| `kakao_share_cache.py <url> [--check]` | 카카오톡 공유 미리보기(OG) 캐시 초기화 + 새 메타 조회(카카오 디벨로퍼스 공유 디버거). 로그아웃이면 QR을 잘라 저장·전송, 270초마다 새 QR | 제출 |
| `pass_sms_verify.py send [--captcha N] [--match mobile-ok] \| code 123456 \| extend` | 휴대폰 본인확인(PASS/mobile-ok) 문자 인증. 사이트에서 인증 창을 먼저 연다. 보안문자 그림을 저장하고 멈춤 → 읽어서 `send --captcha`(틀려도 반복 금지). 사람은 문자 6자리만. 확인 버튼은 DOM click만 먹는다 | 제출 |
| `_template.py` | 새 시나리오 템플릿 | - |

## 제출형 규칙
- `--submit`이 없으면 dry-run이다(채우기만 하고 마지막 버튼은 누르지 않는다).
- `--lock-id`를 주면 `~/.chrome-direct/locks/<id>.submit.lock`으로 같은 일을 두 번 제출하지 않는다.
- 누른 뒤 결과를 확인 못 하면 `UNCONFIRMED`(종료 2)로 멈춘다. 다시 누르지 않는다.
- 결제·약관 동의·공개 같은 되돌리기 어려운 단계는 사용자가 명시했을 때만 한다.

## Codex 폴백(선택)
- Codex 없이 동작한다. 스크립트가 실패하면 실패 내용을 그대로 보고하고 끝난다.
- `CHROME_DIRECT_CODEX_SCRIPT`가 가리키는 래퍼가 있고 `codex`와 `tmux`가 PATH에 있으면, 실패 시 같은 목표를 Codex에 넘긴다.
- 래퍼는 `<프롬프트 파일> <출력 파일> [작업 폴더]` 인자를 받는 셸 스크립트다.

## 알려진 함정
- 페이지 전역 `const`를 다시 선언하면 오류가 난다. JS는 IIFE로 감싸는 `chromectl.js_json`으로 돌린다.
- 구글폼 버튼과 라디오는 단순 `.click()`을 무시한다. `press`(포인터→마우스→클릭)와 네이티브 setter(`__setv`)를 쓴다.
- Chrome이 두 개 떠 있으면 AppleScript가 엉뚱한 쪽을 잡는다. 새 탭은 `--profile-directory`로 Chrome 바이너리를 통해 연다(`new_tab`).
- Gmail URL은 `mail.google.com/mail/?authuser=<email>#search/...` 형태를 쓴다.
- 다른 출처 iframe(파일 선택창 등)은 JS로 못 닿는다. `rclick`(cliclick)을 쓴다.
- AppleScript JS는 페이지 스크립트의 전역 변수를 못 본다. DOM 이벤트로 조작한다.
- `rclick`은 그 창에서 활성인 탭을 클릭한다. 다른 탭이 활성이면 엉뚱한 페이지에 클릭이 간다.
- Google 로그아웃 상태는 `chromectl.google_relogin(tab, email)`로 패스키 시트까지 처리할 수 있다(맥의 패스키 사용 환경, 좌표 기반이라 화면 배치에 따라 실패할 수 있음).

## 시나리오 추가
- 같이 들어 있는 `web-scriptify` 스킬을 쓴다. 새 시나리오는 `~/.chrome-direct/scenarios/`에 저장된다.
