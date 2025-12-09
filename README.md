# 🧚 냉요 (냉장고 요정) - 냉장고를 부탁해!

냉장고에 있는 음식들의 소비기한을 관리하고, 만료 임박 알림을 제공하는 웹 애플리케이션입니다.

## 주요 기능

- ✅ 음식 등록 및 관리 (CRUD)
- 📸 **사진으로 음식 자동 인식 + OCR 날짜 읽기** (OpenAI GPT-4o Vision)
- 📊 대시보드로 한눈에 보는 냉장고 현황
- ⚠️ 소비기한 임박 음식 알림
- 🗑️ 만료된 음식 자동 감지
- 📈 카테고리별 음식 분포 차트
- 🤖 AI 소비기한 추정 및 레시피 추천 (GPT-4o)
- 🔄 보관 위치별 필터링 (냉장/냉동/실온)
- 📅 **구글 캘린더 연동** - 소비기한 자동 동기화 및 알림

## 기술 스택

- **Frontend/Backend**: Streamlit (Python)
- **Database**: SQLite + SQLAlchemy
- **AI**: OpenAI GPT-4o Vision API (이미지 인식, OCR, 레시피 추천)

## 설치 방법

### 1. 저장소 클론

```bash
cd freeze_agent
```

### 2. 가상환경 생성 (권장)

```bash
# venv 사용
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 또는 conda 사용
conda create -n freeze python=3.10
conda activate freeze
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정 (필수 - AI 기능 사용)

```bash
cp .env.example .env
# .env 파일을 열어서 OPENAI_API_KEY에 실제 API 키를 입력
```

**OpenAI API 키 발급 방법:**
1. https://platform.openai.com/api-keys 접속
2. "Create new secret key" 클릭
3. `.env` 파일에 키 입력:
```
OPENAI_API_KEY=sk-proj-xxxxx
```

### 5. 구글 캘린더 연동 설정 (선택사항)

소비기한을 구글 캘린더에 자동으로 동기화하려면 추가 설정이 필요합니다.

자세한 설정 방법은 **[GOOGLE_CALENDAR_SETUP.md](GOOGLE_CALENDAR_SETUP.md)** 문서를 참고하세요.

**간단 요약:**
1. 구글 클라우드 콘솔에서 프로젝트 생성
2. Google Calendar API 활성화
3. OAuth 클라이언트 ID 생성 (데스크톱 앱)
4. `credentials.json` 다운로드 후 프로젝트 폴더에 저장

**주의**: 구글 캘린더 연동은 로컬 환경에서만 작동합니다. Streamlit Cloud에서는 파일 시스템 제약으로 사용할 수 없습니다.

## 실행 방법

```bash
streamlit run app.py
```

브라우저가 자동으로 열리며 `http://localhost:8501`에서 앱을 사용할 수 있습니다.

## 사용 방법

### 음식 추가 (2가지 방법)

**방법 1: 📸 사진으로 자동 인식 (추천)**
1. 사이드바에서 "➕ 음식 추가" 선택
2. 음식 사진 업로드
3. "🤖 AI로 분석하기" 버튼 클릭
4. AI가 자동으로 음식 정보 입력 (이름, 카테고리, 유통기한 등)
5. 필요시 수정 후 "추가하기"

**방법 2: ✍️ 수동 입력**
1. 사이드바에서 "➕ 음식 추가" 선택
2. 음식 이름, 카테고리, 구매일, 유통기한 등 직접 입력
3. "추가하기" 버튼 클릭

### 대시보드
- 전체 음식 수, 임박/만료 음식 통계 확인
- 유통기한 임박 음식 경고 확인
- 카테고리별 분포 차트 확인

### 음식 목록
- 모든 음식을 리스트로 확인
- 카테고리, 위치, 상태별 필터링
- 음식 삭제 기능

## 프로젝트 구조

```
freeze_agent/
├── app.py                    # Streamlit 메인 앱
├── database.py               # 데이터베이스 모델 및 CRUD
├── ai_agent.py               # AI 에이전트 (Vision API, 레시피 추천)
├── calendar_integration.py   # 구글 캘린더 연동
├── requirements.txt          # Python 패키지 의존성
├── .env.example             # 환경 변수 템플릿
├── .env                     # 환경 변수 (직접 생성 필요)
├── .gitignore               # Git 무시 파일
├── fridge.db                # SQLite 데이터베이스 (실행시 자동 생성)
├── credentials.json         # 구글 캘린더 OAuth 인증 파일 (직접 생성 필요)
├── README.md                # 프로젝트 문서
├── DEPLOYMENT.md            # Streamlit Cloud 배포 가이드
└── GOOGLE_CALENDAR_SETUP.md # 구글 캘린더 연동 설정 가이드
```

## 데이터 모델

### FoodItem (음식 아이템)
- `id`: 고유 ID
- `name`: 음식 이름
- `category`: 카테고리 (채소, 육류, 유제품, 과일, 조미료, 음료, 기타)
- `purchase_date`: 구매일
- `expiry_date`: 유통기한
- `location`: 보관 위치 (냉장, 냉동, 실온)
- `quantity`: 수량
- `unit`: 단위
- `memo`: 메모
- `created_at`: 생성일시
- `updated_at`: 수정일시

## 추후 개발 예정 기능

- [x] 이미지 업로드 및 AI 음식 인식 ✅
- [x] OCR로 소비기한/산란일자 자동 읽기 ✅
- [x] AI를 활용한 소비기한 추정 ✅
- [x] AI를 활용한 레시피 추천 ✅
- [x] 음식 수정 기능 ✅
- [x] 구글 캘린더 연동 및 알림 ✅
- [ ] 영수증 OCR로 일괄 등록
- [ ] 바코드/QR 스캔 기능
- [ ] 음성 입력 지원
- [ ] 푸시 알림 (모바일 앱 전환시)
- [ ] 음식 소비 패턴 분석
- [ ] 장보기 리스트 자동 생성
- [ ] 다중 사용자 지원
- [ ] 데이터 내보내기/가져오기

## 라이선스

MIT License

## 기여

버그 리포트나 기능 제안은 이슈로 등록해주세요!
