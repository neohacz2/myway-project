# Topic Digest — Spec

## 개요

지정된 YouTube 채널 1개를 무인으로 매일 폴링하여 새 영상을 본인 NotebookLM 노트북에 자동 적재하고, 주 1회 batch로 노트북의 Audio Overview / Video Overview / Mind Map을 재생성한다. 사용자는 NotebookLM UI를 방문해 누적된 결과물을 본다.

## 범위

### 포함
- 한 주제 1개("AI 에이전트 / LLM 일반")에 대응하는 NotebookLM 노트북 1개
- YouTube 채널 URL 1개의 새 영상을 매일 자동 감지
- 새 영상 URL을 노트북에 source로 자동 push
- 주 1회 batch 시점에 Audio Overview, Video Overview, Mind Map, Infographic을 트리거
- 운영 기록(폴링 결과, 적재 결과, 배치 결과, 실패) 로그 파일

### 제외
- **다중 주제 / 다중 노트북** — 본 라운드는 종단 검증 목적. 검증 후 추가
- **Infographic orientation 선택** — `orientation=PORTRAIT` 고정. 향후 config 노출 가능하나 본 라운드에서는 결정하지 않음
- **artifact 결과물의 외부 회수(노션·로컬 등)** — 사용자가 NotebookLM UI에서 직접 확인
- **YouTube 외 입력 소스(RSS, 블로그)** — 다음 라운드
- **발행 자동화(블로그/SNS 포스팅)** — idea.md의 Not Doing 그대로 유지

## 시나리오

### 1. 새 영상 일일 적재 (happy path)

- **Given** — 지정된 YouTube 채널에 새 영상 K개(K≥1)가 publish됐고, 이전 폴링 시점 이후 누적된 상태이며, 본인 NotebookLM 노트북이 존재한다
- **When** — 일일 폴링이 실행된다
- **Then** — 해당 K개 영상 URL이 노트북의 source 리스트에 추가되어 있다

성공 기준:
- [ ] 채널에 새 영상 3개가 있는 상태에서 폴링 1회 후 → NotebookLM 노트북의 source 개수가 폴링 전 대비 3 증가, 추가된 항목 각각이 해당 YouTube 영상 제목과 일치
- [ ] 새 영상이 0개인 상태에서 폴링 1회 후 → 노트북 source 개수가 변하지 않는다
- [ ] 폴링 결과(영상 개수, 추가 성공 개수, 실패 개수)가 로그에 한 줄로 기록된다

### 2. 중복 적재 방지

- **Given** — 어제 폴링에서 이미 적재된 영상 URL 1개가 채널 RSS에 여전히 존재한다
- **When** — 오늘 일일 폴링이 실행된다
- **Then** — 노트북 source 리스트에 같은 영상이 2회 등장하지 않는다

성공 기준:
- [ ] 동일한 채널 RSS 상태에서 폴링을 연속 2회 실행 → 노트북 source 개수가 첫 폴링 결과와 같다(증가 0)
- [ ] 로그에 "skipped: already ingested"가 기록된다

### 3. 주1회 artifact batch (happy path)

- **Given** — 노트북에 source가 1개 이상 존재하고, 마지막 batch 이후 적재된 새 source가 1개 이상이다
- **When** — 주1회 batch가 실행된다
- **Then** — 노트북의 Audio Overview, Video Overview, Mind Map, Infographic이 각각 새로 생성되었거나 갱신되었다 (NotebookLM UI에서 새 artifact가 visible)

성공 기준:
- [ ] batch 실행 후 NotebookLM UI에서 각 artifact 타입별로 "최신 생성 시각"이 batch 실행 시각 이후로 갱신된다
- [ ] 4개 artifact 각각에 대해 trigger 성공/실패가 로그에 기록된다
- [ ] artifact 생성 *완료*는 batch 종료 시점에 보장되지 않는다 — batch는 trigger까지만 책임진다

### 4. 새 source 없는 주의 batch (낭비 방지)

- **Given** — 지난 batch 이후 노트북에 새 source가 0개 추가됐다
- **When** — 주1회 batch가 실행된다
- **Then** — artifact trigger를 호출하지 않는다 (이전 artifact 그대로 유지)

