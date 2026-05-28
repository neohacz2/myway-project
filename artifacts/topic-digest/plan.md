# Topic Digest — 구현 계획

## 아키텍처 결정

| 결정 | 선택 | 이유 |
|---|---|---|
| 언어 | Python 3.12 | `notebooklm-py` 의존. 프로젝트의 bun/TS와 별개 |
| 실행 환경 | WSL2 로컬 cron | `storage_state.json` 보안·만료 관리 단순. PC OFF 시 미동작은 학습 단계에서 수용 |
| 디렉토리 | `scripts/topic-digest/` | repo 통합으로 학습 흐름 유지. `lint-fix.sh` 훅은 TS만 대상이라 충돌 없음 |
| 패키지·환경 매니저 | `uv` (이미 spike에서 검증) | venv·lockfile 일체화 |
| 테스트 도구 | `pytest` + `pytest-httpx` (HTTP stub) | Python 표준 + YouTube 응답 mock 가능 |
| NotebookLM 호출 격리 | 자체 어댑터 레이어 (`notebooklm_adapter.py`) | 라이브러리 깨짐 시 RPA fallback 또는 stub 교체 용이. 테스트에서 in-memory stub 주입 |
| 신선도 저장 | 로컬 `state.json` 파일 | 단순, 사용자가 직접 검토·복구 가능 |
| 운영 시각 (default) | 폴링 09:00 KST 매일, batch 18:00 KST 매주 금 | 사용자가 crontab으로 조정 가능 |

## 인프라 리소스

| 리소스 | 유형 | 선언 위치 | 생성 Task |
|---|---|---|---|
| 일일 폴링 cron | Cron job | `scripts/topic-digest/crontab.example` | Task 5 |
| 주1회 batch cron | Cron job | `scripts/topic-digest/crontab.example` | Task 5 |
| `YOUTUBE_CHANNEL_URL` | Env var | `scripts/topic-digest/.env` (gitignored), `.env.example` | Task 1 |
| `NOTEBOOK_ID` | Env var | 동일 | Task 1 |
| `STATE_PATH` | Env var (선택, default `./state.json`) | 동일 | Task 1 |
| `LOG_PATH` | Env var (선택, default `./logs/topic-digest.log`) | 동일 | Task 1 |
| `storage_state.json` | OAuth 자격(쿠키) | `~/.notebooklm/profiles/default/` (이미 존재, spike Task 2에서 발급) | — |

## 데이터 모델

### state.json
- `last_polled_at` (ISO 8601 timestamp) — 마지막 폴링 시작 시각
- `last_batch_at` (ISO 8601 timestamp) — 마지막 batch 시작 시각
- `ingested_video_ids` (List[string]) — 노트북에 push 완료된 YouTube video ID 목록 (중복 방지용)
- `sources_added_since_last_batch` (int) — batch skip 판정용 카운터. batch 성공 직후 0으로 리셋

### Adapter 인터페이스 (`notebooklm_adapter.py`)
- `add_url(notebook_id, url) -> None`
- `generate_audio(notebook_id) -> task_id`
- `generate_video(notebook_id) -> task_id`
- `generate_mind_map(notebook_id) -> task_id`
- 실제 구현은 `notebooklm-py` 래퍼. 테스트에서는 `InMemoryAdapter` stub 주입

## 필요 스킬

| 스킬 | 적용 Task | 용도 |
|---|---|---|
| `execute-plan` | 전체 | TDD 사이클·커밋·리뷰 워크플로우 |

본 feature는 Python 단독 도구. shadcn·next-best-practices·vercel-* 같은 React/Next 스킬은 적용 대상 아님. CLAUDE.md의 `types/lib/services/...` 의존성 순서 또한 TypeScript 전용이라 본 feature에 적용되지 않음 (plan.md에 명시).

## 영향 받는 파일

