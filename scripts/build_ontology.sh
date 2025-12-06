#!/bin/bash
# scripts/build_ontology.sh

SCHEMA_DIR=".agent/schemas"
OUTPUT_DIR="scripts/ontology"

echo "Building Ontology from Schemas in $SCHEMA_DIR..."

# 1. Plan (Modular, includes Job)
echo "Generating Plan & Job..."
/home/palantir/.venv/bin/datamodel-codegen \
    --input $SCHEMA_DIR/plan.schema.json \
    --output $OUTPUT_DIR \
    --input-file-type jsonschema \
    --output-model-type pydantic.BaseModel \
    --use-schema-description \
    --field-constraints \
    --disable-timestamp \
    --target-python-version 3.10

# 2. Others (Single Files)
for schema in action trace event metric; do
    echo "Generating $schema..."
    /home/palantir/.venv/bin/datamodel-codegen \
        --input $SCHEMA_DIR/$schema.schema.json \
        --output $OUTPUT_DIR/$schema.py \
        --input-file-type jsonschema \
        --output-model-type pydantic.BaseModel \
        --use-schema-description \
        --field-constraints \
        --disable-timestamp \
        --target-python-version 3.10
done

echo "Ontology generation complete."
