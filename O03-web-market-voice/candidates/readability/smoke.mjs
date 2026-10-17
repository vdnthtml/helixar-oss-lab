import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';
import { Readability } from '@mozilla/readability';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../..');
const html = fs.readFileSync(path.join(root, 'fixtures/web/index.html'), 'utf8');

function extract() {
  const dom = new JSDOM(html, { url: 'https://authority-fixture.invalid/article' });
  const result = new Readability(dom.window.document.cloneNode(true)).parse();
  if (!result) throw new Error('Readability returned null');
  return {
    title: result.title,
    byline: result.byline,
    dir: result.dir,
    lang: result.lang,
    textContent: result.textContent.replace(/\s+/g, ' ').trim(),
    length: result.length,
  };
}

const a = extract();
const b = extract();
const canonA = JSON.stringify(a);
const canonB = JSON.stringify(b);
const hash = crypto.createHash('sha256').update(canonA).digest('hex');
const assertions = {
  exact_repeat_equal: canonA === canonB,
  title_expected: a.title === 'O03 Synthetic Authority Fixture',
  synthetic_sentence_present: a.textContent.includes('Acme Signal reports a synthetic launch'),
  external_link_text_absent: !a.textContent.includes('About'),
};
const summary = {
  candidate: 'Mozilla Readability',
  version: '0.6.0-source-commit-ab4027a8b37669745016869a37a504727992b2ba',
  output_sha256: hash,
  assertions,
  extracted: a,
  pass: Object.values(assertions).every(Boolean),
};
fs.mkdirSync(path.join(root, 'artifacts/readability'), { recursive: true });
fs.writeFileSync(path.join(root, 'artifacts/readability/summary.json'), JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify(summary, null, 2));
if (!summary.pass) process.exit(2);
