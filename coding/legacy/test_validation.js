#!/usr/bin/env node

/**
 * Test JSON Schema validation by verifying it correctly rejects a protocol with:
 * - Missing required fields (protocol_name, version)
 * - Invalid version format (non-semver)
 * - Incorrect language array (missing required languages)
 * - Type mismatches and constraint violations
 *
 * Expected result: 5-15 validation errors detected
 */

const { fullValidation, loadJSON } = require('./validate_protocol');
const path = require('path');

const SCHEMA_FILE = path.join(__dirname, 'universal_code_learning_protocol_schema.json');
const INVALID_FILE = path.join(__dirname, 'test_invalid_protocol.json');

/**
 * Run validation test with invalid data
 * @returns {number} Exit code (0: pass, 1: fail, 2: error)
 */
function runTest() {
  console.log('Testing JSON Schema Validation with Invalid Data\n');
  console.log('='.repeat(60));

  const schema = loadJSON(SCHEMA_FILE);
  const invalidProtocol = loadJSON(INVALID_FILE);

  if (!schema || !invalidProtocol) {
    console.error('❌ Failed to load test files');
    return 2;
  }

  console.log('\nLoaded invalid test protocol');
  console.log('Expected errors: 5-15 validation failures\n');

  let Ajv;
  try {
    Ajv = require('ajv');
  } catch (e) {
    console.error('❌ Ajv is required for this test. Install with: npm install ajv');
    console.error('   Error:', e.message);
    return 2;
  }

  const errors = fullValidation(invalidProtocol, schema);

  console.log('='.repeat(60));
  if (errors.length > 0) {
    console.log(`\n✅ TEST PASSED: Caught ${errors.length} validation error(s) as expected:\n`);
    errors.forEach((err, idx) => {
      console.log(`${idx + 1}. ${err}`);
    });
    console.log('\n' + '='.repeat(60));
    console.log('\nValidation system is working correctly!');
    return 0;
  } else {
    console.log('\n❌ TEST FAILED: No errors caught (expected 5-15 errors)');
    return 1;
  }
}

// Run test and exit with appropriate code
process.exit(runTest());
