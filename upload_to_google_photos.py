#!/usr/bin/env python3
"""
上傳圖片到 Google Photos（支援續傳）
"""

import os
import json
import pickle
import mimetypes
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests

# 設定
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'
IMAGES_DIR = 'pic.pimg.tw'
OUTPUT_DIR = 'blogger_export'
ALBUM_NAME = '摩卡卡部落格備份'
MAPPING_FILE = os.path.join(OUTPUT_DIR, 'google_photos_mapping.json')
ALBUM_ID_FILE = os.path.join(OUTPUT_DIR, 'album_id.txt')

# Google Photos API 範圍
SCOPES = ['https://www.googleapis.com/auth/photoslibrary.appendonly']


def authenticate():
    """OAuth2 認證"""
    creds = None
    
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=8888)
        
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds


def load_mapping():
    """載入已上傳的映射"""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_mapping(mapping):
    """儲存映射"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def get_or_create_album(service):
    """取得或建立相簿"""
    # 檢查是否已有相簿 ID
    if os.path.exists(ALBUM_ID_FILE):
        with open(ALBUM_ID_FILE, 'r') as f:
            album_id = f.read().strip()
            if album_id:
                print(f"    使用現有相簿: {album_id}")
                return album_id
    
    # 建立新相簿
    try:
        album = service.albums().create(body={'album': {'title': ALBUM_NAME}}).execute()
        album_id = album['id']
        print(f"    建立相簿: {ALBUM_NAME}")
        
        with open(ALBUM_ID_FILE, 'w') as f:
            f.write(album_id)
        
        return album_id
    except Exception as e:
        print(f"    建立相簿失敗: {e}")
        return None


def upload_image(creds, image_path):
    """上傳單張圖片"""
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        mime_type = 'image/jpeg'
    
    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/octet-stream',
        'X-Goog-Upload-File-Name': os.path.basename(image_path),
        'X-Goog-Upload-Protocol': 'raw',
    }
    
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(
                'https://photoslibrary.googleapis.com/v1/uploads',
                headers=headers,
                data=f.read(),
                timeout=60
            )
        
        if response.status_code == 200:
            return response.text
    except Exception as e:
        pass
    
    return None


def add_to_album(service, album_id, upload_tokens, descriptions):
    """將圖片加入相簿"""
    media_items = []
    for token, desc in zip(upload_tokens, descriptions):
        media_items.append({
            'simpleMediaItem': {
                'uploadToken': token,
                'fileName': desc
            }
        })
    
    body = {
        'albumId': album_id,
        'newMediaItems': media_items
    }
    
    try:
        response = service.mediaItems().batchCreate(body=body).execute()
        return response.get('newMediaItemResults', [])
    except Exception as e:
        print(f"\n    批次建立失敗: {e}")
        return []


def main():
    print("=" * 50)
    print("Google Photos 上傳工具（支援續傳）")
    print("=" * 50)
    
    # 載入已上傳的映射
    url_mapping = load_mapping()
    uploaded_paths = set(url_mapping.keys())
    print(f"\n已上傳: {len(uploaded_paths)} 張")
    
    # 認證
    print("\n[1] OAuth 認證...")
    creds = authenticate()
    print("    認證成功！")
    
    # 建立 API 服務
    service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
    
    # 取得或建立相簿
    print("\n[2] 準備相簿...")
    album_id = get_or_create_album(service)
    if not album_id:
        return
    
    # 收集要上傳的圖片（跳過已上傳的）
    print("\n[3] 收集圖片...")
    images = []
    for root, dirs, files in os.walk(IMAGES_DIR):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                path = os.path.join(root, f)
                if path not in uploaded_paths:
                    images.append(path)
    
    print(f"    待上傳: {len(images)} 張")
    
    if not images:
        print("\n全部完成！無需上傳")
        return
    
    # 上傳圖片
    print("\n[4] 開始上傳...")
    batch_size = 20
    success = 0
    failed = 0
    
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]
        upload_tokens = []
        descriptions = []
        valid_paths = []
        
        for img_path in batch:
            token = upload_image(creds, img_path)
            if token:
                upload_tokens.append(token)
                descriptions.append(os.path.basename(img_path))
                valid_paths.append(img_path)
            else:
                failed += 1
        
        if upload_tokens:
            results = add_to_album(service, album_id, upload_tokens, descriptions)
            
            for path, result in zip(valid_paths, results):
                if 'mediaItem' in result:
                    media_item = result['mediaItem']
                    url_mapping[path] = {
                        'id': media_item['id'],
                        'productUrl': media_item.get('productUrl', ''),
                        'baseUrl': media_item.get('baseUrl', '')
                    }
                    success += 1
                else:
                    failed += 1
            
            # 每批次後儲存進度
            save_mapping(url_mapping)
        
        progress = min(i + batch_size, len(images))
        total = len(images) + len(uploaded_paths)
        done = len(uploaded_paths) + progress
        print(f"\r    進度: {done}/{total} ({success} 成功, {failed} 失敗)", end='', flush=True)
    
    print(f"\n\n[5] 完成！")
    print(f"    本次上傳: {success} 成功, {failed} 失敗")
    print(f"    總計: {len(url_mapping)} 張")
    print(f"    映射檔: {MAPPING_FILE}")


if __name__ == '__main__':
    main()