| 파일 경로 | 변경 유형 | 관련 Task |
|---|---|---|
| `scripts/topic-digest/pyproject.toml` | New | Task 1 |
| `scripts/topic-digest/.gitignore` | New | Task 1 |
| `scripts/topic-digest/.env.example` | New | Task 1 |
| `scripts/topic-digest/topic_digest/__init__.py` | New | Task 1 |
| `scripts/topic-digest/topic_digest/config.py` | New | Task 1 |
| `scripts/topic-digest/topic_digest/logging_setup.py` | New | Task 1 |
| `scripts/topic-digest/topic_digest/freshness.py` | New | Task 1 |
| `scripts/topic-digest/topic_digest/youtube.py` | New | Task 1 |
| `scripts/topic-digest/topic_digest/notebooklm_adapter.py` | New | Task 1 |
| `scripts/topic-digest/topic_digest/poll.py` | New | Task 1 |
| `scripts/topic-digest/tests/test_freshness.py` | New | Task 1 |
| `scripts/topic-digest/tests/test_youtube.py` | New | Task 1 |
| `scripts/topic-digest/tests/test_poll.py` | New | Task 1 |
| `scripts/topic-digest/topic_digest/poll.py` | Modify | Task 2 |
| `scripts/topic-digest/topic_digest/freshness.py` | Modify | Task 2 (실패 시 `last_polled_at` 보존 로직) |
| `scripts/topic-digest/topic_digest/notebooklm_adapter.py` | Modify | Task 2 |
| `scripts/topic-digest/tests/test_poll.py` | Modify | Task 2 |
| `scripts/topic-digest/topic_digest/batch.py` | New | Task 3 |
| `scripts/topic-digest/tests/test_batch.py` | New | Task 3 |
| `scripts/topic-digest/topic_digest/batch.py` | Modify | Task 4 |
| `scripts/topic-digest/tests/test_batch.py` | Modify | Task 4 |
| `scripts/topic-digest/crontab.example` | New | Task 5 |
| `scripts/topic-digest/README.md` | New | Task 5 |
| `artifacts/topic-digest/evidence/` | New (디렉토리) | Task 5 검증 증거 저장 |

## Tasks

### Task 1: 일일 폴링 — 새 영상 적재 + 중복 방지

- **담당 시나리오**: Scenario 1 (full), Scenario 2 (full)
- **크기**: M (5-6 구현 파일 + 3 테스트 파일, single subsystem)
- **의존성**: None
- **참조**:
  - `artifacts/topic-digest/spike-log.md` — adapter 호출 시그니처 검증된 부분
  - `notebooklm-py` README — `client.notebooks.get(id)`, `client.sources.add_url(notebook_id, url, wait=True)`
- **구현 대상**:
  - `scripts/topic-digest/pyproject.toml` (pytest, pytest-httpx, notebooklm-py, feedparser 의존)
  - `scripts/topic-digest/.gitignore` (`.venv`, `state.json`, `logs/`, `.env`)
  - `scripts/topic-digest/.env.example`
  - `scripts/topic-digest/topic_digest/config.py` (env 로드)
  - `scripts/topic-digest/topic_digest/logging_setup.py` (파일+stdout 핸들러)
  - `scripts/topic-digest/topic_digest/freshness.py` (state.json 읽기/쓰기, 중복 판정 순수 함수)
  - `scripts/topic-digest/topic_digest/youtube.py` (채널 RSS fetch → `[(video_id, url, title), ...]`)
  - `scripts/topic-digest/topic_digest/notebooklm_adapter.py` (`Adapter` ABC + `NotebookLMAdapter` 실구현 + `InMemoryAdapter` stub)
  - `scripts/topic-digest/topic_digest/poll.py` (`poll()` 엔트리: 채널 fetch → freshness 필터 → adapter.add_url → state 저장 → 로그)
  - `scripts/topic-digest/tests/test_freshness.py`
  - `scripts/topic-digest/tests/test_youtube.py` (pytest-httpx로 RSS 응답 mock)
  - `scripts/topic-digest/tests/test_poll.py` (InMemoryAdapter + 임시 디렉토리 state.json)
