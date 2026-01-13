from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class NamespaceProfile:
    name: str
    uris: Dict[str, str]

    def uri(self, prefix: str) -> Optional[str]:
        return self.uris.get(prefix)

    def qname(self, prefix: str, local: str) -> str:
        uri = self.uris.get(prefix)
        if not uri:
            raise KeyError(f"Unknown namespace prefix: {prefix}")
        return f"{{{uri}}}{local}"

    def register(self) -> None:
        for prefix, uri in self.uris.items():
            if uri:
                ET.register_namespace(prefix, uri)


PROFILE_2011 = NamespaceProfile(
    name="2011",
    uris={
        "hs": "http://www.hancom.co.kr/hwpml/2011/section",
        "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
        "hh": "http://www.hancom.co.kr/hwpml/2011/head",
        "ha": "http://www.hancom.co.kr/hwpml/2011/app",
        "hc": "http://www.hancom.co.kr/hwpml/2011/core",
        "hm": "http://www.hancom.co.kr/hwpml/2011/master-page",
        "hhs": "http://www.hancom.co.kr/hwpml/2011/history",
        "hp10": "http://www.hancom.co.kr/hwpml/2016/paragraph",
        "hpf": "http://www.hancom.co.kr/schema/2011/hpf",
        "ooxmlchart": "http://www.hancom.co.kr/hwpml/2016/ooxmlchart",
        "hwpunitchar": "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar",
        "hv": "http://www.hancom.co.kr/hwpml/2011/version",
        "opf": "http://www.idpf.org/2007/opf/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "epub": "http://www.idpf.org/2007/ops",
        "config": "urn:oasis:names:tc:opendocument:xmlns:config:1.0",
    },
)

PROFILE_2024 = NamespaceProfile(
    name="2024",
    uris={
        "hh": "http://www.owpml.org/owpml/2024/head",
        "hb": "http://www.owpml.org/owpml/2024/body",
        "hp": "http://www.owpml.org/owpml/2024/paragraph",
        "hc": "http://www.owpml.org/owpml/2024/core",
        "hv": "http://www.owpml.org/owpml/2024/version",
        "hm": "http://www.owpml.org/owpml/2024/master-page",
        "hs": "http://www.owpml.org/owpml/2024/history",
        "ha": "http://www.owpml.org/owpml/2024/app",
        "ooxmlchart": "http://www.hancom.co.kr/hwpml/2016/ooxmlchart",
        "hwpunitchar": "http://www.hancom.co.kr/hwpml/2016/HwpUnitChar",
        "opf": "http://www.idpf.org/2007/opf/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "epub": "http://www.idpf.org/2007/ops",
        "config": "urn:oasis:names:tc:opendocument:xmlns:config:1.0",
    },
)

PROFILES = {
    "2011": PROFILE_2011,
    "2024": PROFILE_2024,
}


def get_profile(name: str) -> NamespaceProfile:
    profile = PROFILES.get(name)
    if not profile:
        raise KeyError(f"Unknown namespace profile: {name}")
    return profile


def detect_profile_from_tag(tag: str) -> NamespaceProfile:
    if tag.startswith("{") and "}" in tag:
        uri = tag.split("}")[0][1:]
        if "owpml.org/owpml/2024" in uri:
            return PROFILE_2024
        if "hancom.co.kr/hwpml/2011" in uri:
            return PROFILE_2011
    return PROFILE_2011


def build_namespace_decls(profile: NamespaceProfile, prefixes: Optional[list[str]] = None) -> str:
    items = profile.uris.items() if prefixes is None else ((p, profile.uris.get(p)) for p in prefixes)
    parts = []
    for prefix, uri in items:
        if not uri:
            continue
        parts.append(f'xmlns:{prefix}="{uri}"')
    return " ".join(parts)
