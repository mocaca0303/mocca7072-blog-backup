#!/usr/bin/env python3
"""
生成 Blogger 匯入檔，並將圖片連結替換為 Google Photos
"""

import os
import re
import json
import html
from datetime import datetime
from bs4 import BeautifulSoup

# 設定
POSTS_DIR = "mocca7072.pixnet.net/blog/posts"
OUTPUT_DIR = "blogger_export"
MAPPING_FILE = os.path.join(OUTPUT_DIR, 'google_photos_mapping.json')


def load_image_mapping():
    """載入 Google Photos 映射"""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        # 建立 URL 到 Google Photos 的映射
        url_map = {}
        for local_path, info in mapping.items():
            # 從本地路徑提取原始 URL
            # pic.pimg.tw/mocca7072/xxx.jpg -> https://pic.pimg.tw/mocca7072/xxx.jpg
            if local_path.startswith('pic.pimg.tw/'):
                original_url = 'https://' + local_path
                # baseUrl 需要加上尺寸參數才能顯示
                if info.get('baseUrl'):
                    url_map[original_url] = info['baseUrl'] + '=w1024'
                    # 也加上 http 版本
                    url_map[original_url.replace('https://', 'http://')] = info['baseUrl'] + '=w1024'
        
        return url_map
    return {}


def parse_post(filepath, url_map):
    """解析文章並替換圖片連結"""
    filename = os.path.basename(filepath)
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # 解析檔名取得日期
    match = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)-(\d+)\.html$', filename)
    if not match:
        return None
    
    date_str = match.group(1)
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
    except:
        return None
    
    # 取得標題
    title_el = soup.find('title')
    if not title_el:
        return None
    
    title = title_el.text.strip()
    title = re.sub(r'\s*[@|:].*痞客邦.*$', '', title)
    title = re.sub(r'\s*::.*$', '', title)
    
    # 取得文章內容
    content_el = soup.select_one('.article-content')
    if not content_el:
        return None
    
    # 移除不需要的元素
    for tag in content_el.select('script, style, .ad, .advertisement, .sidebar'):
        tag.decompose()
    
    content_html = str(content_el)
    
    # 替換圖片連結
    replaced = 0
    for original_url, new_url in url_map.items():
        if original_url in content_html:
            content_html = content_html.replace(original_url, new_url)
            replaced += 1
        # 處理跳脫字元
        escaped_url = original_url.replace('/', '\\/')
        if escaped_url in content_html:
            content_html = content_html.replace(escaped_url, new_url.replace('/', '\\/'))
    
    return {
        'title': title,
        'date': date,
        'content': content_html,
        'filename': filename,
        'replaced_images': replaced
    }


def generate_blogger_xml(posts, output_file):
    """生成 Blogger Atom XML"""
    xml_parts = ['''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>摩卡卡部落格</title>
  <generator>Pixnet Migration Script</generator>
''']
    
    for post in posts:
        date_str = post['date'].strftime('%Y-%m-%dT12:00:00+08:00')
        title_escaped = html.escape(post['title'])
        content_escaped = html.escape(post['content'])
        
        entry = f'''  <entry>
    <title>{title_escaped}</title>
    <published>{date_str}</published>
    <updated>{date_str}</updated>
    <content type="html">{content_escaped}</content>
  </entry>
'''
        xml_parts.append(entry)
    
    xml_parts.append('</feed>')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(xml_parts))


def main():
    print("=" * 50)
    print("生成 Blogger 匯入檔")
    print("=" * 50)
    
    # 載入圖片映射
    print("\n[1] 載入 Google Photos 映射...")
    url_map = load_image_mapping()
    print(f"    載入 {len(url_map)} 個圖片映射")
    
    # 解析文章
    print("\n[2] 解析文章...")
    posts = []
    total_replaced = 0
    
    for f in sorted(os.listdir(POSTS_DIR)):
        if f.endswith('.html') and f[0].isdigit() and '-' in f:
            filepath = os.path.join(POSTS_DIR, f)
            post = parse_post(filepath, url_map)
            if post:
                posts.append(post)
                total_replaced += post['replaced_images']
    
    print(f"    解析 {len(posts)} 篇文章")
    print(f"    替換 {total_replaced} 個圖片連結")
    
    # 按日期排序
    posts.sort(key=lambda x: x['date'])
    
    # 生成 XML
    print("\n[3] 生成 Blogger XML...")
    xml_file = os.path.join(OUTPUT_DIR, 'blogger_import.xml')
    generate_blogger_xml(posts, xml_file)
    print(f"    輸出: {xml_file}")
    
    # 統計
    print("\n" + "=" * 50)
    print("完成！")
    print(f"\n文章數: {len(posts)}")
    print(f"日期範圍: {posts[0]['date'].strftime('%Y-%m-%d')} ~ {posts[-1]['date'].strftime('%Y-%m-%d')}")
    print(f"\n匯入檔: {xml_file}")
    print(f"檔案大小: {os.path.getsize(xml_file) / 1024 / 1024:.1f} MB")
    
    print("\n下一步:")
    print("1. 前往 Blogger.com 建立新部落格")
    print("2. 設定 → 其他 → 匯入內容")
    print("3. 選擇 blogger_import.xml")


if __name__ == '__main__':
    main()
