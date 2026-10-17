#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const lab = path.resolve(__dirname, '..');

const cookieJar = new Map([
  ['necessary_session', 'synthetic'],
  ['analytics_id', 'synthetic'],
]);
global.window = { location: { hostname: 'lab.invalid' } };
global.document = {
  querySelectorAll() { return []; },
  get cookie() {
    return [...cookieJar.entries()].map(([name, value]) => `${name}=${value}`).join('; ');
  },
  set cookie(value) {
    const [pair, ...attributes] = value.split(';').map((part) => part.trim());
    const separator = pair.indexOf('=');
    const name = pair.slice(0, separator);
    const cookieValue = pair.slice(separator + 1);
    const deleting = attributes.some((attribute) => attribute.toLowerCase().startsWith('max-age=-'));
    if (deleting) cookieJar.delete(name);
    else cookieJar.set(name, cookieValue);
  },
};

const { default: ConsentManager } = require(path.join(lab, 'artifacts', 'klaro-consent-manager.cjs'));
class MemoryStore {
  constructor() { this.value = null; this.deleted = 0; }
  get() { return this.value; }
  set(value) { this.value = value; }
  delete() { this.value = null; this.deleted += 1; }
}

const events = [];
const store = new MemoryStore();
const auxiliaryStore = new MemoryStore();
const config = {
  storageName: 'o06-consent',
  services: [
    { name: 'necessary', required: true, cookies: ['necessary_session'], callback: (consent) => events.push(['necessary', consent]) },
    { name: 'analytics', default: false, cookies: ['analytics_id'], callback: (consent) => events.push(['analytics', consent]) },
  ],
};
const manager = new ConsentManager(config, store, auxiliaryStore);
if (!manager.getConsent('necessary')) throw new Error('required service was not enabled');
if (manager.getConsent('analytics')) throw new Error('analytics must default denied');
if (cookieJar.has('analytics_id')) throw new Error('denied analytics cookie was not suppressed');
if (!cookieJar.has('necessary_session')) throw new Error('required cookie was incorrectly deleted');

manager.updateConsent('analytics', true);
manager.saveAndApplyConsents('synthetic-accept');
if (!manager.getConsent('analytics') || !manager.confirmed) throw new Error('accept was not persisted');
const saved = JSON.parse(decodeURIComponent(store.value));
if (saved.analytics !== true || saved.necessary !== true) throw new Error('stored consent mismatch');

cookieJar.set('analytics_id', 'synthetic-recreated');
manager.updateConsent('analytics', false);
manager.saveAndApplyConsents('synthetic-withdraw');
if (cookieJar.has('analytics_id')) throw new Error('withdrawal did not suppress analytics cookie');
if (manager.getConsent('analytics')) throw new Error('withdrawal state mismatch');

manager.resetConsents();
if (store.value !== null || store.deleted !== 1) throw new Error('consent deletion/reset failed');

const result = {
  status: 'PASS',
  source: 'repos/klaro/src/consent-manager.js',
  syntheticOrigin: 'lab.invalid',
  defaultDenied: true,
  requiredServicePreserved: true,
  explicitAcceptPersisted: true,
  withdrawalSuppressedCookie: true,
  resetDeletedConsentRecord: true,
  callbackEvents: events,
  networkRequests: 0,
};
fs.writeFileSync(path.join(lab, 'artifacts', 'klaro-consent-smoke.json'), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result));
