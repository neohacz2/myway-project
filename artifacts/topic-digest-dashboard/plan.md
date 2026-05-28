# Topic Digest Dashboard — 구현 계획

## 아키텍처 결정

| 결정 | 선택 | 이유 |
|---|---|---|
| 라우트 배치 | `/` = 대시보드, 기존 예제 → `/examples` | 가장 자주 쓰는 화면이 루트여야 자연스러움 |
| state.json 읽기 | Server Component에서 `fs.readFileSync` | 빌드 시가 아닌 요청 시 읽어야 최신 상태 반영. RSC는 서버 파일시스템 접근 가능 |
| state.json 경로 | `process.env.STATE_PATH` 환경변수, 기본값 `scripts/topic-digest/state.json` | 경로 변경 시 코드 수정 없이 env만 바꿈 |
| 트리거 API | `POST /api/trigger` — `action: "poll" | "batch"` | 단일 엔드포인트가 두 명령 처리. 서버에서 `child_process.spawn("uv", ...)` |
| 트리거 타임아웃 | 120초 | 폴링 실 소요 시간(spike에서 ~3s), 배치는 trigger만 하므로 짧음 |
| 클라이언트 데이터 갱신 | 트리거 완료 후 `router.refresh()` | Next.js App Router의 server data 재검증. 추가 상태 관리 불필요 |
| 컴포넌트 위치 | `components/topic-digest-dashboard/` | CLAUDE.md 아키텍처 규약: components/ 레이어 |

## 인프라 리소스

| 리소스 | 유형 | 선언 위치 | 생성 Task |
|---|---|---|---|
| `STATE_PATH` | Env var | `.env.local` (gitignored) | Task 1 |
| `TOPIC_DIGEST_DIR` | Env var | `.env.local` | Task 3 (트리거 API) |

## 데이터 모델

### DigestState (state.json → UI 표현)
- `totalSources: number` — `ingested_video_ids.length`
- `sourcesAddedSinceBatch: number` — `sources_added_since_last_batch`
- `lastPolledAt: string | null` — ISO → KST 포맷 변환
- `lastBatchAt: string | null` — ISO → KST 포맷 변환
- `recentVideos: { id: string; url: string }[]` — 최신 10개, URL = `https://www.youtube.com/watch?v={id}`

### TriggerResult
- `ok: boolean`
- `message: string` — "폴링 완료" / "폴링 실패: …" / "배치 완료" / "배치 실패: …"

## 필요 스킬

| 스킬 | 적용 Task | 용도 |
|---|---|---|
| `shadcn` | Task 1, 2 | Card, Button, Badge 컴포넌트 확인·사용 |
| `next-best-practices` | Task 1, 3 | RSC 경계, route handler 패턴, `router.refresh()` |

## 영향 받는 파일

| 파일 경로 | 변경 유형 | 관련 Task |
|---|---|---|
| `app/page.tsx` | Modify | Task 1 (대시보드로 교체) |
| `app/examples/page.tsx` | New | Task 1 (기존 ComponentExample 이동) |
| `app/examples/layout.tsx` | New | Task 1 |
| `components/topic-digest-dashboard/status-cards.tsx` | New | Task 1 |
| `components/topic-digest-dashboard/status-cards.test.tsx` | New | Task 1 |
| `components/topic-digest-dashboard/video-list.tsx` | New | Task 2 |
| `components/topic-digest-dashboard/video-list.test.tsx` | New | Task 2 |
| `app/api/trigger/route.ts` | New | Task 3 |
| `app/api/trigger/route.test.ts` | New | Task 3 |
| `components/topic-digest-dashboard/trigger-panel.tsx` | New | Task 4 |
| `components/topic-digest-dashboard/trigger-panel.test.tsx` | New | Task 4 |
| `lib/digest-state.ts` | New | Task 1 (state.json 파싱 유틸) |
| `lib/digest-state.test.ts` | New | Task 1 |
| `.env.local.example` | New | Task 1 |

## Tasks

### Task 1: 상태 카드 + 루트 라우트 교체

- **담당 시나리오**: Scenario 1 (full), Scenario 2 (full)
- **크기**: M (6-8 파일)
- **의존성**: None
- **참조**:
  - `shadcn` — Card, Badge 컴포넌트
  - `next-best-practices` — RSC 경계, async Server Component
  - `artifacts/topic-digest-dashboard/wireframe.html` — screen-0 상태 카드 4개 레이아웃, screen-1 빈 상태
  - `scripts/topic-digest/topic_digest/freshness.py` — AppState 필드명 확인
