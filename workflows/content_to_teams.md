# 콘텐츠 아이디어 → Teams 연동 워크플로우
> 최종 업데이트: 2026-02-26

---

## 목적
콘텐츠 아이디어를 Contents Planning 채널에 공유하여 팀 리뷰 & 피드백 수집

---

## 채널 정보
- Team ID: `b0fc344e-80d4-4c36-89e3-b423a38e3485`
- Channel ID: `19:c4cce3572af747d8a2744013e6d1e10a@thread.tacv2`
- 채널명: Contents Planning

---

## 사용 방법

### 1. 콘텐츠 플랜 카드 포스팅 (요약 알림)
```bash
# content_plan.json 기반으로 Adaptive Card 전송
python tools/teams_content.py --post-plan

# 특정 JSON 파일
python tools/teams_content.py --post-plan --plan-file .tmp/my_plan.json
```

### 2. 엑셀 파일 업로드 (전체 플랜)
```bash
# 엑셀 업로드
python tools/teams_content.py --upload "Japan_Marketing Plan_Monthly_V8.xlsx" --notify

# 특정 하위 폴더에 업로드
python tools/teams_content.py --upload "file.xlsx" --folder "2026-02" --notify
```

### 3. 아이디어 직접 포스팅 (Python 코드에서)
```python
from tools.teams_content import post_ideas_card

ideas = [
    {"title": "夜泣き対策 5選", "description": "...", "format": "carousel"},
    {"title": "ストローマグ比較", "description": "...", "format": "reel"},
]
post_ideas_card(ideas)
```

---

## 전형적 파이프라인

1. `plan_content.py` → `.tmp/content_plan.json` 생성
2. `teams_content.py --post-plan` → Teams 카드로 요약 공유
3. `teams_content.py --upload "V8.xlsx" --notify` → 엑셀 업로드 + 알림
4. 팀원이 Teams에서 피드백
5. 피드백 반영 후 `post_instagram.py`로 실행

---

## 셋업 필요사항

### Graph API (파일 업로드) — 이미 설정됨
같은 Azure AD 앱 사용 (TEAMS_GRAPH_CLIENT_ID/SECRET)

### Webhook (카드 알림) — 설정 필요
1. Teams → Contents Planning 채널 → 커넥터 관리
2. "Incoming Webhook" 추가
3. Webhook URL → `.env`의 `TEAMS_CONTENT_WEBHOOK_URL`에 추가

---

## .env 변수
```
# 기존 (공유)
TEAMS_TENANT_ID=...
TEAMS_GRAPH_CLIENT_ID=...
TEAMS_GRAPH_CLIENT_SECRET=...

# Contents Planning 전용
TEAMS_CONTENT_TEAM_ID=b0fc344e-80d4-4c36-89e3-b423a38e3485
TEAMS_CONTENT_CHANNEL_ID=19:c4cce3572af747d8a2744013e6d1e10a@thread.tacv2
TEAMS_CONTENT_WEBHOOK_URL=  ← Incoming Webhook URL 필요
```
