# Grosmimi Japan - 콘텐츠 제작 워크플로우
> 최종 업데이트: 2026-02-25

---

## 목적
일본 인스타그램 피드/카루셀/Meta 광고용 콘텐츠를 4개 카테고리별로 체계적으로 생산한다.

---

## 사전 준비 (필수 참고 파일)

| 참고 문서 | 경로 | 용도 |
|-----------|------|------|
| 브랜드 가이드라인 | `workflows/jp_brand_guideline.md` | 브랜드 톤, 비주얼 규칙, 카피 레퍼런스 |
| 경쟁사 인사이트 | `workflows/jp_competitor_insights.md` | 차별화 포인트, 시장 트렌드 |
| 디자이너 기존 작업물 | `2601/`, `2602/`, `0109_PPSU/`, `0128/`, `0212_JP/` | 비주얼 스타일 레퍼런스 |
| 참고 이미지 | `참고 이미지/` | 로고, 제품 배너, 촬영 원본 |
| 제품 데이터 | `.firecrawl/onzenna_grosmimi_*.md` | 제품 스펙, 설명 |

---

## 카테고리 1: 재미있는 육아 Meme (共感コンテンツ)

### 목적
- 엄마/파파의 공감을 얻어 저장·공유 유도
- 브랜드 친근감 형성
- 팔로워 확대 (Non-follower reach)

### 콘텐츠 유형
| 유형 | 예시 | 포맷 |
|------|------|------|
| 육아 あるある | "ストローマグ振り回す赤ちゃん vs ママ" | 1080x1080 정사각 |
| Before/After | "外出前のカバン vs 帰宅後のカバン" | 1080x1080 정사각 |
| 비교 밈 | "理想の水分補給 vs 現実" | 1080x1080 정사각 |
| 퀴즈/투표 | "ストローマグ、何個試しましたか？" | 1080x1080 or Story |

### 비주얼 스타일
- 밝고 가벼운 톤 (크림/파스텔 배경)
- 귀여운 일러스트 또는 실사+텍스트 오버레이
- 큰 일본어 텍스트 (스크롤 멈추게)
- GROSMIMI 로고: 하단 작게

### 카피 가이드
- 1~2줄의 임팩트 있는 공감 문구
- 이모지 적절히 사용
- 댓글 유도: "あるある！と思ったらいいね❤️"
- 해시태그: #育児あるある #ママあるある #育児の味方

### 생산 프로세스
```
1. 일본 육아 커뮤니티 트렌드 확인 (X/Twitter, Instagram)
2. 공감 포인트 선정 (페인포인트 기반)
3. 카피 작성 (일본어)
4. 이미지 프롬프트 작성
5. tools/generate_image.py 실행 (--model flash)
6. 디자이너 검수 & 텍스트 보정
7. 해시태그 세트 첨부
```

### 월간 생산량 목표: 4~6개

---

## 카테고리 2: 제품 교육 (プロダクト教育コンテンツ)

### 목적
- 제품 기능/특징을 이해하기 쉽게 전달
- "왜 Grosmimi인가?" 설득
- 구매 전환 유도

### 콘텐츠 유형
| 유형 | 예시 | 포맷 |
|------|------|------|
| 기능 소개 카드 | "+CUT ストロー って何？" | 1080x1350 (4:5) |
| 비교 인포그래픽 | "PPSU vs PP: 何が違う？" | 카루셀 (3~6슬라이드) |
| HowTo / Q&A | "ストローマグ いつから始める？" | 카루셀 (4~8슬라이드) |
| 제품 라인 가이드 | "月齢別おすすめマグガイド" | 카루셀 (5~7슬라이드) |
| ストロー交換 가이드 | "ストローの替え時サイン" | 1080x1080 or 카루셀 |

