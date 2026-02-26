import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SERVICE_ACCOUNT_FILE = 'service-account.json'
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_service():
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('drive', 'v3', credentials=creds)

def download_recursive(service, folder_id, current_local_path):
    # ローカルにディレクトリを作成
    if not os.path.exists(current_local_path):
        os.makedirs(current_local_path)
        print(f"Created directory: {current_local_path}")

    # フォルダ内のアイテム（ファイルとサブフォルダ）をリストアップ
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query, 
        fields="files(id, name, mimeType)"
    ).execute()
    items = results.get('files', [])

    for item in items:
        file_id = item['id']
        file_name = item['name']
        mime_type = item['mimeType']

        # 1. アイテムが「フォルダ」の場合：自分自身を再度呼び出す（再帰）
        if mime_type == 'application/vnd.google-apps.folder':
            new_path = os.path.join(current_local_path, file_name)
            download_recursive(service, file_id, new_path)
        
        # 2. アイテムが「ファイル」の場合：ダウンロード実行
        else:
            # Googleドキュメント形式などはスキップ（必要ならexport処理を追加）
            if 'application/vnd.google-apps' in mime_type:
                print(f"Skipping Google native file: {file_name}")
                continue

            file_path = os.path.join(current_local_path, file_name)
            print(f"Downloading: {file_path}...")

            request = service.files().get_media(fileId=file_id)
            with io.FileIO(file_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

if __name__ == '__main__':
    service = get_service()
    
    # 開始ポイントの設定
    START_FOLDER_ID = '1gdTk--Y1nwJeCTXl7WT5QKGeqx-f6K9C'
    BASE_DOWNLOAD_PATH = './downloads'
    
    download_recursive(service, START_FOLDER_ID, BASE_DOWNLOAD_PATH)
    print("Done!")
