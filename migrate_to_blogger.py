#!/usr/bin/env python3
"""
Pixnet to Blogger Migration Script
將 Pixnet 部落格備份轉換為 Blogger 格式，並處理圖片
"""

import os
import re
import json
import html
from datetime import datetime
from bs4 import BeautifulSoup
from pathlib import Path

# 設定
POSTS_DIR = "mocca7072.pixnet.net/blog/posts"
IMAGES_DIR = "pic.pimg.tw"
OUTPUT_DIR = "blogger_export"

class BlogPost:
    def __init__(self, filepath):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.title = ""
        self.date = None
        self.content = ""
        self.images = []
        self.local_images = []
        self._parse()
    
    def _parse(self):
        """解析 HTML 檔案"""
        with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # 解析檔名取得日期
        match = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)-(\d+)\.html$', self.filename)
        if match:
            date_str, title_part, post_id = match.groups()
            self.date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # 取得標題
        title_el = soup.find('title')
        if title_el:
            self.title = title_el.text.strip()
            # 清理標題
            self.title = re.sub(r'\s*[@|:].*痞客邦.*$', '', self.title)
            self.title = re.sub(r'\s*::.*$', '', self.title)
        
        # 取得文章內容
        content_el = soup.select_one('.article-content')
        if content_el:
            # 移除不需要的元素
            for tag in content_el.select('script, style, .ad, .advertisement'):
                tag.decompose()
            
            self.content = str(content_el)
            
            # 找出所有圖片
            self._extract_images(content_el)
    
    def _extract_images(self, content_el):
        """提取並映射圖片"""
        # 找 HTML 中的圖片 URL
        img_pattern = r'https?://pic\.pimg\.tw/([^/]+)/([^"\'<>\s\\]+\.(jpg|jpeg|png|gif))'
        matches = re.findall(img_pattern, self.content, re.IGNORECASE)
        
        for user, filename, ext in matches:
            url = f"https://pic.pimg.tw/{user}/{filename}"
            local_path = os.path.join(IMAGES_DIR, user, filename)
            
            self.images.append({
                'url': url,
                'user': user,
                'filename': filename,
                'local_path': local_path if os.path.exists(local_path) else None
            })
    
    def to_dict(self):
        return {
            'title': self.title,
            'date': self.date.isoformat() if self.date else None,
            'content': self.content,
            'images': self.images,
            'filename': self.filename
        }


def scan_posts():
    """掃描所有文章"""
    posts = []
    for f in sorted(os.listdir(POSTS_DIR)):
        if f.endswith('.html') and not f.startswith('30'):  # 跳過未解析的
            filepath = os.path.join(POSTS_DIR, f)
            post = BlogPost(filepath)
            if post.title and post.date:
                posts.append(post)
    return posts


def generate_blogger_xml(posts, output_file):
    """生成 Blogger 匯入用的 XML (Atom 格式)"""
    xml_header = '''<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:blogger="http://schemas.google.com/blogger/2008">
  <title>摩卡卡部落格</title>
  <generator>Pixnet Migration Script</generator>
'''
    xml_footer = '</feed>'
    
    entries = []
    for post in posts:
        # 轉換日期格式
        date_str = post.date.strftime('%Y-%m-%dT%H:%M:%S+08:00')
        
        # 轉義內容
        content_escaped = html.escape(post.content)
        
        entry = f'''  <entry>
    <title>{html.escape(post.title)}</title>
    <published>{date_str}</published>
    <content type="html">{content_escaped}</content>
    <category scheme="http://schemas.google.com/g/2005#kind" term="http://schemas.google.com/blogger/2008/kind#post"/>
  </entry>
'''
        entries.append(entry)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml_header)
        f.writelines(entries)
        f.write(xml_footer)
    
    return len(entries)


def analyze_images(posts):
    """分析圖片狀況"""
    all_images = []
    local_count = 0
    missing_count = 0
    
    for post in posts:
        for img in post.images:
            all_images.append(img)
            if img['local_path']:
                local_count += 1
            else:
                missing_count += 1
    
    return {
        'total': len(all_images),
        'local': local_count,
        'missing': missing_count,
        'unique_users': len(set(img['user'] for img in all_images))
    }


def main():
    print("=" * 50)
    print("Pixnet → Blogger 轉換工具")
    print("=" * 50)
    
    # 建立輸出目錄
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 掃描文章
    print("\n[1] 掃描文章...")
    posts = scan_posts()
    print(f"    找到 {len(posts)} 篇文章")
    
    # 分析圖片
    print("\n[2] 分析圖片...")
    img_stats = analyze_images(posts)
    print(f"    圖片總數: {img_stats['total']}")
    print(f"    本地備份: {img_stats['local']}")
    print(f"    需要下載: {img_stats['missing']}")
    
    # 生成 Blogger XML
    print("\n[3] 生成 Blogger 匯入檔...")
    xml_file = os.path.join(OUTPUT_DIR, 'blogger_import.xml')
    count = generate_blogger_xml(posts, xml_file)
    print(f"    已生成: {xml_file}")
    print(f"    包含 {count} 篇文章")
    
    # 生成文章清單 JSON
    print("\n[4] 生成文章清單...")
    posts_json = os.path.join(OUTPUT_DIR, 'posts.json')
    with open(posts_json, 'w', encoding='utf-8') as f:
        json.dump([p.to_dict() for p in posts], f, ensure_ascii=False, indent=2)
    print(f"    已生成: {posts_json}")
    
    # 收集需要上傳的本地圖片
    print("\n[5] 收集本地圖片...")
    local_images = []
    for post in posts:
        for img in post.images:
            if img['local_path'] and os.path.exists(img['local_path']):
                local_images.append(img['local_path'])
    
    local_images = list(set(local_images))  # 去重
    images_list = os.path.join(OUTPUT_DIR, 'local_images.txt')
    with open(images_list, 'w') as f:
        f.write('\n'.join(local_images))
    print(f"    本地圖片: {len(local_images)} 張")
    print(f"    清單: {images_list}")
    
    print("\n" + "=" * 50)
    print("完成！")
    print("\n下一步:")
    print("1. 檢查 blogger_export/blogger_import.xml")
    print("2. 上傳圖片到 Google Photos 或其他圖床")
    print("3. 更新文章中的圖片連結")
    print("4. 匯入 Blogger")


if __name__ == '__main__':
    main()
