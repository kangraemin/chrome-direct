# chrome-direct

LLM 없이 내 Mac의 실제 Chrome을 조작하는 스크립트 모음과, 새 웹 조작을 스크립트로 쌓아 가는 Claude Code 플러그인입니다.

English: AppleScript + JS scenario scripts that drive your real, already-signed-in Mac Chrome without an LLM (Gmail search/codes, Google Forms, Notion export, page checks), plus a `web-scriptify` skill that turns any finished browser task into a reusable script. Works without Codex; Codex fallback is optional.

## 무엇을 하나
- 로그인된 실제 Chrome의 새 탭을 열어 AppleScript `execute javascript`로 화면을 읽고 누릅니다.
- 한 번 만든 시나리오는 LLM 호출 없이 한 줄로 돌아서 빠르고 같은 결과를 냅니다.
- 로그인 세션을 그대로 쓰므로 별도 브라우저·프로필·쿠키 복사가 필요 없습니다.
- 끝나면 자기가 연 탭만 닫습니다.
- JS로 못 닿는 곳은 진짜 마우스·키보드로 누릅니다(Codex 없이 화면 조작).
  - `rclick`: 요소의 화면 좌표를 계산해 `cliclick`으로 실제 클릭합니다. 다른 출처 iframe, 파일 선택창 버튼 등에 씁니다.
  - `rtype`: 포커스된 칸에 실제 키 입력을 보냅니다. JS로 값을 넣으면 거부하는 입력칸에 씁니다.
  - macOS 패스키 시트처럼 웹페이지 밖에 뜨는 창은 System Events로 창 위치를 구해 좌표로 누릅니다(`google_relogin`).

```
python3 chromectl.py rclick --match example.com --text "파일 선택"
python3 chromectl.py rtype --value "hello" --enter
```

## 요구사항
- macOS, Google Chrome, Python 3.9 이상(맥 기본 `python3`로 됩니다).
- Codex는 필요 없습니다.

## 설치
1. Claude Code에서 플러그인을 설치합니다.

```
/plugin marketplace add kangraemin/chrome-direct
/plugin install chrome-direct@chrome-direct
```

2. 필수 설정을 한 번에 켭니다. Claude에게 "chrome-direct setup 돌려줘"라고 하거나 직접 실행합니다.

```
python3 plugins/chrome-direct/skills/chrome-direct/chromectl.py setup
```

- 필수 설정만 차례로 점검하고, 켤 수 있는 건 바로 켭니다. 마지막 줄이 `READY`면 끝입니다.
  - `cliclick`이 없으면 Homebrew로 설치합니다.
  - macOS 권한 창(터미널 앱이 Chrome·System Events 제어)이 뜨면 '허용'을 누릅니다. 놔두면 거부로 굳습니다.
  - 권한이 꺼져 있으면 해당 시스템 설정 화면(자동화·손쉬운 사용)을 열어 두고 무엇을 켤지 한 줄로 알려 줍니다.
  - Chrome 메뉴 `보기 > 개발자 정보 > Apple Events의 자바스크립트 허용`을 켭니다. 진짜 마우스를 그 항목 위에 올린 뒤 클릭해서 자동으로 켭니다(접근성 API로 누르는 방식은 Chrome이 무시합니다). 이미 켜져 있으면 누르지 않습니다.
  - 자동 클릭이 안 먹으면 메뉴를 그 항목까지 펼쳐 두고 "반드시 지금 누르라"고 알려 줍니다. Claude가 돌릴 때는 기다리지 않고 `TODO js`로 끝나며, Claude가 먼저 안내한 뒤 `setup --wait-js`로 다시 펼칩니다.
- 사람 손이 남으면 종료코드 2로 끝납니다. 알려 준 것을 누르고 다시 실행합니다.
- 메뉴 이름은 Chrome 언어마다 다릅니다(영어판 `View > Developer > Allow JavaScript from Apple Events`, 미검증). 스크립트는 이름에 `Apple Events`가 든 항목을 찾습니다.
- 이 설정은 Chrome 프로필마다 따로입니다. 다른 프로필 창에서 막히면 그 창에서 setup을 다시 돌립니다.
- 선택: 스크린샷(`shot`, `--proof`)을 쓰려면 터미널에 화면 기록 권한을 줍니다.
- 플러그인 없이 쓰려면 레포를 clone하고 같은 경로의 스크립트를 직접 실행합니다. 스킬 두 개(`chrome-direct`, `web-scriptify`)가 들어 있습니다.

## 설정(모두 선택)
- `CHROME_DIRECT_PROFILE`은 기본 Chrome 프로필 폴더입니다(기본 `Default`, `chrome://version`의 프로필 경로 끝에서 확인).
- `CHROME_DIRECT_GOOGLE_ACCOUNT`는 Gmail 시나리오가 쓸 Google 계정입니다.
- `CHROME_DIRECT_INFO`는 폼 자동 입력용 개인정보 JSON 경로입니다(기본 `~/.chrome-direct/info.json`, 예: `{"name": "...", "email": "..."}`).
  - 본인확인(`pass_sms_verify.py`)을 쓰려면 `birth`(1990-01-31), `phone`, `gender_digit`(주민번호 뒷자리 첫 숫자), `carrier`(skt/kt/lgu), `mvno`(알뜰폰이면 true)도 넣습니다.
  - 이 파일은 내 컴퓨터에만 둡니다. 레포에는 개인정보가 없습니다.
