"""
Schedule Parser Module
- Excel 파일 파싱
- 날짜별 스케줄 필터링
- 셀 데이터 추출
"""

import re
from pathlib import Path
from datetime import datetime, date
from typing import Optional, Union

import pandas as pd


class ScheduleParser:
    """Excel 스케줄 파서"""

    def __init__(self, data_dir: str = '/home/palantir/cow/schedule/data'):
        """
        Args:
            data_dir: xlsx 파일이 저장된 디렉토리
        """
        self.data_dir = Path(data_dir)

    def list_files(self) -> list[Path]:
        """데이터 디렉토리의 모든 xlsx 파일 목록"""
        if not self.data_dir.exists():
            return []
        return sorted(self.data_dir.glob('*.xlsx'))

    def read_excel(
        self,
        file_path: Union[str, Path],
        sheet_name: Optional[Union[str, int]] = None
    ) -> dict[str, pd.DataFrame]:
        """
        Excel 파일 읽기

        Args:
            file_path: xlsx 파일 경로
            sheet_name: 특정 시트만 읽을 경우 시트 이름 또는 인덱스

        Returns:
            {시트명: DataFrame} 딕셔너리
        """
        file_path = Path(file_path)

        if sheet_name is not None:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            return {str(sheet_name): df}

        # 모든 시트 읽기
        xlsx = pd.ExcelFile(file_path)
        return {
            sheet: pd.read_excel(xlsx, sheet_name=sheet)
            for sheet in xlsx.sheet_names
        }

    def find_date_column(self, df: pd.DataFrame) -> Optional[str]:
        """날짜 컬럼 자동 탐지"""
        date_patterns = ['날짜', 'date', 'Date', 'DATE', '일자', '일시']

        # 컬럼명에서 날짜 패턴 찾기
        for col in df.columns:
            col_str = str(col).lower()
            if any(p.lower() in col_str for p in date_patterns):
                return col

        # datetime 타입 컬럼 찾기
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                return col

        return None

    def parse_date(self, date_str: str) -> Optional[date]:
        """다양한 날짜 포맷 파싱"""
        date_str = str(date_str).strip()

        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%Y년 %m월 %d일',
            '%Y년%m월%d일',
            '%m/%d/%Y',
            '%d/%m/%Y',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # pandas Timestamp 처리
        try:
            ts = pd.Timestamp(date_str)
            if not pd.isna(ts):
                return ts.date()
        except:
            pass

        return None

    def filter_by_date(
        self,
        target_date: Union[str, date],
        columns: Optional[list[str]] = None
    ) -> pd.DataFrame:
        """
        특정 날짜의 스케줄만 필터링

        Args:
            target_date: 조회할 날짜 (YYYY-MM-DD 또는 date 객체)
            columns: 가져올 컬럼 목록 (None이면 전체)

        Returns:
            필터링된 DataFrame
        """
        if isinstance(target_date, str):
            target = self.parse_date(target_date)
            if target is None:
                raise ValueError(f"날짜 파싱 실패: {target_date}")
        else:
            target = target_date

        results = []

        for file_path in self.list_files():
            sheets = self.read_excel(file_path)

            for sheet_name, df in sheets.items():
                date_col = self.find_date_column(df)

                if date_col is None:
                    # 날짜 컬럼이 없으면 첫 번째 컬럼 시도
                    date_col = df.columns[0] if len(df.columns) > 0 else None

                if date_col is None:
                    continue

                # 날짜 필터링
                for idx, row in df.iterrows():
                    row_date = self.parse_date(row[date_col])
                    if row_date == target:
                        row_dict = row.to_dict()
                        row_dict['_source_file'] = file_path.name
                        row_dict['_source_sheet'] = sheet_name
                        results.append(row_dict)

        result_df = pd.DataFrame(results)

        # 특정 컬럼만 선택
        if columns and not result_df.empty:
            available_cols = [c for c in columns if c in result_df.columns]
            # 메타 컬럼 항상 포함
            available_cols.extend(['_source_file', '_source_sheet'])
            result_df = result_df[available_cols]

        return result_df

    def get_cell_value(
        self,
        file_name: str,
        sheet_name: Union[str, int],
        row: int,
        col: Union[int, str]
    ) -> any:
        """
        특정 셀의 값 가져오기

        Args:
            file_name: xlsx 파일명
            sheet_name: 시트 이름 또는 인덱스
            row: 행 번호 (0-indexed)
            col: 열 번호 (0-indexed) 또는 컬럼명

        Returns:
            셀 값
        """
        file_path = self.data_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없음: {file_name}")

        df = pd.read_excel(file_path, sheet_name=sheet_name)

        if isinstance(col, str):
            return df.loc[row, col]
        else:
            return df.iloc[row, col]

    def get_range(
        self,
        file_name: str,
        sheet_name: Union[str, int],
        start_row: int,
        end_row: int,
        start_col: Union[int, str],
        end_col: Union[int, str]
    ) -> pd.DataFrame:
        """
        셀 범위 가져오기 (Excel 범위 선택처럼)

        Args:
            file_name: xlsx 파일명
            sheet_name: 시트 이름
            start_row, end_row: 행 범위 (0-indexed, 포함)
            start_col, end_col: 열 범위

        Returns:
            선택된 범위의 DataFrame
        """
        file_path = self.data_dir / file_name
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        if isinstance(start_col, str) and isinstance(end_col, str):
            cols = list(df.columns)
            start_idx = cols.index(start_col)
            end_idx = cols.index(end_col) + 1
            return df.iloc[start_row:end_row + 1, start_idx:end_idx]
        else:
            return df.iloc[start_row:end_row + 1, start_col:end_col + 1]

    def summary(self) -> dict:
        """데이터 요약 정보"""
        files = self.list_files()
        summary = {
            'total_files': len(files),
            'files': []
        }

        for f in files:
            sheets = self.read_excel(f)
            file_info = {
                'name': f.name,
                'sheets': []
            }
            for sheet_name, df in sheets.items():
                file_info['sheets'].append({
                    'name': sheet_name,
                    'rows': len(df),
                    'columns': list(df.columns)
                })
            summary['files'].append(file_info)

        return summary


