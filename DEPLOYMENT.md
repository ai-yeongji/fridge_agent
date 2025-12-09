# 🚀 Streamlit Cloud 배포 가이드

## 📋 사전 준비

1. **GitHub 계정** - https://github.com
2. **Streamlit Cloud 계정** - https://streamlit.io/cloud (GitHub로 로그인)
3. **OpenAI API 키** - https://platform.openai.com/api-keys

---

## 1️⃣ GitHub에 코드 업로드

### 1. Git 커밋 및 푸시

```bash
# 현재 프로젝트 디렉토리에서
git add .
git commit -m "Initial commit: 냉요 (냉장고 요정) 앱"

# GitHub에 새 저장소 만들기 (https://github.com/new)
# 저장소 이름: freeze-agent (또는 원하는 이름)
# Public 또는 Private 선택

# 원격 저장소 연결 및 푸시
git remote add origin https://github.com/당신의아이디/freeze-agent.git
git branch -M main
git push -u origin main
```

---

## 2️⃣ Streamlit Cloud 배포

### 1. Streamlit Cloud 접속
- https://share.streamlit.io 방문
- GitHub 계정으로 로그인

### 2. New app 클릭
- Repository: `당신의아이디/freeze-agent` 선택
- Branch: `main`
- Main file path: `app.py`

### 3. Advanced settings 클릭

#### Secrets 설정 (매우 중요!)
```toml
OPENAI_API_KEY = "sk-proj-xxxxx여기에당신의API키입력"
```

### 4. Deploy! 버튼 클릭

---

## 3️⃣ ⚠️ 중요 사항

### 데이터베이스 문제
**현재 SQLite 사용 시 Streamlit Cloud에서는 데이터가 재시작 시 삭제됩니다!**

해결 방법:
1. **개인 사용**: 그냥 사용 (재시작 시 데이터 손실 감수)
2. **공개 서비스**: 클라우드 DB로 변경 필요
   - PostgreSQL (Supabase 무료)
   - MongoDB
   - Firebase

### Supabase로 변경하는 방법 (추천)

1. **Supabase 가입**: https://supabase.com
2. **requirements.txt에 추가**:
   ```
   psycopg2-binary
   ```
3. **database.py 수정**:
   ```python
   import os

   # PostgreSQL 연결
   db_url = os.getenv('DATABASE_URL', 'sqlite:///fridge.db')
   ```
4. **Streamlit Secrets에 추가**:
   ```toml
   DATABASE_URL = "postgresql://user:password@host:port/database"
   ```

---

## 4️⃣ 비용 관련

### 무료 플랜
- **Streamlit Cloud**: 무료 (Public 앱 무제한)
- **GitHub**: 무료
- **OpenAI API**:
  - 사용량만큼 과금
  - GPT-4o Vision: 이미지당 약 $0.01-0.02
  - 월 사용량 제한 설정 권장

### 주의사항
⚠️ **공개 배포 시 다른 사람들이 당신의 OpenAI API를 사용하게 됩니다!**

해결책:
1. **인증 추가**: streamlit-authenticator 사용
2. **API 키 직접 입력**: 사용자가 자신의 API 키 입력하게
3. **비공개**: Private 저장소 + 초대된 사람만 접근

---

## 5️⃣ 사용자 인증 추가 (선택)

```python
# requirements.txt에 추가
streamlit-authenticator==0.2.3

# app.py 상단에 추가
import streamlit_authenticator as stauth

# 간단한 패스워드 보호
password = st.text_input("접속 비밀번호", type="password")
if password != st.secrets.get("APP_PASSWORD", ""):
    st.error("비밀번호가 틀렸습니다")
    st.stop()
```

---

## 6️⃣ 배포 후 확인

✅ 체크리스트:
- [ ] 앱이 정상적으로 로드되는가?
- [ ] 이미지 업로드가 작동하는가?
- [ ] AI 분석이 작동하는가?
- [ ] 데이터베이스 저장이 작동하는가?
- [ ] 대시보드가 정상적으로 표시되는가?

---

## 📱 완성된 앱 주소

배포 완료 후 주소:
```
https://당신의앱이름.streamlit.app
```

이 주소를 친구들과 공유하면 됩니다! 🎉

---

## 🔧 문제 해결

### 앱이 로드되지 않을 때
1. Streamlit Cloud 로그 확인
2. requirements.txt 확인
3. Secrets 설정 확인

### API 에러 발생 시
- Streamlit Secrets에 OPENAI_API_KEY가 올바르게 설정되었는지 확인
- OpenAI 계정에 크레딧이 있는지 확인

### 데이터가 사라질 때
- Streamlit Cloud는 앱 재시작 시 파일 시스템 초기화
- 클라우드 DB로 변경 필요
