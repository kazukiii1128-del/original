# 인스타그램 경쟁사 분석 워크플로우
> 최종 업데이트: 2026-02-26

---

## 목적
경쟁사 인스타그램 콘텐츠를 수집·분석하여 Grosmimi JP 콘텐츠 아이디어에 반영

---

## 방법 (2가지 병행)

### 방법 A: 수동 스크린샷 (빠르고 직관적)
1. 경쟁사 인스타를 보면서 참고할 게시물 스크린샷
2. `.tmp/competitor_refs/manual/`에 저장
3. Claude에게 "이거 분석해줘" 요청
4. 장점: 사람의 감각으로 필터링, 비용 0

### 방법 B: 자동 스크래핑 (정기적 모니터링)
1. `tools/scrape_ig_competitor.py` 실행
2. picuki.com에서 퍼블릭 데이터 수집 (무료)
3. 이미지 + 메타데이터 자동 저장
4. 장점: 정량 데이터(좋아요, 해시태그) 자동 수집

---

## 도구

### scrape_ig_competitor.py
```bash
# 기본 경쟁사 전체 (bboxforkidsjapan, pigeon_official.jp, richell_official, thermos_k.k)
python tools/scrape_ig_competitor.py

# 특정 계정만
python tools/scrape_ig_competitor.py bboxforkidsjapan

# 게시물 수 제한
python tools/scrape_ig_competitor.py bboxforkidsjapan --max 5

# 이미지 다운로드 생략 (메타데이터만)
python tools/scrape_ig_competitor.py --no-images

# 미리보기
python tools/scrape_ig_competitor.py --dry-run
```

### 출력 구조
```
.tmp/competitor_refs/
├── summary.json              ← 전체 요약 (빠른 참조용)
├── manual/                   ← 수동 스크린샷 폴더
├── bboxforkidsjapan/
│   ├── metadata.json         ← 프로필 + 게시물 데이터
│   ├── bboxforkidsjapan_001.jpg
│   └── ...
└── pigeon_official.jp/
    ├── metadata.json
    └── ...
```

---

## 분석 항목

Claude에게 요청할 수 있는 분석:

1. **콘텐츠 유형 분류** — 제품샷, UGC, 캠페인, 교육, 라이프스타일
2. **인게이지먼트 패턴** — 어떤 유형이 좋아요/댓글 많은지
3. **비주얼 트렌드** — 색감, 구도, 텍스트 오버레이 스타일
4. **캡션 전략** — 일본어 톤앤매너, CTA, 해시태그 조합
5. **우리 콘텐츠에 적용** — Grosmimi 스타일로 변환한 아이디어

---

## 추적 대상 계정

| 계정 | 브랜드 | 유형 |
|------|--------|------|
| bboxforkidsjapan | b.box Japan | 직접 경쟁 |
| pigeon_official.jp | Pigeon | 간접 경쟁 |
| richell_official | Richell | 직접 경쟁 |
| thermos_k.k | Thermos | 간접 경쟁 |

필요시 accounts 추가 가능

---

## 비용
- 방법 A (수동): 0원
- 방법 B (자동): 0원 (Firecrawl 미사용, requests로 직접 스크래핑)

---

## 주의사항
- picuki.com 구조 변경 시 파서 업데이트 필요
- 과도한 요청 자제 (RATE_LIMIT_DELAY = 2초)
- 수집 데이터는 내부 참고용으로만 사용
