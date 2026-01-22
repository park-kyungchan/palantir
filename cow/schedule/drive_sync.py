"""
Google Drive Sync Module
- Service Account 기반 Google Drive 폴더 접근
- xlsx 파일 다운로드 및 동기화
"""

import os
import io
from pathlib import Path
from typing import Optional
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


class DriveSync:
    """Google Drive 동기화 클래스"""

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(
        self,
        credentials_path: str,
        folder_id: str,
        local_dir: str
    ):
        """
        Args:
            credentials_path: Service Account JSON 키 파일 경로
            folder_id: Google Drive 폴더 ID
            local_dir: 로컬 저장 디렉토리
        """
        self.credentials_path = Path(credentials_path)
        self.folder_id = folder_id
        self.local_dir = Path(local_dir)
        self.local_dir.mkdir(parents=True, exist_ok=True)

        self._service = None

    @property
    def service(self):
        """Google Drive API 서비스 (lazy initialization)"""
        if self._service is None:
            credentials = service_account.Credentials.from_service_account_file(
                str(self.credentials_path),
                scopes=self.SCOPES
            )
            self._service = build('drive', 'v3', credentials=credentials)
        return self._service

    def list_xlsx_files(self) -> list[dict]:
        """폴더 내 모든 xlsx 파일 목록 조회"""
        query = (
            f"'{self.folder_id}' in parents and "
            "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' and "
            "trashed=false"
        )

        results = self.service.files().list(
            q=query,
            fields="files(id, name, modifiedTime, size)",
            orderBy="modifiedTime desc"
        ).execute()

        return results.get('files', [])

    def download_file(self, file_id: str, file_name: str) -> Path:
        """단일 파일 다운로드"""
        request = self.service.files().get_media(fileId=file_id)

        local_path = self.local_dir / file_name

        with open(local_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print(f"  다운로드 진행: {int(status.progress() * 100)}%")

        return local_path

    def sync_all(self, force: bool = False) -> list[Path]:
        """
        모든 xlsx 파일 동기화

        Args:
            force: True면 모든 파일 재다운로드, False면 변경된 파일만

        Returns:
            다운로드된 파일 경로 리스트
        """
        files = self.list_xlsx_files()
        downloaded = []

        print(f"📁 발견된 xlsx 파일: {len(files)}개")

        for file_info in files:
            file_id = file_info['id']
            file_name = file_info['name']
            modified_time = file_info.get('modifiedTime', '')

            local_path = self.local_dir / file_name

            # 변경 여부 확인 (force가 아닌 경우)
            if not force and local_path.exists():
                # 메타데이터 파일에서 마지막 동기화 시간 확인
                meta_path = self.local_dir / '.sync_meta.txt'
                if meta_path.exists():
                    with open(meta_path) as f:
                        last_sync = f.read().strip()
                    if modified_time <= last_sync:
                        print(f"⏭️  {file_name} - 변경 없음, 스킵")
                        continue

            print(f"⬇️  다운로드: {file_name}")
            path = self.download_file(file_id, file_name)
            downloaded.append(path)

        # 동기화 시간 기록
        meta_path = self.local_dir / '.sync_meta.txt'
        with open(meta_path, 'w') as f:
            f.write(datetime.utcnow().isoformat())

        print(f"✅ 동기화 완료: {len(downloaded)}개 파일 다운로드됨")
        return downloaded


def main():
    """CLI 진입점"""
    import argparse

    parser = argparse.ArgumentParser(description='Google Drive xlsx 동기화')
    parser.add_argument('--credentials', '-c',
                       default='/home/palantir/kc-palantir-2aaee2ef708e.json',
                       help='Service Account JSON 경로')
    parser.add_argument('--folder-id', '-f',
                       default='1mEnWm8KEF9hntbNaFFSjWeP3chAJ9vsC',
                       help='Google Drive 폴더 ID')
    parser.add_argument('--local-dir', '-l',
                       default='/home/palantir/cow/schedule/data',
                       help='로컬 저장 디렉토리')
    parser.add_argument('--force', action='store_true',
                       help='모든 파일 강제 재다운로드')
    parser.add_argument('--list-only', action='store_true',
                       help='파일 목록만 출력')

    args = parser.parse_args()

    syncer = DriveSync(
        credentials_path=args.credentials,
        folder_id=args.folder_id,
        local_dir=args.local_dir
    )

    if args.list_only:
        files = syncer.list_xlsx_files()
        print(f"\n📋 xlsx 파일 목록 ({len(files)}개):")
        for f in files:
            print(f"  - {f['name']} (수정: {f['modifiedTime'][:10]})")
    else:
        syncer.sync_all(force=args.force)


if __name__ == '__main__':
    main()
