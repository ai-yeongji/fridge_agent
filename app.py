"""
냉장고 음식 소비기한 관리 앱
"""
import streamlit as st
from datetime import date, timedelta
import pandas as pd
import base64
import os
from dotenv import load_dotenv
from database import Database, FoodItem
from ai_agent import FoodRecognitionAgent
from calendar_integration import GoogleCalendarIntegration
from PIL import Image
import io

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="냉요",
    page_icon="🧚",
    layout="wide",
    initial_sidebar_state="collapsed"  # 모바일에서 사이드바 기본 접힘
)

# 데이터베이스 초기화
@st.cache_resource
def init_db():
    return Database()

db = init_db()

# 카테고리 및 위치 옵션
CATEGORIES = [
    "채소", "과일", "육류/해산물", "계란/두부", "유제품", "쌀/잡곡",
    "조미료/소스", "반찬/김치", "즉석식품/밀키트", "빵/디저트", "음료", "기타"
]
LOCATIONS = ["냉장", "냉동", "실온"]
UNITS = ["개", "kg", "g", "L", "mL", "팩", "봉지"]

# 상태별 색상
STATUS_COLORS = {
    "신선": "🟢",
    "임박": "🟡",
    "만료": "🔴"
}

# 보관 위치별 아이콘 및 색상
LOCATION_ICONS = {
    "냉장": "❄️",
    "냉동": "🧊",
    "실온": "🌡️"
}

LOCATION_COLORS = {
    "냉장": "#E3F2FD",  # 연한 파랑
    "냉동": "#B3E5FC",  # 진한 파랑
    "실온": "#FFF9C4"   # 연한 노랑
}

# 카테고리별 아이콘 및 색상
CATEGORY_ICONS = {
    "채소": "🥬",
    "과일": "🍎",
    "육류/해산물": "🥩",
    "계란/두부": "🥚",
    "유제품": "🥛",
    "쌀/잡곡": "🌾",
    "조미료/소스": "🧂",
    "반찬/김치": "🥘",
    "즉석식품/밀키트": "🍱",
    "빵/디저트": "🍰",
    "음료": "🥤",
    "기타": "📦"
}

CATEGORY_COLORS = {
    "채소": "#C8E6C9",      # 연한 초록
    "과일": "#FFCCBC",      # 연한 주황
    "육류/해산물": "#D7CCC8",  # 연한 갈색
    "계란/두부": "#FFF9C4",    # 연한 노랑
    "유제품": "#E1F5FE",     # 연한 하늘색
    "쌀/잡곡": "#F0E68C",    # 카키색
    "조미료/소스": "#F5F5F5",   # 연한 회색
    "반찬/김치": "#FFCDD2",    # 연한 빨강
    "즉석식품/밀키트": "#FFE0B2", # 연한 오렌지
    "빵/디저트": "#F8BBD0",    # 연한 핑크
    "음료": "#B3E5FC",      # 연한 파랑
    "기타": "#E0E0E0"       # 회색
}


def fix_image_orientation(image_bytes):
    """EXIF 정보를 읽어서 이미지 방향 수정"""
    try:
        image = Image.open(io.BytesIO(image_bytes))

        # EXIF 데이터에서 Orientation 태그 읽기
        exif = image.getexif()
        if exif:
            orientation = exif.get(0x0112)  # 0x0112는 Orientation 태그

            # Orientation 값에 따라 회전
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)

        # 수정된 이미지를 bytes로 변환
        output = io.BytesIO()
        image.save(output, format=image.format or 'JPEG')
        return output.getvalue()
    except Exception as e:
        print(f"이미지 방향 수정 오류: {e}")
        return image_bytes  # 오류 시 원본 반환


def main():
    st.title("🧚 냉요(냉장고 요정) - 냉장고를 부탁해!")
    st.caption("냉장고 음식 소비기한 관리 및 레시피 추천 에이전트")

    # 탭 메뉴
    tab1, tab2, tab3, tab4 = st.tabs(["📊 대시보드", "➕ 음식 추가", "📝 음식 목록", "🤖 AI 추천"])

    with tab1:
        show_dashboard()

    with tab2:
        show_add_food()

    with tab3:
        show_food_list()

    with tab4:
        show_ai_recommendations()


