# Palantir Ontology Collection & Specialized Storage Components

Palantir's Ontology system provides three essential components for managing collections and specialized data: **ObjectSet** for querying and manipulating object collections, **TimeSeries** for temporal measurements, and **MediaSet** for unstructured media files. This reference documents the official specifications, operations, and implementation patterns for each component based on current Palantir documentation.

---

## ObjectSet: The foundation for object queries

An **ObjectSet** represents an unordered collection of objects of a single type within the Palantir Ontology. It serves as the primary mechanism for filtering, traversing relationships, computing aggregations, and retrieving concrete objects. ObjectSets are lazy-evaluated—operations like `filter()`, `union()`, and `orderBy()` create new set definitions without executing queries until terminal operations (`.all()`, `.fetchPage()`, `.count()`) are invoked.

### Official definition and characteristics

ObjectSets are fundamentally **immutable** and **single-typed**—each set contains objects of exactly one object type. Operations return new ObjectSet instances rather than modifying the original. The TypeScript OSDK 2.0 explicitly supports lazy loading, meaning applications only load what they use when they use it.

Key constraints apply: filter operations only work on properties with the **Searchable render hint** enabled in the Ontology configuration. This is a common source of confusion when filters appear to return empty results.

### Temporary versus permanent ObjectSets

**Temporary ObjectSets** are created via the `createTemporary` API endpoint and expire after **one hour**. They receive RIDs in the format `ri.object-set.main.temporary-object-set.XXXXXXXX` and are designed for transient operations and cross-application data transfer. The API endpoint is:

```
POST /api/v2/ontologies/{ontology}/objectSets/createTemporary
```

**Permanent ObjectSets** persist beyond session boundaries and are typically created through application interfaces like Object Explorer. While the documentation doesn't explicitly define "permanent" as a category, saved object sets in applications represent this durability model.

### Complete ObjectSet operations reference

| Operation | Description | Example (TypeScript OSDK) |
|-----------|-------------|---------------------------|
| `filter()` / `where()` | Apply predicate filtering | `client(Employee).where({ age: { $gt: 25 } })` |
| `union()` | Combine objects from multiple sets | `setA.union(setB)` |
| `intersect()` | Find objects in ALL sets | `setA.intersect(setB)` |
| `subtract()` | Remove objects present in another set | `setA.subtract(setB)` |
| `searchAround()` / `pivotTo()` | Traverse link relationships | `baseSet.pivotTo("tasks")` |
| `aggregate()` | Compute summary statistics | `.aggregate("$count")` |
| `orderBy()` | Sort results | `{ $orderBy: { "dueDate": "desc" } }` |
| `take()` | Limit result count | `.take(10)` |
| `fetchPage()` | Paginated retrieval | `.fetchPage({ $pageSize: 30 })` |

### Filter operators complete reference

The filter system supports different operator syntaxes depending on SDK version:

**Comparison operators (TypeScript v2 OSDK / REST API)**:
- `$eq` — Equals: `{ age: { $eq: 25 } }`
- `$ne` — Not equals: `{ status: { $ne: "closed" } }`
- `$gt`, `$gte` — Greater than (or equal): `{ capacity: { $gt: 200 } }`
- `$lt`, `$lte` — Less than (or equal): `{ price: { $lt: 100 } }`

**String operators** support sophisticated text matching:
- `.exactMatch()` / `==` — Exact equality matching
- `.phrase()` / `.contains_all_terms_in_order()` — All tokens in exact order
- `.phrasePrefix()` / `.starts_with()` — Prefix matching
- `.matchAnyToken()` / `.contains_any_term()` — Any token matches
- `.matchAllTokens()` / `.contains_all_terms()` — All tokens present (any order)
- `.fuzzyMatchAnyToken()` — Approximate matching with fuzzy=True

**Property-specific operators** vary by data type:
- **Boolean**: `.isTrue()`, `.isFalse()`
- **Numeric/Date**: `.range()` with `.lt()`, `.lte()`, `.gt()`, `.gte()`
- **GeoPoint**: `.withinDistanceOf()`, `.withinPolygon()`, `.withinBoundingBox()`
- **Arrays**: `.contains()`
- **Links**: `.isPresent()`

**Null checking** uses `.hasProperty()` in TypeScript v1 or `.is_null()` in Python OSDK. The NOT null pattern in Python is `~Property.is_null()`.

**Logical operators** combine conditions:
```python
# Python OSDK - AND
Restaurant.object_type.id.is_null() & (Restaurant.id == 'key')
# Python OSDK - OR  
Restaurant.object_type.id.is_null() | (Restaurant.id == 'key')
# TypeScript v1
Filters.and(filter1, filter2)
Filters.or(filter1, filter2)
```

### Link traversal with searchAround / pivotTo