- **수용 기준**:
  - [ ] 채널 RSS에 새 영상 3개가 있는 상태에서 `poll()` 1회 실행 → InMemoryAdapter에 정확히 3개의 `add_url` 호출이 누적되고, 각 호출의 URL이 RSS의 영상 URL과 일치 (Scenario 1 항목 1)
  - [ ] 새 영상 0개 상태에서 `poll()` 실행 → InMemoryAdapter의 `add_url` 호출 0회, `state.json`의 `ingested_video_ids` 길이 변화 없음 (Scenario 1 항목 2)
  - [ ] 로그 파일 마지막 줄에 정규식 `polled .+; found \d+ new; added \d+; skipped \d+; failed \d+` 한 줄 (Scenario 1 항목 3 — spec의 "영상 개수·추가 성공·실패"를 포함, skipped 카운트는 plan에서 추가)
  - [ ] 동일 RSS 상태로 `poll()` 연속 2회 → 2회차에서 InMemoryAdapter `add_url` 호출 0회, `state.json`의 `ingested_video_ids` 1회차와 동일 (Scenario 2 항목 1)
  - [ ] 2회차 로그에 `skipped: already ingested` 문자열 포함 (Scenario 2 항목 2)
- **검증**:
  - `cd scripts/topic-digest && uv run pytest tests/test_freshness.py tests/test_youtube.py tests/test_poll.py -v`
  - 종단 1회 (수동): 실제 채널 URL 1개 + 실제 노트북 ID로 `uv run python -m topic_digest.poll` 실행 → NotebookLM UI에서 노트북 source 리스트에 새 영상이 추가됐는지 확인. 증거 스크린샷 `artifacts/topic-digest/evidence/task1-end-to-end.png`

---

### Task 2: 일일 폴링 — 에러 경로

- **담당 시나리오**: Scenario 5 (full), Scenario 6 (full)
- **크기**: S (2-3 파일 수정)
- **의존성**: Task 1 (`poll()` 골격, adapter 인터페이스)
- **참조**:
  - `notebooklm-py` README — 인증 만료 시 발생 예외 유형 (테스트에서 stub로 재현)
- **구현 대상**:
  - `scripts/topic-digest/topic_digest/poll.py` (Modify — try/except 분기 + 부분 실패 카운트)
  - `scripts/topic-digest/topic_digest/notebooklm_adapter.py` (Modify — `AuthExpiredError` 도메인 예외 정의·매핑)
  - `scripts/topic-digest/tests/test_poll.py` (Modify — 채널 fetch 실패·인증 실패 케이스 추가)
- **수용 기준**:
  - [ ] YouTube 채널이 HTTP 500/타임아웃을 반환하는 stub 상황에서 `poll()` 실행 → InMemoryAdapter `add_url` 호출 0회, `state.json` 변동 없음, 종료 코드 0 (다음 회 재시도 가능) (Scenario 5 항목 1)
  - [ ] **같은 상황에서 `state.json`의 `last_polled_at`이 갱신되지 않음** — 실패 시 dirty write 방지로 24시간 후 정상 응답 복귀 시 그 사이 publish된 새 영상이 누락 없이 적재됨 (Scenario 5 항목 3)
  - [ ] 같은 상황의 로그에 "channel fetch failed:" 와 예외 메시지 포함 (Scenario 5 항목 2)
  - [ ] InMemoryAdapter가 `AuthExpiredError`를 던지는 상황에서 `poll()` 실행 → `state.json`의 `ingested_video_ids` 변동 없음 (Scenario 6 항목 1)
  - [ ] 같은 상황의 로그에 `auth expired — run \`notebooklm login\` to re-authenticate` 정확 문자열 포함 (Scenario 6 항목 2)
  - [ ] **불변 규칙 2 — 인증 정보 노출 금지**: 인증 실패 stub 상황에서 생성된 로그·예외 메시지에 `storage_state.json`의 내용을 나타내는 키워드(`cookies`, `session_state`, JWT 패턴 `eyJ[A-Za-z0-9_-]+\.eyJ`)가 포함되지 않음 — grep으로 검증
