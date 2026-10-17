var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __export = (target, all) => {
  for (var name in all)
    __defProp(target, name, { get: all[name], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// repos/klaro/src/consent-manager.js
var consent_manager_exports = {};
__export(consent_manager_exports, {
  default: () => ConsentManager
});
module.exports = __toCommonJS(consent_manager_exports);

// repos/klaro/src/utils/cookies.js
function getCookies() {
  const cookieStrings = document.cookie.split(";");
  const cookies = [];
  const regex = new RegExp("^\\s*([^=]+)\\s*=\\s*(.*?)$");
  for (let i = 0; i < cookieStrings.length; i++) {
    const cookieStr = cookieStrings[i];
    const match = regex.exec(cookieStr);
    if (match === null) continue;
    cookies.push({
      name: match[1],
      value: match[2]
    });
  }
  return cookies;
}
function getCookie(name) {
  const cookies = getCookies();
  for (let i = 0; i < cookies.length; i++) {
    if (cookies[i].name === name) return cookies[i];
  }
  return null;
}
function setCookie(name, value, days, domain, path) {
  let expires = "";
  if (days) {
    const date = /* @__PURE__ */ new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1e3);
    expires = "; expires=" + date.toUTCString();
  }
  if (domain !== void 0) {
    expires += "; domain=" + domain;
  }
  if (path !== void 0) {
    expires += "; path=" + path;
  } else {
    expires += "; path=/";
  }
  document.cookie = name + "=" + (value || "") + expires + "; SameSite=Lax";
}
function deleteCookie(name, path, domain) {
  let str = name + "=; Max-Age=-99999999;";
  document.cookie = str;
  str += " path=" + (path || "/") + ";";
  document.cookie = str;
  if (domain !== void 0) {
    str += " domain=" + domain + ";";
    document.cookie = str;
  }
}

// repos/klaro/src/utils/compat.js
function dataset(element) {
  const dataset2 = {};
  for (let i = 0; i < element.attributes.length; i++) {
    const attribute = element.attributes[i];
    if (attribute.name.startsWith("data-")) {
      dataset2[attribute.name.slice(5)] = attribute.value;
    }
  }
  return dataset2;
}
function applyDataset(ds, element) {
  const keys = Object.keys(ds);
  for (let i = 0; i < keys.length; i++) {
    const key = keys[i];
    const value = ds[key];
    if (element[key] === value) continue;
    else element.setAttribute("data-" + key, value);
  }
}

// repos/klaro/src/stores.js
var TestStore = class {
  constructor() {
    this.value = null;
  }
  get() {
    return this.value;
  }
  set(value) {
    this.value = value;
  }
  delete() {
    this.value = null;
  }
};
var CookieStore = class {
  constructor(manager) {
    this.cookieName = manager.storageName;
    this.cookieDomain = manager.cookieDomain;
    this.cookiePath = manager.cookiePath;
    this.cookieExpiresAfterDays = manager.cookieExpiresAfterDays;
  }
  get() {
    const cookie = getCookie(this.cookieName);
    return cookie ? cookie.value : null;
  }
  set(value) {
    return setCookie(this.cookieName, value, this.cookieExpiresAfterDays, this.cookieDomain, this.cookiePath);
  }
  delete() {
    return deleteCookie(this.cookieName);
  }
};
var StorageStore = class {
  constructor(manager, handle) {
    this.key = manager.storageName;
    this.handle = handle;
  }
  get() {
    return this.handle.getItem(this.key);
  }
  getWithKey(key) {
    return this.handle.getItem(key);
  }
  set(value) {
    return this.handle.setItem(this.key, value);
  }
  setWithKey(key, value) {
    return this.handle.setItem(key, value);
  }
  delete() {
    return this.handle.removeItem(this.key);
  }
  deleteWithKey(key) {
    return this.handle.removeItem(key);
  }
};
var LocalStorageStore = class extends StorageStore {
  constructor(manager) {
    super(manager, localStorage);
  }
};
var SessionStorageStore = class extends StorageStore {
  constructor(manager) {
    super(manager, sessionStorage);
  }
};
var stores = {
  "cookie": CookieStore,
  "test": TestStore,
  "localStorage": LocalStorageStore,
  "sessionStorage": SessionStorageStore
};
var stores_default = stores;

// repos/klaro/src/consent-manager.js
var ConsentManager = class {
  constructor(config, store, auxiliaryStore) {
    this.config = config;
    if (store !== void 0)
      this.store = store;
    else
      this.store = new stores_default[this.storageMethod](this);
    if (this.store === void 0)
      this.store = stores_default["cookie"];
    if (auxiliaryStore !== void 0)
      this.auxiliaryStore = auxiliaryStore;
    else
      this.auxiliaryStore = new SessionStorageStore(this);
    this.consents = this.defaultConsents;
    this.confirmed = false;
    this.changed = false;
    this.states = {};
    this.initialized = {};
    this.executedOnce = {};
    this.watchers = /* @__PURE__ */ new Set([]);
    this.loadConsents();
    this.applyConsents();
    this.savedConsents = { ...this.consents };
  }
  get storageMethod() {
    return this.config.storageMethod || "cookie";
  }
  get storageName() {
    return this.config.storageName || this.config.cookieName || "klaro";
  }
  get cookieDomain() {
    return this.config.cookieDomain || void 0;
  }
  get cookiePath() {
    return this.config.cookiePath || void 0;
  }
  get cookieExpiresAfterDays() {
    return this.config.cookieExpiresAfterDays || 120;
  }
  get defaultConsents() {
    const consents = {};
    for (let i = 0; i < this.config.services.length; i++) {
      const service = this.config.services[i];
      consents[service.name] = this.getDefaultConsent(service);
    }
    return consents;
  }
  watch(watcher) {
    if (!this.watchers.has(watcher))
      this.watchers.add(watcher);
  }
  unwatch(watcher) {
    if (this.watchers.has(watcher))
      this.watchers.delete(watcher);
  }
  notify(name, data) {
    this.watchers.forEach((watcher) => {
      watcher.update(this, name, data);
    });
  }
  getService(name) {
    const matchingServices = this.config.services.filter((service) => service.name === name);
    if (matchingServices.length > 0)
      return matchingServices[0];
    return void 0;
  }
  getDefaultConsent(service) {
    let consent = service.default || service.required;
    if (consent === void 0)
      consent = this.config.default;
    if (consent === void 0)
      consent = false;
    return consent;
  }
  changeAll(value) {
    let changedServices = 0;
    this.config.services.filter((service) => !service.contextualConsentOnly).map((service) => {
      if (service.required || this.config.required || value) {
        if (this.updateConsent(service.name, true))
          changedServices++;
      } else {
        if (this.updateConsent(service.name, false))
          changedServices++;
      }
    });
    return changedServices;
  }
  updateConsent(name, value) {
    const changed = (this.consents[name] || false) !== value;
    this.consents[name] = value;
    this.notify("consents", this.consents);
    return changed;
  }
  resetConsents() {
    this.consents = this.defaultConsents;
    this.states = {};
    this.confirmed = false;
    this.applyConsents();
    this.savedConsents = { ...this.consents };
    this.store.delete();
    this.notify("consents", this.consents);
  }
  getConsent(name) {
    return this.consents[name] || false;
  }
  loadConsents() {
    const consentData = this.store.get();
    if (consentData !== null) {
      this.consents = JSON.parse(decodeURIComponent(consentData));
      this._checkConsents();
      this.notify("consents", this.consents);
    }
    return this.consents;
  }
  saveAndApplyConsents(eventType) {
    this.saveConsents(eventType);
    this.applyConsents();
  }
  changedConsents() {
    const cc = {};
    for (const [k, v] of Object.entries(this.consents)) {
      if (this.savedConsents[k] !== v)
        cc[k] = v;
    }
    return cc;
  }
  saveConsents(eventType) {
    const v = encodeURIComponent(JSON.stringify(this.consents));
    this.store.set(v);
    this.confirmed = true;
    this.changed = false;
    const changes = this.changedConsents();
    this.savedConsents = { ...this.consents };
    this.notify("saveConsents", { changes, consents: this.consents, type: eventType || "script" });
  }
  applyConsents(dryRun, interactive, serviceName) {
    function executeHandler(handler, opts) {
      if (handler === void 0)
        return;
      let handlerFunction;
      if (typeof handler === "function") {
        handlerFunction = handler;
      } else {
        handlerFunction = new Function("opts", handler);
      }
      return handlerFunction(opts);
    }
    let changedServices = 0;
    for (let i = 0; i < this.config.services.length; i++) {
      const service = this.config.services[i];
      if (serviceName !== void 0 && serviceName !== service.name)
        continue;
      const vars = service.vars || {};
      const handlerOpts = { service, config: this.config, vars };
      if (!this.initialized[service.name]) {
        this.initialized[service.name] = true;
        executeHandler(service.onInit, handlerOpts);
      }
    }
    for (let i = 0; i < this.config.services.length; i++) {
      const service = this.config.services[i];
      if (serviceName !== void 0 && serviceName !== service.name)
        continue;
      const state = this.states[service.name];
      const vars = service.vars || {};
      const optOut = service.optOut !== void 0 ? service.optOut : this.config.optOut || false;
      const required = service.required !== void 0 ? service.required : this.config.required || false;
      const confirmed = this.confirmed || optOut || dryRun || interactive;
      const consent = this.getConsent(service.name) && confirmed || required;
      const handlerOpts = { service, config: this.config, vars, consents: this.consents, confirmed: this.confirmed };
      if (state !== consent)
        changedServices++;
      if (dryRun)
        continue;
      executeHandler(consent ? service.onAccept : service.onDecline, handlerOpts);
      this.updateServiceElements(service, consent);
      this.updateServiceStorage(service, consent);
      if (service.callback !== void 0)
        service.callback(consent, service);
      if (this.config.callback !== void 0)
        this.config.callback(consent, service);
      this.states[service.name] = consent;
    }
    this.notify("applyConsents", changedServices, serviceName);
    return changedServices;
  }
  updateServiceElements(service, consent) {
    if (consent) {
      if (service.onlyOnce && this.executedOnce[service.name])
        return;
      this.executedOnce[service.name] = true;
    }
    const elements = document.querySelectorAll("[data-name='" + service.name + "']");
    for (let i = 0; i < elements.length; i++) {
      const element = elements[i];
      const parent = element.parentElement;
      const ds = dataset(element);
      const { type, src, href } = ds;
      const attrs = ["href", "src", "type"];
      if (type === "placeholder") {
        if (consent) {
          element.style.display = "none";
          ds["original-display"] = element.style.display;
        } else {
          element.style.display = ds["original-display"] || "block";
        }
        continue;
      }
      if (element.tagName === "IFRAME") {
        if (consent && element.src === src) {
          console.debug(`Skipping ${element.tagName} for service ${service.name}, as it already has the correct type...`);
          continue;
        }
        const newElement = document.createElement(element.tagName);
        for (const attribute of element.attributes) {
          if (attribute.name === "style") {
            const [styleProperty, styleValue] = attribute.value.split(":");
            newElement.style[styleProperty.trim()] = styleValue.trim();
          } else {
            newElement.setAttribute(attribute.name, attribute.value);
          }
        }
        newElement.innerText = element.innerText;
        newElement.text = element.text;
        if (consent) {
          if (ds["original-display"] !== void 0)
            newElement.style.display = ds["original-display"];
          if (ds.src !== void 0)
            newElement.src = ds.src;
        } else {
          newElement.src = "";
          if (ds["modified-by-klaro"] !== void 0 && ds["original-display"] !== void 0)
            newElement.setAttribute("data-original-display", ds["original-display"]);
          else {
            if (element.style.display !== void 0)
              newElement.setAttribute("data-original-display", element.style.display);
            newElement.setAttribute("data-modified-by-klaro", "yes");
          }
          newElement.style.display = "none";
        }
        parent.insertBefore(newElement, element);
        parent.removeChild(element);
      } else if (element.tagName === "SCRIPT" || element.tagName === "LINK") {
        if (consent && element.type === (type || "") && element.src === src) {
          console.debug(`Skipping ${element.tagName} for service ${service.name}, as it already has the correct type or src...`);
          continue;
        }
        const newElement = document.createElement(element.tagName);
        for (const attribute of element.attributes) {
          newElement.setAttribute(attribute.name, attribute.value);
        }
        if (element.hasAttribute("nonce")) {
          newElement.setAttribute("nonce", element.nonce);
        }
        newElement.innerText = element.innerText;
        newElement.text = element.text;
        if (consent) {
          newElement.type = type || "";
          if (src !== void 0)
            newElement.src = src;
          if (href !== void 0)
            newElement.href = href;
        } else {
          newElement.type = "text/plain";
        }
        parent.insertBefore(newElement, element);
        parent.removeChild(element);
      } else {
        if (consent) {
          for (const attr of attrs) {
            const attrValue = ds[attr];
            if (attrValue === void 0)
              continue;
            if (ds["original-" + attr] === void 0)
              ds["original-" + attr] = element[attr];
            element[attr] = attrValue;
          }
          if (ds.title !== void 0)
            element.title = ds.title;
          if (ds["original-display"] !== void 0) {
            element.style.display = ds["original-display"];
          } else {
            element.style.removeProperty("display");
          }
        } else {
          if (ds.title !== void 0)
            element.removeAttribute("title");
          if (ds["original-display"] === void 0 && element.style.display !== void 0)
            ds["original-display"] = element.style.display;
          element.style.display = "none";
          for (const attr of attrs) {
            const attrValue = ds[attr];
            if (attrValue === void 0)
              continue;
            if (ds["original-" + attr] !== void 0)
              element[attr] = ds["original-" + attr];
            else
              element.removeAttribute(attr);
          }
        }
        applyDataset(ds, element);
      }
    }
  }
  updateServiceStorage(service, consent) {
    if (consent)
      return;
    function escapeRegexStr(str) {
      return str.replace(/[-[\]/{}()*+?.\\^$|]/g, "\\$&");
    }
    if (service.cookies !== void 0 && service.cookies.length > 0) {
      const cookies = getCookies();
      for (let i = 0; i < service.cookies.length; i++) {
        let cookiePattern = service.cookies[i];
        let cookiePath, cookieDomain;
        if (cookiePattern instanceof Array) {
          [cookiePattern, cookiePath, cookieDomain] = cookiePattern;
        } else if (cookiePattern instanceof Object && !(cookiePattern instanceof RegExp)) {
          const cp = cookiePattern;
          cookiePattern = cp.pattern;
          cookiePath = cp.path;
          cookieDomain = cp.domain;
        }
        if (cookiePattern === void 0)
          continue;
        if (!(cookiePattern instanceof RegExp)) {
          if (cookiePattern.startsWith("^"))
            cookiePattern = new RegExp(cookiePattern);
          else
            cookiePattern = new RegExp("^" + escapeRegexStr(cookiePattern) + "$");
        }
        for (let j = 0; j < cookies.length; j++) {
          const cookie = cookies[j];
          const match = cookiePattern.exec(cookie.name);
          if (match !== null) {
            console.debug(
              "Deleting cookie:",
              cookie.name,
              "Matched pattern:",
              cookiePattern,
              "Path:",
              cookiePath,
              "Domain:",
              cookieDomain
            );
            deleteCookie(cookie.name, cookiePath, cookieDomain);
            if (cookieDomain === void 0)
              deleteCookie(cookie.name, cookiePath, "." + window.location.hostname);
          }
        }
      }
    }
  }
  _checkConsents() {
    let complete = true;
    const services = new Set(this.config.services.map((service) => {
      return service.name;
    }));
    const consents = new Set(Object.keys(this.consents));
    for (const key of Object.keys(this.consents)) {
      if (!services.has(key)) {
        delete this.consents[key];
      }
    }
    for (const service of this.config.services) {
      if (!consents.has(service.name)) {
        this.consents[service.name] = this.getDefaultConsent(service);
        complete = false;
      }
    }
    this.confirmed = complete;
    if (!complete)
      this.changed = true;
  }
};
