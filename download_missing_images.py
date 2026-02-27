#!/usr/bin/env python3
"""
下載缺漏的圖片
"""

import os
import re
import json
import time
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

IMAGES_DIR = "pic.pimg.tw"
OUTPUT_DIR = "blogger_export"

def download_image(url, local_path):
    """下載單張圖片"""
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # 設定 headers 避免被擋
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        with urllib.request.urlopen(req, timeout=15) as response:
            with open(local_path, 'wb') as f:
                f.write(response.read())
        
        return True, url, None
    except Exception as e:
        return False, url, str(e)


def main():
    # 讀取文章清單
    with open(os.path.join(OUTPUT_DIR, 'posts.json'), 'r', encoding='utf-8') as f:
        posts = json.load(f)
    
    # 收集需要下載的圖片
    to_download = []
    already_have = 0
    
    for post in posts:
        for img in post.get('images', []):
            url = img['url']
            user = img['user']
            filename = img['filename']
            local_path = os.path.join(IMAGES_DIR, user, filename)
            
            if os.path.exists(local_path):
                already_have += 1
            else:
                to_download.append((url, local_path))
    
    # 去重
    to_download = list(set(to_download))
    
    print(f"已有: {already_have} 張")
    print(f"需下載: {len(to_download)} 張")
    
    if not to_download:
        print("無需下載")
        return
    
    print(f"\n開始下載...")
    
    success = 0
    failed = 0
    failed_list = []
    
    # 使用多執行緒下載
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(download_image, url, path): (url, path) 
                   for url, path in to_download}
        
        for i, future in enumerate(as_completed(futures), 1):
            ok, url, error = future.result()
            if ok:
                success += 1
                print(f"\r[{i}/{len(to_download)}] 成功: {success}, 失敗: {failed}", end='', flush=True)
            else:
                failed += 1
                failed_list.append((url, error))
                print(f"\r[{i}/{len(to_download)}] 成功: {success}, 失敗: {failed}", end='', flush=True)
            
            # 避免太快
            time.sleep(0.1)
    
    print(f"\n\n完成！")
    print(f"成功: {success}")
    print(f"失敗: {failed}")
    
    if failed_list:
        print(f"\n失敗清單（前 20 筆）:")
        for url, error in failed_list[:20]:
            print(f"  {url}: {error}")
        
        # 儲存失敗清單
        with open(os.path.join(OUTPUT_DIR, 'failed_images.txt'), 'w') as f:
            for url, error in failed_list:
                f.write(f"{url}\t{error}\n")


if __name__ == '__main__':
    main()
