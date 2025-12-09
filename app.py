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
CATEGORIES = ["채소", "육류", "유제품", "과일", "조미료", "음료", "기타"]
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

    # 사이드바 스타일 및 동작 개선
    st.markdown("""
        <style>
        /* 사이드바 너비 축소 */
        [data-testid="stSidebar"] {
            min-width: 200px;
            max-width: 200px;
        }
        [data-testid="stSidebar"] > div:first-child {
            width: 200px;
        }
        </style>

        <script>
        // 라디오 버튼 클릭 시 사이드바 자동으로 접기
        const doc = window.parent.document;
        const radioButtons = doc.querySelectorAll('[data-testid="stSidebar"] input[type="radio"]');
        radioButtons.forEach(button => {
            button.addEventListener('click', () => {
                setTimeout(() => {
                    const closeButton = doc.querySelector('[data-testid="collapsedControl"]');
                    if (!closeButton) {
                        const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                        if (sidebar) {
                            const collapseBtn = sidebar.querySelector('button[kind="header"]');
                            if (collapseBtn) collapseBtn.click();
                        }
                    }
                }, 100);
            });
        });
        </script>
    """, unsafe_allow_html=True)

    # 사이드바 메뉴
    menu = st.sidebar.radio(
        "메뉴",
        ["📊 대시보드", "➕ 음식 추가", "📝 음식 목록", "🤖 AI 추천"]
    )

    if menu == "📊 대시보드":
        show_dashboard()
    elif menu == "➕ 음식 추가":
        show_add_food()
    elif menu == "📝 음식 목록":
        show_food_list()
    elif menu == "🤖 AI 추천":
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

        df = pd.DataFrame(list(category_data.items()), columns=['카테고리', '개수'])
        st.bar_chart(df.set_index('카테고리'))


def show_add_food():
    """음식 추가 화면"""
    st.header("➕ 음식 추가")

    # AI 이미지 인식 섹션
    st.subheader("📸 사진으로 빠르게 추가")

    uploaded_file = st.file_uploader(
        "음식 사진을 업로드하세요 (AI가 자동으로 인식합니다)",
        type=['jpg', 'jpeg', 'png'],
        help="음식 사진을 업로드하면 AI가 자동으로 음식 정보를 추출합니다."
    )

    # 세션 스테이트 초기화
    if 'ai_result' not in st.session_state:
        st.session_state.ai_result = None

    if uploaded_file is not None:
        col1, col2 = st.columns([1, 2])

        # 이미지 방향 수정
        image_bytes = uploaded_file.read()
        fixed_image_bytes = fix_image_orientation(image_bytes)

        with col1:
            st.image(fixed_image_bytes, caption="업로드된 이미지", use_column_width=True)

        with col2:
            if st.button("🤖 AI로 분석하기", type="primary"):
                with st.spinner("AI가 이미지를 분석하고 있습니다..."):
                    try:
                        # API 키 확인
                        api_key = os.getenv('OPENAI_API_KEY')
                        if not api_key:
                            st.error("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
                        else:
                            agent = FoodRecognitionAgent(api_key=api_key)

                            # 이미지를 base64로 인코딩 (방향 수정된 이미지 사용)
                            image_base64 = base64.b64encode(fixed_image_bytes).decode('utf-8')

                            # 이미지 타입 결정
                            image_type = f"image/{uploaded_file.type.split('/')[-1]}"

                            # AI 분석
                            result = agent.analyze_food_image(image_base64, image_type)

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

                            # 결과 저장
                            st.session_state.estimated_shelf_life = result

                            # 결과 표시
                            st.success(f"✅ **{search_name}** 소비기한 정보를 찾았습니다!")

                            col_r1, col_r2 = st.columns(2)
                            with col_r1:
                                st.metric("추천 보관 기간", f"{result['estimated_days']}일")
                                st.caption(f"최소 {result['min_days']}일 ~ 최대 {result['max_days']}일")
                            with col_r2:
                                st.info(f"💡 **보관 팁**\n\n{result['tips']}")

                            st.info("👇 아래 폼에 자동으로 적용됩니다. 음식 이름을 다시 입력하고 '추가하기'를 눌러주세요.")

                    except Exception as e:
                        st.error(f"❌ 소비기한 추정 중 오류가 발생했습니다: {str(e)}")

    st.subheader("📝 음식 정보 입력")

    # AI 결과가 있으면 자동으로 폼에 입력
    ai_result = st.session_state.ai_result
    default_name = ai_result['name'] if ai_result and ai_result['confidence'] > 50 else ""
    default_category_idx = CATEGORIES.index(ai_result['category']) if ai_result and ai_result['category'] in CATEGORIES else 0
    default_location_idx = LOCATIONS.index(ai_result['location']) if ai_result and ai_result['location'] in LOCATIONS else 0
    default_expiry_days = ai_result['estimated_shelf_life_days'] if ai_result else 7
    default_quantity = float(ai_result.get('quantity', 1.0)) if ai_result and ai_result['confidence'] > 50 else 1.0

    # 세션 스테이트에 추천 소비기한 저장
    if 'estimated_shelf_life' not in st.session_state:
        st.session_state.estimated_shelf_life = None

    with st.form("add_food_form"):
        col1, col2 = st.columns(2)

        with col1:
            name = st.text_input("음식 이름 *", value=default_name, placeholder="예: 우유, 사과, 닭고기")
            category = st.selectbox("카테고리 *", CATEGORIES, index=default_category_idx)
            location = st.selectbox("보관 위치 *", LOCATIONS, index=default_location_idx)

        with col2:
            purchase_date = st.date_input("구매일 *", value=date.today())

            # 추천된 소비기한이 있으면 사용
            if st.session_state.estimated_shelf_life:
                expiry_days = st.session_state.estimated_shelf_life.get('estimated_days', default_expiry_days)
            else:
                expiry_days = default_expiry_days

            expiry_date = st.date_input("소비기한 *", value=date.today() + timedelta(days=expiry_days))

            col2_1, col2_2 = st.columns(2)
            with col2_1:
                quantity = st.number_input("수량", min_value=0.1, value=default_quantity, step=0.1)
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
                st.success(f"✅ '{name}'이(가) 추가되었습니다!")
                st.balloons()

                # AI 결과 및 추정 소비기한 초기화
                st.session_state.ai_result = None
                st.session_state.estimated_shelf_life = None


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
                                edit_quantity = st.number_input("수량", min_value=0.1, value=float(food.quantity), step=0.1)
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
                st.markdown(recipes)

            except Exception as e:
                st.error(f"❌ 레시피 추천 중 오류가 발생했습니다: {str(e)}")
                st.info("💡 API 키가 올바른지 확인해주세요.")


if __name__ == "__main__":
    main()
