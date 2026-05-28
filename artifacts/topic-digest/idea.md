# Topic Digest Pipeline

## Problem Statement
HMW — NotebookLM이 단발 콘텐츠 시각화는 이미 잘 하는데, *한 주제에 대한 내 이해가 시간이 흐르며 자동으로 누적되어*, 그 자체로 학습 자산이자 발행 가능한 콘텐츠가 되도록 할 수 있을까?

## Recommended Direction
**한 주제로 좁혀, "자동 수집 → NotebookLM 자동 적재 → 시각 출력 회수"의 가장 좁은 종단 슬라이스를 먼저 만든다. (방향 C → A로 자란다)**

NotebookLM은 2026.04 기준 인포그래픽 10종·시네마틱 비디오·마인드맵을 이미 자체 제공한다. 외부에서 재구현할 이유가 없다. 진짜 비어 있는 곳은 (a) 노트북에 source가 *자동으로 누적*되는 수집 레이어, (b) 결과물을 내 도구로 흘려보내는 회수 레이어다.

잡식·발행 자동화·횡단 검색은 이번 라운드에서 전부 제외하고, **"한 주제의 YouTube 채널/RSS → 노트북 자동 갱신 → 인포그래픽/비디오 산출"** 만 종단 동작시킨다. 학습 목적을 만족시키면서, 가장 위험한 가정(unofficial NotebookLM API의 안정성)을 가장 빠르게 깬다.

## Key Assumptions to Validate
- [ ] **Must Be True**: `notebooklm-py` 류 unofficial 클라이언트로 노트북에 source 자동 추가가 안정적으로 동작한다 — 30분 스파이크: 노트북 생성 + YouTube URL 1개 추가 + Audio/Video Overview 생성까지 종단 호출
- [ ] **Should Be True**: 자동 생성된 인포그래픽/비디오 품질이 *내가 보기에 만족스럽다* — 동일 주제로 수동 5개 vs 자동 5개를 비교
- [ ] **Might Be True**: 신선한 source가 주 1회 들어와도 NotebookLM 출력이 의미 있게 갱신된다 (정체된 노트북 함정 방지) — 2주 운영 후 점검

## MVP Scope

**포함:**
- 입력 1종: 단일 YouTube 채널 1개 *또는* RSS 피드 1개
- 자동 수집 cron (bun 스크립트 + 로컬 cron 또는 GitHub Actions)
- `notebooklm-py`로 노트북에 source push
- 결과물(인포그래픽 + 비디오 1개) **수동 트리거** — 자동 생성은 다음 라운드
- 출력 회수: 노션 페이지 1개에 링크 적재

**제외:** 다중 소스, UI, 자동 발행, 멀티 노트북, 자체 시각화 엔진

## Not Doing (and Why)
- **잡식 입력** — 시그널이 약해 결과물 가치가 안 나옴. NotebookLM 노트북 단위(source 50개 제한)와 구조적 충돌
- **노트북 간 횡단 검색** — NotebookLM 다음 버전이 채울 가능성이 높음. 지금 만들면 곧 무용
- **발행 자동화 (블로그·인스타)** — 출력 품질 검증 전엔 무의미. 손 발행 비용이 0에 가까움
- **공식 Enterprise API** — 일반 사용자 불가
- **자체 시각화 엔진** — NotebookLM이 이미 함. 다시 만들지 않음

## Open Questions
- 시작 주제는 무엇인가? (예: Claude Code · AI 에이전트 — `/write-spec`에서 확정)
- Cron 주기는? (매일 vs 주 1회 — 입력 빈도에 따라)
- 결과물 회수 채널은? (노션 vs 옵시디언 vs 로컬 파일)
- `notebooklm-py`가 막히면 대안은? (RPA/브라우저 자동화 fallback vs 수동 회귀)
