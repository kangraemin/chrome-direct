# chrome-direct

LLM 없이 내 Mac의 실제 Chrome을 조작하는 스크립트 모음과, 새 웹 조작을 스크립트로 쌓아 가는 Claude Code 플러그인입니다.

English: AppleScript + JS scenario scripts that drive your real, already-signed-in Mac Chrome without an LLM (Gmail search/codes, Google Forms, Notion export, page checks), plus a `web-scriptify` skill that turns any finished browser task into a reusable script. Works without Codex; Codex fallback is optional.

## 무엇을 하나
- 로그인된 실제 Chrome의 새 탭을 열어 AppleScript `execute javascript`로 화면을 읽고 누릅니다.
- 한 번 만든 시나리오는 LLM 호출 없이 한 줄로 돌아서 빠르고 같은 결과를 냅니다.
- 로그인 세션을 그대로 쓰므로 별도 브라우저·프로필·쿠키 복사가 필요 없습니다.
- 끝나면 자기가 연 탭만 닫습니다.

## 요구사항
- macOS와 Google Chrome.
- Python 3.9 이상.
- Chrome 메뉴 `보기 > 개발자 정보 > Apple Events의 JavaScript 허용`을 켭니다.
- 스크린샷(`shot`, `--proof`)을 쓰려면 터미널에 화면 기록 권한을 줍니다.
- 실제 마우스 클릭(`rclick`)을 쓰려면 `brew install cliclick`과 손쉬운 사용 권한이 필요합니다.
- Codex는 필요 없습니다.

## 설치
Claude Code 플러그인으로 설치합니다.

```
/plugin marketplace add kangraemin/chrome-direct
/plugin install chrome-direct@chrome-direct
```

- 스킬 두 개가 들어옵니다: `chrome-direct`, `web-scriptify`.
- 플러그인 없이 쓰려면 레포를 clone하고 `plugins/chrome-direct/skills/chrome-direct/scenarios/`의 스크립트를 직접 실행합니다.

## 설정(모두 선택)
- `CHROME_DIRECT_PROFILE`은 기본 Chrome 프로필 폴더입니다(기본 `Default`, `chrome://version`의 프로필 경로 끝에서 확인).
- `CHROME_DIRECT_GOOGLE_ACCOUNT`는 Gmail 시나리오가 쓸 Google 계정입니다.
- `CHROME_DIRECT_INFO`는 폼 자동 입력용 개인정보 JSON 경로입니다(기본 `~/.chrome-direct/info.json`, 예: `{"name": "...", "email": "..."}`).
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
