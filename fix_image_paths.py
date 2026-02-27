#!/usr/bin/env python3
"""把 HTML 裡的 Pixnet 圖片連結換成 GitHub Pages 相對路徑"""
import os
import re
from pathlib import Path

blog_dir = Path("mocca7072.pixnet.net/blog/posts")
count = 0

for html_file in blog_dir.glob("*.html"):
    content = html_file.read_text(encoding='utf-8', errors='ignore')
    
    # 把 https://pic.pimg.tw/ 換成相對路徑 ../../../pic.pimg.tw/
    new_content = re.sub(
        r'https?://pic\.pimg\.tw/',
        '../../../pic.pimg.tw/',
        content
    )
    
    if new_content != content:
        html_file.write_text(new_content, encoding='utf-8')
        count += 1
        print(f"Fixed: {html_file.name}")

print(f"\n共修改 {count} 個檔案")
