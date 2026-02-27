# 摩卡卡部落格備份

Pixnet 部落格 `mocca7072.pixnet.net` 的完整備份與遷移工具。

## 備份內容

| 項目 | 數量 | 位置 |
|------|------|------|
| 文章 | 194 篇 | `mocca7072.pixnet.net/blog/posts/` |
| 圖片 | 1,252 張 | `pic.pimg.tw/` |
| Google Photos 備份 | 1,250 張 | 「摩卡卡部落格備份」相簿 |

## 檔案說明

```
mocca7072-blog-backup/
├── mocca7072.pixnet.net/    # 原始 HTML 備份
│   └── blog/posts/          # 194 篇文章
├── pic.pimg.tw/             # 圖片備份 (185 MB)
├── blogger_export/          # Blogger 匯入檔
│   ├── blogger_import.xml   # 匯入用 XML
│   ├── posts.json           # 文章清單
│   └── google_photos_mapping.json  # Google Photos 映射
├── venv/                    # Python 虛擬環境
├── credentials.json         # Google Cloud OAuth
├── token.pickle             # Google 認證 token
├── migrate_to_blogger.py    # 轉換工具
├── upload_to_google_photos.py  # Google Photos 上傳
├── download_missing_images.py  # 圖片下載
├── generate_blogger_import.py  # 生成匯入檔
└── emergency_imgur_migration.py  # 緊急 Imgur 遷移
```

## 匯入 Blogger

1. 前往 https://www.blogger.com
2. 建立新部落格
3. 設定 → 管理網誌 → 匯入內容
4. 選擇 `blogger_export/blogger_import.xml`

## 緊急備援（當 Pixnet 圖床掛掉）

```bash
# 1. 取得 Imgur API Client ID
#    https://api.imgur.com/oauth2/addclient

# 2. 設定環境變數
export IMGUR_CLIENT_ID=你的client_id

# 3. 執行遷移腳本
cd ~/Documents/workspace/mocca7072-blog-backup
source venv/bin/activate
python3 emergency_imgur_migration.py

# 4. 使用新的匯入檔
#    blogger_export/blogger_import_imgur.xml
```

## 備份時間

- 2026-02-26

## 備註

- 文章日期範圍：2008-06-17 ~ 2019-01-23
- 部分文章從 Wayback Machine 救回
- 4 篇文章因原始頁面已刪除無法恢復
