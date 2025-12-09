"""
Vision API 테스트 스크립트
"""
import os
from ai_agent import FoodRecognitionAgent
import sys

def test_vision(image_path):
    """이미지로 Vision API 테스트"""
    print(f"테스트 시작: {image_path}")

    # API 키 확인
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
        return False

    print(f"✓ API 키 확인: {api_key[:20]}...")

    try:
        # Agent 초기화
        agent = FoodRecognitionAgent(api_key=api_key)
        print("✓ Agent 초기화 완료")

        # 이미지 분석
        print("🤖 AI 분석 중...")
        result = agent.analyze_food_image(image_path)

        # 결과 출력
        print("\n" + "="*50)
        print("분석 결과:")
        print("="*50)
        print(f"음식 이름: {result['name']}")
        print(f"카테고리: {result['category']}")
        print(f"예상 소비기한: {result['estimated_shelf_life_days']}일")
        print(f"보관 위치: {result['location']}")
        print(f"신뢰도: {result['confidence']}%")
        print("="*50)

        if result['confidence'] > 50:
            print("\n✅ 성공! 음식을 정확하게 인식했습니다.")
            return True
        else:
            print("\n⚠️ 신뢰도가 낮습니다.")
            return False

    except Exception as e:
        print(f"\n❌ 에러 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # 현재 디렉토리에서 이미지 찾기
        import glob
        images = glob.glob("*.jpg") + glob.glob("*.jpeg") + glob.glob("*.png") + glob.glob("*.JPG")
        if images:
            image_path = images[0]
            print(f"발견한 이미지: {image_path}")
        else:
            print("사용법: python test_vision.py <image_path>")
            print("또는 현재 디렉토리에 이미지 파일(.jpg, .png)을 넣어주세요.")
            sys.exit(1)

    success = test_vision(image_path)
    sys.exit(0 if success else 1)