def format_schedule(df: pd.DataFrame, format_type: str = 'table') -> str:
    """
    스케줄 데이터 포맷팅

    Args:
        df: 스케줄 DataFrame
        format_type: 'table', 'markdown', 'json', 'simple'
    """
    if df.empty:
        return "조회 결과가 없습니다."

    if format_type == 'json':
        return df.to_json(orient='records', force_ascii=False, indent=2)

    elif format_type == 'markdown':
        return df.to_markdown(index=False)

    elif format_type == 'simple':
        lines = []
        for _, row in df.iterrows():
            line_parts = []
            for col, val in row.items():
                if not col.startswith('_'):  # 메타 컬럼 제외
                    line_parts.append(f"{col}: {val}")
            lines.append(' | '.join(line_parts))
        return '\n'.join(lines)

    else:  # table
        return df.to_string(index=False)


def main():
    """CLI 진입점"""
    import argparse

    parser = argparse.ArgumentParser(description='스케줄 조회 및 필터링')
    parser.add_argument('date', nargs='?',
                       help='조회할 날짜 (YYYY-MM-DD)')
    parser.add_argument('--data-dir', '-d',
                       default='/home/palantir/cow/schedule/data',
                       help='데이터 디렉토리')
    parser.add_argument('--columns', '-c', nargs='+',
                       help='가져올 컬럼 목록')
    parser.add_argument('--format', '-f',
                       choices=['table', 'markdown', 'json', 'simple'],
                       default='table',
                       help='출력 포맷')
    parser.add_argument('--summary', '-s', action='store_true',
                       help='데이터 요약 정보 출력')
    parser.add_argument('--cell',
                       help='특정 셀 조회 (파일명:시트:행:열)')

    args = parser.parse_args()

    schedule_parser = ScheduleParser(args.data_dir)

    if args.summary:
        import json
        summary = schedule_parser.summary()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.cell:
        # 형식: 파일명:시트:행:열
        parts = args.cell.split(':')
        if len(parts) != 4:
            print("셀 형식 오류. 예: file.xlsx:Sheet1:0:A")
            return
        file_name, sheet, row, col = parts
        try:
            row = int(row)
            col = int(col) if col.isdigit() else col
        except ValueError:
            pass
        value = schedule_parser.get_cell_value(file_name, sheet, row, col)
        print(f"셀 값: {value}")
        return

    if not args.date:
        # 날짜 미지정시 오늘 날짜
        args.date = date.today().isoformat()
        print(f"📅 날짜 미지정 - 오늘({args.date}) 스케줄 조회")

    df = schedule_parser.filter_by_date(args.date, args.columns)
    print(format_schedule(df, args.format))


if __name__ == '__main__':
    main()
