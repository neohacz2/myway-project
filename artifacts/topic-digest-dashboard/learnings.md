# topic-digest-dashboard learnings

---
category: tooling
applied: not-yet
---
## vitest.config exclude에 e2e/ 패턴이 빠지면 Playwright 파일이 Vitest에 흡수된다

**상황**: Step 3 Task 4, `bun run test` 전체 실행 시 e2e/smoke.spec.ts가 Vitest 런너에 포함되어 "Playwright Test did not expect test() to be called here" 에러 발생.
**판단**: vitest.config.ts의 `exclude` 배열에 `"e2e/**"` 추가. Next.js 프로젝트 초기화 시 기본으로 포함됐어야 할 패턴.
**다시 마주칠 가능성**: 높음 — Playwright + Vitest 공존하는 모든 Next.js 프로젝트에서 재발 가능. 다음 feature 시작 전에 vitest.config exclude를 점검.

---
category: code-review
applied: not-yet
---
## child_process.spawn의 'error' 이벤트를 빠뜨리면 Promise가 영원히 pending 된다

**상황**: Step 4(code-reviewer). route.ts의 runPython()이 'close'만 리스닝 — uv 바이너리가 없으면 Node가 'error' 이벤트만 발생시키고 'close'는 오지 않아 route가 무한 hang.
**판단**: 'error' 핸들러 추가 → resolve({ code:1, stderr: err.message }). 'close' 콜백의 code도 null 가능성 타입 처리.
**다시 마주칠 가능성**: 높음 — spawn을 쓰는 모든 route/server action에서 'error' 이벤트 핸들러는 필수. spawn 패턴 쓸 때마다 점검.

---
category: code-review
applied: not-yet
---
## RSC에서 JSON.parse는 try/catch로 감싸야 500을 피할 수 있다

**상황**: Step 4(code-reviewer). readDigestState()에서 state.json이 부분 쓰기나 손상으로 malformed면 JSON.parse가 throw → RSC render에서 uncaught → 500 페이지.
**판단**: try/catch 추가 후 empty state 반환. 파일 없음과 같은 경로로 처리.
**다시 마주칠 가능성**: 높음 — 파일 기반 데이터를 RSC에서 읽는 패턴 반복 시 항상 이 가드 필요. cron으로 생성된 파일은 언제든 partial write 가능.

---
category: spec-ambiguity
applied: not-yet
---
## `Record<string, unknown>` 타입은 Next.js 빌드에서 배열 필드 접근을 막는다

**상황**: Step 4(code-review 후 수정). raw를 `Record<string, unknown>`으로 선언하니 raw.ingested_video_ids를 string[]에 할당 불가 → 빌드 에러.
**판단**: `any`로 선언 + eslint-disable 주석. JSON.parse의 결과를 구조적으로 검증하는 게 이상적이지만 개인용 로컬 대시보드에서는 과도한 복잡도.
**다시 마주칠 가능성**: 중간 — JSON.parse 결과 타이핑 시 any vs Record<string,unknown> vs Zod 중 선택이 매번 필요. 다음에는 Zod safeParse를 쓰면 타입 추론과 가드를 동시에 해결.
