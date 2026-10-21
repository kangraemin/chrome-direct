---
name: web-scriptify
description: After a task that involved web or console actions in the browser (Chrome driven directly, an admin console, a form, a login flow) is finished, save that procedure as a reusable chrome-direct scenario script so the next run needs no LLM. Skip when the task is one-off, needs human judgment each time, or is dominated by payment/identity steps only the user can do. Use when the user says "scriptify this", "save this as a script", "make it one command next time".
---

# web-scriptify

웹 조작은 매번 화면을 보고 헤매면 느리고 틀린다. 한 번 성공한 순서를 스크립트로 남기면 다음엔 한 줄로 끝난다.
새 시나리오는 이 플러그인 폴더가 아니라 **사용자 폴더 `~/.chrome-direct/scenarios/`**에 저장한다(플러그인 업데이트로 지워지지 않는다).

## 0. 준비(매번)
- `~/.chrome-direct/core`가 이 플러그인의 chrome-direct 폴더를 가리키게 한다(플러그인이 업데이트돼도 경로가 안 깨지게 하는 링크).

```
mkdir -p ~/.chrome-direct/scenarios && ln -sfn "${CLAUDE_SKILL_DIR}/../chrome-direct" ~/.chrome-direct/core
```

- 설정 폴더를 바꾸고 싶으면 `CHROME_DIRECT_HOME_DIR` 환경변수를 쓴다(기본 `~/.chrome-direct`).

## 1. 이번 작업에서 한 웹 조작을 적는다
- 들어간 주소, 누른 버튼·입력칸(셀렉터), 기다린 문구, 막힌 곳과 푼 방법.
- 실패했다가 성공한 순서는 성공한 순서만 남긴다.

## 2. 스크립트로 만들 수 있는지 판단한다
다음은 만들지 않는다. 이유만 한 줄로 보고한다.
- 다시 할 일이 없는 일회성 작업.
- 매번 사람 판단이 필요한 작업(디자인 고르기, 글 내용 쓰기).
- 결제·본인인증·서명처럼 사용자만 할 수 있는 단계가 핵심인 작업(앞뒤 단계만 만들 수 있으면 그 부분만).
- 화면이 매번 달라 셀렉터로 잡을 수 없는 경우(캔버스·이미지 기반 UI).

## 3. 넣을 곳을 정한다
- 먼저 기존 스크립트를 찾는다: `ls ~/.chrome-direct/scenarios ${CLAUDE_SKILL_DIR}/../chrome-direct/scenarios`.
- 비슷한 게 있으면 새로 만들지 말고 옵션을 더한다(플러그인 쪽 파일은 직접 고치지 말고 사용자 폴더로 복사해서 고친다).
- 없으면 `${CLAUDE_SKILL_DIR}/../chrome-direct/scenarios/_template.py`를 `~/.chrome-direct/scenarios/<이름>.py`로 복사해 시작한다.

## 4. 이렇게 쓴다
- 파일 맨 위에서 `sys.path.insert(0, os.path.expanduser("~/.chrome-direct/core/scenarios"))` 후 `from _common import ...`를 쓴다(템플릿에 들어 있다).
- 기본 틀은 `parser()`로 인자 만들기 → `with tab(url, a) as tid:` → `js`/`poll`로 DOM 조작 → `emit(결과, 상태)` → `run(main, a, 폴백용 작업 설명)`이다.
- 쓰는 함수: `js`, `poll`, `c.press`, `c.fill`, `c.rclick`, `c.shot`, `c.google_relogin`.
- 탭은 `tab()`이 준 `id:`로만 가리킨다. 다른 세션이 탭을 열고 닫아도 안 깨진다.
- Angular·Vue 화면은 백그라운드 탭에서 안 그려진다. 읽기 전에 `c.shot(tid, png)`로 탭을 앞으로 띄운다.
- 멱등하게 만든다. 이미 등록·생성돼 있으면 남은 단계만 하거나 상태만 출력한다.
- 제출·결제·공개 같은 되돌리기 어려운 단계는 `--submit`이 있을 때만 실행하고, `--lock-id`로 중복 제출을 막는다.
- 사전 조건(로그인 여부 등)은 시작 전에 확인하고 `Blocked`로 막는다(종료 코드 2).
- 출력의 마지막 줄은 `RESULT: <상태>`다.
- 재시도 루프 안에서 사용자에게 묻지 않는다.
- 비밀값은 환경변수나 `~/.chrome-direct/.env`에서만 읽고(`chromectl.secret(NAME)`) 출력하지 않는다.
- 개인정보는 `~/.chrome-direct/info.json`에서 자리표시자(`{name}`)로만 쓴다.
- 파일 맨 위 docstring에 사용법 한 줄, 하는 일, 사전 조건, 왜 화면 조작인지(API가 막힌 이유 등)를 적는다.

## 5. 지금 돌려서 확인한다
- 읽기 경로나 이미 끝난 대상(멱등 경로), 또는 dry-run으로 실제로 돌린다.
- 실제 제출을 확인하려고 한 번 더 제출하지 않는다.
- 못 돌린 경로는 "미검증"으로 보고한다.

## 6. 보고한다
- 형식: `스크립트화: <경로> — <한 줄 사용법> (검증: 됨/미검증 이유)`.
- 만들지 않았으면 `스크립트화 안 함: <이유>`.
- 다른 사람과 공유하고 싶으면 `~/.chrome-direct/scenarios/`의 파일에서 개인정보를 제거한 뒤 이 플러그인 레포에 PR로 보낸다.