The `searchAround` (v1) or `pivotTo` (v2) operation traverses relationships defined in the Ontology. Critical limits apply:

- Maximum **3 search arounds** when loading objects into memory via `.all()` or `.allAsync()`
- Object Storage V2: Resulting set cannot exceed **10 million objects**
- Object Storage V1: Limit is **100,000 objects**

```typescript
// TypeScript v2 - Count tasks linked to projects
baseObjectSet.pivotTo("codingTasks").where({
    "status": { $eq: "COMPLETED" }
}).aggregate("$count")
```

### Aggregation capabilities

ObjectSets support these aggregation functions: `.count()`, `.average(property)`, `.max(property)`, `.min(property)`, `.sum(property)` (numeric only), and `.cardinality(property)` for approximate distinct counts.

**GroupBy options** enable dimensional analysis:
- **Strings**: `.topValues()` (top 1,000), `.exactValues()` (up to 10,000 buckets)
- **Numeric**: `.byRanges()`, `.byFixedWidth()`
- **Date**: `.byYear()`, `.byQuarter()`, `.byMonth()`, `.byWeek()`, `.byDays()`
- **Timestamp**: All date options plus `.byHours()`, `.byMinutes()`, `.bySeconds()`

The hard limit is **10,000 total aggregation buckets**.

### Performance limits and optimization

| Storage Type | Loading Limit | Search Around Limit |
|--------------|---------------|---------------------|
| Object Storage V1 (Phonograph) | 10,000 objects | 100,000 objects |
| Object Storage V2 | No explicit limit | 10,000,000 objects |

**Function execution** has practical constraints: maximum **100,000 objects** via `.all()`, with **10,000 recommended** to avoid timeouts. Pagination supports up to **10,000 objects per page**.

**Optimization strategies**: Use `.topValues()` for rapid low-cardinality aggregations. Prefer `pivotTo` over loading objects then searching around. Exclude `__rid` property for better OSv2 performance. Enable snapshot consistency for large paginated queries.

### SDK usage patterns

**TypeScript OSDK 2.0**:
```typescript
import { createClient } from "@osdk/client";
import { Employee } from "@ontology/sdk";

const client = createClient("https://stack.palantir.com", "ri.foundry.main", auth);

// Filtered query with pagination
const result = await client(Employee)
    .where({ age: { $gt: 25 } })
    .fetchPage({ $pageSize: 30 });

// Async iteration
for await (const obj of client(Employee).asyncIter()) {
    console.log(obj);
}
```

**Python OSDK**:
```python
from ontology_sdk.ontology.objects import ExampleRestaurant

# Filtered iteration
filtered = client.ontology.objects.ExampleRestaurant.where(
    ExampleRestaurant.object_type.restaurant_name == "Restaurant Name"
).iterate()

# Aggregation
avg = client.ontology.objects.ExampleRestaurant \
    .avg(ExampleRestaurant.object_type.number_of_reviews) \
    .compute()
```

### K-12 Education domain examples

- **StudentSet filtering**: Query students by grade level, enrollment status, or performance thresholds
- **Link traversal**: Navigate from Student → Enrollments → Courses → Instructors
- **Aggregations**: Count students by grade, average assessment scores by subject area
- **Union operations**: Combine students from multiple programs or schools

### Anti-patterns to avoid

- Calling `.all()` on large unbounded ObjectSets without pagination
- Filtering on properties without Searchable render hint enabled
- Exceeding 3 levels of searchAround operations
- Expecting ordered results without explicit `orderBy()` (ObjectSets are unordered)
- Using `.exactValues()` on high-cardinality fields exceeding 10,000 distinct values

---

## TimeSeries: Temporal measurement storage

A **Time Series Property (TSP)** is an Ontology property type designed for storing and querying measurements taken over time, typically at regular intervals. TSPs connect objects to time series data indexed by a **Time Series Sync**, enabling efficient temporal queries on sensor readings, metrics, and other time-varying values.

### Core concepts and architecture

**Time Series Property**: Links objects to temporal data; stores references rather than raw values
**Time Series Sync**: Resource backed by a dataset that indexes and provides values for TSPs
**Time Series Object Type**: Defines metadata structure for time series datasets
**Sensor Object Type**: Specialized linked object for variable configurations (optional pattern)

Each time series point consists of two components:
- **timestamp**: Measurement time (typically nanoseconds or milliseconds from epoch)
- **value**: Measured value (float for numeric, string for categorical)

### Source dataset configuration

The backing dataset must contain columns mapping to:
- **Series ID**: Unique identifier linking measurements to specific objects
- **Timestamp**: Time column in supported format (nanoseconds from epoch typical)
- **Value**: The measured quantity

Configuration occurs in Ontology Manager under the Capabilities tab, where you specify the Time Series Sync and configure units and interpolation strategies via formatters.

### Query methods and API

