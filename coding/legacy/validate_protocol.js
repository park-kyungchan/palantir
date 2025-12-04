#!/usr/bin/env node

/**
 * Universal Code Learning Protocol - JSON Schema Validator
 *
 * Usage:
 *   node validate_protocol.js
 *   npm run validate (if package.json configured)
 *
 * Exit codes:
 *   0: Validation passed
 *   1: Validation failed
 *   2: File read error
 */

const fs = require('fs');
const path = require('path');

// Try to use Ajv if available, otherwise fallback to basic validation
let Ajv;
try {
  Ajv = require('ajv');
} catch (e) {
  console.error('Warning: ajv not installed. Install with: npm install ajv ajv-formats');
  console.error('Falling back to basic JSON parsing validation only.\n');
}

const PROTOCOL_FILE = path.join(__dirname, 'universal_code_learning_protocol_v2.json');
const SCHEMA_FILE = path.join(__dirname, 'universal_code_learning_protocol_schema.json');

/**
 * Load and parse JSON file
 */
function loadJSON(filepath) {
  try {
    const content = fs.readFileSync(filepath, 'utf8');
    return JSON.parse(content);
  } catch (error) {
    console.error(`Error reading ${filepath}:`, error.message);
    process.exit(2);
  }
}

/**
 * Basic validation without Ajv
 */
function basicValidation(protocol) {
  const errors = [];

  // Check required top-level fields
  const requiredFields = [
    'protocol_name',
    'version',
    'description',
    'target_llms',
    'languages',
    'sections',
    'usage_instructions',
    'authoritative_sources'
  ];

  requiredFields.forEach(field => {
    if (!(field in protocol)) {
      errors.push(`Missing required field: ${field}`);
    }
  });

  // Check version format
  if (protocol.version && !/^\d+\.\d+\.\d+$/.test(protocol.version)) {
    errors.push(`Invalid version format: ${protocol.version} (expected semver like 1.0.0)`);
  }

  // Check languages array
  if (protocol.languages) {
    const validLangs = ['go', 'python', 'swift'];
    const hasAllLangs = validLangs.every(lang => protocol.languages.includes(lang));
    if (!hasAllLangs || protocol.languages.length !== 3) {
      errors.push(`languages must be exactly ["go", "python", "swift"]`);
    }
  }

  // Check sections exist
  if (protocol.sections) {
    const requiredSections = ['core_philosophy', 'response_structure', 'comparison_framework', 'dynamic_context'];
    requiredSections.forEach(section => {
      if (!(section in protocol.sections)) {
        errors.push(`Missing required section: sections.${section}`);
      }
    });
  }

  return errors;
}

/**
 * Full validation with Ajv
 */
function fullValidation(protocol, schema) {
  const ajv = new Ajv({
    allErrors: true,
    verbose: true,
    strict: false
  });

  // Add formats if ajv-formats is available
  try {
    const addFormats = require('ajv-formats');
    addFormats(ajv);
  } catch (e) {
    console.warn('ajv-formats not found, URI format validation may be limited');
  }

  const validate = ajv.compile(schema);
  const valid = validate(protocol);

  if (!valid) {
    return validate.errors.map(err => {
      const path = err.instancePath || 'root';
      const message = err.message;
      const params = JSON.stringify(err.params);
      return `${path}: ${message} ${params}`;
    });
  }

  return [];
}

/**
 * Main validation logic
 */
function main() {
  console.log('Universal Code Learning Protocol - Schema Validation\n');
  console.log('='.repeat(60));

  // Load files
  console.log(`\nLoading protocol: ${PROTOCOL_FILE}`);
  const protocol = loadJSON(PROTOCOL_FILE);
  console.log('✓ Protocol JSON parsed successfully');

  console.log(`\nLoading schema: ${SCHEMA_FILE}`);
  const schema = loadJSON(SCHEMA_FILE);
  console.log('✓ Schema JSON parsed successfully');

  // Validate
  console.log('\n' + '='.repeat(60));
  console.log('Running validation...\n');

  let errors;
  if (Ajv) {
    console.log('Using Ajv for full JSON Schema validation');
    errors = fullValidation(protocol, schema);
  } else {
    console.log('Using basic validation (install ajv for full validation)');
    errors = basicValidation(protocol);
  }

  // Report results
  console.log('\n' + '='.repeat(60));
  if (errors.length === 0) {
    console.log('\n✅ VALIDATION PASSED');
    console.log(`\nProtocol: ${protocol.protocol_name}`);
    console.log(`Version: ${protocol.version}`);
    const languages = protocol.languages_metadata ? Object.keys(protocol.languages_metadata) : protocol.languages;
    console.log(`Languages: ${languages.join(', ')}`);
    const targetLLMs = protocol.metadata?.target_llms || protocol.target_llms || [];
    console.log(`Target LLMs: ${targetLLMs.join(', ')}`);

    // Summary statistics
    const stats = {
      concept_categories: protocol.sections.comparison_framework.concept_categories.length,
      total_concepts: protocol.sections.comparison_framework.concept_categories
        .reduce((sum, cat) => sum + cat.concepts.length, 0),
      comparison_axes: protocol.sections.comparison_framework.comparison_axes.length,
      required_sections: protocol.sections.response_structure.template.required_sections.length,
      optional_sections: protocol.sections.response_structure.template.optional_sections.length
    };

    console.log('\nProtocol Statistics:');
    console.log(`  - Concept categories: ${stats.concept_categories}`);
    console.log(`  - Total concepts: ${stats.total_concepts}`);
    console.log(`  - Comparison axes: ${stats.comparison_axes}`);
    console.log(`  - Required response sections: ${stats.required_sections}`);
    console.log(`  - Optional response sections: ${stats.optional_sections}`);

    process.exit(0);
  } else {
    console.log('\n❌ VALIDATION FAILED');
    console.log(`\nFound ${errors.length} error(s):\n`);
    errors.forEach((err, idx) => {
      console.log(`${idx + 1}. ${err}`);
    });
    console.log('\n' + '='.repeat(60));
    process.exit(1);
  }
}

// Run validation
if (require.main === module) {
  main();
}

module.exports = { basicValidation, fullValidation, loadJSON };