- **검증**:
  - `cd scripts/topic-digest && uv run pytest tests/test_poll.py -v`
  - `cd scripts/topic-digest && uv run pytest tests/test_poll.py -v && ! grep -EI 'cookies|session_state|eyJ[A-Za-z0-9_-]+\.eyJ' logs/topic-digest.log` (인증 노출 검증)

---

### Checkpoint: Tasks 1-2 이후

- [ ] `cd scripts/topic-digest && uv run pytest` 전체 통과
- [ ] Spec Scenario 1·2·5·6 모두 covered
- [ ] **End-to-end 동작**: 실제 채널·노트북으로 `python -m topic_digest.poll`을 1회 실행해 NotebookLM UI에서 새 영상 적재 확인 (증거 `artifacts/topic-digest/evidence/checkpoint-1.png`)

---

### Task 3: 주1회 batch — artifact 트리거 + 빈 batch skip

- **담당 시나리오**: Scenario 3 (full), Scenario 4 (full), Scenario 6 (batch 경로)
- **크기**: M (3-4 파일)
- **의존성**: Task 1 (adapter 인터페이스, state.json)
- **참조**:
  - `artifacts/topic-digest/spike-log.md` — `generate_audio/video/mind_map`의 dict 반환 우회 패턴
- **구현 대상**:
  - `scripts/topic-digest/topic_digest/batch.py` (New — `run_batch()` 엔트리: state 확인 → 3 artifact trigger → state.last_batch_at 갱신 + counter 0 리셋. **첫 trigger 호출에서 `AuthExpiredError` 발생 시 조기 종료, state 미갱신**)
  - `scripts/topic-digest/topic_digest/notebooklm_adapter.py` (Modify — `generate_audio/video/mind_map` 메서드 추가)
  - `scripts/topic-digest/tests/test_batch.py` (New)
- **수용 기준**:
  - [ ] `state.json`의 `sources_added_since_last_batch` ≥ 1 인 상태로 `run_batch()` 실행 → InMemoryAdapter에 `generate_audio`, `generate_video`, `generate_mind_map`이 정확히 1회씩 호출 (Scenario 3 항목 1)
  - [ ] 같은 상황의 로그에 artifact 타입별 trigger 결과 3줄(success/fail) (Scenario 3 항목 2)
  - [ ] `run_batch()` 종료 시점에 InMemoryAdapter의 `wait_for_completion` 호출 0회 (Scenario 3 항목 3 — trigger만 책임)
  - [ ] `state.json`의 `sources_added_since_last_batch == 0` 상태로 `run_batch()` 실행 → adapter `generate_*` 호출 0회, `last_batch_at` 변동 없음 (Scenario 4 항목 1)
  - [ ] 같은 상황의 로그에 `no new sources; skip artifact batch` 정확 문자열 포함 (Scenario 4 항목 2)
  - [ ] **InMemoryAdapter가 `generate_audio` 호출 시 `AuthExpiredError`를 던지는 상황에서 `run_batch()` 실행 → `generate_video`·`generate_mind_map` 호출 0회 (조기 종료), `state.json`의 `last_batch_at`·`sources_added_since_last_batch` 변동 없음, 로그에 `auth expired — run \`notebooklm login\` to re-authenticate` 정확 문자열 포함** (Scenario 6 batch 경로)
- **검증**:
  - `cd scripts/topic-digest && uv run pytest tests/test_batch.py -v`

---

### Task 4: 주1회 batch — 부분 실패 격리

- **담당 시나리오**: Scenario 7 (full)
- **크기**: S (1-2 파일 수정)
- **의존성**: Task 3
- **참조**:
  - `artifacts/topic-digest/spike-log.md` — Mind Map dict 반환·Infographic `UnknownRPCMethodError` 실제 패턴
- **구현 대상**:
  - `scripts/topic-digest/topic_digest/batch.py` (Modify — 각 `generate_*`를 독립 try/except로 감싸 한 실패가 다른 trigger를 막지 않게)
  - `scripts/topic-digest/tests/test_batch.py` (Modify — Mind Map만 예외 던지는 stub 추가)
