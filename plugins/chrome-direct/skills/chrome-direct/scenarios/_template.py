#!/usr/bin/env python3
"""[읽기] 새 시나리오 템플릿 — 복사해서 쓴다. 한 줄 사용법, 하는 일, 사전 조건, 왜 화면 조작인지를 여기에 적는다.

  my_scenario.py https://example.com --kw 키워드
"""
import os, sys
# 핵심 모듈은 ~/.chrome-direct/core (플러그인 폴더로 가는 링크) 에 있다. 링크는 web-scriptify 스킬이 만든다.
sys.path.insert(0, os.path.expanduser("~/.chrome-direct/core/scenarios"))
from _common import emit, js, parser, poll, run, tab

ap = parser(__doc__)
ap.add_argument("url")
a = ap.parse_args()


def main():
    with tab(a.url, a) as tid:                      # 새 탭을 열고 끝나면 닫는다
        title = poll(tid, "return document.readyState === 'complete' ? document.title : null")
        emit({"url": a.url, "title": title}, "OK", title)   # 마지막 줄 RESULT: OK <title>


run(main, a, f"READ ONLY. {a.url} 을 열어 제목만 보고하라.")