def show_dashboard():
    """대시보드 화면"""
    st.header("📊 대시보드")

    # 선택된 위치 필터 세션 스테이트
    if 'dashboard_filter' not in st.session_state:
        st.session_state.dashboard_filter = None

    # 통계
    all_foods = db.get_all_foods()
    expiring_soon = db.get_expiring_soon(days=3)
    expired = db.get_expired_foods()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("전체 음식", len(all_foods))
    with col2:
        st.metric("임박 (3일 이내)", len(expiring_soon), delta=None, delta_color="inverse")
    with col3:
        st.metric("만료됨", len(expired), delta=None, delta_color="inverse")

    # 날짜별 소비기한 캘린더 (맨 위로 이동)
    if all_foods:
        st.subheader("📅 소비기한 캘린더 (향후 1개월)")

        # 향후 30일간의 날짜별 만료 음식 그룹화
        from collections import defaultdict
        calendar_data = defaultdict(list)
        today = date.today()

        for food in all_foods:
            if food.expiry_date >= today and food.expiry_date <= today + timedelta(days=30):
                calendar_data[food.expiry_date].append(food)

        if calendar_data:
            # 날짜순으로 정렬
            sorted_dates = sorted(calendar_data.keys())

            for expiry_date in sorted_dates:
                foods = calendar_data[expiry_date]
                days_left = (expiry_date - today).days

                # 날짜별 카드
                if days_left == 0:
                    date_label = f"🚨 오늘 ({expiry_date.strftime('%m/%d %a')})"
                    date_color = "#FFCDD2"  # 빨강
                elif days_left <= 3:
                    date_label = f"⚠️ D-{days_left} ({expiry_date.strftime('%m/%d %a')})"
                    date_color = "#FFE082"  # 노랑
                else:
                    date_label = f"📌 D-{days_left} ({expiry_date.strftime('%m/%d %a')})"
                    date_color = "#E3F2FD"  # 파랑

                with st.expander(f"{date_label} - {len(foods)}개", expanded=(days_left <= 14)):
                    for food in foods:
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            category_icon = CATEGORY_ICONS.get(food.category, "📦")
                            location_icon = LOCATION_ICONS.get(food.location, "📦")
                            st.write(f"{category_icon} **{food.name}** {location_icon}")
                        with col2:
                            st.write(f"{food.quantity} {food.unit}")
                        with col3:
                            st.write(f"{food.category}")
        else:
            st.info("📌 향후 1개월 내 만료 예정인 음식이 없습니다.")

        # 구글 캘린더 동기화 버튼 (credentials.json이 있을 때만 표시)
        if os.path.exists('credentials.json'):
            st.markdown("---")
            col_sync1, col_sync2, col_sync3 = st.columns([1, 1, 1])

            with col_sync1:
                if st.button("📅 구글 캘린더 동기화", type="primary", use_container_width=True):
                    with st.spinner("구글 캘린더에 동기화하는 중..."):
                        try:
                            calendar = GoogleCalendarIntegration()

                            # 향후 30일 내 만료 예정 음식만 동기화
                            foods_to_sync = [food for food in all_foods
                                           if food.expiry_date >= date.today()
                                           and food.expiry_date <= date.today() + timedelta(days=30)]

                            if foods_to_sync:
                                success_count, fail_count = calendar.sync_food_items(foods_to_sync)
                                if success_count > 0:
                                    st.success(f"✅ {success_count}개 음식을 구글 캘린더에 추가했습니다!")
                                if fail_count > 0:
                                    st.warning(f"⚠️ {fail_count}개 음식 동기화 실패")
                            else:
                                st.info("동기화할 음식이 없습니다.")
                        except Exception as e:
                            st.error(f"동기화 오류: {str(e)}")

            with col_sync2:
                if st.button("🗑️ 캘린더 이벤트 삭제", use_container_width=True):
                    with st.spinner("구글 캘린더에서 냉요 이벤트를 삭제하는 중..."):
                        try:
                            calendar = GoogleCalendarIntegration()
                            deleted_count = calendar.delete_expiry_events()
                            if deleted_count > 0:
                                st.success(f"✅ {deleted_count}개 이벤트를 삭제했습니다!")
                            else:
                                st.info("삭제할 이벤트가 없습니다.")
                        except Exception as e:
                            st.error(f"삭제 오류: {str(e)}")

            with col_sync3:
                st.info("💡 첫 사용 시 구글 계정 로그인이 필요합니다")

    # 보관 위치별 통계 (클릭 가능)
    if all_foods:
        st.subheader("📍 보관 위치별 현황 (클릭하여 상세보기)")
        location_data = {}
        for food in all_foods:
            location_data[food.location] = location_data.get(food.location, 0) + 1

        col_loc1, col_loc2, col_loc3, col_loc4 = st.columns(4)

        with col_loc1:
            count = location_data.get("냉장", 0)
            if st.button(f"{LOCATION_ICONS['냉장']} 냉장\n{count}개", key="filter_냉장", use_container_width=True):
                st.session_state.dashboard_filter = "냉장"

        with col_loc2:
            count = location_data.get("냉동", 0)
            if st.button(f"{LOCATION_ICONS['냉동']} 냉동\n{count}개", key="filter_냉동", use_container_width=True):
                st.session_state.dashboard_filter = "냉동"

        with col_loc3:
            count = location_data.get("실온", 0)
            if st.button(f"{LOCATION_ICONS['실온']} 실온\n{count}개", key="filter_실온", use_container_width=True):
                st.session_state.dashboard_filter = "실온"

        with col_loc4:
            if st.button("🔄 전체보기", key="filter_all", use_container_width=True):
                st.session_state.dashboard_filter = None

        # 필터링된 음식 목록 표시
        if st.session_state.dashboard_filter:
            filtered_foods = [f for f in all_foods if f.location == st.session_state.dashboard_filter]
            location_icon = LOCATION_ICONS.get(st.session_state.dashboard_filter, "📦")

            st.subheader(f"{location_icon} {st.session_state.dashboard_filter} 음식 목록 ({len(filtered_foods)}개)")

            if filtered_foods:
                for food in filtered_foods[:10]:  # 최대 10개만 표시
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"{STATUS_COLORS[food.status()]} **{food.name}**")
                    with col2:
                        days = food.days_until_expiry()
                        if days >= 0:
                            st.write(f"D-{days}")
                        else:
                            st.write(f"{abs(days)}일 전 만료")
                    with col3:
                        st.write(f"{food.quantity} {food.unit}")

                if len(filtered_foods) > 10:
                    st.info(f"💡 {len(filtered_foods) - 10}개 더 있습니다. '음식 목록'에서 전체를 확인하세요.")
            else:
                st.info(f"{st.session_state.dashboard_filter}에 보관된 음식이 없습니다.")

    # 임박한 음식
    if expiring_soon:
        st.subheader("⚠️ 곧 만료되는 음식")
        for food in expiring_soon:
            days = food.days_until_expiry()
            location_icon = LOCATION_ICONS.get(food.location, "📦")
            st.warning(f"{STATUS_COLORS[food.status()]} {location_icon} **{food.name}** ({food.location}) - {days}일 남음 (만료일: {food.expiry_date})")

    # 만료된 음식
    if expired:
        st.subheader("🗑️ 만료된 음식")
        for food in expired:
            days = abs(food.days_until_expiry())
            location_icon = LOCATION_ICONS.get(food.location, "📦")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.error(f"{STATUS_COLORS[food.status()]} {location_icon} **{food.name}** ({food.location}) - {days}일 전 만료")
            with col2:
                if st.button("삭제", key=f"del_{food.id}"):
                    db.delete_food(food.id)
                    st.rerun()

    # 카테고리별 분포
    if all_foods:
        st.subheader("📈 카테고리별 분포")
        category_data = {}
        for food in all_foods:
            category_data[food.category] = category_data.get(food.category, 0) + 1

        # 카테고리별 카드 형식으로 표시
        cols = st.columns(4)
        for idx, (category, count) in enumerate(sorted(category_data.items(), key=lambda x: x[1], reverse=True)):
            with cols[idx % 4]:
                icon = CATEGORY_ICONS.get(category, "📦")
                color = CATEGORY_COLORS.get(category, "#E0E0E0")
                st.markdown(f"""
                    <div style="background-color: {color}; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
                        <div style="font-size: 32px;">{icon}</div>
                        <div style="font-size: 14px; font-weight: bold;">{category}</div>
                        <div style="font-size: 24px; font-weight: bold; color: #333;">{count}개</div>
                    </div>
                """, unsafe_allow_html=True)

        df = pd.DataFrame(list(category_data.items()), columns=['카테고리', '개수'])
        st.bar_chart(df.set_index('카테고리'))


