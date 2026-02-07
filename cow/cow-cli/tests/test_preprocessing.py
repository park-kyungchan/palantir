"""
Tests for image preprocessing module.
"""
import pytest
from pathlib import Path
import tempfile
import io

from PIL import Image

from cow_cli.preprocessing import (
    ImageValidator,
    validate_image,
    ValidationError,
    ValidationResult,
    ImageInfo,
    ImageDeduplicator,
    DeduplicationResult,
    find_duplicates,
)


class TestImageValidator:
    """Tests for ImageValidator."""

    @pytest.fixture
    def validator(self):
        """Create default validator."""
        return ImageValidator()

    @pytest.fixture
    def valid_png_bytes(self):
        """Create valid PNG image bytes."""
        img = Image.new("RGB", (100, 100), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @pytest.fixture
    def valid_jpg_bytes(self):
        """Create valid JPEG image bytes."""
        img = Image.new("RGB", (100, 100), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()

    def test_validate_valid_png(self, validator, valid_png_bytes):
        """Test validating a valid PNG image."""
        result = validator.validate(valid_png_bytes)

        assert result.valid is True
        assert result.format == "PNG"
        assert result.width == 100
        assert result.height == 100
        assert result.error == ValidationError.NONE

    def test_validate_valid_jpg(self, validator, valid_jpg_bytes):
        """Test validating a valid JPEG image."""
        result = validator.validate(valid_jpg_bytes)

        assert result.valid is True
        assert result.format in ("JPEG", "JPG")
        assert result.width == 100
        assert result.height == 100

    def test_validate_file_path(self, validator, valid_png_bytes):
        """Test validating from file path."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(valid_png_bytes)
            f.flush()

            result = validator.validate(Path(f.name))

            assert result.valid is True
            assert result.format == "PNG"

    def test_validate_string_path(self, validator, valid_png_bytes):
        """Test validating from string path."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(valid_png_bytes)
            f.flush()

            result = validator.validate(f.name)

            assert result.valid is True

    def test_validate_file_not_found(self, validator):
        """Test file not found error."""
        result = validator.validate(Path("/nonexistent/path.png"))

        assert result.valid is False
        assert result.error == ValidationError.FILE_NOT_FOUND

    def test_validate_too_small(self):
        """Test resolution too low."""
        validator = ImageValidator(min_width=100, min_height=100)

        # Create small image
        img = Image.new("RGB", (50, 50), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        result = validator.validate(buffer.getvalue())

        assert result.valid is False
        assert result.error == ValidationError.RESOLUTION_TOO_LOW

    def test_validate_too_large(self):
        """Test file too large."""
        validator = ImageValidator(max_size_mb=0.0001)  # ~100 bytes limit

        # Create larger image to exceed limit
        img = Image.new("RGB", (500, 500), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()

        # Verify image is actually larger than limit
        assert len(data) > 100, f"Image is only {len(data)} bytes"

        result = validator.validate(data)

        assert result.valid is False
        assert result.error == ValidationError.FILE_TOO_LARGE

    def test_validate_corrupted_data(self, validator):
        """Test corrupted image data."""
        result = validator.validate(b"not an image")

        assert result.valid is False
        assert result.error == ValidationError.CORRUPTED_IMAGE

    def test_validation_result_size_mb(self):
        """Test size_mb property."""
        result = ValidationResult(
            valid=True,
            size_bytes=1024 * 1024 * 2,  # 2MB
        )

        assert result.size_mb == 2.0

    def test_get_info(self, validator, valid_png_bytes):
        """Test get_info method."""
        info = validator.get_info(valid_png_bytes)

        assert info is not None
        assert info.format == "PNG"
        assert info.width == 100
        assert info.height == 100
        assert info.mode == "RGB"


class TestImageDeduplicator:
    """Tests for ImageDeduplicator."""

    @pytest.fixture
    def deduplicator(self):
        """Create default deduplicator."""
        return ImageDeduplicator(threshold=5)

    @pytest.fixture
    def complex_image_bytes(self):
        """Create a complex image with patterns."""
        img = Image.new("RGB", (100, 100))
        # Add some pattern
        for x in range(100):
            for y in range(100):
                img.putpixel((x, y), (x * 2, y * 2, (x + y) % 256))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    def test_compute_hash(self, deduplicator, complex_image_bytes):
        """Test hash computation."""
        hash_val = deduplicator.compute_hash(complex_image_bytes)

        assert hash_val is not None

    def test_same_image_same_hash(self, deduplicator, complex_image_bytes):
        """Test that same image produces same hash."""
        hash1 = deduplicator.compute_hash(complex_image_bytes)
        hash2 = deduplicator.compute_hash(complex_image_bytes)

        assert hash1 == hash2

    def test_is_duplicate_first_image(self, deduplicator, complex_image_bytes):
        """Test first image is not duplicate."""
        result = deduplicator.is_duplicate(complex_image_bytes, Path("test1.png"))

        assert result is None

    def test_is_duplicate_same_image(self, deduplicator, complex_image_bytes):
        """Test same image is detected as duplicate."""
        deduplicator.is_duplicate(complex_image_bytes, Path("test1.png"))
        result = deduplicator.is_duplicate(complex_image_bytes, Path("test2.png"))

        assert result == Path("test1.png")

    def test_different_images_not_duplicate(self, deduplicator):
        """Test different images are not duplicates."""
        # Create two different patterned images
        img1 = Image.new("RGB", (100, 100))
        for x in range(100):
            for y in range(100):
                img1.putpixel((x, y), (x * 2, y * 2, 0))

        img2 = Image.new("RGB", (100, 100))
        for x in range(100):
            for y in range(100):
                img2.putpixel((x, y), (255 - x * 2, 255 - y * 2, 255))

        buf1 = io.BytesIO()
        buf2 = io.BytesIO()
        img1.save(buf1, format="PNG")
        img2.save(buf2, format="PNG")

        deduplicator.is_duplicate(buf1.getvalue(), Path("img1.png"))
        result = deduplicator.is_duplicate(buf2.getvalue(), Path("img2.png"))

        assert result is None

    def test_clear_cache(self, deduplicator, complex_image_bytes):
        """Test cache clearing."""
        deduplicator.is_duplicate(complex_image_bytes, Path("test.png"))
        assert deduplicator.cache_size == 1

        deduplicator.clear_cache()
        assert deduplicator.cache_size == 0

    def test_hash_types(self):
        """Test different hash algorithms."""
        # Note: imagehash uses 'average_hash' not 'ahash'
        for hash_type in ["phash", "dhash", "whash"]:
            dedup = ImageDeduplicator(hash_type=hash_type)
            assert dedup.hash_type == hash_type

    def test_invalid_hash_type(self):
        """Test invalid hash type raises error."""
        with pytest.raises(ValueError):
            ImageDeduplicator(hash_type="invalid")


class TestDeduplicationResult:
    """Tests for DeduplicationResult."""

    def test_empty_result(self):
        """Test empty result properties."""
        result = DeduplicationResult()

        assert result.total_processed == 0
        assert result.duplicate_count == 0
        assert result.api_calls_saved == 0

    def test_result_with_data(self):
        """Test result with data."""
        from cow_cli.preprocessing.deduplicator import DuplicateInfo

        result = DeduplicationResult(
            unique_images=[Path("a.png"), Path("b.png")],
            duplicates=[
                DuplicateInfo(
                    duplicate_path=Path("c.png"),
                    original_path=Path("a.png"),
                    hash_distance=2,
                    hash_type="phash",
                )
            ],
            failed=[(Path("d.png"), "error")],
        )

        assert result.total_processed == 4
        assert result.duplicate_count == 1
        assert result.api_calls_saved == 1

    def test_get_duplicate_groups(self):
        """Test duplicate grouping."""
        from cow_cli.preprocessing.deduplicator import DuplicateInfo

        result = DeduplicationResult(
            duplicates=[
                DuplicateInfo(Path("b.png"), Path("a.png"), 1, "phash"),
                DuplicateInfo(Path("c.png"), Path("a.png"), 2, "phash"),
                DuplicateInfo(Path("e.png"), Path("d.png"), 1, "phash"),
            ]
        )

        groups = result.get_duplicate_groups()

        assert len(groups) == 2
        assert len(groups[Path("a.png")]) == 2
        assert len(groups[Path("d.png")]) == 1


class TestFindDuplicates:
    """Tests for find_duplicates convenience function."""

    def test_find_duplicates_empty_list(self):
        """Test with empty list."""
        result = find_duplicates([])

        assert result.total_processed == 0
        assert len(result.unique_images) == 0

    def test_find_duplicates_with_files(self):
        """Test with actual files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test images
            img1 = Image.new("RGB", (100, 100))
            for x in range(100):
                for y in range(100):
                    img1.putpixel((x, y), (x * 2, y * 2, x + y))

            path1 = Path(tmpdir) / "img1.png"
            path2 = Path(tmpdir) / "img2.png"

            img1.save(path1)
            img1.save(path2)  # Save same image twice

            result = find_duplicates([path1, path2])

            assert len(result.unique_images) == 1
            assert len(result.duplicates) == 1
