# HWPX Skeleton Structure Analysis

To resolve "Silent Crash" issues in Hancom Office 2024, an official/working HWPX file (`Skeleton.hwpx`) from the `python-hwpx` library was decompiled and analyzed.

## 1. Package Entry Points (`META-INF/`)

### 1.1 `container.xml`
Hancom Office expects multiple entry points for different document parts.
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container">
    <ocf:rootfiles>
        <ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/>
        <ocf:rootfile full-path="Preview/PrvText.txt" media-type="text/plain"/>
        <ocf:rootfile full-path="META-INF/container.rdf" media-type="application/rdf+xml"/>
    </ocf:rootfiles>
</ocf:container>
```

### 1.2 `container.rdf` (CRITICAL)
This file defines the logical relationships between files using the Resource Description Framework. Without this, the rendering engine may fail to associate `section0.xml` with the document core.
```xml
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about="">
        <ns0:hasPart xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" rdf:resource="Contents/header.xml"/>
        <ns0:hasPart xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" rdf:resource="Contents/section0.xml"/>
    </rdf:Description>
    <rdf:Description rdf:about="Contents/header.xml">
        <rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#HeaderFile"/>
    </rdf:Description>
    <rdf:Description rdf:about="Contents/section0.xml">
        <rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#SectionFile"/>
    </rdf:Description>
</rdf:RDF>
```

## 2. Root Files

### 2.1 `version.xml`
Strictly requires the `hv` namespace and precise application version strings.
- **Namespace**: `http://www.hancom.co.kr/hwpml/2011/version`
- **Target Application**: `WORDPROCESSOR`

### 2.2 `settings.xml`
- **Namespace**: `http://www.hancom.co.kr/hwpml/2011/app`
- **Root Tag**: `<ha:HWPApplicationSetting>`

## 3. `Contents/content.hpf`

The manifest requires a comprehensive set of namespaces to prevent parsing errors in strict mode:
- `ha`: `http://www.hancom.co.kr/hwpml/2011/app`
- `hp`: `http://www.hancom.co.kr/hwpml/2011/paragraph`
- `hs`: `http://www.hancom.co.kr/hwpml/2011/section`
- `hh`: `http://www.hancom.co.kr/hwpml/2011/head`
- `hpf`: `http://www.hancom.co.kr/schema/2011/hpf`

### 3.1 Spine Ordering
The spine must include the header as a linear item:
```xml
<opf:spine>
    <opf:itemref idref="header" linear="yes"/>
    <opf:itemref idref="section0" linear="yes"/>
</opf:spine>
```

## 4. Derived Guidelines for ODA HWPX Generation
1.  **Strict ZIP Encoding**: `mimetype` must be stored at offset 0.
2.  **Logical Linkage**: `container.rdf` MUST accompany `container.xml`.
3.  **Comprehensive HPF**: All OWPML namespaces must be declared at the package level regardless of usage in specific sections.