**TypeScript OSDK**:
```typescript
// Latest point
const latest = await machine.temperatureId?.getLastPointV2();
const latestValue = latest?.value;

// Earliest point
const earliest = await machine.temperatureId?.getFirstPointV2();
```

**Python OSDK** (returns pandas or Polars DataFrame):
```python
@function
def aircraft_altimeter_mean(aircraft: Aircraft) -> float:
    df = aircraft.altimeter.to_pandas(all_time=True)
    return df["value"].mean()
```

The DataFrame contains `timestamp` and `value` columns.

**REST API v2 Endpoints**:
- `GET /api/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}/timeseries/{property}/firstPoint`
- `GET /api/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}/timeseries/{property}/lastPoint`
- `POST /api/v2/ontologies/{ontology}/objects/{objectType}/{primaryKey}/timeseries/{property}/streamPoints`

The streamPoints endpoint supports time range filtering (absolute or relative), output formats (JSON or ARROW), and aggregation operations.

### Aggregation and granularity options

**Aggregation types** (Workshop/Quiver):
- First/Last value in time window
- Min/Max values
- Mean (average)
- Sum
- Difference (last minus first)
- Relative difference (percent change)
- Standard deviation
- Product

**Granularity options**: HOUR, DAY, WEEK, MONTH, YEAR, and finer granularities for timestamps.

The **FoundryTS library** (Python, not compatible with Functions) provides advanced operations:
- `time_range(start, end)` — Filter to specific range
- `interpolate()` — Resample with strategies: LINEAR, NEAREST, PREVIOUS, ZERO
- `periodic_aggregate()` — Periodic window aggregations
- `rolling_aggregate()` — Rolling window computations
- `statistics()` — Compute mean, count, min, max

### Performance characteristics

Time series data uses a **caching database** that hydrates data at read time. The first query triggers data loading from the backing dataset. Least recently used series are evicted when disk space becomes constrained.

**Optimization**: Add time filters to improve hydration speed. Time series syncs create projections optimized for series ID and timestamp queries. Use incremental pipelines for efficient ongoing updates.

### K-12 Education domain examples

- **Student progress tracking**: Assessment scores over time, reading level progression
- **Attendance patterns**: Daily attendance status as categorical time series
- **Engagement metrics**: Platform usage minutes per day
- **Growth monitoring**: Longitudinal academic performance by subject

### Anti-patterns to avoid

- Using FoundryTS in Python Functions (incompatible—use Python OSDK instead)
- Querying entire time series without time range filters
- Storing categorical data that changes infrequently as time series (use regular properties)
- Creating separate TSPs for each metric when a sensor object pattern would be cleaner

---

## MediaSet: Unstructured file storage

A **MediaSet** is a collection of media files with a common schema, designed for high-scale unstructured data including audio, imagery, video, and documents. MediaSets enable flexible storage, compute optimizations, and schema-specific transformations such as OCR, transcription, and format conversion.

### Official definition

From Palantir documentation: "Media sets are designed to work with high-scale, unstructured data and enable the processing of media items such as audio, imagery, video, and documents. Media sets enable access to flexible storage, compute optimizations, and schema-specific transformations to enhance media workflows and pipelines."

### MediaSet creation and configuration

**Creation process**:
1. Navigate to a Project folder
2. Select New → Media set
3. Choose the schema type (media file type)
4. Configure primary format and optional additional input formats
5. Create and upload media via drag-and-drop or file selection

**Configuration options**:
- **Schema Type**: Defines allowed file types (documents, images, audio, etc.)
- **Primary Format**: Required format; all files must match or be converted
- **Additional Input Formats**: Files auto-convert to primary format on upload
- **Transaction Policy**: Transactionless (immediate writes, no rollback) or Transactional (atomic commits)
- **Retention Policy**: Optional time-based deletion (e.g., 14 days)

### MediaReference versus Attachment properties

**MediaReference** is the recommended approach for linking objects to media:

| Feature | MediaReference | Attachment |
|---------|----------------|------------|
| **Scalability** | Billions of files | Limited |
| **File Size** | 20MB recommended for functions | **200MB hard limit** |
| **Object Links** | Unlimited (same MediaSet) | **Max 10 objects lifetime** |
| **Transformations** | OCR, transcription, format conversion | None |
| **Format Support** | NITF, GeoTIFF, DICOM, advanced formats | Basic |

MediaReference stores structured references:
```json
{
  "mimeType": "image/png",
  "reference": {
    "type": "mediaSetViewItem",
    "mediaSetViewItem": {
      "mediaSetRid": "ri.mio.main.media-set.00000000-...",
      "mediaSetViewRid": "ri.mio.main.view.00000000-...",
      "mediaItemRid": "ri.mio.main.media-item.00000000-..."
    }
  }
}
```