- **구현 대상**:
  - `lib/digest-state.ts` — `readDigestState()`: state.json 읽기·파싱·KST 변환. 파일 없으면 empty state 반환
  - `lib/digest-state.test.ts`
  - `components/topic-digest-dashboard/status-cards.tsx` — 4개 카드 (총 적재, 다음 배치, 마지막 폴링, 마지막 배치). RSC
  - `components/topic-digest-dashboard/status-cards.test.tsx`
  - `app/page.tsx` — Server Component. `readDigestState()` 호출 후 StatusCards + VideoList + TriggerPanel 조합 (VideoList·TriggerPanel은 Task 2·4에서 구현, 여기선 placeholder)
  - `app/examples/page.tsx` — 기존 `ComponentExample` 이동
  - `app/examples/layout.tsx`
  - `.env.local.example`
- **수용 기준**:
  - [ ] `ingested_video_ids: ["a","b","c"]`인 state.json이 주어질 때 "3" 숫자가 카드에 표시된다 (Scenario 1 항목 3)
  - [ ] `sources_added_since_last_batch: 5` → "다음 배치까지 5개" 텍스트가 표시된다 (Scenario 1 항목 4)
  - [ ] `last_polled_at: "2026-05-28T00:00:00+00:00"` → "2026-05-28 09:00" (KST) 텍스트가 표시된다 (Scenario 1 항목 1)
  - [ ] `last_batch_at: "2026-05-23T00:00:00+00:00"` → "2026-05-23 09:00" (KST) 텍스트가 표시된다 (Scenario 1 항목 2)
  - [ ] state.json 없을 때 `readDigestState()`가 empty state를 반환하고, 카드에 "—" 또는 "아직 없음" 텍스트가 표시된다 (Scenario 2)
  - [ ] 페이지 로드 후 state.json이 변경되어도 사용자가 새로고침하기 전까지 표시 수치가 바뀌지 않는다 (불변 규칙 — 상태 데이터 최신성, RSC는 자동 갱신 없음)
  - [ ] `bun run build` 성공
- **검증**:
  - `bun run test -- status-cards`
  - `bun run test -- digest-state`
  - `bun run build`

---

### Task 2: 최근 적재 영상 목록

- **담당 시나리오**: Scenario 3 (full)
- **크기**: S (2 파일)
- **의존성**: Task 1 (`lib/digest-state.ts`의 `recentVideos` 필드)
- **참조**:
  - `artifacts/topic-digest-dashboard/wireframe.html` — screen-0 영상 목록 섹션 (screen-3 NEW 배지는 spec 범위 밖 — 구현 제외)
- **구현 대상**:
  - `components/topic-digest-dashboard/video-list.tsx` — `recentVideos` prop을 받아 최대 10개 링크 목록. RSC
  - `components/topic-digest-dashboard/video-list.test.tsx`
- **수용 기준**:
  - [ ] `[{id:"vid1"}, ...(15개)]` 전달 시 화면에 링크가 정확히 10개 렌더된다 (Scenario 3 항목 2)
  - [ ] 렌더된 링크의 href가 `https://www.youtube.com/watch?v=vid1` 형식이다 (Scenario 3 항목 1)
  - [ ] `recentVideos: []` 전달 시 "아직 적재된 영상이 없습니다" 텍스트가 표시된다 (Scenario 3 항목 3)
- **검증**:
  - `bun run test -- video-list`

---

### Checkpoint: Tasks 1-2 이후
- [ ] `bun run test` 전체 통과
- [ ] `bun run build` 성공
- [ ] `http://localhost:3001` 접속 시 상태 카드 4개 + 영상 목록 렌더 확인 (Human review)

---

### Task 3: 트리거 API Route

- **담당 시나리오**: Scenario 4 (partial — API 레이어), Scenario 5 (partial — API 레이어)
- **크기**: S (2 파일)
- **의존성**: None (Python 파이프라인은 외부 의존)
- **참조**:
  - `next-best-practices` — route-handlers.md, POST body 검증
  - `scripts/topic-digest/topic_digest/poll.py`, `batch.py` — 진입점 `python -m topic_digest.poll/batch`
