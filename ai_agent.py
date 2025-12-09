"""
AI 에이전트 - OpenAI GPT-4o Vision을 사용한 음식 인식
"""
import os
import base64
from datetime import date, timedelta
from openai import OpenAI
import json

class FoodRecognitionAgent:
    """음식 인식 AI 에이전트"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        self.client = OpenAI(api_key=self.api_key)

    def encode_image(self, image_path):
        """이미지를 base64로 인코딩"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def analyze_food_image(self, image_data, image_type="image/jpeg"):
        """
        이미지에서 음식 정보 추출

        Args:
            image_data: base64 인코딩된 이미지 데이터 또는 파일 경로
            image_type: 이미지 MIME 타입

        Returns:
            dict: 음식 정보 (name, category, estimated_shelf_life_days)
        """
        # 파일 경로인 경우 base64로 인코딩
        if isinstance(image_data, str) and os.path.exists(image_data):
            image_data = self.encode_image(image_data)

        # 오늘 날짜 가져오기
        today = date.today()
        today_str = f"{today.year}년 {today.month}월 {today.day}일"

        # 예시 날짜 계산 (오늘 기준)
        example_egg_date = date(today.year, 12, 1) if today.month <= 12 else date(today.year, today.month, 1)
        example_egg_expiry = example_egg_date + timedelta(days=40)
        example_days_left = (example_egg_expiry - today).days

        # 날짜 문자열 미리 포맷
        example_egg_date_str = f"{example_egg_date.year}-{example_egg_date.month:02d}-{example_egg_date.day:02d}"
        today_short = f"{today.month}/{today.day}"

        prompt = f"""이 이미지에 있는 음식을 분석해주세요.

**중요: 이미지에 날짜가 적혀있다면 반드시 OCR로 읽어서 실제 소비기한을 계산하세요!**

**계란(달걀) 특별 규칙:**
- 계란 껍질에 적힌 숫자는 **산란일자**(닭이 알을 낳은 날)입니다
- 냉장 보관 기준: 산란일자 + 40일 = 소비기한
- 예시: "1201" → 12월 1일 산란 → 냉장 보관 시 {example_egg_expiry.year}년 {example_egg_expiry.month}월 {example_egg_expiry.day}일 소비기한

날짜 형식 예시:
- 계란 껍질: "1201" = {example_egg_date.year}년 12월 1일 산란 → 냉장 보관 시 산란일 + 40일 = {example_egg_expiry.year}년 {example_egg_expiry.month}월 {example_egg_expiry.day}일 소비기한
- 우유팩: "2024.12.15" = 소비기한 12월 15일 (표기된 날짜가 소비기한)
- "25/12/20" = 2025년 12월 20일
- "2025.12.20" = 2025년 12월 20일

오늘 날짜: {today_str}

다음 정보를 JSON 형식으로 정확하게 반환해주세요:
{{
    "name": "음식 이름 (한글, 구체적으로)",
    "category": "카테고리 (채소/과일/육류/해산물/계란/두부/유제품/쌀/잡곡/조미료/소스/반찬/김치/즉석식품/밀키트/빵/디저트/음료/기타 중 가장 적합한 것)",
    "estimated_shelf_life_days": 소비기한까지 남은 일수 (오늘 기준, 숫자만),
    "location": "보관 위치 (냉장/냉동/실온 중 하나)",
    "quantity": 이미지에 보이는 개수 (숫자만, 정확히 세기),
    "confidence": "인식 신뢰도 (0-100 사이 숫자)",
    "detected_date": "이미지에서 읽은 날짜 (없으면 null)"
}}

예시:
- 계란 10개, "1201" 표시 → 12월 1일 산란 → 소비기한 {example_egg_expiry.year}년 {example_egg_expiry.month}월 {example_egg_expiry.day}일 → 오늘({today_short}) 기준 {example_days_left}일 남음
  {{"name": "달걀", "category": "계란", "estimated_shelf_life_days": {example_days_left}, "location": "냉장", "quantity": 10, "confidence": 95, "detected_date": "{example_egg_date_str}"}}
- 우유 1팩, "2024.12.15" → 소비기한 12월 15일 → 남은 일수 계산
  {{"name": "우유", "category": "유제품", "estimated_shelf_life_days": (계산된 일수), "location": "냉장", "quantity": 1, "confidence": 95, "detected_date": "2024-12-15"}}
- 사과 3개, 날짜 없음 → 일반적인 소비기한 추정
  {{"name": "사과", "category": "과일", "estimated_shelf_life_days": 14, "location": "냉장", "quantity": 3, "confidence": 90, "detected_date": null}}
- 김치 1팩 → 반찬 카테고리
  {{"name": "김치", "category": "반찬", "estimated_shelf_life_days": 30, "location": "냉장", "quantity": 1, "confidence": 95, "detected_date": null}}

같은 종류의 음식이 여러 개 있다면 개수를 정확히 세서 quantity에 입력해주세요.
음식이 아닌 것으로 판단되면 confidence를 0으로 설정하세요.

JSON만 반환하고 다른 설명은 추가하지 마세요."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{image_type};base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1024
            )

            # 응답에서 JSON 추출
            response_text = response.choices[0].message.content

            # JSON 파싱 시도
            try:
                # JSON 블록 찾기 (```json ... ``` 형식)
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response_text.strip()

                result = json.loads(json_str)

                # 필수 필드 검증
                required_fields = ["name", "category", "estimated_shelf_life_days", "location", "confidence"]
                for field in required_fields:
                    if field not in result:
                        raise ValueError(f"필수 필드 '{field}'가 없습니다.")

                # quantity가 없으면 기본값 1로 설정 (하위 호환성)
                if "quantity" not in result:
                    result["quantity"] = 1

                return result

            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"응답 텍스트: {response_text}")
                raise ValueError(f"AI 응답을 파싱할 수 없습니다: {response_text}")

        except Exception as e:
            print(f"이미지 분석 오류: {e}")
            raise

    def estimate_shelf_life(self, food_name, category="기타", storage_location="냉장"):
        """
        음식의 일반적인 소비기한 추정

        Args:
            food_name: 음식 이름
            category: 카테고리 (채소/육류/유제품/과일/조미료/음료/기타)
            storage_location: 보관 위치 (냉장/냉동/실온)

        Returns:
            dict: 추정 소비기한 정보
        """
        prompt = f"""음식 이름: {food_name}