성공 기준:
- [ ] 새 source 0개 상태에서 batch 실행 후 NotebookLM artifact 생성 시각이 갱신되지 않는다
- [ ] 로그에 "no new sources; skip artifact batch"가 기록된다

### 5. YouTube 채널 접근 실패

- **Given** — 지정된 YouTube 채널 URL이 일시적으로 응답하지 않거나 변경되었다
- **When** — 일일 폴링이 실행된다
- **Then** — 적재가 시도되지 않으며, 다음 폴링은 정상 시도된다

성공 기준:
- [ ] 채널 응답 실패 1회 후 노트북 source 개수가 변하지 않는다
- [ ] 로그에 채널 응답 에러가 기록된다 (HTTP 상태/예외 메시지 포함)
- [ ] 24시간 후 정상 응답으로 복귀하면 그 시점부터 누적된 새 영상이 모두 적재된다

### 6. NotebookLM 인증 만료

- **Given** — `storage_state.json`의 쿠키가 만료되었거나 NotebookLM이 거부한다
- **When** — 일일 폴링 또는 주1회 batch가 실행된다
- **Then** — 작업이 즉시 중단되고 명확한 인증 실패 메시지가 로그에 기록된다 — 노트북 상태는 변경되지 않는다

성공 기준:
- [ ] 인증 실패 1회 발생 시 노트북 source/artifact 어떤 것도 변경되지 않는다
- [ ] 로그에 "auth expired — run `notebooklm login` to re-authenticate"가 기록된다

### 7. 라이브러리 메서드 깨짐 (개별 artifact)

- **Given** — `notebooklm-py`가 특정 artifact 타입(예: Mind Map)에서 라이브러리 내부 오류를 발생시킨다
- **When** — 주1회 batch가 실행된다
- **Then** — 다른 artifact 타입은 정상 trigger되고, 깨진 타입만 로그에 실패로 기록된다

성공 기준:
- [ ] Mind Map만 실패하는 상황에서 Audio + Video + Infographic은 NotebookLM UI에서 새로 생성된 것이 확인된다
- [ ] 로그에 실패한 artifact 타입과 예외 메시지가 분리되어 기록된다

## 불변 규칙

- **중복 적재 금지**: 동일 영상 URL은 노트북 source 리스트에 정확히 1회만 존재한다 (모든 시나리오 적용)
- **인증 정보 외부 노출 금지**: `storage_state.json`은 사용자 머신 바깥으로 전송되거나 로그에 포함되지 않는다
- **운영 흔적 누락 금지**: 폴링·batch 각 실행은 시작/종료 시각·결과 요약을 로그 1줄 이상으로 남긴다
- **부분 실패 격리**: 한 artifact 타입의 실패가 같은 batch의 다른 artifact trigger를 막지 않는다
- **안정성 목표**: 7일 연속 무인 실행 중 실패(폴링/적재/trigger 전체) 1회 이하

## 의존성

- 본인 Google 계정의 NotebookLM 접근 권한
- `notebooklm login`으로 발급된 유효한 `storage_state.json`
- 지정된 YouTube 채널 URL 1개 (publish 정보를 가져올 수 있어야 함 — 채널 RSS, YouTube Data API 키, 또는 동등한 수단)
- 인터넷 접근 가능한 환경 (실행 호스트 종류는 plan.md 소관)

## 미결정 항목

- **노트북 source 50개 한도 도달 시 처리**: 새 노트북 분기 vs 가장 오래된 source archive vs 처리 중단. 현 페이스(주 평균 N개 적재)에서 도달 시점이 6개월 이상이라 본 라운드 결정에서 제외. 도달 전에 별도 spec 필요.
- **Infographic 자동화 복귀 시점**: `notebooklm-py` 다음 릴리스 또는 RPA fallback 도입 여부. 본 라운드는 자동화 제외.
- **폴링/batch 정확한 시각**: 09:00 KST 폴링, 금요일 18:00 KST batch가 default 후보지만 사용자 일정에 따라 plan.md에서 조정.
