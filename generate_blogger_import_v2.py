#!/usr/bin/env python3
"""
生成 Blogger 正確格式的匯入檔
"""

import os
import re
import html
from datetime import datetime
from bs4 import BeautifulSoup

POSTS_DIR = "mocca7072.pixnet.net/blog/posts"
OUTPUT_DIR = "blogger_export"
BLOG_ID = "mocca7072"


def parse_post(filepath):
    """解析文章"""
    filename = os.path.basename(filepath)
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    # 解析檔名取得日期
    match = re.match(r'^(\d{4}-\d{2}-\d{2})-(.+)-(\d+)\.html$', filename)
    if not match:
        return None
    
    date_str = match.group(1)
    post_id = match.group(3)
    
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
    content_el = soup.select_one('.article-content-inner')
    if not content_el:
        content_el = soup.select_one('.article-content')
    if not content_el:
        return None
    
    # 清理內容
    for tag in content_el.select('script, style, .ad, .advertisement, .sidebar, .tag-container, .author-profile'):
        tag.decompose()
    
    # 取得內部 HTML
    content_html = ''.join(str(child) for child in content_el.children)
    
    return {
        'title': title,
        'date': date,
        'content': content_html,
        'post_id': post_id
    }


def generate_blogger_xml(posts, output_file):
    """生成 Blogger 格式 XML"""
    
    # Blogger XML header
    xml = '''<?xml version='1.0' encoding='UTF-8'?>
<?xml-stylesheet href="http://www.blogger.com/styles/atom.css" type="text/css"?>
<feed xmlns='http://www.w3.org/2005/Atom' xmlns:openSearch='http://a9.com/-/spec/opensearchrss/1.0/' xmlns:blogger='http://schemas.google.com/blogger/2008' xmlns:georss='http://www.georss.org/georss' xmlns:gd='http://schemas.google.com/g/2005' xmlns:thr='http://purl.org/syndication/thread/1.0'>
  <id>tag:blogger.com,1999:blog-{blog_id}</id>
  <updated>{updated}</updated>
  <title type='text'>摩卡卡部落格</title>
  <link rel='http://schemas.google.com/g/2005#feed' type='application/atom+xml' href='http://www.blogger.com/feeds/{blog_id}/posts/default'/>
  <link rel='self' type='application/atom+xml' href='http://www.blogger.com/feeds/{blog_id}/posts/default'/>
  <link rel='alternate' type='text/html' href='http://{blog_id}.blogspot.com/'/>
  <author>
    <name>摩卡卡</name>
  </author>
  <generator version='7.00' uri='http://www.blogger.com'>Blogger</generator>
'''.format(
        blog_id=BLOG_ID,
        updated=datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
    )
    
    # Add entries
    for i, post in enumerate(posts):
        date_str = post['date'].strftime('%Y-%m-%dT12:00:00.000+08:00')
        title_escaped = html.escape(post['title'])
        content_escaped = html.escape(post['content'])
        post_id = f"{i+1}"
        
        entry = '''  <entry>
    <id>tag:blogger.com,1999:blog-{blog_id}.post-{post_id}</id>
    <published>{date}</published>
    <updated>{date}</updated>
    <category scheme='http://schemas.google.com/g/2005#kind' term='http://schemas.google.com/blogger/2008/kind#post'/>
    <title type='text'>{title}</title>
    <content type='html'>{content}</content>
    <author>
      <name>摩卡卡</name>
    </author>
  </entry>
'''.format(
            blog_id=BLOG_ID,
            post_id=post_id,
            date=date_str,
            title=title_escaped,
            content=content_escaped
        )
        xml += entry
    
    xml += '</feed>'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(xml)


def main():
    print("生成 Blogger 匯入檔 v2")
    print("=" * 40)
    
    # 解析文章
    print("\n[1] 解析文章...")
    posts = []
    
    for f in sorted(os.listdir(POSTS_DIR)):
        if f.endswith('.html') and f[0].isdigit() and '-' in f:
            filepath = os.path.join(POSTS_DIR, f)
            post = parse_post(filepath)
            if post:
                posts.append(post)
    
    print(f"    {len(posts)} 篇文章")
    
    # 按日期排序
    posts.sort(key=lambda x: x['date'])
    
    # 生成 XML
    print("\n[2] 生成 XML...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    xml_file = os.path.join(OUTPUT_DIR, 'blogger_import_v2.xml')
    generate_blogger_xml(posts, xml_file)
    
    size = os.path.getsize(xml_file) / 1024 / 1024
    print(f"    輸出: {xml_file}")
    print(f"    大小: {size:.1f} MB")
    
    print("\n完成！")


if __name__ == '__main__':
    main()
