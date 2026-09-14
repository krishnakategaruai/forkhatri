// Minimal Chrome DevTools Protocol driver for manual-style testing when the
// shared DevTools MCP browser is held by another session. Usage:
//   node scripts/cdp.mjs <scenario.mjs>   (scenario exports default async (page) => {...})
// page API: goto(url), eval(fn|string), click(selector), type(selector, text),
//           waitFor(selector|text, ms), shot(path), text(), setStorage(k,v), console()

import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';

const PORT = process.env.CDP_PORT ?? '9333';

async function json(url) { const r = await fetch(url); return r.json(); }

export async function connect() {
  const targets = await json(`http://127.0.0.1:${PORT}/json/list`);
  let t = targets.find((x) => x.type === 'page');
  if (!t) t = await json(`http://127.0.0.1:${PORT}/json/new?about:blank`);
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  let id = 0; const pending = new Map(); const events = [];
  const netFailures = []; const reqUrls = new Map();
  ws.onmessage = (m) => {
    const msg = JSON.parse(m.data);
    if (msg.id && pending.has(msg.id)) { const { res, rej } = pending.get(msg.id); pending.delete(msg.id); msg.error ? rej(new Error(msg.error.message)) : res(msg.result); }
    else if (msg.method) {
      events.push(msg);
      if (msg.method === 'Network.requestWillBeSent') reqUrls.set(msg.params.requestId, msg.params.request.url);
      if (msg.method === 'Network.responseReceived' && msg.params.response.status >= 400) netFailures.push(`${msg.params.response.status} ${msg.params.response.url}`);
      if (msg.method === 'Network.loadingFailed' && !msg.params.canceled) netFailures.push(`FAILED ${msg.params.errorText} ${reqUrls.get(msg.params.requestId) ?? ''}`);
    }
  };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
  await send('Page.enable'); await send('Runtime.enable'); await send('Log.enable');
  // CDP_VIEWPORT=1440x900 switches to a desktop viewport (mouse, no touch); default is a phone.
  const vp = (process.env.CDP_VIEWPORT ?? '412x915').split('x').map(Number);
  const mobile = vp[0] < 800;
  await send('Emulation.setDeviceMetricsOverride', { width: vp[0], height: vp[1], deviceScaleFactor: mobile ? 2 : 1, mobile });
  await send('Emulation.setTouchEmulationEnabled', { enabled: mobile });
  // Network failures (4xx/5xx and load errors) are as important as console errors for "does it actually work".
  await send('Network.enable');
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const evalIn = async (expr) => {
    const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description ?? 'eval failed');
    return r.result.value;
  };
  const page = {
    send, events,
    async goto(url) { await send('Page.navigate', { url }); await sleep(1200); await page.waitFor('body', 8000); },
    async eval(fn) { return evalIn(typeof fn === 'function' ? `(${fn.toString()})()` : fn); },
    async click(sel) { const ok = await evalIn(`(() => { const el = document.querySelector(${JSON.stringify(sel)}); if (!el) return false; el.scrollIntoView({block:'center'}); el.click(); return true; })()`); if (!ok) throw new Error(`click: not found ${sel}`); await sleep(400); },
    async clickText(text, tag = '*') { const ok = await evalIn(`(() => { const els = [...document.querySelectorAll(${JSON.stringify(tag)})]; const norm = (s) => s.replace(/\\s+/g, ' ').trim(); const T = ${JSON.stringify(text)}; const cand = els.filter(e => (e.tagName==='BUTTON'||e.tagName==='A'||e.getAttribute('role')==='button'||e.children.length===0) && e.offsetParent !== null && norm(e.textContent).includes(T) && norm(e.textContent).length < T.length + 60); const strip = (s) => s.replace(/^[^A-Za-z0-9]+/, ''); const el = cand.find(e => norm(e.textContent) === T) || cand.find(e => strip(norm(e.textContent)) === T) || cand.find(e => strip(norm(e.textContent)).startsWith(T)) || cand[0]; if (!el) return false; el.scrollIntoView({block:'center'}); el.click(); return true; })()`); if (!ok) throw new Error(`clickText: not found ${text}`); await sleep(400); },
    async type(sel, text) { const ok = await evalIn(`(() => { const el = document.querySelector(${JSON.stringify(sel)}); if (!el) return false; el.focus(); const setter = Object.getOwnPropertyDescriptor(el.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,'value').set; setter.call(el, ${JSON.stringify(text)}); el.dispatchEvent(new Event('input',{bubbles:true})); return true; })()`); if (!ok) throw new Error(`type: not found ${sel}`); await sleep(200); },
    async select(sel, value) { const ok = await evalIn(`(() => { const el = typeof ${JSON.stringify(sel)} === 'number' ? document.querySelectorAll('select')[${JSON.stringify(sel)}] : document.querySelector(${JSON.stringify(sel)}); if (!el) return false; const setter = Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype,'value').set; setter.call(el, ${JSON.stringify(value)}); el.dispatchEvent(new Event('change',{bubbles:true})); return true; })()`); if (!ok) throw new Error(`select: not found ${sel}`); await sleep(200); },
    async waitFor(what, ms = 6000) { const t0 = Date.now(); while (Date.now() - t0 < ms) { const ok = await evalIn(`(() => { try { if (document.querySelector(${JSON.stringify(what)})) return true; } catch {} return document.body && document.body.innerText.toLowerCase().includes(${JSON.stringify(what)}.toLowerCase()); })()`); if (ok) return true; await sleep(200); } throw new Error(`waitFor timeout: ${what}`); },
    async text() { return evalIn('document.body.innerText'); },
    async shot(path) { const r = await send('Page.captureScreenshot', { format: 'png' }); const { writeFile } = await import('node:fs/promises'); await writeFile(path, Buffer.from(r.data, 'base64')); return path; },
    async setStorage(k, v) { return evalIn(`localStorage.setItem(${JSON.stringify(k)}, ${JSON.stringify(v)})`); },
    netFailures() { return [...netFailures]; },
    clearFailures() { netFailures.length = 0; },
    consoleErrors() { return events.filter((e) => (e.method === 'Runtime.exceptionThrown') || (e.method === 'Log.entryAdded' && e.params.entry.level === 'error') || (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error')).map((e) => e.method === 'Runtime.exceptionThrown' ? e.params.exceptionDetails.exception?.description ?? e.params.exceptionDetails.text : e.method === 'Log.entryAdded' ? e.params.entry.text : e.params.args.map((a) => a.value ?? a.description).join(' ')); },
    sleep,
    close() { ws.close(); },
  };
  return page;
}

if (process.argv[1] && process.argv[1].endsWith('cdp.mjs') && process.argv[2]) {
  const mod = await import(pathToFileURL(process.argv[2]).href);
  const page = await connect();
  try { await mod.default(page); } finally { page.close(); }
}
