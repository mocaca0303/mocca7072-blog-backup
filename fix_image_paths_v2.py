#!/usr/bin/env python3
"""把 HTML 裡所有 Pixnet 圖片連結換成相對路徑"""
import os
import re
from pathlib import Path

blog_dir = Path("mocca7072.pixnet.net/blog/posts")
count = 0

for html_file in blog_dir.glob("*.html"):
    content = html_file.read_text(encoding='utf-8', errors='ignore')
    original = content
    
    # 處理各種格式的 pic.pimg.tw 連結
    # 1. https://pic.pimg.tw/
    # 2. http://pic.pimg.tw/
    # 3. //pic.pimg.tw/
    content = re.sub(
        r'(https?:)?//pic\.pimg\.tw/',
        '../../../pic.pimg.tw/',
        content
    )
    
    if content != original:
        html_file.write_text(content, encoding='utf-8')
        count += 1

print(f"共修改 {count} 個檔案")

# 確認結果
import subprocess
result = subprocess.run(['grep', '-r', 'pic.pimg.tw', 'mocca7072.pixnet.net/blog/posts/'], capture_output=True, text=True)
remaining = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
print(f"剩餘連結數: {remaining}")