def show_add_food():
    """음식 추가 화면"""
    st.header("➕ 음식 추가")

    # 탭 진입 시 이전 완료 상태 초기화
    if 'food_added_flag' not in st.session_state:
        st.session_state.food_added_flag = False

    if st.session_state.food_added_flag:
        # 음식 추가 후 다른 탭 갔다가 돌아온 경우 초기화
        st.session_state.ai_result = None
        st.session_state.estimated_shelf_life = None
        if 'uploader_key' in st.session_state:
            st.session_state.uploader_key += 1
        st.session_state.food_added_flag = False

    # AI 이미지 인식 섹션
    st.subheader("📸 사진으로 빠르게 추가")
    st.caption("💡 여러 장 업로드 가능 (앞면, 뒷면 등)")

    # 파일 업로더 키 초기화 (음식 추가 후 리셋용)
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0

    # 폼 키 초기화 (음식 추가 후 폼 리셋용)
    if 'form_key' not in st.session_state:
        st.session_state.form_key = 0

    uploaded_files = st.file_uploader(
        "음식 사진을 업로드하세요 (AI가 자동으로 인식합니다)",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="여러 장의 사진을 업로드할 수 있습니다 (예: 앞면, 뒷면)",
        key=f"uploader_{st.session_state.uploader_key}"
    )

    # 세션 스테이트 초기화
    if 'ai_result' not in st.session_state:
        st.session_state.ai_result = None

    if uploaded_files:
        # 업로드된 이미지 미리보기
        cols = st.columns(min(len(uploaded_files), 4))
        fixed_images = []

        for idx, uploaded_file in enumerate(uploaded_files):
            # 이미지 방향 수정
            image_bytes = uploaded_file.read()
            fixed_image_bytes = fix_image_orientation(image_bytes)
            fixed_images.append((fixed_image_bytes, uploaded_file))

            with cols[idx % 4]:
                st.image(fixed_image_bytes, caption=f"사진 {idx+1}", use_column_width=True)

        if st.button("🤖 AI로 분석하기", type="primary"):
            with st.spinner("AI가 이미지를 분석하고 있습니다..."):
                try:
                    # API 키 확인
                    api_key = os.getenv('OPENAI_API_KEY')
                    if not api_key:
                        st.error("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
                    else:
                        agent = FoodRecognitionAgent(api_key=api_key)

                        # 첫 번째 이미지로 기본 분석
                        first_image_bytes, first_file = fixed_images[0]
                        image_base64 = base64.b64encode(first_image_bytes).decode('utf-8')
                        image_type = f"image/{first_file.type.split('/')[-1]}"

                        # AI 분석
                        result = agent.analyze_food_image(image_base64, image_type)

                        # 여러 이미지가 있으면 추가 분석 (날짜 정보 등)
                        if len(fixed_images) > 1:
                            st.info(f"📸 {len(fixed_images)}장의 사진을 분석했습니다.")
                            for idx, (img_bytes, img_file) in enumerate(fixed_images[1:], start=2):
                                try:
                                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                                    img_type = f"image/{img_file.type.split('/')[-1]}"
                                    extra_result = agent.analyze_food_image(img_base64, img_type)

                                    # 추가 이미지에서 날짜 정보가 있으면 업데이트
                                    if extra_result.get('detected_date') and not result.get('detected_date'):
                                        result['detected_date'] = extra_result['detected_date']
                                        result['estimated_shelf_life_days'] = extra_result['estimated_shelf_life_days']
                                        st.success(f"✅ 사진 {idx}에서 날짜 정보를 발견했습니다!")
                                except:
                                    continue

                        # 결과 저장
                        st.session_state.ai_result = result

                        # 분석 결과 표시
                        if result['confidence'] > 50:
                            st.success(f"✅ **{result['name']}** 인식 완료! (신뢰도: {result['confidence']}%)")
                            st.info(f"📦 카테고리: {result['category']}\n"
                                   f"🏠 보관위치: {result['location']}\n"
                                   f"🔢 수량: {result.get('quantity', 1)}개\n"
                                   f"📅 예상 소비기한: {result['estimated_shelf_life_days']}일")
                        else:
                            st.warning(f"⚠️ 음식을 명확하게 인식하지 못했습니다. (신뢰도: {result['confidence']}%)\n"
                                      "수동으로 입력해주세요.")

                except Exception as e:
                    st.error(f"❌ 이미지 분석 중 오류가 발생했습니다: {str(e)}")
                    st.info("💡 API 키가 올바른지, 인터넷 연결이 되어있는지 확인해주세요.")

    st.divider()

    # 소비기한 자동 추천 섹션
    with st.expander("🔍 소비기한 모를 때? AI가 자동으로 추천해드립니다!", expanded=False):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            search_name = st.text_input("음식 이름", placeholder="예: 토마토, 두부")
        with col_b:
            search_category = st.selectbox("카테고리", CATEGORIES, key="search_category")
        with col_c:
            search_location = st.selectbox("보관 위치", LOCATIONS, key="search_location")

        if st.button("🤖 소비기한 자동 추천 받기", type="primary", use_container_width=True):
            if not search_name:
                st.warning("음식 이름을 입력해주세요.")
            else:
                with st.spinner("AI가 소비기한을 검색하고 있습니다..."):
                    try:
                        api_key = os.getenv('OPENAI_API_KEY')
                        if not api_key:
                            st.error("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
                        else:
                            agent = FoodRecognitionAgent(api_key=api_key)
                            result = agent.estimate_shelf_life(search_name, search_category, search_location)

                            # 결과 저장 (음식 정보도 함께 저장)
                            st.session_state.estimated_shelf_life = result
                            st.session_state.estimated_food_name = search_name
                            st.session_state.estimated_food_category = search_category
                            st.session_state.estimated_food_location = search_location

                            # 결과 표시
                            st.success(f"✅ **{search_name}** 소비기한 정보를 찾았습니다!")

                            col_r1, col_r2 = st.columns(2)
                            with col_r1:
                                st.metric("추천 보관 기간", f"{result['estimated_days']}일")
                                st.caption(f"최소 {result['min_days']}일 ~ 최대 {result['max_days']}일")
                            with col_r2:
                                st.info(f"💡 **보관 팁**\n\n{result['tips']}")

                            st.info("👇 아래 폼에 자동으로 적용되었습니다. 확인 후 '추가하기'를 눌러주세요!")

                    except Exception as e:
                        st.error(f"❌ 소비기한 추정 중 오류가 발생했습니다: {str(e)}")

    st.subheader("📝 음식 정보 입력")

    # 성공 메시지 표시 (폼 바로 위에 표시)
    if 'success_message' in st.session_state and st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.toast(st.session_state.success_message, icon="✅")
        st.balloons()
        del st.session_state.success_message

    # AI 결과가 있으면 자동으로 폼에 입력
    ai_result = st.session_state.ai_result

    # 이미지 분석 결과가 있으면 우선 사용
    if ai_result and ai_result['confidence'] > 50:
        default_name = ai_result['name']
        default_category_idx = CATEGORIES.index(ai_result['category']) if ai_result['category'] in CATEGORIES else 0
        default_location_idx = LOCATIONS.index(ai_result['location']) if ai_result['location'] in LOCATIONS else 0
        default_expiry_days = ai_result['estimated_shelf_life_days']
        default_quantity = float(ai_result.get('quantity', 1.0))
    # 소비기한 추정 결과가 있으면 사용
    elif 'estimated_food_name' in st.session_state and st.session_state.estimated_food_name:
        default_name = st.session_state.estimated_food_name
        default_category_idx = CATEGORIES.index(st.session_state.estimated_food_category) if st.session_state.estimated_food_category in CATEGORIES else 0
        default_location_idx = LOCATIONS.index(st.session_state.estimated_food_location) if st.session_state.estimated_food_location in LOCATIONS else 0
        default_expiry_days = st.session_state.estimated_shelf_life.get('estimated_days', 7) if st.session_state.estimated_shelf_life else 7
        default_quantity = 1.0
    else:
        default_name = ""
        default_category_idx = 0
        default_location_idx = 0
        default_expiry_days = 7
        default_quantity = 1.0

    # 세션 스테이트에 추천 소비기한 저장
    if 'estimated_shelf_life' not in st.session_state:
        st.session_state.estimated_shelf_life = None

    with st.form(key=f"add_food_form_{st.session_state.form_key}"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("음식 이름 *", value=default_name, placeholder="예: 우유, 사과, 닭고기")
            category = st.selectbox("카테고리 *", CATEGORIES, index=default_category_idx)
            location = st.selectbox("보관 위치 *", LOCATIONS, index=default_location_idx)

        with col2:
            purchase_date = st.date_input("구매일 *", value=date.today(), key="purchase_date_input")

            # 추천된 소비기한이 있으면 사용
            if st.session_state.estimated_shelf_life:
                expiry_days = st.session_state.estimated_shelf_life.get('estimated_days', default_expiry_days)
            else:
                expiry_days = default_expiry_days

            # 구매일 기준으로 소비기한 계산 (구매일이 변경되면 자동 반영)
            expiry_date = st.date_input(
                "소비기한 *",
                value=purchase_date + timedelta(days=expiry_days),
                help=f"구매일로부터 {expiry_days}일 후"
            )

            col2_1, col2_2 = st.columns(2)
            with col2_1:
                quantity = st.number_input("수량", min_value=1, value=int(default_quantity) if default_quantity >= 1 else 1, step=1)
            with col2_2:
                unit = st.selectbox("단위", UNITS)

        memo = st.text_area("메모", placeholder="추가 정보를 입력하세요 (선택)")

        submitted = st.form_submit_button("추가하기", use_container_width=True)

        if submitted:
            if not name:
                st.error("음식 이름을 입력해주세요.")
            elif expiry_date < purchase_date:
                st.error("소비기한은 구매일보다 이후여야 합니다.")
            else:
                db.add_food(
                    name=name,
                    category=category,
                    purchase_date=purchase_date,
                    expiry_date=expiry_date,
                    location=location,
                    quantity=quantity,
                    unit=unit,
                    memo=memo
                )
                # AI 결과 및 추정 소비기한 초기화 (페이지 전체 리셋)
                st.session_state.ai_result = None
                st.session_state.estimated_shelf_life = None
                st.session_state.estimated_food_name = None
                st.session_state.estimated_food_category = None
                st.session_state.estimated_food_location = None

                # 파일 업로더 키 변경 (파일 업로더 리셋)
                st.session_state.uploader_key += 1

                # 폼 키 변경 (폼 완전 리셋)
                st.session_state.form_key += 1

                # 음식 추가 완료 플래그 설정 (다른 탭 갔다가 돌아오면 초기화)
                st.session_state.food_added_flag = True

                # 성공 메시지 저장 (rerun 후 표시됨: 상단 메시지 + 팝업 + 풍선)
                st.session_state.success_message = f"✅ '{name}' 추가 완료!"

                # 페이지 새로고침 (입력 폼 초기화)
                st.rerun()


def show_food_list():
    """음식 목록 화면"""
    st.header("📝 음식 목록")

    # 편집 중인 음식 ID 세션 스테이트
    if 'editing_food_id' not in st.session_state:
        st.session_state.editing_food_id = None

    # 필터
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_category = st.selectbox("카테고리 필터", ["전체"] + CATEGORIES)
    with col2:
        filter_location = st.selectbox("위치 필터", ["전체"] + LOCATIONS)
    with col3:
        filter_status = st.selectbox("상태 필터", ["전체", "신선", "임박", "만료"])

    # 음식 목록 조회
    foods = db.get_all_foods()

    # 필터 적용
    if filter_category != "전체":
        foods = [f for f in foods if f.category == filter_category]
    if filter_location != "전체":
        foods = [f for f in foods if f.location == filter_location]
    if filter_status != "전체":
        foods = [f for f in foods if f.status() == filter_status]

    if not foods:
        st.info("등록된 음식이 없습니다. '음식 추가' 메뉴에서 음식을 추가해보세요!")
        return

    st.write(f"총 {len(foods)}개의 음식")

    # 테이블로 표시
    for food in foods:
        location_icon = LOCATION_ICONS.get(food.location, "📦")
        location_color = LOCATION_COLORS.get(food.location, "#FFFFFF")

        with st.container():
            # 배경색으로 보관 위치 구분
            st.markdown(f"""
            <div style="background-color: {location_color}; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])

            with col1:
                st.write(f"{STATUS_COLORS[food.status()]} {location_icon} **{food.name}**")
                st.caption(f"{food.category} | {food.location}")

            with col2:
                st.write(f"구매: {food.purchase_date}")

            with col3:
                st.write(f"만료: {food.expiry_date}")
                days = food.days_until_expiry()
                if days >= 0:
                    st.caption(f"D-{days}")
                else:
                    st.caption(f"{abs(days)}일 전 만료")

            with col4:
                st.write(f"{food.quantity} {food.unit}")

            with col5:
                col5_1, col5_2 = st.columns(2)
                with col5_1:
                    if st.button("✏️", key=f"edit_{food.id}", help="수정"):
                        st.session_state.editing_food_id = food.id
                        st.rerun()
                with col5_2:
                    if st.button("❌", key=f"delete_{food.id}", help="삭제"):
                        db.delete_food(food.id)
                        st.session_state.editing_food_id = None
                        st.rerun()

            if food.memo:
                st.caption(f"📝 {food.memo}")

            # 편집 폼 표시
            if st.session_state.editing_food_id == food.id:
                with st.expander("✏️ 수정하기", expanded=True):
                    with st.form(key=f"edit_form_{food.id}"):
                        edit_col1, edit_col2 = st.columns(2)

                        with edit_col1:
                            edit_name = st.text_input("음식 이름", value=food.name)
                            edit_category = st.selectbox("카테고리", CATEGORIES, index=CATEGORIES.index(food.category))
                            edit_location = st.selectbox("보관 위치", LOCATIONS, index=LOCATIONS.index(food.location))

                        with edit_col2:
                            edit_purchase_date = st.date_input("구매일", value=food.purchase_date)
                            edit_expiry_date = st.date_input("소비기한", value=food.expiry_date)

                            edit_col2_1, edit_col2_2 = st.columns(2)
                            with edit_col2_1:
                                edit_quantity = st.number_input("수량", min_value=1, value=int(food.quantity) if food.quantity >= 1 else 1, step=1)
                            with edit_col2_2:
                                edit_unit = st.selectbox("단위", UNITS, index=UNITS.index(food.unit) if food.unit in UNITS else 0)

                        edit_memo = st.text_area("메모", value=food.memo if food.memo else "")

                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 저장", use_container_width=True):
                                if not edit_name:
                                    st.error("음식 이름을 입력해주세요.")
                                elif edit_expiry_date < edit_purchase_date:
                                    st.error("소비기한은 구매일보다 이후여야 합니다.")
                                else:
                                    db.update_food(
                                        food.id,
                                        name=edit_name,
                                        category=edit_category,
                                        purchase_date=edit_purchase_date,
                                        expiry_date=edit_expiry_date,
                                        location=edit_location,
                                        quantity=edit_quantity,
                                        unit=edit_unit,
                                        memo=edit_memo if edit_memo else None
                                    )
                                    st.success(f"✅ '{edit_name}'이(가) 수정되었습니다!")
                                    st.session_state.editing_food_id = None
                                    st.rerun()
                        with col_cancel:
                            if st.form_submit_button("❌ 취소", use_container_width=True):
                                st.session_state.editing_food_id = None
                                st.rerun()

            st.divider()


def show_ai_recommendations():
    """AI 레시피 추천 화면"""
    st.header("🤖 AI 레시피 추천")

    foods = db.get_all_foods()

    if not foods:
        st.info("냉장고에 음식이 없습니다. 음식을 추가해주세요!")
        return

    st.subheader("냉장고에 있는 재료")

    # 재료 리스트
    ingredients = []
    expiring_ingredients = []

    for food in foods:
        if food.status() != "만료":
            ingredients.append(food.name)
            if food.status() == "임박":
                expiring_ingredients.append(food.name)

    if not ingredients:
        st.warning("신선한 재료가 없습니다.")
        return

    # 재료 표시
    col1, col2 = st.columns(2)
    with col1:
        st.write("**전체 재료:**")
        st.write(", ".join(ingredients))

    with col2:
        if expiring_ingredients:
            st.write("**🔴 임박 재료 (우선 사용):**")
            st.write(", ".join(expiring_ingredients))

    st.divider()

    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        st.warning("⚠️ OPENAI_API_KEY가 설정되지 않았습니다.")
        st.info("💡 .env 파일을 만들고 다음과 같이 설정하세요:\n```\nOPENAI_API_KEY=sk-proj-xxxxx\n```")
        return

    # 레시피 추천 버튼
    if st.button("🍳 AI 레시피 추천 받기", type="primary", use_container_width=True):
        with st.spinner("AI가 레시피를 추천하고 있습니다..."):
            try:
                agent = FoodRecognitionAgent(api_key=api_key)
                recipes = agent.get_recipe_suggestions(ingredients)

                st.subheader("📖 추천 레시피")

                # 레시피 표시
                st.markdown(recipes)

                # 복사 및 다운로드 버튼
                st.divider()
                col1, col2 = st.columns(2)

                with col1:
                    # 복사 버튼 (code 블록 사용)
                    with st.expander("📋 레시피 복사하기"):
                        st.code(recipes, language=None)

                with col2:
                    # 다운로드 버튼
                    from datetime import datetime
                    filename = f"레시피_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    st.download_button(
                        label="💾 레시피 다운로드",
                        data=recipes,
                        file_name=filename,
                        mime="text/plain",
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ 레시피 추천 중 오류가 발생했습니다: {str(e)}")
                st.info("💡 API 키가 올바른지 확인해주세요.")

    st.divider()

    # 대화형 AI 질문 섹션
    st.subheader("💬 AI에게 요리 질문하기")
    st.caption("아니면 직접 AI에게 요리 관련 질문을 해보세요!")

    # 채팅 히스토리 초기화
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []

    # 이전 대화 표시
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 채팅 입력
    if user_question := st.chat_input("예: 된장찌개 끓이는 법 알려줘", key="cooking_chat_input"):
        # 사용자 메시지 추가
        st.session_state.chat_messages.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)

        # AI 응답 생성
        with st.chat_message("assistant"):
            with st.spinner("AI가 답변을 생성하고 있습니다..."):
                try:
                    agent = FoodRecognitionAgent(api_key=api_key)
                    response = agent.ask_cooking_question(user_question, ingredients)
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"❌ 답변 생성 중 오류가 발생했습니다: {str(e)}"
                    st.error(error_msg)

    # 대화 내역 관리 버튼
    if st.session_state.chat_messages:
        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🗑️ 대화 내역 지우기", key="clear_chat", use_container_width=True):
                st.session_state.chat_messages = []
                st.rerun()

        with col2:
            # 전체 대화 내용 포맷팅
            conversation_text = ""
            for msg in st.session_state.chat_messages:
                role = "질문" if msg["role"] == "user" else "답변"
                conversation_text += f"[{role}]\n{msg['content']}\n\n"

            # 복사용 expander
            with st.expander("📋 대화 복사하기"):
                st.code(conversation_text, language=None)

        with col3:
            # 다운로드 버튼
            from datetime import datetime
            filename = f"요리대화_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            st.download_button(
                label="💾 대화 다운로드",
                data=conversation_text,
                file_name=filename,
                mime="text/plain",
                use_container_width=True
            )


if __name__ == "__main__":
    main()
