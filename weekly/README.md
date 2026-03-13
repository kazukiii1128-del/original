# Kazuki Japan Team — Weekly Report Automation

매주 업무 로그를 작성하면 자동으로 Notion 위클리 리포트를 생성합니다.

---

## 폴더 구조

```
kazuki/
├── generate_weekly.py       # 메인 실행 스크립트
├── notion_template.md       # 리포트 양식 (참조용)
├── config.json              # API 연동 정보 ← 최초 1회 설정 필요
├── work_log/
│   ├── work_log_template.md # 매주 복사해서 작성
│   └── work_YYYY_MM_DD_log.md  # 실제 업무 로그 (매주 생성)
└── reports/
    └── weekly_YYYY_MM_DD.md # 생성된 리포트 저장
```

---

## 최초 설정 (1회만)

### 1. Python 패키지 설치

```bash
pip install anthropic requests
```

### 2. config.json 설정

`config.json` 을 열어 두 값을 실제 값으로 교체:

```json
{
  "notion": {
    "weekly_report_db_id": "YOUR_NOTION_DB_ID",
    "member_id": "YOUR_KAZUKI_NOTION_USER_ID"
  }
}
```

**weekly_report_db_id 확인 방법:**
- Notion에서 위클리 리포트 DB 페이지 열기
- URL에서 `?v=` 앞의 32자리 ID 복사
- 예: `notion.so/abc123...def456?v=xxx` → `abc123...def456`

**member_id 확인 방법:**
- 아래 명령 실행 후 본인 이름 옆의 id 복사:
```bash
curl -X GET "https://api.notion.com/v1/users" \
  -H "Authorization: Bearer YOUR_NOTION_API_TOKEN" \
  -H "Notion-Version: 2022-06-28"
```

---

## 매주 사용 방법

### 1. 업무 로그 작성

매주 금요일 또는 월요일에 `work_log/work_log_template.md` 를 복사하여 이번 주 월요일 날짜로 저장:

```
work_log/work_YYYY_MM_DD_log.md
예: work_2026_03_09_log.md  (이번 주 월요일 날짜)
```

파일 상단의 `## OKR_UPDATE` 섹션에 이번 주 수치 입력:

```
## OKR_UPDATE
new_skus_last=0          # 지난 주 SKU 수
new_skus_this=2          # 이번 주 SKU 수
contents_last=0
contents_this=5
reviews_last=12
reviews_this=13
ig_followers_last=826
ig_followers_this=855
ig_post_1=https://www.instagram.com/p/XXXXX/
ig_post_2=https://www.instagram.com/p/YYYYY/
ig_top_post=https://www.instagram.com/reel/ZZZZZ/
ig_top_likes=60
ig_top_comments=17
```

이후 섹션에 이번 주 업무 내용을 작성합니다.

### 2. 리포트 생성 실행

```bash
python generate_weekly.py
```

또는 날짜를 지정하여 실행:

```bash
python generate_weekly.py --date 2026-03-09
```

이미 생성된 리포트를 덮어쓰려면:

```bash
python generate_weekly.py --force
```

### 3. 결과 확인

- 로컬 파일: `reports/weekly_YYYY_MM_DD.md`
- Notion: 자동 업로드됨 (로그에 URL 출력)

---

## API 연동 정보

| 항목 | 값 |
|------|-----|
| Anthropic API Key | config.json 참조 |
| Notion API Token | config.json 참조 |
| Notion DB ID | config.json 설정 필요 |
| Claude 모델 | claude-sonnet-4-6 |

---

## 문제 해결

**`weekly_report_db_id 를 실제 값으로 교체하세요` 오류**
→ config.json 의 `weekly_report_db_id` 를 실제 Notion DB ID로 변경

**`work_log 파일이 없습니다` 오류**
→ `work_log/work_YYYY_MM_DD_log.md` 파일이 이번 주 월요일 날짜로 존재하는지 확인

**Notion 업로드 실패**
→ config.json 의 `api_token` 이 올바른지 확인
→ Notion Integration 이 해당 DB에 연결되어 있는지 확인 (DB → ... → Connections)
