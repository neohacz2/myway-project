# topic-digest learnings

---
category: tooling
applied: not-yet
---
## notebooklm-py 공식 API가 아님 — method drift는 일상

**상황**: Step 1(spike). Infographic trigger가 `UnknownRPCMethodError: method_id='R7cb6c'`로 깨진 채 0.5.0이 릴리스됨 (2026-05-24 ~ 5-28 사이 Google이 내부 RPC 변경).
**판단**: 라이브러리 호출 레이어(`NotebookLMAdapter._gen`)에 generate 메서드를 집중시켜, Google이 method를 바꿀 때 adapter 한 곳만 고치면 되도록 설계. 테스트는 `InMemoryAdapter`로 격리해 라이브러리 변경에 영향받지 않게.
**다시 마주칠 가능성**: 높음 — unofficial API 특성상 어떤 메서드도 언제든 drift 가능. 다음 feature에서도 동일 패턴(adapter ABC + stub + 실구현 분리) 유지해야 함.

---
category: task-ordering
applied: not-yet
---
## Task 3에서 AuthExpiredError batch 경로를 plan-reviewer가 발견

**상황**: plan.md 작성 후 plan-reviewer가 Scenario 6의 batch 경로 누락을 Critical로 지적. plan에서 Task 2가 poll 경로만 다루고 Task 3은 batch를 다루는데, auth 실패 수용 기준이 poll에만 있었음.
**판단**: plan-reviewer 지적을 수용해 Task 3 수용 기준에 batch auth 경로 추가. 구현 중에 재발견하면 Task 중간에 범위가 확장됐을 것.
**다시 마주칠 가능성**: 중간 — 동일 오류 경로가 여러 진입점(poll/batch 등)에 존재하는 구조에서 plan이 하나를 놓치는 패턴.

---
category: code-review
applied: not-yet
---
## logger.propagate=False — 서드파티 라이브러리 로거의 쿠키 누출 경로

**상황**: Step 4(code-reviewer). `logging_setup.py`에서 `propagate`를 `False`로 설정하지 않으면 `notebooklm-py`·Playwright가 root logger로 raw cookie/Bearer 토큰을 흘릴 수 있다는 지적.
**판단**: `logger.propagate = False` 한 줄 추가. 우리가 직접 쓰는 로그 경로만 sanitize하는 건 불완전 — 라이브러리가 던지는 traceback이 root handler를 타는 경로를 막는 게 더 근본적.
**다시 마주칠 가능성**: 높음 — 인증 라이브러리(Playwright, OAuth SDK, requests-auth 등)를 쓰는 feature라면 항상 같은 리스크. `setup_logging()` 함수를 만들 때마다 `propagate = False` 점검.

---
category: code-review
applied: not-yet
---
## 보안 불변 규칙(sanitize)은 한 곳에서만 정의해야 한다

**상황**: Step 4(code-reviewer). `_sanitize` + `_SECRET_PATTERNS`가 `poll.py`와 `batch.py` 두 곳에 복사됨을 지적. 두 복사본이 drift하면 한쪽이 누출을 막고 한쪽이 못 막는 상황이 생김.
**판단**: `notebooklm_adapter.py`로 `sanitize_log()`를 이동. 보안 규칙은 한 곳에서 관리해야 다음 진입점(예: 나중에 추가할 manual trigger 스크립트)이 자동으로 같은 보호를 받음.
**다시 마주칠 가능성**: 높음 — 일반 원칙: 보안 관련 함수(sanitize, redact, mask)는 utils/shared 모듈에 두고 절대 복사하지 않는다.

---
category: tooling
applied: not-yet
---
## state.json 비원자 쓰기는 cron 환경에서 크래시 복구 불가

**상황**: Step 4(code-reviewer). `path.open("w")` 즉시 파일을 truncate하므로 write 중 crash 시 빈 파일 또는 partial JSON이 남아 다음 폴링이 빈 `AppState`로 시작 → 모든 영상 재적재.
**판단**: `tmp + os.replace` 패턴으로 교체. 원자적 rename은 같은 파일시스템 내에서 atomic을 보장(POSIX).
**다시 마주칠 가능성**: 높음 — cron 등 무인 환경의 상태 파일은 모두 이 패턴이 default여야 함.

---
category: tooling
applied: not-yet
---
## polling 모델이 NotebookLM artifact 생성에 맞지 않음

**상황**: spike. `wait_for_completion`에 5분 timeout을 줬지만 Audio·Video 모두 timeout. NotebookLM은 artifact를 수분~수십 분에 걸쳐 비동기로 생성함.
**판단**: "trigger만 책임, 완료 확인은 NotebookLM UI"로 spec·plan을 조정. 자동 완료 확인을 원한다면 별도 polling cron 또는 NotebookLM이 webhook/push를 제공할 때까지 대기.
**다시 마주칠 가능성**: 중간 — 장기 실행 작업(ML 처리, 문서 변환 등)을 외부 API에 위임하는 feature라면 동일 패턴.
