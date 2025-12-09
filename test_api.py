"""
간단한 API 테스트
"""
import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('ANTHROPIC_API_KEY')
print(f"API Key: {api_key[:20]}...")

client = Anthropic(api_key=api_key)

# 간단한 텍스트 메시지 테스트 (이미지 없이)
try:
    message = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=100,
        messages=[{"role": "user", "content": "Hello!"}]
    )
    print("\n✅ API 연결 성공!")
    print(f"응답: {message.content[0].text}")
except Exception as e:
    print(f"\n❌ API 연결 실패: {e}")
    print("\n다른 모델로 시도...")

    try:
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[{"role": "user", "content": "Hello!"}]
        )
        print("\n✅ claude-3-sonnet-20240229 작동!")
        print(f"응답: {message.content[0].text}")
    except Exception as e2:
        print(f"❌ 이것도 실패: {e2}")
