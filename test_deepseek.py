"""
测试 DeepSeek API 连接
"""
import httpx
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config

def test_api():
    config = get_config()
    
    print("=" * 60)
    print("DeepSeek API 连接测试")
    print("=" * 60)
    
    print(f"\n配置信息:")
    print(f"  API Key: {config.llm_api_key[:10]}...{config.llm_api_key[-4:]}")
    print(f"  模型：{config.llm_model}")
    print(f"  端点：{config.llm_base_url}")
    
    url = f"{config.llm_base_url}/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.llm_api_key}",
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": "Hello"},
        ],
        "temperature": 0.7,
        "max_tokens": 10,
    }
    
    print(f"\n发送测试请求...")
    print(f"  URL: {url}")
    
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        
        print(f"\n响应状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n[OK] API 调用成功!")
            content = data['choices'][0]['message']['content']
            # 替换 emoji 字符
            content = content.replace('\U0001f44b', '[emoji]')
            print(f"  返回内容：{content}")
            if 'usage' in data:
                print(f"  Token 使用：{data['usage']}")
        else:
            print(f"\n[ERROR] API 调用失败!")
            print(f"  错误信息：{response.text[:300]}")
            
            # 解析错误
            try:
                error_data = response.json()
                if 'error' in error_data:
                    print(f"  错误详情：{error_data['error']}")
            except:
                pass
    
    except Exception as e:
        print(f"\n[ERROR] 请求失败：{e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_api()
