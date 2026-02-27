#!/usr/bin/env python3
"""
緊急備援：將圖片上傳到 Imgur 並更新 Blogger
當 Pixnet 圖床掛掉時使用

使用前：
1. 前往 https://api.imgur.com/oauth2/addclient
2. 註冊應用程式（Application name 隨意，Authorization type 選 OAuth 2 without callback）
3. 取得 Client ID
4. 設定環境變數：export IMGUR_CLIENT_ID=你的client_id
"""

import os
import re
import json
import time
import base64
import requests
from concurrent.futures import ThreadPoolExecutor

# 設定
IMAGES_DIR = "pic.pimg.tw"
OUTPUT_DIR = "blogger_export"
MAPPING_FILE = os.path.join(OUTPUT_DIR, 'imgur_mapping.json')
POSTS_DIR = "mocca7072.pixnet.net/blog/posts"

IMGUR_API = "https://api.imgur.com/3/image"


def load_existing_mapping():
    """載入已上傳的映射（支援續傳）"""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_mapping(mapping):
    """儲存映射"""
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def upload_to_imgur(image_path, client_id):
    """上傳圖片到 Imgur"""
    try:
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        
        headers = {'Authorization': f'Client-ID {client_id}'}
        response = requests.post(
            IMGUR_API,
            headers=headers,
            data={'image': image_data, 'type': 'base64'},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data['data']['link']
    except Exception as e:
        print(f"\n    錯誤: {image_path} - {e}")
    
    return None


def collect_images():
    """收集所有圖片"""
    images = []
    for root, dirs, files in os.walk(IMAGES_DIR):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                path = os.path.join(root, f)
                # 建立原始 URL
                relative = path.replace(IMAGES_DIR + '/', '')
                original_url = f"https://pic.pimg.tw/{relative}"
                images.append((path, original_url))
    return images


def update_blogger_xml(url_mapping):
    """更新 Blogger 匯入檔中的圖片連結"""
    xml_file = os.path.join(OUTPUT_DIR, 'blogger_import.xml')
    xml_file_new = os.path.join(OUTPUT_DIR, 'blogger_import_imgur.xml')
    
    with open(xml_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    replaced = 0
    for original, imgur_url in url_mapping.items():
        # 替換 https 和 http 版本
        for prefix in ['https://', 'http://']:
            old_url = original.replace('https://', prefix)
            if old_url in content:
                content = content.replace(old_url, imgur_url)
                replaced += 1
    
    with open(xml_file_new, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return xml_file_new, replaced


def main():
    print("=" * 50)
    print("緊急備援：Imgur 圖片遷移")
    print("=" * 50)
    
    # 檢查 Client ID
    client_id = os.environ.get('IMGUR_CLIENT_ID')
    if not client_id:
        print("\n錯誤：請先設定 IMGUR_CLIENT_ID 環境變數")
        print("\n步驟：")
        print("1. 前往 https://api.imgur.com/oauth2/addclient")
        print("2. 註冊應用程式")
        print("3. export IMGUR_CLIENT_ID=你的client_id")
        print("4. 重新執行此腳本")
        return
    
    print(f"\n使用 Client ID: {client_id[:8]}...")
    
    # 載入已上傳的映射
    url_mapping = load_existing_mapping()
    print(f"已上傳: {len(url_mapping)} 張")
    
    # 收集圖片
    print("\n[1] 收集圖片...")
    all_images = collect_images()
    
    # 過濾已上傳的
    to_upload = [(path, url) for path, url in all_images if url not in url_mapping]
    print(f"    總計: {len(all_images)} 張")
    print(f"    待上傳: {len(to_upload)} 張")
    
    if not to_upload:
        print("\n全部已上傳！")
    else:
        # 上傳
        print("\n[2] 上傳到 Imgur...")
        success = 0
        failed = 0
        
        for i, (path, original_url) in enumerate(to_upload, 1):
            imgur_url = upload_to_imgur(path, client_id)
            
            if imgur_url:
                url_mapping[original_url] = imgur_url
                success += 1
            else:
                failed += 1
            
            # 每 10 張儲存一次進度
            if i % 10 == 0:
                save_mapping(url_mapping)
                print(f"\r    進度: {i}/{len(to_upload)} ({success} 成功, {failed} 失敗)", end='', flush=True)
            
            # Imgur 限流：每小時約 1250 張，保守一點
            time.sleep(0.5)
        
        save_mapping(url_mapping)
        print(f"\n    完成: {success} 成功, {failed} 失敗")
    
    # 更新 Blogger XML
    print("\n[3] 更新 Blogger 匯入檔...")
    new_xml, replaced = update_blogger_xml(url_mapping)
    print(f"    替換 {replaced} 個連結")
    print(f"    輸出: {new_xml}")
    
    print("\n" + "=" * 50)
    print("完成！")
    print(f"\n新的匯入檔: {new_xml}")
    print("可以匯入 Blogger 了")


if __name__ == '__main__':
    main()
