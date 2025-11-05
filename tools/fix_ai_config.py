# -*- coding: utf-8 -*-

"""
修复 AI 助手配置文件中的空字符串
将空字符串替换为默认值
"""

import json
from pathlib import Path

# 配置文件路径
config_file = Path.home() / "AppData" / "Roaming" / "ue_toolkit" / "user_data" / "configs" / "ai_assistant" / "ai_assistant_config.json"

print(f"配置文件路径: {config_file}")
print(f"文件存在: {config_file.exists()}")

if not config_file.exists():
    print("配置文件不存在，无需修复")
    exit(0)

# 读取现有配置
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

print(f"\n修复前的配置:")
print(json.dumps(config, indent=2, ensure_ascii=False))

# 修复空字符串
fixed = False

# 修复 API 设置
if "api_settings" in config:
    if not config["api_settings"].get("api_url"):
        config["api_settings"]["api_url"] = "https://api.openai-hk.com/v1/chat/completions"
        print("修复: api_url")
        fixed = True
    
    if not config["api_settings"].get("api_key"):
        config["api_settings"]["api_key"] = "hk-rf256210000027899536cbcb497417e8dfc70c2960229c22"
        print("修复: api_key")
        fixed = True
    
    if not config["api_settings"].get("default_model"):
        config["api_settings"]["default_model"] = "gemini-2.5-flash"
        print("修复: default_model")
        fixed = True

# 修复 Ollama 设置
if "ollama_settings" in config:
    if not config["ollama_settings"].get("base_url"):
        config["ollama_settings"]["base_url"] = "http://localhost:11434"
        print("修复: base_url")
        fixed = True
    
    if not config["ollama_settings"].get("model_name"):
        config["ollama_settings"]["model_name"] = "llama3"
        print("修复: model_name")
        fixed = True

if fixed:
    # 备份原文件
    backup_file = config_file.with_suffix('.json.old')
    import shutil
    shutil.copy(config_file, backup_file)
    print(f"\n已备份原文件到: {backup_file}")
    
    # 保存修复后的配置
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n修复后的配置:")
    print(json.dumps(config, indent=2, ensure_ascii=False))
    print(f"\n✅ 配置已修复并保存！")
else:
    print("\n配置无需修复")

