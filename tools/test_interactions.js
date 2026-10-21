const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\vades\\.gemini\\antigravity-ide\\brain\\51af84ca-a1bf-41b6-a144-6cce96eb7193';

async function main() {
  const versionRes = await fetch('http://localhost:9222/json/version');
  const { webSocketDebuggerUrl } = await versionRes.json();
  const ws = new WebSocket(webSocketDebuggerUrl);
  let id = 1;
  const pending = new Map();

  function send(method, params = {}, sessionId = undefined) {
    return new Promise((resolve, reject) => {
      const msgId = id++;
      pending.set(msgId, { resolve, reject });
      const payload = { id: msgId, method, params };
      if (sessionId) payload.sessionId = sessionId;
      ws.send(JSON.stringify(payload));
    });
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id && pending.has(data.id)) {
      const { resolve, reject } = pending.get(data.id);
      pending.delete(data.id);
      if (data.error) reject(new Error(data.error.message));
      else resolve(data.result);
    }
  };

  await new Promise(r => ws.onopen = r);

  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  const page = (method, params = {}) => send(method, params, sessionId);

  await page('Page.enable');
  await page('Runtime.enable');
  await page('Emulation.setDeviceMetricsOverride', {
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
    mobile: false
  });

  const snap = async (filename) => {
    const { data } = await page('Page.captureScreenshot', { format: 'png' });
    const p = path.join(ARTIFACT_DIR, filename);
    fs.writeFileSync(p, Buffer.from(data, 'base64'));
    console.log('Saved snapshot:', p);
  };

  // Test 1: Load Initial View with Incident Decision Center
  await page('Page.navigate', { url: 'http://localhost:8765/preview.html?v=' + Date.now() });
  await new Promise(r => setTimeout(r, 2000));
  await snap('01_initial_incident_decision_center.png');

  // Test 2: Reveal plaintext secret
  const revealRes = await page('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelectorAll('.yg-breakdown-cell')[1].querySelector('button');
      if (btn) { btn.click(); return 'clicked'; }
      return 'not found';
    })()`,
    returnByValue: true
  });
  console.log('Reveal button click result:', revealRes.result.value);
  await new Promise(r => setTimeout(r, 500));
  await snap('02_secret_revealed_full_key.png');

  // Test 3: Click Protect & Send
  const protectRes = await page('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelector('.yg-btn-protect');
      if (btn) { btn.click(); return 'clicked'; }
      return 'not found';
    })()`,
    returnByValue: true
  });
  console.log('Protect button click result:', protectRes.result.value);
  await new Promise(r => setTimeout(r, 900));
  await snap('03_scramble_and_vault_protect.png');

  // Test 4: Open Master Switch dropdown
  const masterRes = await page('Runtime.evaluate', {
    expression: `(() => {
      const btn = document.querySelector('.yg-master-btn');
      if (btn) { btn.click(); return 'clicked'; }
      return 'not found';
    })()`,
    returnByValue: true
  });
  console.log('Master switch click result:', masterRes.result.value);
  await new Promise(r => setTimeout(r, 500));
  await snap('04_master_switch_dropdown_open.png');

  // Test 5: Click Pause for 5 minutes
  const pauseRes = await page('Runtime.evaluate', {
    expression: `(() => {
      const items = Array.from(document.querySelectorAll('.yg-master-item'));
      const item = items.find(el => el.innerText.includes('5 минут'));
      if (item) { item.click(); return 'clicked'; }
      return 'not found';
    })()`,
    returnByValue: true
  });
  console.log('Pause 5m click result:', pauseRes.result.value);
  await new Promise(r => setTimeout(r, 600));
  await snap('05_guard_paused_state.png');

  await send('Target.closeTarget', { targetId });
  ws.close();
  console.log('Finished testing interactions!');
}

main().catch(console.error);
