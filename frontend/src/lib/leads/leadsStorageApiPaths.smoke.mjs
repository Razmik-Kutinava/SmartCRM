/** Smoke: URL путей coverage/managers в leadsStorage (без двойного /leads). */

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import assert from 'node:assert/strict';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..', '..');
const src = readFileSync(join(root, 'src', 'lib', 'leadsStorage.js'), 'utf8');

test('fetchLeadCoverage uses /api/leads/coverage not /leads/leads/coverage', () => {
	assert.match(src, /\$\{API\(\)\}\/coverage/);
	assert.doesNotMatch(src, /\$\{API\(\)\}\/leads\/coverage/);
});

test('fetchLeadManagers uses /api/leads/managers not /leads/leads/managers', () => {
	assert.match(src, /\$\{API\(\)\}\/managers/);
	assert.doesNotMatch(src, /\$\{API\(\)\}\/leads\/managers/);
});
