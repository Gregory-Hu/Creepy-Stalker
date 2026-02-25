"""
配置检查工具

检查 API Key 等配置是否正确
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config


def main():
    print("=" * 60)
    print("配置检查工具")
    print("=" * 60)
    
    config = get_config()
    
    print("\n配置状态:\n")
    
    # LLM 配置
    print("[LLM 配置]")
    if config.is_llm_configured:
        print(f"  [OK] API Key: {config.llm_api_key[:10]}...{config.llm_api_key[-4:]}")
    else:
        print(f"  [ERROR] API Key: 未配置或无效")
        print(f"     当前值：{config.llm_api_key}")
    
    print(f"  模型：{config.llm_model}")
    print(f"  端点：{config.llm_base_url}")
    
    # 目录配置
    print("\n[目录配置]")
    print(f"  工作目录：{config.workspace_dir}")
    print(f"  记忆存储：{config.memory_storage_path}")
    print(f"  报告目录：{config.reports_dir}")
    
    # 检查目录是否存在
    print("\n[目录检查]")
    for name, path in [
        ("工作目录", config.workspace_dir),
        ("记忆存储", config.memory_storage_path),
        ("报告目录", config.reports_dir),
    ]:
        if os.path.exists(path):
            print(f"  [OK] {name}: {path} (存在)")
        else:
            print(f"  [WARN] {name}: {path} (不存在，将自动创建)")
    
    # 创建目录
    for path in [config.workspace_dir, config.memory_storage_path, config.reports_dir]:
        os.makedirs(path, exist_ok=True)
    
    print("\n" + "=" * 60)
    
    if config.is_llm_configured:
        print("[OK] 配置完成！可以运行示例脚本。")
        print("\n运行测试:")
        print("  python examples\\deepseek_example.py")
    else:
        print("[ERROR] API Key 未配置!")
        print("\n请按以下步骤操作:")
        print("  1. 打开 .env 文件")
        print("  2. 找到 LLM_API_KEY=sk-")
        print("  3. 将 sk- 后面的内容替换为你的 DeepSeek API Key")
        print("  4. 重新运行此脚本")
        print("\n获取 API Key:")
        print("  https://platform.deepseek.com/")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