- **수용 기준**:
  - [ ] InMemoryAdapter의 `generate_mind_map`만 (`AuthExpiredError`가 아닌) 일반 예외를 던지는 상황에서 `run_batch()` 실행 → `generate_audio`·`generate_video` 호출은 정상적으로 발생 (Scenario 7 항목 1, Scenario 6 batch 경로와 구분: 일반 예외만 격리, 인증 실패는 조기 종료)
  - [ ] 같은 상황의 로그에 `audio: ok` / `video: ok` 줄과 정규식 `mind_map: fail .*(Error|Exception).*`이 매칭되는 줄(예외 메시지 포함)이 분리되어 존재 (Scenario 7 항목 2)
- **검증**:
  - `cd scripts/topic-digest && uv run pytest tests/test_batch.py -v`

---

### Checkpoint: Tasks 3-4 이후

- [ ] `cd scripts/topic-digest && uv run pytest` 전체 통과
- [ ] Spec Scenario 3·4·7 covered
- [ ] **End-to-end 동작**: Task 1 종단에서 적재한 노트북에 대해 `python -m topic_digest.batch` 1회 실행 → NotebookLM UI에서 Audio·Video·Mind Map의 최신 생성 시각이 갱신됐는지 확인 (증거 `artifacts/topic-digest/evidence/checkpoint-2.png`)

---

### Task 5: cron 등록 + 운영 문서 + 1주 운영 검증

- **담당 시나리오**: 모든 시나리오의 **불변 규칙 4·5** (부분 실패 격리, 7일 무인 안정성)를 실제 운영으로 입증
- **크기**: S (3 파일 + 운영)
- **의존성**: Tasks 1-4
- **참조**:
  - `man 5 crontab` (외부)
- **구현 대상**:
  - `scripts/topic-digest/crontab.example` (폴링·batch 라인 + 환경 변수)
  - `scripts/topic-digest/README.md` (설치·인증·cron 등록·로그 확인·트러블슈팅 절차)
  - `artifacts/topic-digest/evidence/` (운영 증거 누적)
- **수용 기준**:
  - [ ] `crontab.example`에 적힌 라인을 그대로 사용자가 `crontab -e`에 붙여넣어 등록 가능 (READMD의 절차 그대로 따라 7일 운영 시작) — Human review
  - [ ] **불변 규칙 검증**: 7일 연속 cron 운영 중 폴링·batch 합쳐 실패 1회 이하 — `logs/topic-digest.log`를 7일 후 grep해 "error|exception|fail" 빈도 ≤ 1 — Human review with log evidence
  - [ ] **NotebookLM UI 누적 확인**: 7일 차에 노트북 source 리스트에 새 영상이 누적되어 있고, 1주차 batch 결과로 artifact 생성 시각이 batch 등록 시각 이후로 갱신됨 — Human review with screenshot `artifacts/topic-digest/evidence/week1-notebook.png`
- **검증**:
  - Human review only — 7일 무인 운영 후 로그·UI 직접 점검. 단위 테스트로 증명 불가한 불변 규칙

---

### Final Checkpoint: Task 5 이후

- [ ] `cd scripts/topic-digest && uv run pytest` 전체 통과 (단위·통합)
- [ ] 7일 운영 증거 `artifacts/topic-digest/evidence/`에 누적
- [ ] Spec의 7개 시나리오·5개 불변 규칙 전부 covered (마지막 두 불변 규칙은 운영 증거로)
- [ ] `learnings.md` 작성: 라이브러리 깨짐 발생 여부, cron PC OFF 사고 발생 여부, NotebookLM 출력 품질 평가(Should Be True 가정)

---

## 미결정 항목

- **노트북 source 50개 한도 도달 시 처리** — 도달 시점이 ≥ 6개월 이후. 도달 전 별도 spec
- **Infographic 자동화 복귀 시점** — `notebooklm-py` 다음 릴리스 모니터링. 현재는 NotebookLM UI 수동
- **batch 정확한 요일·시각** — `crontab.example`은 default 제안. 사용자가 등록 시 조정
