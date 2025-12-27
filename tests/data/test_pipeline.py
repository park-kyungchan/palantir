import pytest
import csv
import json
from pathlib import Path
from scripts.data import DataPipeline, CSVDataSource, JSONDataSource

@pytest.fixture
def sample_csv(tmp_path):
    file = tmp_path / "input.csv"
    with open(file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "status"])
        writer.writeheader()
        writer.writerow({"id": "1", "status": "active"})
        writer.writerow({"id": "2", "status": "inactive"})
        writer.writerow({"id": "3", "status": "active"})
    return str(file)

@pytest.fixture
def output_json(tmp_path):
    return str(tmp_path / "output.json")

@pytest.mark.asyncio
async def test_csv_to_json_pipeline(sample_csv, output_json):
    """Test full ETL flow: CSV -> Transform -> JSON."""
    
    # Define Transform
    def only_active(data):
        return [d for d in data if d["status"] == "active"]
        
    pipeline = DataPipeline("test_pipe")
    pipeline.extract(CSVDataSource(sample_csv))
    pipeline.transform(only_active)
    pipeline.load(JSONDataSource(output_json))
    
    await pipeline.execute()
    
    # Verify Output
    with open(output_json, "r") as f:
        result = json.load(f)
        
    assert len(result) == 2
    assert result[0]["id"] == "1"
    assert result[1]["id"] == "3"

@pytest.mark.asyncio
async def test_empty_source(tmp_path):
    """Test handling of missing source file."""
    bad_csv = str(tmp_path / "nonexistent.csv")
    out_json = str(tmp_path / "out.json")
    
    pipeline = DataPipeline("empty_test") \
        .extract(CSVDataSource(bad_csv)) \
        .load(JSONDataSource(out_json))
        
    await pipeline.execute()
    
    # Should write empty array or nothing?
    # Implementation of JSONDataSource write uses 'w' mode, dumps data.
    # If read returns [], write gets [].
    
    pass # Currently implementation doesn't fail, just empty list.
    # Verify file content
    if Path(out_json).exists():
        with open(out_json, "r") as f:
             assert json.load(f) == []

@pytest.mark.asyncio
async def test_async_transform(sample_csv, output_json):
    """Test pipeline with async transform function."""
    
    async def augment_data(data):
        for d in data:
            d["augmented"] = True
        return data
        
    pipeline = DataPipeline("async_test") \
        .extract(CSVDataSource(sample_csv)) \
        .transform(augment_data) \
        .load(JSONDataSource(output_json))
        
    await pipeline.execute()
    
    with open(output_json, "r") as f:
        result = json.load(f)
        
    assert result[0].get("augmented") is True
