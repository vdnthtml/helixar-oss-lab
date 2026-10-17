#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const lab = path.resolve(__dirname, '..');
const repo = path.join(lab, 'repos', 'opencats');
const pipelineSource = fs.readFileSync(path.join(repo, 'js', 'pipeline.js'), 'utf8');
const pipelinePhp = fs.readFileSync(path.join(repo, 'ajax', 'getPipelineJobOrder.php'), 'utf8');
const schema = fs.readFileSync(path.join(repo, 'db', 'cats_schema.sql'), 'utf8');

const checkboxes = [
  { value: 'candidate-101', checked: true },
  { value: 'candidate-102', checked: false },
  { value: 'candidate-103', checked: true },
];
const sandbox = {
  document: {
    getElementsByName(name) {
      if (name !== 'checked') throw new Error(`unexpected element name: ${name}`);
      return checkboxes;
    },
  },
};
vm.createContext(sandbox);
vm.runInContext(pipelineSource, sandbox, { filename: 'OpenCATS/js/pipeline.js' });

const selected = Array.from(sandbox.getSelected_candidates());
if (JSON.stringify(selected) !== JSON.stringify(['candidate-101', 'candidate-103'])) {
  throw new Error(`selected-candidate export mismatch: ${JSON.stringify(selected)}`);
}
sandbox.selectAll_candidates({ checked: true });
if (!checkboxes.every((item) => item.checked)) throw new Error('select-all failed');

const requiredPermissionGuards = [
  "getAccessLevel('pipelines.changeStatus') >= ACCESS_LEVEL_EDIT",
  "getAccessLevel('pipelines.removeFromPipeline') >= ACCESS_LEVEL_DELETE",
];
for (const guard of requiredPermissionGuards) {
  if (!pipelinePhp.includes(guard)) throw new Error(`missing human permission guard: ${guard}`);
}

const statusMatches = [...schema.matchAll(/VALUES \((\d+), '([^']+)',/g)].map((match) => ({
  id: Number(match[1]),
  name: match[2],
}));
const statusNames = new Set(statusMatches.map((status) => status.name));
for (const required of ['No Contact', 'Contacted', 'Interviewing', 'Offered', 'Placed']) {
  if (!statusNames.has(required)) throw new Error(`missing ATS status: ${required}`);
}
if (!schema.includes('candidate_joborder_status_history')) {
  throw new Error('missing status history table');
}

const result = {
  status: 'PASS',
  executedSource: 'repos/opencats/js/pipeline.js',
  selectedCandidateIds: selected,
  humanOwnedStateGuards: requiredPermissionGuards,
  hiringStatesVerified: ['No Contact', 'Contacted', 'Interviewing', 'Offered', 'Placed'],
  statusHistorySchemaVerified: true,
  serviceStarted: false,
  limitation: 'PHP 8.4.1 and database runtime unavailable; source/UI/schema component smoke only',
};
fs.writeFileSync(path.join(lab, 'artifacts', 'opencats-source-smoke.json'), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result));
