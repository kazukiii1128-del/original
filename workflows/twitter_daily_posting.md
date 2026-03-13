# Twitter/X Daily Posting SOP (Grosmimi Japan)

> 그로미미 재팬 트위터 일일 운영 표준 작업 절차

---

## 파이프라인 플로우

```
[1. 예산 확인] → [2. 트렌드 수집] → [3. 콘텐츠 기획] → [4. 포스팅] → [5. 멘션 모니터링]
```

---

## Step 1: 일일 예산 확인

```bash
py -3 tools/twitter_post.py --budget
```

Free 티어 예산 (일 50트윗):
- 오리지널 트윗: 2~3
- 스레드 (3~5트윗): 1개
- 멘션 응답: 최대 5
- 예비 버퍼: ~35

---

## Step 2: 트렌드 수집 (3일에 1회)

```bash
# 트위터 트렌드 스크래핑
py -3 tools/twitter_trends.py

# 기존 트렌드 파일에 병합
py -3 tools/twitter_trends.py --merge
```

트렌드 데이터가 3일 이상 된 경우에만 재수집.

---

## Step 3: 콘텐츠 기획

### Option A: 트위터 네이티브 콘텐츠

```bash
# 3일치 기획
py -3 tools/plan_twitter_content.py --count 3

# 스레드만 기획
py -3 tools/plan_twitter_content.py --count 2 --type thread

# 특정 주제
py -3 tools/plan_twitter_content.py --topic "ストローデビュー" --type single
```

### Option B: 인스타그램 콘텐츠 크로스포스팅

```bash
py -3 tools/plan_twitter_content.py --convert-from-ig
```

### 기획안 검토

```bash
# dry-run으로 먼저 확인
py -3 tools/twitter_post.py --dry-run
```

---

## Step 4: 포스팅

```bash
# 다음 예정된 트윗 포스팅
py -3 tools/twitter_post.py

# 특정 기획안 포스팅
py -3 tools/twitter_post.py --post-id 20260225_T001

# 즉석 트윗 (기획안 없이)
py -3 tools/twitter_post.py --text "今日もお疲れさま！育児って大変だけど、一緒に頑張ろうね🍼✨ #育児 #ママ"

# 이미지 첨부 트윗
py -3 tools/twitter_post.py --text "テスト" --image .tmp/content_images/slide_1.jpg
```

---

## Step 5: 멘션 모니터링

```bash
# 새 멘션 확인만
py -3 tools/twitter_reply.py --check-only

# 멘션 확인 + 자동 응답
py -3 tools/twitter_reply.py

# 응답 미리보기
py -3 tools/twitter_reply.py --dry-run
```

---

## 최적 포스팅 시간 (JST)

| 시간대 | 추천 | 이유 |
|--------|------|------|
| 07:00-08:00 | 평일 아침 | 출근길 스크롤 타임 (워킹맘) |
| 12:00-13:00 | 점심 | 점심시간 SNS 체크 |
| 20:00-22:00 | 저녁 | 아이 재운 후 자유 시간 (가장 반응 좋음) |
| 10:00-12:00 | 주말 | 느긋한 주말 오전 |

---

## 콘텐츠 믹스 (주간)

| 요일 | 콘텐츠 | 형식 |
|------|--------|------|
| 월 | 육아팁 or 브랜드 | 스레드 |
| 화 | 밈/공감 | 단일 트윗 |
| 수 | K-이유식 or 트렌드 | 단일 트윗 + 이미지 |
| 목 | 브랜드 or 육아팁 | 단일 트윗 |
| 금 | 밈/공감 | 단일 트윗 |
| 토 | 주말 느긋 콘텐츠 | 단일 트윗 |
| 일 | (선택) 가벼운 공감 | 단일 트윗 |

고정이 아니라 자율 배치. 트렌드와 밸런스를 보고 조정.

---

## 해시태그 전략 (Twitter)

Instagram과 다르게 Twitter는 2~3개가 최적:

```
항상 포함 (1개): #育児 또는 #子育て
선택 (1~2개): #ストローマグ, #ベビー用品, #育児グッズ, #ママ, #グロミミ
트렌딩: 관련 트렌드 해시태그 (있을 때만)
```

---

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| 예산 초과 | `--budget`으로 확인. 내일까지 대기 |
| 트윗 280자 초과 | 스레드로 분할하거나 문구 축약 |
| 이미지 업로드 실패 | 5MB 이하, JPEG/PNG/GIF 확인 |
| 멘션 조회 안됨 | Free tier 15분 제한. 시간 후 재시도 |
| API 403 에러 | `py -3 tools/twitter_auth.py --verify` |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-02-25 | 초안 작성 |