카테고리: {category}
보관 위치: {storage_location}

위 음식의 일반적인 소비기한을 알려주세요.

다음 정보를 JSON 형식으로 반환해주세요:
{{
    "estimated_days": 예상 소비기한 일수 (숫자),
    "min_days": 최소 보관 가능 일수 (숫자),
    "max_days": 최대 보관 가능 일수 (숫자),
    "tips": "보관 팁 (한글, 1-2문장)"
}}

예시:
- 우유 (냉장): {{"estimated_days": 7, "min_days": 5, "max_days": 10, "tips": "개봉 후에는 3일 이내 섭취하세요."}}
- 사과 (냉장): {{"estimated_days": 21, "min_days": 14, "max_days": 30, "tips": "비닐봉지에 담아 냉장 보관하면 더 오래 유지됩니다."}}
- 달걀 (냉장): {{"estimated_days": 40, "min_days": 30, "max_days": 45, "tips": "산란일 기준 냉장 보관 시 40일 정도 보관 가능합니다."}}

JSON만 반환하고 다른 설명은 추가하지 마세요."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=512
            )

            response_text = response.choices[0].message.content

            # JSON 파싱
            try:
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response_text.strip()

                result = json.loads(json_str)
                return result

            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                print(f"응답 텍스트: {response_text}")
                return {
                    "estimated_days": 7,
                    "min_days": 5,
                    "max_days": 10,
                    "tips": "일반적인 보관 기간을 사용합니다."
                }

        except Exception as e:
            print(f"소비기한 추정 오류: {e}")
            return {
                "estimated_days": 7,
                "min_days": 5,
                "max_days": 10,
                "tips": "일반적인 보관 기간을 사용합니다."
            }

    def get_recipe_suggestions(self, ingredients):
        """
        냉장고 재료로 만들 수 있는 레시피 추천

        Args:
            ingredients: 재료 리스트 (음식 이름들)

        Returns:
            str: 레시피 추천 텍스트
        """
        if not ingredients:
            return "냉장고에 재료가 없습니다."

        prompt = f"""냉장고에 다음 재료들이 있습니다:
{', '.join(ingredients)}

이 재료들로 만들 수 있는 레시피 3가지를 추천해주세요. 각 레시피는:
1. 요리 이름
2. 필요한 주재료 (위 재료 중)
3. 간단한 조리 방법 (3-4단계)
4. 예상 조리 시간

소비기한이 임박한 재료를 우선적으로 사용하는 레시피를 추천해주세요."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=2048
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"레시피 추천 오류: {e}")
            return f"레시피 추천 중 오류가 발생했습니다: {str(e)}"
