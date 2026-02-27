#!/usr/bin/env python3
"""生成乾淨的 HTML 版本"""
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup

blog_dir = Path("mocca7072.pixnet.net/blog/posts")
clean_dir = Path("clean")
clean_dir.mkdir(exist_ok=True)

# 建立文章列表
articles = []

for html_file in sorted(blog_dir.glob("*.html")):
    try:
        content = html_file.read_text(encoding='utf-8', errors='ignore')
        soup = BeautifulSoup(content, 'html.parser')
        
        # 提取標題
        title_tag = soup.find('title')
        title = title_tag.get_text() if title_tag else html_file.stem
        
        # 提取文章內容 - 找 article-content-inner
        article_div = soup.find('div', class_='article-content-inner')
        if not article_div:
            # 備用：找 article-content
            article_div = soup.find('div', class_='article-content')
        
        if not article_div:
            print(f"Skip (no content): {html_file.name}")
            continue
        
        # 提取日期（從檔名）
        match = re.match(r'(\d{4}-\d{2}-\d{2})', html_file.name)
        date = match.group(1) if match else ""
        
        # 修正圖片路徑
        article_html = str(article_div)
        # ../../../pic.pimg.tw/ -> ../pic.pimg.tw/
        article_html = article_html.replace('../../../pic.pimg.tw/', '../pic.pimg.tw/')
        
        # 生成乾淨 HTML
        clean_html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; line-height: 1.6; }}
        h1 {{ color: #333; }}
        .date {{ color: #666; margin-bottom: 20px; }}
        img {{ max-width: 100%; height: auto; }}
        a {{ color: #0066cc; }}
        .back {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p class="date">{date}</p>
    <div class="content">
        {article_html}
    </div>
    <div class="back"><a href="index.html">← 返回文章列表</a></div>
</body>
</html>'''
        
        # 儲存
        clean_file = clean_dir / html_file.name
        clean_file.write_text(clean_html, encoding='utf-8')
        articles.append((date, title, html_file.name))
        print(f"OK: {title[:30]}...")
        
    except Exception as e:
        print(f"Error: {html_file.name} - {e}")

# 生成首頁
articles.sort(reverse=True)  # 按日期排序
index_html = '''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>摩卡卡部落格備份</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        .subtitle { color: #666; margin-bottom: 30px; }
        ul { list-style: none; padding: 0; }
        li { padding: 10px 0; border-bottom: 1px solid #eee; }
        a { color: #0066cc; text-decoration: none; }
        a:hover { text-decoration: underline; }
        .date { color: #999; font-size: 14px; margin-right: 10px; }
    </style>
</head>
<body>
    <h1>🐕 摩卡卡部落格備份</h1>
    <p class="subtitle">遇見"小眼睛"柯基~摩卡卡 | 共 ''' + str(len(articles)) + ''' 篇文章</p>
    <ul>
'''
for date, title, filename in articles:
    index_html += f'        <li><span class="date">{date}</span><a href="{filename}">{title}</a></li>\n'

index_html += '''    </ul>
</body>
</html>'''

(clean_dir / "index.html").write_text(index_html, encoding='utf-8')
print(f"\n完成！共處理 {len(articles)} 篇文章")
print(f"首頁: clean/index.html")
