#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const Ajv = require('ajv');
const addFormats = require('ajv-formats');

const SCHEMA_FILE = path.join(__dirname, 'uclp-languages.schema.json');

function loadJSON(filepath) {
  try {
    return JSON.parse(fs.readFileSync(filepath, 'utf8'));
  } catch (error) {
    console.error(`Error reading ${filepath}: ${error.message}`);
    process.exit(2);
  }
}

function validate(dataFile) {
  const schema = loadJSON(SCHEMA_FILE);
  const data = loadJSON(dataFile);

  const ajv = new Ajv({ allErrors: true });
  addFormats(ajv);

  const validateFn = ajv.compile(schema);
  const valid = validateFn(data);

  if (!valid) {
    console.error(`
❌ Validation Failed for ${path.basename(dataFile)}:`);
    validateFn.errors.forEach(err => {
      console.error(`  - ${err.instancePath} ${err.message}`);
    });
    process.exit(1);
  } else {
    console.log(`
✅ Validation Passed: ${path.basename(dataFile)} matches UCLP v3.0.0 Schema.`);
  }
}

if (process.argv.length < 3) {
  console.log('Usage: node validate.js <json_file>');
  process.exit(1);
}

validate(process.argv[2]);
