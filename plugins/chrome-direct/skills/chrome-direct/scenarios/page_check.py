#!/usr/bin/env python3
"""[읽기] 아무 페이지나 열어 키워드가 있는지, 그 줄과 맞는 링크를 뽑는다 (게시판 결과·접수 완료 확인 등).
로그인 화면이면 BLOCKED. 아무것도 누르지 않음.

  page_check.py https://example.com/notice --kw 결과 --kw 발표
  page_check.py https://example.com/apply --kw 접수완료 --name     # info.json의 name(마스킹 이름 포함) 찾기, 출력은 [이름]
"""
from _common import emit, js, parser, personal_info, poll, run, tab
from _pagecheck import scan

ap = parser(__doc__)
ap.add_argument("url")
ap.add_argument("--kw", action="append", default=[], help="찾을 단어 (여러 번)")
ap.add_argument("--name", action="store_true", help="info.json의 name·마스킹 이름도 찾기")
ap.add_argument("--wait", type=int, default=20)
a = ap.parse_args()


def main():
    with tab(a.url, a) as tid:
        res = scan(tid, a.kw, personal_info().get("name") if a.name else None, a.wait)
        emit({"url": a.url, **res}, "LOGIN_REQUIRED" if res["login"] else ("FOUND" if res["hits"] or res["nameHits"] else "NOT_FOUND"),
             f"{len(res['hits'])} kw lines, {len(res['nameHits'])} name lines")


run(main, a, f"READ ONLY. {a.url} 을 열어 다음 단어가 있는 줄과 링크를 보고: {', '.join(a.kw)}. 아무 버튼도 누르지 마라. 로그인 필요하면 LOGIN_REQUIRED.")
