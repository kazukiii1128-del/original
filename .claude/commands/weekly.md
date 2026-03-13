Kazuki의 이번 주 업무 내용을 받아 work_log 파일로 저장하고 위클리 리포트를 생성합니다.

## 처리 순서

1. 오늘 날짜 기준 이번 주 월요일 날짜 계산
2. 사용자가 제공한 내용을 파싱하여 `weekly/work_log/work_YYYY_MM_DD_log.md` 형식으로 저장
3. `python weekly/generate_weekly.py` 실행 (이미 파일이 있으면 `--force` 추가)

## 입력 형식

사용자는 아래 항목들을 자유롭게 한국어 또는 일본어로 작성합니다:

- **OKR 수치**: new_skus, contents, reviews (지난주/이번주 누적값)
- **이번 주 성과** (Wins & Achievements)
- **어려웠던 점** (Challenges)
- **해결한 문제 / 배운 점** (Problems Solved / Learnings)
- **다음 주 계획** (Next Week)

## work_log 파일 생성 규칙

사용자 입력을 아래 템플릿 구조에 맞춰 변환하여 저장하세요.
입력이 일본어이면 그대로 일본어로 저장합니다 (번역 불필요).
입력이 한국어이면 그대로 한국어로 저장합니다.

```
## OKR_UPDATE
new_skus_last=[지난주값]
new_skus_this=[이번주값]
contents_last=[지난주값]
contents_this=[이번주값]
reviews_last=[지난주값]
reviews_this=[이번주값]
# ig_followers / posts / top_post → Instagram API 자동 수집 (입력 불필요)

---

## 1️⃣ Primary Focus Areas

- 목표 SKU 전체 수출 준비 완료 상태 달성
- 300개 콘텐츠 제작 (형식 무관)
- 라쿠텐 리뷰 100개 달성
- 인스타그램 팔로워 10,000명 달성
- 라쿠텐 슈퍼 로지스틱스(RSL)로 전환

---

## 2️⃣ Wins & Achievements

[성과 내용]

---

## 3️⃣ Challenges

[도전 과제 내용]

Blockers:
- [없으면 "없음"]

Resource Needs:
- [없으면 "없음"]

---

## 4️⃣ Problems Solved / Learnings

[해결한 문제 및 배운 점]

---

## 5️⃣ Next Week

[다음 주 계획]
```

## 실행

파일 저장 후 터미널에서 `generate_weekly.py`를 실행하고 결과(Notion URL)를 사용자에게 알려주세요.

---

사용자 입력:
$ARGUMENTS
