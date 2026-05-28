# topic-digest

YouTube 채널 1개 → NotebookLM 노트북 자동 적재 + 주1회 Audio/Video/Mind Map 재생성.

## 동작 방식

```
매일 09:00 KST
  YouTube 채널 RSS 폴링 → 신선 영상만 NotebookLM 노트북에 source push

매주 금 09:00 KST
  (신선 source가 1개 이상일 때만)
  Audio Overview, Video Overview, Mind Map 재생성 trigger
  → NotebookLM이 백그라운드에서 생성 완료
  → NotebookLM UI에서 결과 확인
```

결과물 회수 자동화는 없습니다. 생성 후 [NotebookLM](https://notebooklm.google.com/) 을 방문해 직접 확인하세요.

## 요구사항

| 항목 | 버전 |
|---|---|
| Python | 3.12+ |
| uv | 최신 |
| notebooklm-py | 0.5.0 (unofficial) |
| WSL2 or Linux | cron 실행 환경 |

## 설치

```bash
cd ~/edu/myway-project/scripts/topic-digest
uv sync                          # .venv 생성 + 의존성 설치
playwright install chromium      # 브라우저 인증용 (최초 1회)
```

## 설정

```bash
cp .env.example .env
# .env 편집:
#   YOUTUBE_CHANNEL_URL=https://www.youtube.com/channel/UC...
#   NOTEBOOK_ID=<NotebookLM 노트북 UUID>
#   STATE_PATH=./state.json       # 기본값 사용 가능
#   LOG_PATH=./logs/topic-digest.log
```

**NOTEBOOK_ID 확인**: NotebookLM에서 노트북을 열고 URL의 UUID 부분을 복사.
예: `https://notebooklm.google.com/notebook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` → `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

## 인증

```bash
notebooklm login
# 브라우저가 열리면 Google 계정으로 로그인
# 완료 시 ~/.notebooklm/profiles/default/storage_state.json 자동 저장
```

쿠키 만료(보통 수 주~수 개월) 시 로그에 아래 메시지가 나타납니다:

```
auth expired — run `notebooklm login` to re-authenticate
```

이 경우 `notebooklm login`을 다시 실행하세요.

## 수동 실행 (테스트)

```bash
cd ~/edu/myway-project/scripts/topic-digest

# 폴링 1회 실행
uv run python -m topic_digest.poll

# 배치 1회 실행
uv run python -m topic_digest.batch
```

## cron 등록

```bash
crontab -e
```

`crontab.example` 내용을 붙여넣고 경로를 본인 환경에 맞게 수정하세요.

> **KST 09:00** = UTC 00:00. 다른 시각을 원하면 cron 표현식을 조정하세요.

등록 확인:

```bash
crontab -l
```

## 로그 확인

```bash
# 실시간 tail
tail -f logs/topic-digest.log

# 오류만 필터
grep -E 'ERROR|FAIL|auth expired' logs/topic-digest.log

# 7일치 요약 (불변 규칙 5 검증)
grep -c -E 'error|exception|fail' logs/topic-digest.log
```

## 트러블슈팅

| 증상 | 원인 | 조치 |
|---|---|---|
| `auth expired` 로그 | storage_state.json 만료 | `notebooklm login` 재실행 |
| `channel fetch failed` 로그 | 채널 URL 오류 또는 일시 장애 | URL 확인, 다음 폴링 자동 재시도 |
| `mind_map: fail UnknownRPCMethodError` | 라이브러리 method drift | `notebooklm-py` 업데이트 확인. NotebookLM UI에서 수동 트리거 가능 |
| `infographic` 자동 생성 안 됨 | 현재 라이브러리 버전에서 미지원 | NotebookLM UI에서 수동 트리거 |
| cron이 실행 안 됨 | WSL2 cron 서비스 미시작 | `sudo service cron start` |

## 테스트 실행

```bash
cd ~/edu/myway-project/scripts/topic-digest
uv run pytest -v
```

## 운영 증거

7일 운영 후 결과물을 `artifacts/topic-digest/evidence/` 에 저장하세요:

- `week1-log.txt` — `grep -E 'ERROR|fail' logs/topic-digest.log` 결과
- `week1-notebook.png` — NotebookLM UI 스크린샷 (source 누적 + artifact 최신 시각)
