# COW CLI

Layout/Content Separation Pipeline with Claude Agent SDK.

## Features

- **Process**: Process math/science images through Mathpix OCR
- **Review**: Human-in-the-loop review workflow
- **Export**: Export to DOCX, LaTeX, PDF formats
- **Config**: Manage CLI configuration

## Installation

```bash
pip install -e .
```

## Usage

```bash
cow --help
cow process image.png -o ./output
cow review list
cow export item-123 -f docx
cow config show
```

## Requirements

- Python 3.11+
- Mathpix API credentials
- Claude MAX subscription (for Agent SDK)
