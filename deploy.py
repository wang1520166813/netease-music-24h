#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署脚本 - 将应用部署到 Hugging Face Space
"""

import os
import sys
from huggingface_hub import HfApi, login

def deploy_to_hf():
    """部署到 Hugging Face Space"""
    
    # 获取环境变量
    hf_token = os.getenv('HF_TOKEN')
    space_name = os.getenv('HF_SPACE_NAME')
    
    if not hf_token:
        print("❌ 错误：未找到 HF_TOKEN 环境变量")
        print("请在 GitHub Secrets 中设置 HF_TOKEN")
        sys.exit(1)
    
    if not space_name:
        print("❌ 错误：未找到 HF_SPACE_NAME 环境变量")
        print("请在 GitHub Secrets 中设置 HF_SPACE_NAME (格式：username/space-name)")
        sys.exit(1)
    
    try:
        # 登录 Hugging Face
        login(token=hf_token)
        
        # 初始化 API
        api = HfApi()
        
        # 上传文件到 Space
        print(f"🚀 开始部署到 Hugging Face Space: {space_name}")
        
        # 上传所有文件
        api.upload_folder(
            folder_path=".",
            repo_id=space_name,
            repo_type="space",
            ignore_patterns=[".git", ".github", "*.md"],
            token=hf_token
        )
        
        print(f"✅ 部署成功！")
        print(f"📍 访问地址：https://huggingface.co/spaces/{space_name}")
        
    except Exception as e:
        print(f"❌ 部署失败：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    deploy_to_hf()
