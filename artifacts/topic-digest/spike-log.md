# Spike: NotebookLM end-to-end pipeline

**Date**: 2026-05-28
**Library**: `notebooklm-py` 0.5.0 (unofficial)
**Account**: neohacz2@gmail.com
**Test source**: `https://www.youtube.com/watch?v=AJpK3YTTKZ4`
**Notebook id**: `6c171f1a-4839-46be-9b16-b91495aa8c4b` (남겨둠 — UI에서 결과물 확인 후 삭제)

## Goal

Idea의 **Must Be True** 가정 검증: `notebooklm-py`로 노트북 생성 + source push + artifact trigger가 안정적으로 동작하는가.

## Raw Result

| Step | Latency | Outcome |
|---|---|---|
| Create notebook | 1.5s | ✅ |
| Add YouTube URL | 3.0s | ✅ |
| Audio Overview — trigger | 4.2s | ✅ task_id 반환 |
| Audio Overview — completion | 290s timeout | ⏳ backend 생성 중 (NotebookLM UI에서 확인 필요) |
| Video Overview — trigger | 2.7s | ✅ task_id 반환 |
| Video Overview — completion | 290s timeout | ⏳ backend 생성 중 |
| Infographic — trigger | 2.3s | ❌ `UnknownRPCMethodError: safe_index drift … method_id='R7cb6c'` — **원인 규명됨, 아래 참고** |
| Mind Map — trigger | 4.9s | ⚠️ HTTP 성공, 라이브러리 반환 타입이 dict (코드의 `status.task_id` 접근 실패) |

## Verdict

**PASS — 조건부.** 핵심 자동화 경로(노트북 생성 → source push → artifact trigger)는 동작한다. Aspect별로:

- **Audio·Video**: 자동화 가능. 단, polling 모델은 실용성 낮음(5분 안에 안 끝남). **fire-and-poll-later 패턴**이 현실적: trigger 후 UI/별도 cron으로 완료 확인.
- **Infographic**: **자동화 가능 — orientation 필수.** `orientation=None`(라이브러리 기본값)이면 Google 백엔드가 즉시 null 반환 → 라이브러리가 `UnknownRPCMethodError`로 crash. `orientation=InfographicOrientation.PORTRAIT` 명시 시 정상 동작. CLI `notebooklm generate infographic --orientation portrait` 및 라이브러리 직접 호출 모두 `status=COMPLETED` 확인. 자세한 내용 아래 **2026-05-28 Infographic 재검증** 섹션 참조.
- **Mind Map**: HTTP는 성공하지만 라이브러리 반환 타입 비일관. dict에서 `task_id` 키 직접 추출하면 우회 가능. 라이브러리 이슈로 보고 가치 있음.

## Discovered Risks (Spec 단계로 가져갈 것)

1. **Polling은 안 맞는 모델**. NotebookLM artifact 생성은 분 단위. Spec의 동작 정의에서 *동기 완료*를 가정하면 안 된다 → "trigger 후 N분 뒤 결과 회수" 또는 "사용자가 UI에서 보러 간다" 모델.
2. **라이브러리 깨짐 가능성이 일상**. `notebooklm-py` 0.5.0이 2026.05.24 출시인데 5월 28일 시점 이미 Infographic 깨짐. **두 단계 fallback** 설계 필요:
   - L1: 라이브러리 호출
   - L2: Playwright로 NotebookLM UI 직접 조작
   - L3: 사용자 수동 트리거
3. **노트북당 source 50개 제한**. Daily/weekly ingestion이면 1-2년 안에 한계 도달 → 노트북 rotation 또는 archive 전략.
4. **DeprecationWarning**: `await NotebookLMClient.from_storage()`가 v1.0에서 제거. 컨텍스트 매니저만 쓰는 형태로 작성한다.

## Should Be True 검증 (다음)

생성된 Audio/Video/Mind Map의 *품질*은 NotebookLM UI에서 직접 확인 가능. 노트북 id `6c171f1a-…`에 가서:
- Audio Overview가 내용을 정확히 요약하는가?
- Video Overview의 비주얼이 발행할 만한가?
- Mind Map이 의미 있게 구조화되어 있는가?

## Open Items

- [ ] NotebookLM UI에서 결과물 품질 확인 (사용자 직접)
- [x] `notebooklm-py` 이슈 트래커에서 Infographic R7cb6c 이슈 검색 — **원인 규명됨**: method ID 문제 아님, orientation=None이 근본 원인
- [x] Mind Map dict 반환 경로 확인 — `_extract_task_id`에서 dict·객체 양쪽 처리하는 것으로 해결됨
- [ ] Source 50개 제한에 부딪히는 시점 추정 (예: 주 5개 ingestion → 약 10개월)

---

## 2026-05-28 Infographic 재검증

**Date**: 2026-05-28 (초기 스파이크 당일)
**목적**: Infographic 실패 원인 규명 및 자동화 가능성 재확인

### 조사 과정

| 단계 | 시도 | 결과 |
|---|---|---|
| 1 | 라이브러리 그대로 재시도 (`orientation=None`) | `UnknownRPCMethodError` 동일 |
| 2 | raw RPC 직접 호출 (orientation=None) | HTTP 200, 응답 `None`, 5초 내 `status=4(FAILED)` |
| 3 | Audio·Video 동일 raw RPC 경로 비교 | Audio·Video는 task_id 반환 — **infographic만 None 반환** |
| 4 | 파라미터 구조 변형 4종 (position 6/14, 최소, sids2 추가) | 모두 동일하게 FAILED |
| 5 | 소스 상태 확인 | `SourceStatus.READY (2)` — 소스 문제 아님 |
| 6 | CLI `notebooklm generate infographic --orientation portrait` | ✅ task_id 반환, `status=3(COMPLETED)` 확인 |
| 7 | `generate_infographic(orientation=PORTRAIT)` 라이브러리 호출 | ✅ `GenerationStatus` 정상 반환 (rate limit 중에도 crash 없음) |

### 근본 원인

`orientation` 파라미터가 **Google 백엔드의 필수값**이었음.

- `orientation=None` → params에 `null` 전달 → Google이 즉시 null 반환 → 라이브러리 `safe_index(None, 0, 0)` crash
- `orientation=PORTRAIT(2)` → Google이 정상 처리 → task_id 반환 → `status=COMPLETED`

초기 스파이크에서 "method_id가 바뀐 것으로 추정"한 것은 오진이었음.

### 적용된 코드 변경 (commit `a4842f0`)

- `notebooklm_adapter.py`: `Adapter` Protocol·`NotebookLMAdapter`·`InMemoryAdapter`에 `generate_infographic` 추가. `orientation=InfographicOrientation.PORTRAIT` 기본값으로 고정.
- `batch.py`: `_ARTIFACT_TYPES = ("audio", "video", "mind_map", "infographic")`
- `test_batch.py`: 4개 artifact 기준으로 전체 테스트 업데이트 (13/13 통과)

### 업데이트된 Verdict

**PASS — 조건부 해제.** Infographic 포함 4개 artifact 모두 자동화 가능.

- **rate limit 주의**: 짧은 시간에 다수 trigger 시 `RateLimitError (Resource exhausted)` 발생. 주 1회 batch 패턴에서는 문제 없을 것으로 예상.
- **orientation 고정값**: `PORTRAIT`을 기본으로 사용. 향후 config에서 조정 가능하도록 열어둘 수 있음.