- `CHROME_DIRECT_TG_TOKEN` / `CHROME_DIRECT_TG_CHAT_ID`를 주면 로그인 QR을 텔레그램으로 받습니다(선택). 맥 앞에 없을 때 폰으로 스캔하는 용도입니다.
- `CHROME_DIRECT_HOME_DIR`은 설정·잠금·사용자 시나리오 폴더입니다(기본 `~/.chrome-direct`).
- 비밀값은 환경변수나 `~/.chrome-direct/.env`에서만 읽고 출력하지 않습니다.

## 시나리오
모두 `python3 plugins/chrome-direct/skills/chrome-direct/scenarios/<이름>.py`로 실행합니다. 출력의 마지막 줄은 `RESULT: <상태>`입니다.

| 스크립트 | 하는 일 |
|---|---|
| `google_account.py` | 이 프로필에 로그인된 Google 계정 확인 |
| `gmail_search.py "in:sent to:a@b.com" --limit 20` | Gmail 검색 결과 목록, `--open N`으로 본문 읽기 |
| `gmail_code.py "from:example.com" --newer 20m` | 최근 메일에서 인증번호(`CODE n`)나 링크(`LINK url`) 뽑기 |
| `gform_read.py <url> --skeleton answers.json` | 구글폼 구조를 읽고 답변 틀 만들기 |
| `gform_fill.py <url> answers.json` | 구글폼 채우기(기본 dry-run, `--submit --lock-id 이름`일 때만 제출) |
| `page_check.py <url> --kw 결과 --kw 발표` | 아무 페이지에서 키워드가 든 줄과 링크 뽑기 |
| `notion_export.py <page_id> <out_dir>` | 노션 페이지 트리를 마크다운으로 내보내기 |
| `naver_login.py [--qr --notify] [--otp N]` | 네이버 로그인 확인. 로그아웃이면 QR 로그인(앱으로 스캔만) |
| `kakao_share_cache.py <url> [--check]` | 카카오톡 공유 미리보기 캐시 초기화. 로그아웃이면 QR 로그인 |
| `pass_sms_verify.py send` → `send --captcha N` → `code 123456` | 휴대폰 본인확인(PASS) 문자 인증. 사람은 문자로 온 6자리만 |

사용 예:

```
export CHROME_DIRECT_GOOGLE_ACCOUNT=me@gmail.com
python3 gmail_code.py "from:service.example 인증번호" --newer 10m --profile "Profile 2"
```

## web-scriptify로 새 시나리오 추가하는 흐름
- 브라우저로 무언가를 한 번 해냅니다(Claude가 직접 하거나, 내가 알려 줍니다).
- 작업이 끝나면 Claude가 `web-scriptify` 스킬을 씁니다("스크립트화해", "다음엔 바로 되게 저장해"라고 말해도 됩니다).
- 스킬이 먼저 스크립트로 만들 수 있는 일인지 판단합니다(일회성, 사람 판단, 결제·본인인증 중심이면 만들지 않습니다).
- 만들 수 있으면 `_template.py`를 복사해 `~/.chrome-direct/scenarios/<이름>.py`에 저장합니다.
- 저장 위치가 플러그인 폴더가 아니라 사용자 폴더라서 플러그인을 업데이트해도 내 시나리오가 남습니다.
- 스킬이 `~/.chrome-direct/core` 링크를 만들어 어디서든 `from _common import ...`가 되게 합니다.
- 읽기 경로나 `--submit` 없는 dry-run으로 실제로 돌려 확인하고 `스크립트화: <경로> — <사용법>`으로 보고합니다.
- 공유하고 싶은 시나리오는 개인정보를 지운 뒤 PR로 보내 주세요.

## Codex 폴백(선택)
- Codex 없이 동작합니다. 스크립트가 실패하면 실패 내용을 그대로 출력하고 종료 코드 1로 끝납니다(에러로 죽지 않음).
- Codex가 있으면 실패 시 같은 목표를 Codex에 넘길 수 있습니다.
- `CHROME_DIRECT_CODEX_SCRIPT`에 래퍼 스크립트(`<프롬프트 파일> <출력 파일> [작업 폴더]`를 받는 셸 스크립트)를 지정하고 `codex`와 `tmux`가 PATH에 있을 때만 켜집니다.
- 끄고 싶으면 `--no-fallback`을 줍니다.

## 종료 코드
- 0은 성공입니다.
- 1은 실패입니다.
- 2는 막힘입니다(로그인 필요, 이미 제출, 잠금). 폴백 없이 이유만 보고합니다.

## 한계
- macOS 전용이고 Google Chrome만 지원합니다.
- 사이트 화면이 바뀌면 셀렉터가 깨질 수 있습니다.
- 다른 출처 iframe(파일 선택창 등)은 JS로 못 건드립니다. 마우스 클릭(`rclick`)이 필요합니다.
- `google_relogin`은 화면 좌표 기반이라 환경에 따라 실패할 수 있습니다.
- 본인인증·결제·캡차는 자동화 대상이 아닙니다.
- 이 레포는 개인 계정에 묶인 시나리오(특정 콘솔·스티커 업로드·메일 접수 등)를 뺀 일반화 버전입니다.
- 로그인된 브라우저를 조작하므로 보는 사이트의 약관과 법을 지키고, 본인 계정에만 쓰세요.

## 라이선스
MIT