- **구현 대상**:
  - `app/api/trigger/route.ts` — `POST /api/trigger`. body `{action: "poll"|"batch"}`. `child_process.spawn("uv", ["run","python","-m",`topic_digest.${action}`], {cwd: TOPIC_DIGEST_DIR, timeout: 120_000})`. 성공 → `{ok:true, message:"폴링 완료"}`. 실패 → `{ok:false, message:"폴링 실패: …"}`
  - `app/api/trigger/route.test.ts` — child_process를 mock해 성공/실패/알 수 없는 action 검증
- **수용 기준**:
  - [ ] `POST /api/trigger {action:"poll"}` 성공 시 응답 JSON `{ok:true, message:"폴링 완료"}` 반환 (Scenario 4)
  - [ ] `POST /api/trigger {action:"batch"}` 성공 시 응답 JSON `{ok:true, message:"배치 완료"}` 반환 (Scenario 5)
  - [ ] child_process가 exit code 1로 종료하면 `{ok:false, message:"폴링 실패: ..."}` 반환 (Scenario 4 실패 케이스)
  - [ ] `action` 값이 `"poll"/"batch"` 외이면 `400 Bad Request` 반환
- **검증**:
  - `bun run test -- trigger`

---

### Task 4: 트리거 버튼 패널 (로딩·결과 상태)

- **담당 시나리오**: Scenario 4 (full), Scenario 5 (full), Scenario 6 (full), Scenario 7 (full), 불변 규칙 (트리거 중복 방지)
- **크기**: M (3-4 파일)
- **의존성**: Task 3 (`/api/trigger` route 존재)
- **참조**:
  - `shadcn` — Button (loading state), Badge
  - `artifacts/topic-digest-dashboard/wireframe.html` — screen-2 로딩 상태, screen-3 결과 배지
  - `next-best-practices` — `useRouter` / `router.refresh()` 클라이언트 패턴
- **구현 대상**:
  - `components/topic-digest-dashboard/trigger-panel.tsx` — `"use client"`. "지금 폴링" / "지금 배치" / "NotebookLM 열기" / "새로고침" 버튼. 클릭 → fetch `/api/trigger` → loading 상태 → 결과 배지. 완료 후 `router.refresh()`
  - `components/topic-digest-dashboard/trigger-panel.test.tsx` — `fetch` mock, `useRouter` mock
- **수용 기준**:
  - [ ] "지금 폴링" 클릭 직후 버튼이 disabled + 로딩 텍스트로 바뀐다 (Scenario 4 항목 1)
  - [ ] API 성공 응답 후 "폴링 완료" 텍스트가 화면에 나타난다 (Scenario 4 항목 2)
  - [ ] API 실패 응답 후 "폴링 실패" 텍스트가 화면에 나타난다 (Scenario 4 항목 3)
  - [ ] "지금 배치" 클릭 직후 버튼이 disabled + 로딩 텍스트로 바뀐다 (Scenario 5 항목 1)
  - [ ] 배치 성공 후 "배치 완료" 텍스트가 화면에 나타난다 (Scenario 5 항목 2)
  - [ ] 배치 실패 시 "배치 실패" 텍스트(또는 동등한 오류 메시지)가 화면에 나타난다 (Scenario 5 항목 3)
  - [ ] "NotebookLM 열기" 링크의 href가 `https://notebooklm.google.com/`이고 `target="_blank"`이다 (Scenario 6)
  - [ ] "새로고침" 버튼 클릭 시 `router.refresh()`가 호출된다 (Scenario 7)
  - [ ] "지금 폴링" 실행 중에 "지금 배치" 버튼도 disabled이다 (불변 규칙 — 중복 방지)
  - [ ] 트리거 완료 후 `router.refresh()`가 호출되어 상태 카드 수치가 최신 state.json 값으로 갱신된다 (Scenario 4 항목 4)
- **검증**:
  - `bun run test -- trigger-panel`

---

### Checkpoint: Tasks 3-4 이후
- [ ] `bun run test` 전체 통과
- [ ] `bun run build` 성공
- [ ] 브라우저에서 "지금 폴링" 클릭 → 로딩 → 완료 메시지 → 카드 수치 갱신 end-to-end 확인 (Human review, 증거 `artifacts/topic-digest-dashboard/evidence/checkpoint-2.png`)

---

## 미결정 항목

- 없음. 모든 high-cost 결정 확정됨.
