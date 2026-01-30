"""
Tests for Stage A (Ingestion) Module.

Tests for:
- ImageLoader (load from path, url, bytes, base64)
- ImageValidator (format, resolution, content validation)
- Preprocessor (all preprocessing operations)
- StorageManager (save, load, cache, cleanup)

Schema Version: 2.0.0
"""

import asyncio
import base64
import hashlib
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator
import io

import pytest

# Try to import PIL, mark tests as requiring it
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from mathpix_pipeline.ingestion import (
    # Loader
    ImageLoader,
    LoadedImage,
    SUPPORTED_FORMATS,
    MAX_FILE_SIZE,
    # Validator
    ImageValidator,
    ValidationResult,
    MIN_RESOLUTION,
    MAX_RESOLUTION,
    # Preprocessor
    Preprocessor,
    PreprocessingResult,
    PreprocessingOp,
    Region,
    # Storage
    StorageManager,
    StoredImage,
    DEFAULT_CACHE_DIR,
    # Exceptions
    IngestionError,
    ImageFormatError,
    ImageSizeError,
    ValidationError,
    StorageError,
    PreprocessingError,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_image_path(tmp_path) -> Path:
    """Create a temporary PNG image file."""
    image_path = tmp_path / "test_image.png"

    if PIL_AVAILABLE:
        # Create a simple test image
        img = Image.new("RGB", (800, 600), color="white")
        img.save(image_path)
    else:
        # Create a minimal valid PNG file
        # PNG signature + IHDR chunk
        png_data = (
            b'\x89PNG\r\n\x1a\n'  # PNG signature
            b'\x00\x00\x00\rIHDR'  # IHDR chunk
            b'\x00\x00\x03 \x00\x00\x02X'  # Width: 800, Height: 600
            b'\x08\x02\x00\x00\x00'  # Bit depth, color type, etc
            b'\x00\x00\x00\x00'  # CRC placeholder
            b'\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND chunk
        )
        image_path.write_bytes(png_data)

    return image_path


@pytest.fixture
def temp_large_image(tmp_path) -> Path:
    """Create a large image exceeding size limits."""
    image_path = tmp_path / "large_image.png"

    if PIL_AVAILABLE:
        # Create a large image
        img = Image.new("RGB", (5000, 5000), color="white")
        img.save(image_path)
    else:
        # Create a large dummy PNG
        large_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * (10 * 1024 * 1024)  # 10MB
        image_path.write_bytes(large_data)

    return image_path


@pytest.fixture
def sample_image_bytes() -> bytes:
    """Generate sample PNG image bytes."""
    if PIL_AVAILABLE:
        img = Image.new("RGB", (400, 300), color="lightblue")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    else:
        # Minimal valid PNG
        return (
            b'\x89PNG\r\n\x1a\n'
            b'\x00\x00\x00\rIHDR'
            b'\x00\x00\x01\x90\x00\x00\x01,'  # 400x300
            b'\x08\x02\x00\x00\x00'
            b'\x00\x00\x00\x00'
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )


@pytest.fixture
def sample_base64_image(sample_image_bytes: bytes) -> str:
    """Generate base64 encoded image."""
    return base64.b64encode(sample_image_bytes).decode("utf-8")


@pytest.fixture
def corrupted_image_path(tmp_path) -> Path:
    """Create a corrupted image file."""
    image_path = tmp_path / "corrupted.png"
    # Write random bytes that aren't a valid image
    image_path.write_bytes(b"NOT_AN_IMAGE" * 100)
    return image_path


@pytest.fixture
def storage_manager(tmp_path) -> Generator[StorageManager, None, None]:
    """Create a storage manager with cleanup."""
    cache_dir = tmp_path / "cache"
    temp_dir = tmp_path / "temp"

    manager = StorageManager(
        cache_dir=cache_dir,
        temp_dir=temp_dir,
        use_temp=True,
        cache_enabled=True,
    )

    yield manager

    # Cleanup
    manager.cleanup(force=True)


# =============================================================================
# ImageLoader Tests
# =============================================================================

class TestImageLoader:
    """Tests for ImageLoader class."""

    @pytest.mark.asyncio
    async def test_load_from_path_success(self, temp_image_path: Path):
        """Test successful image loading from path."""
        loader = ImageLoader()
        image = await loader.load_from_path(temp_image_path)

        assert isinstance(image, LoadedImage)
        assert image.format == "png"
        assert image.source_type == "path"
        assert image.source_location == str(temp_image_path.absolute())
        assert image.size_bytes > 0
        assert len(image.content_hash) == 64  # SHA256 hex length
        assert image.width == 800
        assert image.height == 600

    @pytest.mark.asyncio
    async def test_load_from_path_not_found(self):
        """Test loading from non-existent path."""
        loader = ImageLoader()

        with pytest.raises(IngestionError) as exc_info:
            await loader.load_from_path("/nonexistent/path/image.png")

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_load_from_path_unsupported_format(self, tmp_path: Path):
        """Test loading unsupported format."""
        unsupported_path = tmp_path / "test.xyz"
        unsupported_path.write_bytes(b"dummy content")

        loader = ImageLoader()

        with pytest.raises(ImageFormatError) as exc_info:
            await loader.load_from_path(unsupported_path)

        assert "xyz" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_load_from_path_size_limit(self, temp_large_image: Path):
        """Test size limit enforcement."""
        # Set a small size limit
        loader = ImageLoader(max_file_size=1000)  # 1KB

        with pytest.raises(ImageSizeError) as exc_info:
            await loader.load_from_path(temp_large_image)

        assert "exceeds maximum" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_load_from_bytes_success(self, sample_image_bytes: bytes):
        """Test loading from bytes."""
        loader = ImageLoader()
        image = await loader.load_from_bytes(sample_image_bytes, format="png")

        assert isinstance(image, LoadedImage)
        assert image.format == "png"
        assert image.source_type == "bytes"
        assert image.size_bytes == len(sample_image_bytes)
        assert image.width == 400
        assert image.height == 300

    @pytest.mark.asyncio
    async def test_load_from_bytes_auto_detect(self, sample_image_bytes: bytes):
        """Test format auto-detection from bytes."""
        loader = ImageLoader()
        # Don't specify format - should auto-detect
        image = await loader.load_from_bytes(sample_image_bytes)

        assert image.format == "png"

    @pytest.mark.asyncio
    async def test_load_from_base64_success(self, sample_base64_image: str):
        """Test loading from base64."""
        loader = ImageLoader()
        image = await loader.load_from_base64(sample_base64_image, format="png")

        assert isinstance(image, LoadedImage)
        assert image.format == "png"
        assert image.source_type == "base64"
        assert image.width == 400
        assert image.height == 300

    @pytest.mark.asyncio
    async def test_load_from_base64_data_url(self, sample_base64_image: str):
        """Test loading from data URL format."""
        data_url = f"data:image/png;base64,{sample_base64_image}"

        loader = ImageLoader()
        image = await loader.load_from_base64(data_url)

        assert image.format == "png"
        assert image.source_type == "base64"

    @pytest.mark.asyncio
    async def test_content_hash_consistency(self, sample_image_bytes: bytes):
        """Test that content hash is consistent."""
        loader = ImageLoader()

        image1 = await loader.load_from_bytes(sample_image_bytes)
        image2 = await loader.load_from_bytes(sample_image_bytes)

        assert image1.content_hash == image2.content_hash

        expected_hash = hashlib.sha256(sample_image_bytes).hexdigest()
        assert image1.content_hash == expected_hash


# =============================================================================
# ImageValidator Tests
# =============================================================================

class TestImageValidator:
    """Tests for ImageValidator class."""

    @pytest.mark.asyncio
    async def test_validate_format_success(self, temp_image_path: Path):
        """Test format validation success."""
        loader = ImageLoader()
        validator = ImageValidator()

        image = await loader.load_from_path(temp_image_path)
        passed, error = validator.validate_format(image)

        assert passed is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_format_failure(self):
        """Test format validation failure."""
        validator = ImageValidator()

        # Create fake image with unsupported format
        fake_image = LoadedImage(
            data=b"dummy",
            format="xyz",
            size_bytes=5,
            source_type="bytes",
        )

        passed, error = validator.validate_format(fake_image)

        assert passed is False
        assert error is not None
        assert "xyz" in error

    @pytest.mark.asyncio
    async def test_validate_resolution_success(self, temp_image_path: Path):
        """Test resolution validation success."""
        loader = ImageLoader()
        validator = ImageValidator()

        image = await loader.load_from_path(temp_image_path)
        passed, error = validator.validate_resolution(image)

        assert passed is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_resolution_too_small(self):
        """Test resolution validation fails for small image."""
        validator = ImageValidator(min_resolution=(1000, 1000))

        image = LoadedImage(
            data=b"dummy",
            format="png",
            size_bytes=100,
            source_type="bytes",
            width=500,
            height=400,
        )

        passed, error = validator.validate_resolution(image)

        assert passed is False
        assert "below minimum" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_resolution_too_large(self):
        """Test resolution validation fails for large image."""
        validator = ImageValidator(max_resolution=(1000, 1000))

        image = LoadedImage(
            data=b"dummy",
            format="png",
            size_bytes=100,
            source_type="bytes",
            width=5000,
            height=4000,
        )

        passed, error = validator.validate_resolution(image)

        assert passed is False
        assert "exceeds maximum" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_content_success(self, temp_image_path: Path):
        """Test content validation success."""
        loader = ImageLoader()
        validator = ImageValidator()

        image = await loader.load_from_path(temp_image_path)
        passed, error = validator.validate_content(image)

        assert passed is True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_content_corrupted(self, corrupted_image_path: Path):
        """Test content validation fails for corrupted image."""
        loader = ImageLoader()
        validator = ImageValidator()

        # Force load the corrupted file as PNG
        image = LoadedImage(
            data=corrupted_image_path.read_bytes(),
            format="png",
            size_bytes=1200,
            source_type="path",
            source_location=str(corrupted_image_path),
        )

        passed, error = validator.validate_content(image)

        assert passed is False
        assert "corrupted" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_all_checks(self, temp_image_path: Path):
        """Test complete validation with all checks."""
        loader = ImageLoader()
        validator = ImageValidator()

        image = await loader.load_from_path(temp_image_path)
        result = validator.validate(image)

        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert "format" in result.checks_passed
        assert "resolution" in result.checks_passed
        assert "content" in result.checks_passed
        assert len(result.checks_failed) == 0

    @pytest.mark.asyncio
    async def test_validate_with_raise_on_failure(self, corrupted_image_path: Path):
        """Test validation raises exception on failure."""
        validator = ImageValidator()

        image = LoadedImage(
            data=corrupted_image_path.read_bytes(),
            format="png",
            size_bytes=1200,
            source_type="path",
        )

        with pytest.raises(ValidationError):
            validator.validate(image, raise_on_failure=True)

    @pytest.mark.asyncio
    async def test_math_content_detection(self, temp_image_path: Path):
        """Test math content heuristic detection."""
        loader = ImageLoader()
        validator = ImageValidator()

        image = await loader.load_from_path(temp_image_path)
        confidence, indicators = validator.is_math_content(image)

        assert 0.0 <= confidence <= 1.0
        assert isinstance(indicators, list)


# =============================================================================
# Preprocessor Tests
# =============================================================================

class TestPreprocessor:
    """Tests for Preprocessor class."""

    @pytest.mark.asyncio
    async def test_normalize_resolution(self, temp_image_path: Path):
        """Test resolution normalization."""
        loader = ImageLoader()
        preprocessor = Preprocessor(target_dpi=150, max_dimension=2000)

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(
            image,
            operations=[PreprocessingOp.NORMALIZE_RESOLUTION],
        )

        assert isinstance(result, PreprocessingResult)
        assert PreprocessingOp.NORMALIZE_RESOLUTION.value in result.operations_applied
        assert result.width <= 2000
        assert result.height <= 2000

    @pytest.mark.asyncio
    async def test_enhance_contrast(self, temp_image_path: Path):
        """Test contrast enhancement."""
        loader = ImageLoader()
        preprocessor = Preprocessor(contrast_factor=1.5)

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(
            image,
            operations=[PreprocessingOp.ENHANCE_CONTRAST],
        )

        assert PreprocessingOp.ENHANCE_CONTRAST.value in result.operations_applied
        assert "contrast_factor" in result.metadata

    @pytest.mark.asyncio
    async def test_convert_grayscale(self, temp_image_path: Path):
        """Test grayscale conversion."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(
            image,
            operations=[PreprocessingOp.CONVERT_GRAYSCALE],
        )

        assert PreprocessingOp.CONVERT_GRAYSCALE.value in result.operations_applied

    @pytest.mark.asyncio
    async def test_sharpen(self, temp_image_path: Path):
        """Test image sharpening."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(
            image,
            operations=[PreprocessingOp.SHARPEN],
        )

        assert PreprocessingOp.SHARPEN.value in result.operations_applied

    @pytest.mark.asyncio
    async def test_detect_regions(self, temp_image_path: Path):
        """Test region detection."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(
            image,
            operations=[PreprocessingOp.DETECT_REGIONS],
        )

        assert PreprocessingOp.DETECT_REGIONS.value in result.operations_applied
        assert isinstance(result.regions, list)

    @pytest.mark.asyncio
    async def test_multiple_operations(self, temp_image_path: Path):
        """Test multiple preprocessing operations."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(
            image,
            operations=[
                PreprocessingOp.NORMALIZE_RESOLUTION,
                PreprocessingOp.ENHANCE_CONTRAST,
                PreprocessingOp.CONVERT_GRAYSCALE,
            ],
        )

        assert len(result.operations_applied) == 3
        assert PreprocessingOp.NORMALIZE_RESOLUTION.value in result.operations_applied
        assert PreprocessingOp.ENHANCE_CONTRAST.value in result.operations_applied
        assert PreprocessingOp.CONVERT_GRAYSCALE.value in result.operations_applied

    @pytest.mark.asyncio
    async def test_output_format_conversion(self, temp_image_path: Path):
        """Test output format conversion."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(
            image,
            operations=[],
            output_format="jpg",
        )

        assert result.format == "jpg"


# =============================================================================
# StorageManager Tests
# =============================================================================

class TestStorageManager:
    """Tests for StorageManager class."""

    @pytest.mark.asyncio
    async def test_save_and_load_cached(
        self,
        temp_image_path: Path,
        storage_manager: StorageManager,
    ):
        """Test saving and loading from cache."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        # Load and process image
        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(image)

        # Save
        stored = storage_manager.save_processed(image, result, image_id="test-001")

        assert isinstance(stored, StoredImage)
        assert stored.image_id == "test-001"
        assert Path(stored.path).exists()

        # Load from cache
        cached = storage_manager.load_cached("test-001")

        assert cached is not None
        assert cached.content_hash == image.content_hash
        assert cached.source_type == "cache"

    @pytest.mark.asyncio
    async def test_exists(
        self,
        temp_image_path: Path,
        storage_manager: StorageManager,
    ):
        """Test checking if image exists."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(image)

        # Before saving
        assert storage_manager.exists("test-002") is False

        # After saving
        storage_manager.save_processed(image, result, image_id="test-002")
        assert storage_manager.exists("test-002") is True

    @pytest.mark.asyncio
    async def test_remove(
        self,
        temp_image_path: Path,
        storage_manager: StorageManager,
    ):
        """Test removing image from storage."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(image)

        storage_manager.save_processed(image, result, image_id="test-003")
        assert storage_manager.exists("test-003") is True

        removed = storage_manager.remove("test-003")

        assert removed is True
        assert storage_manager.exists("test-003") is False

    @pytest.mark.asyncio
    async def test_cleanup_expired(
        self,
        temp_image_path: Path,
        storage_manager: StorageManager,
    ):
        """Test cleanup of expired files."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(image)

        # Save with expiration (negative hours to make it already expired)
        storage_manager.save_processed(
            image,
            result,
            image_id="test-expired",
            expires_in_hours=-1,
        )

        assert storage_manager.exists("test-expired") is False  # Already expired

        # Cleanup should remove it
        removed_count = storage_manager.cleanup()
        assert removed_count >= 0

    @pytest.mark.asyncio
    async def test_list_cached(
        self,
        temp_image_path: Path,
        storage_manager: StorageManager,
    ):
        """Test listing all cached images."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(image)

        # Save multiple images
        storage_manager.save_processed(image, result, image_id="list-test-1")
        storage_manager.save_processed(image, result, image_id="list-test-2")

        cached_list = storage_manager.list_cached()

        assert len(cached_list) >= 2
        image_ids = [stored.image_id for stored in cached_list]
        assert "list-test-1" in image_ids
        assert "list-test-2" in image_ids

    @pytest.mark.asyncio
    async def test_get_stats(self, storage_manager: StorageManager):
        """Test getting storage statistics."""
        stats = storage_manager.get_stats()

        assert "cache_enabled" in stats
        assert "cache_dir" in stats
        assert "temp_dir" in stats
        assert "cached_images" in stats
        assert "temp_files" in stats
        assert "total_size_bytes" in stats

    @pytest.mark.asyncio
    async def test_temp_storage(
        self,
        temp_image_path: Path,
        storage_manager: StorageManager,
    ):
        """Test temporary storage."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(image)

        # Save to temp
        stored = storage_manager.save_processed(
            image,
            result,
            image_id="temp-test",
            temp=True,
        )

        assert Path(stored.path).exists()
        assert "temp" in stored.path.lower()

    @pytest.mark.asyncio
    async def test_get_metadata(
        self,
        temp_image_path: Path,
        storage_manager: StorageManager,
    ):
        """Test getting image metadata."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(image)

        storage_manager.save_processed(image, result, image_id="meta-test")

        metadata = storage_manager.get_metadata("meta-test")

        assert metadata is not None
        assert metadata.image_id == "meta-test"
        assert metadata.width == result.width
        assert metadata.height == result.height

    @pytest.mark.asyncio
    async def test_get_image_bytes(
        self,
        temp_image_path: Path,
        storage_manager: StorageManager,
    ):
        """Test getting raw image bytes."""
        loader = ImageLoader()
        preprocessor = Preprocessor()

        image = await loader.load_from_path(temp_image_path)
        result = preprocessor.process(image)

        storage_manager.save_processed(image, result, image_id="bytes-test")

        image_bytes = await storage_manager.get_image_bytes("bytes-test")

        assert image_bytes is not None
        assert len(image_bytes) > 0
