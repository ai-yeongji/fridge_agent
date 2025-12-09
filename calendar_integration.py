"""
구글 캘린더 연동 모듈
"""
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle
import streamlit as st

# 구글 캘린더 API 스코프
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarIntegration:
    """구글 캘린더 연동 클래스"""

    def __init__(self):
        self.creds = None
        self.service = None

    def authenticate(self):
        """
        구글 캘린더 인증

        Returns:
            bool: 인증 성공 여부
        """
        try:
            # 저장된 토큰이 있는지 확인
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    self.creds = pickle.load(token)

            # 토큰이 없거나 유효하지 않으면 새로 로그인
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # credentials.json 파일이 있어야 함
                    if not os.path.exists('credentials.json'):
                        st.error("❌ 구글 캘린더 인증 파일(credentials.json)이 없습니다.")
                        st.info("""
                        **구글 캘린더 연동 설정 방법:**

                        1. https://console.cloud.google.com/ 접속
                        2. 새 프로젝트 생성 (또는 기존 프로젝트 선택)
                        3. "API 및 서비스" > "사용 설정된 API 및 서비스" > "+ API 및 서비스 사용 설정"
                        4. "Google Calendar API" 검색 후 사용 설정
                        5. "사용자 인증 정보" > "사용자 인증 정보 만들기" > "OAuth 클라이언트 ID"
                        6. 애플리케이션 유형: "데스크톱 앱"
                        7. 생성된 JSON 파일을 다운로드하여 `credentials.json`으로 저장
                        """)
                        return False

                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    self.creds = flow.run_local_server(port=0)

                # 토큰 저장
                with open('token.pickle', 'wb') as token:
                    pickle.dump(self.creds, token)

            # 캘린더 서비스 생성
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True

        except Exception as e:
            st.error(f"구글 캘린더 인증 오류: {str(e)}")
            return False

    def create_expiry_event(self, food_name, expiry_date, category="기타", location="냉장", quantity=1, unit="개"):
        """
        소비기한 만료 이벤트 생성

        Args:
            food_name: 음식 이름
            expiry_date: 소비기한 날짜 (date 객체)
            category: 카테고리
            location: 보관 위치
            quantity: 수량
            unit: 단위

        Returns:
            dict: 생성된 이벤트 정보
        """
        if not self.service:
            if not self.authenticate():
                return None

        try:
            # 이벤트 날짜 (소비기한 당일)
            event_date = expiry_date.isoformat()

            # 이벤트 생성
            event = {
                'summary': f'🚨 소비기한: {food_name}',
                'description': f'''
냉장고 음식 소비기한 알림

음식: {food_name}
카테고리: {category}
보관 위치: {location}
수량: {quantity} {unit}
소비기한: {expiry_date.strftime('%Y년 %m월 %d일')}

냉요(냉장고 요정)에서 자동 추가된 일정입니다.
                '''.strip(),
                'start': {
                    'date': event_date,
                },
                'end': {
                    'date': event_date,
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 24 * 60},  # 1일 전
                        {'method': 'popup', 'minutes': 3 * 24 * 60},  # 3일 전
                    ],
                },
                'colorId': '11',  # 빨간색
            }

            event = self.service.events().insert(calendarId='primary', body=event).execute()
            return event

        except HttpError as error:
            st.error(f"구글 캘린더 이벤트 생성 오류: {error}")
            return None

    def sync_food_items(self, food_items):
        """
        여러 음식 아이템을 구글 캘린더에 동기화

        Args:
            food_items: 음식 아이템 리스트

        Returns:
            tuple: (성공 개수, 실패 개수)
        """
        if not self.service:
            if not self.authenticate():
                return (0, len(food_items))

        success_count = 0
        fail_count = 0

        for food in food_items:
            event = self.create_expiry_event(
                food_name=food.name,
                expiry_date=food.expiry_date,
                category=food.category,
                location=food.location,
                quantity=food.quantity,
                unit=food.unit
            )

            if event:
                success_count += 1
            else:
                fail_count += 1

        return (success_count, fail_count)

    def delete_expiry_events(self):
        """
        냉요에서 생성한 모든 소비기한 이벤트 삭제

        Returns:
            int: 삭제된 이벤트 개수
        """
        if not self.service:
            if not self.authenticate():
                return 0

        try:
            # 향후 1년간의 이벤트 검색
            now = datetime.utcnow()
            time_min = now.isoformat() + 'Z'
            time_max = (now + timedelta(days=365)).isoformat() + 'Z'

            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                q='냉요',  # 냉요로 검색
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            deleted_count = 0

            for event in events:
                if '냉요(냉장고 요정)' in event.get('description', ''):
                    self.service.events().delete(
                        calendarId='primary',
                        eventId=event['id']
                    ).execute()
                    deleted_count += 1

            return deleted_count

        except HttpError as error:
            st.error(f"구글 캘린더 이벤트 삭제 오류: {error}")
            return 0
