from __future__ import annotations
import csv
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from .source import DataSource

class CSVDataSource(DataSource):
    """Source for reading/writing CSV files."""
    
    def __init__(self, path: str):
        self.path = Path(path)

    @property
    def name(self) -> str:
        return f"CSV({self.path.name})"

    async def read(self, **kwargs) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
            
        # Using run_in_executor to avoid blocking the event loop with I/O
        return await asyncio.to_thread(self._read_sync)

    def _read_sync(self) -> List[Dict[str, Any]]:
        with open(self.path, mode='r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            return list(reader)

    async def write(self, data: List[Dict[str, Any]], **kwargs) -> None:
        if not data:
            return
        await asyncio.to_thread(self._write_sync, data)

    def _write_sync(self, data: List[Dict[str, Any]]):
        fieldnames = data[0].keys()
        with open(self.path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)


class JSONDataSource(DataSource):
    """Source for reading/writing JSON files."""
    
    def __init__(self, path: str):
        self.path = Path(path)

    @property
    def name(self) -> str:
        return f"JSON({self.path.name})"

    async def read(self, **kwargs) -> List[Dict[str, Any]]:
        if not self.path.exists():
            return []
        return await asyncio.to_thread(self._read_sync)

    def _read_sync(self) -> List[Dict[str, Any]]:
        with open(self.path, mode='r', encoding='utf-8') as f:
            return json.load(f)

    async def write(self, data: List[Dict[str, Any]], **kwargs) -> None:
        await asyncio.to_thread(self._write_sync, data)

    def _write_sync(self, data: List[Dict[str, Any]]):
        with open(self.path, mode='w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