### 비주얼 스타일
- 클린 배경 (아이보리 #F5F0E8 또는 화이트)
- 인포그래픽: 둥근 모서리 카드, 아이콘+텍스트
- 제품 사진 크게 배치 (참고 이미지 폴더 활용)
- 숫자/데이터 강조 (200°C, 6시간, BPA Free)
- 색상: 코랄 액센트 (#E8735A) + 소프트 블루 (#6B9BD2) 뱃지

### 카피 가이드
- 교육적이되 딱딱하지 않게
- "知ってた？" "実は…" 로 호기심 유도
- 기능 → 베네핏 변환:
  - ❌ "PPSU素材を使用"
  - ✅ "病院でも使われる安全素材だから、安心"
- CTA: "詳しくはプロフィールリンクから" / "保存して後で読む📌"
- 해시태그: #ストローマグ #PPSUマグ #漏れないマグ #離乳食グッズ

### 참고 기존 작업물
- `2601/260123/` — 4포인트 기능 소개
- `2601/260130/` — PPSU vs PP 비교
- `2602/260204/` — 월령별 체크리스트 카루셀
- `2602/260220/` — Why Grosmimi 카루셀

### 생산 프로세스
```
1. 교육 토픽 선정 (소비자 Q&A 기반)
   - 참고: jp_competitor_insights.md > 소비자 인사이트
2. 슬라이드 구조 설계 (카루셀인 경우)
3. 각 슬라이드 카피 작성 (일본어)
4. 이미지 프롬프트 작성 (제품 사진 + 텍스트 레이아웃)
5. tools/generate_image.py 실행
   - 제품 실사 필요시: --edit 모드로 참고 이미지 활용
6. 디자이너 검수 & 텍스트/레이아웃 보정
7. 해시태그 세트 첨부
```

### 월간 생산량 목표: 4~8개

---

## 카테고리 3: 이벤트 & 프로모션 (イベント・プロモ)

### 목적
- 시즌/이벤트에 맞춘 적시 콘텐츠
- 직접적 구매/행동 전환
- LINE 친구 추가, 쿠폰 사용 유도

### 콘텐츠 유형
| 유형 | 예시 | 포맷 |
|------|------|------|
| 시즌 기획 | "🌸入園準備チェックリスト" | 카루셀 |
| 할인/쿠폰 | "LINE友だち限定 10%OFF" | 1080x1080 (피드+Story) |
| 기프트 추천 | "出産祝いにおすすめ" | 1080x1350 |
| 캠페인 | "フォロー&いいねでプレゼント" | 1080x1080 |
| 한정 세트 | "季節限定カラー" | 1080x1080 |

### 비주얼 스타일
- 이벤트 분위기 (시즌 컬러, 장식 요소)
- 큰 CTA 버튼 (Shop Now / LINE追加)
- LINE 그린 (#06C755) 배지
- 할인율 대형 표시
- Meta 광고 참고: `0109_PPSU/`, `0128/`, `0212_JP/`

### 시즌 캘린더 연동
```
참고: workflows/jp_brand_guideline.md > 8. 시즌 캘린더
```
| 월 | 핵심 이벤트 | 콘텐츠 방향 |
|----|------------|------------|
| 3月 | ひな祭り・入園準備 | 입원 준비 체크리스트 + 세트 추천 |
| 4月 | 入園/入学・お花見 | 벚꽃 외출 + 마그 |
| 5月 | こどもの日・母の日 | 엄마 감사 기획, 기프트 세트 |
| 6月 | 梅雨・父の日 | 실내 수분보급, 파파 육아 |
| 7月 | 夏休み | 여름 외출 스테인리스 추천 |
| 8月 | お盆 | 귀성 필수 아이템 |
| 9月 | 敬老の日 | 조부모 선물 |
| 10月 | ハロウィン | 시즌 한정 이벤트 |
| 11月 | 七五三・BF | 성장 축하 + 블프 세일 |
| 12月 | クリスマス | 기프트 세트 |

### 카피 가이드
- 긴급감/한정감: "数量限定" "期間限定" "今だけ"
- 명확한 CTA: "商品を見る >" "LINE友だち追加"
- 혜택 강조: "10%OFFクーポン" "送料無料"

### 생산 프로세스
```
1. 다음 달 시즌 캘린더 확인
2. 이벤트에 맞는 콘텐츠 기획 (프로모 내용 확정)
3. 카피 작성 (제목 + CTA + 조건)
4. 이미지 프롬프트 작성
5. tools/generate_image.py 실행
6. Meta 광고 버전 추가 생성 (1:1 + 9:16)
7. 디자이너 검수
8. 해시태그 + CTA 링크 준비
```

### 월간 생산량 목표: 2~4개

---

## 카테고리 4: 라이프스타일 사용 이미지 (ライフスタイル)

### 목적
- 제품이 일상에 자연스럽게 녹아드는 이미지 구축
- 감성적 브랜드 경험 전달
- "이 제품 쓰면 이런 일상" 을 보여주기

### 콘텐츠 유형
| 유형 | 예시 | 포맷 |
|------|------|------|
| 외출 장면 | "公園でのマグタイム 🌳" | 1080x1350 (4:5) |
| 집안 일상 | "朝のルーティン ☀️" | 1080x1080 |
| 성장 모멘트 | "はじめてのストロー飲み 🎉" | 1080x1350 |
| 시즌 라이프 | "桜の下でおやつタイム 🌸" | 1080x1080 |
| 플랫레이 | "お出かけバッグの中身 👜" | 1080x1080 |

### 비주얼 스타일
- 따뜻한 자연광, 소프트 톤
- 일본 가정 인테리어/일본 공원/일본 일상 배경
- 아기 (6개월~2세) 가 마그를 자연스럽게 사용하는 장면
- 제품이 주인공이되, 광고 느낌 최소화
- 기존 촬영 원본 참고: `참고 이미지/2505_photo172.jpg`, `참고 이미지/2508_photo540.jpg`

### 카피 가이드
- 감성적 1~2줄
- 참고 레퍼런스:
  - "今日も、ひと安心。小さな「できた」を大切に。"
  - "ママから贈る はじめてのマグ"
  - "成長のはじまりは、グロミミのマグで"
- 해시태그: #赤ちゃんとお出かけ #赤ちゃんのいる暮らし #子どものいる暮らし #ママライフ

### 생산 프로세스
```
1. 시즌/상황 설정 (외출, 집, 공원, 여행 등)
2. 장면 설계 (배경, 소품, 아기 행동)
3. 감성 카피 작성 (일본어)
4. 이미지 프롬프트 작성
   - 배경: 일본 가정/공원/카페
   - 조명: warm natural light
   - 제품: Grosmimi PPSU 상세 묘사 (amber body, white handle, +CUT straw)
   - 아기: 6~18개월, 자연스러운 포즈
5. tools/generate_image.py 실행 (--model flash 또는 pro)
   - 고품질 필요시: --edit 모드로 실제 제품 사진 합성
6. 디자이너 검수
7. 해시태그 세트 첨부
```

### 월간 생산량 목표: 4~6개

---

## 전체 월간 콘텐츠 캘린더 템플릿

| 주차 | Mon | Wed | Fri |
|------|-----|-----|-----|
| 1주 | 라이프스타일 | 제품교육 | Meme |
| 2주 | 이벤트/프로모 | 라이프스타일 | 제품교육 |
| 3주 | Meme | 라이프스타일 | 제품교육 |
| 4주 | 이벤트/프로모 | Meme | 라이프스타일 |

**월간 총량: 12~24개 콘텐츠**
- Meme: 4~6개
- 제품교육: 4~8개
- 이벤트/프로모: 2~4개
- 라이프스타일: 4~6개

---

## 이미지 생성 공통 규칙

### Gemini 프롬프트 작성 원칙
1. **영어로 작성** (Gemini는 영어 프롬프트가 품질 높음)
2. **제품 묘사 필수 포함**:
   ```
   Grosmimi PPSU straw cup: amber/honey-colored translucent PPSU body,
   white cap with +CUT cross-cut leak-proof straw,
   white 360-degree rotating handles, round compact design
   ```
3. **일본어 텍스트는 프롬프트에 명시**:
   - 주요 카피 그대로 입력
   - Flash 모델은 일본어 렌더링이 불완전할 수 있음 → 디자이너 수정 전제
4. **배경/분위기 지정**:
   - 색상 코드 명시 (#F5F0E8 등)
   - "soft natural lighting", "warm ivory background"
5. **로고 위치 지정**:
   - "small GROSMIMI logo at bottom center"

### 모델 선택 기준
| 상황 | 모델 | 이유 |
|------|------|------|
| 빠른 초안/테스트 | flash | 속도 빠름, 크레딧 절약 |
| 최종 고품질 | pro | 디테일 우수 (서버 상태 확인 필요) |
| 제품 합성/편집 | flash --edit | 실제 제품 이미지 기반 편집 |

### 파일 명명 규칙
```
{카테고리}_{주제}_{날짜}.png

예시:
meme_leaking_bag_20260301.png
edu_ppsu_vs_pp_20260305.png
promo_spring_sale_20260310.png
life_park_outing_20260315.png
```

### 저장 위치
- 초안: `.tmp/images/`
- 최종본: `Data Storage/images/`

---

## 실행 커맨드 예시

### Meme 이미지 생성
```bash
python tools/generate_image.py \
  --prompt "Cute illustration style, split image: LEFT side shows a mom's fantasy of a clean organized diaper bag with a Grosmimi PPSU straw cup neatly placed. RIGHT side shows reality: the bag is a mess with toys, snacks, and baby items everywhere but the Grosmimi cup is still perfectly sealed with no leaks. Japanese text at top: '理想 vs 現実' in bold gothic font. Warm cream background (#F5F0E8). Small GROSMIMI logo at bottom." \
  --model flash \
  --output .tmp/images/meme_ideal_vs_reality.png
```

### 제품교육 카루셀 커버
```bash
python tools/generate_image.py \
  --prompt "Clean infographic style, cream background (#F5F0E8). Center: Grosmimi PPSU straw cup (amber translucent body, white handles). Large Japanese text: 'PPSUって何？' in bold dark charcoal (#333333). Subtitle: '病院でも使われるプレミアム素材' in coral (#E8735A). Small icons around the cup: thermometer (200°C), shield (BPA Free), sparkle (耐久性). Small GROSMIMI logo bottom center." \
  --model flash \
  --output .tmp/images/edu_ppsu_what_cover.png
```

### 라이프스타일 이미지
```bash
python tools/generate_image.py \
  --prompt "Warm lifestyle photograph: a Japanese 10-month-old baby sitting in a highchair in a bright modern Japanese kitchen, holding a Grosmimi PPSU straw cup (amber honey-colored translucent body, white cap with straw, white 360-degree rotating handles). Baby is happily drinking. Soft morning sunlight through the window. Clean minimal Japanese interior. Warm ivory tones. Soft text overlay at bottom: '今日も、ひと安心。' in gentle gothic font. Small GROSMIMI logo at bottom right." \
  --model flash \
  --output .tmp/images/life_morning_routine.png
```

---

## 품질 체크리스트

### 생성 후 확인 사항
- [ ] 제품이 Grosmimi PPSU로 인식 가능한가? (amber body, white handle)
- [ ] 일본어 텍스트가 정확한가? (Flash 모델 오타 확인)
- [ ] 브랜드 컬러 팔레트 준수하는가?
- [ ] GROSMIMI 로고가 포함되어 있는가?
- [ ] 이미지 사이즈가 맞는가? (1080x1080 또는 1080x1350)
- [ ] 타겟 오디언스(25-38세 일본 엄마)에게 적절한 톤인가?
- [ ] 경쟁사 제품과 혼동되지 않는가?

### 디자이너 핸드오프
1. AI 생성 이미지 + 프롬프트 전달
2. 일본어 텍스트 정확도 보정 요청
3. 로고 정확한 배치 확인
4. 최종 PSD/AI 파일로 완성