**Critical constraint**: A media reference must reference the same MediaSet wherever used. You cannot upload to MediaSet A and link it to MediaSet B.

### Supported media types and size limits

**Audio**: WAV, FLAC, MP3, MP4, NIST SPHERE (.sph), WEBM

**Documents**: PDF (primary), with DOCX, PPTX, TXT as input-only formats (auto-converted). Note: Password-protected, digitally signed, or encrypted PDFs are NOT supported.

**Images**: PNG, JPEG, JP2K, BMP, TIFF, NITF

**Video**: MP4, MOV, TS, MKV

**Spreadsheets**: XLSX (advanced formulas and embedded images NOT supported)

**Size limits**:
- Attachments: **200MB hard global limit**
- Functions memory: **20MB recommended** maximum
- Transactional uploads: **10,000 files per transaction**

### Search, indexing, and text extraction

**PDF text extraction** supports three methods:
1. Raw text extraction for machine-generated PDFs with embedded text
2. OCR for scanned documents
3. Layout-aware extraction with bounding boxes (requires Document Information Extraction model)

**Python transform OCR**:
```python
extracted_text = media_input.transform().ocr(
    media_item_rid=None,  # entire media set
    start_page=0,
    end_page=None,
    return_structure="page_per_row",
    languages=[],
    scripts=[]
)
```

**Image OCR** extracts text with multi-language support. **Audio transcription** converts speech to text with language auto-detection and performance modes.

**Semantic search integration**: Extract text → chunk text → embed → vector search workflow enables document discovery.

### SDK implementation examples

**Python OSDK** (v2.145+):
```python
from ontology_sdk import FoundryClient

client = FoundryClient()
edits = client.ontology.edits()

# Upload media
media_reference = client.ontology.media.upload_media(
    body="Hello, world".encode("utf8"),
    filename="/planes/aircraft.txt",
)

# Create object with media reference
edits.objects.Aircraft.create(
    pk="primary_key",
    my_media_property=media_reference,
)

# Access media content
raw_data: BytesIO = my_aircraft.my_media_property.get_media_content()
```

**TypeScript OSDK** (v2.6+):
```typescript
import { createEditBatch, uploadMedia } from "@osdk/functions";

const batch = createEditBatch(client);
const blob = new Blob(["Hello, world"], { type: "text/plain" });

const mediaReference = await uploadMedia(client, {
    data: blob,
    fileName: "/planes/aircraft.txt"
});

batch.create(Aircraft, {
    myMediaProperty: mediaReference,
});
```

**OCR in TypeScript Functions**:
```typescript
if (MediaItem.isDocument(paper.mediaReference)) {
    const text = (await paper.mediaReference.ocrAsync({
        endPage: 1,
        languages: [],
        scripts: [],
        outputType: 'text'
    }))[0];
}
```

### K-12 Education domain examples

- **Student profiles**: Profile photos stored in image MediaSets
- **Assignment submissions**: Student work uploaded as PDF MediaSets with OCR for text extraction
- **Educational content**: Video lectures, audio lessons in media libraries
- **Document archives**: Report cards, transcripts with searchable text extraction
- **Portfolio systems**: Multi-format student work samples with metadata linking

### Anti-patterns to avoid

- Using Attachments for scalable storage (limited to 10 object links per file lifetime)
- Uploading password-protected or encrypted PDFs (unsupported)
- Processing files >20MB in Functions (memory constraints)
- Assuming cross-MediaSet references work (they don't—same MediaSet only)
- Ignoring retention policies that auto-delete files after configured windows

---

## Integration points across components

These three components interconnect within the Ontology:

**ObjectSet + TimeSeries**: Query objects via ObjectSet, then access their time series properties for temporal analysis. Use aggregations across ObjectSets with time series groupings.

**ObjectSet + MediaSet**: Filter objects with MediaReference properties, then access associated media content. Enable document search workflows by combining text extraction with ObjectSet filters.

**TimeSeries + MediaSet**: Link time-stamped media (surveillance video, sensor images) to temporal queries. Combine IoT measurements with media evidence.

**Unified OSDK pattern**: All three components share consistent SDK interfaces across TypeScript and Python, with REST API v2 endpoints enabling programmatic access without SDK dependencies.

---

## Validation rules summary

**ObjectSet validation**:
- Ensure Searchable render hint enabled on filtered properties
- Verify object type exists and is accessible
- Confirm aggregation buckets ≤10,000
- Check search_around depth ≤3 levels

**TimeSeries validation**:
- Verify Time Series Sync configured and healthy
- Confirm backing dataset has required columns (series_id, timestamp, value)
- Validate timestamp format compatibility

**MediaSet validation**:
- Confirm schema type matches uploaded file formats
- Verify file size within limits (200MB attachments, 20MB functions)
- Check media reference points to correct MediaSet
- Validate file not password-protected/encrypted (PDFs)