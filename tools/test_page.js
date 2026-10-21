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
    if (data.method === 'Runtime.consoleAPICalled') {
      console.log('[BROWSER LOG]', data.params.type, data.params.args.map(a => a.value || a.description).join(' '));
    }
    if (data.method === 'Runtime.exceptionThrown') {
      console.error('[BROWSER ERR]', data.params.exceptionDetails.text, data.params.exceptionDetails.exception?.description);
    }
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

  console.log('Navigating to preview...');
  await page('Page.navigate', { url: 'http://localhost:8765/preview.html?v=' + Date.now() });

  await new Promise(r => setTimeout(r, 2500));

  const evalRes = await page('Runtime.evaluate', { expression: 'document.getElementById("root").innerHTML.length' });
  console.log('Root HTML length:', evalRes.result.value);

  const snap = async (filename) => {
    const { data } = await page('Page.captureScreenshot', { format: 'png' });
    const p = path.join(ARTIFACT_DIR, filename);
    fs.writeFileSync(p, Buffer.from(data, 'base64'));
    console.log('Saved:', p);
  };

  // 1. Initial State
  await snap('01_decision_center_active.png');

  // 2. Open master switch
  await page('Runtime.evaluate', { expression: `document.querySelector('.yg-master-btn').click()` });
  await new Promise(r => setTimeout(r, 500));
  await snap('02_master_switch_dropdown.png');

  // 3. Pause for 5 mins
  await page('Runtime.evaluate', {
    expression: `Array.from(document.querySelectorAll('.yg-master-item')).find(el => el.innerText.includes('5 минут')).click()`
  });
  await new Promise(r => setTimeout(r, 600));
  await snap('03_guard_paused_5min_banner.png');

  // 4. Click 'Включить защиту сейчас'
  await page('Runtime.evaluate', {
    expression: `Array.from(document.querySelectorAll('button')).find(el => el.innerText.includes('Включить защиту сейчас')).click()`
  });
  await new Promise(r => setTimeout(r, 600));
  await snap('04_guard_reactivated.png');

  // 5. Reveal Secret
  await page('Runtime.evaluate', {
    expression: `Array.from(document.querySelectorAll('.yg-breakdown-cell button')).find(el => el.innerText.includes('Показать')).click()`
  });
  await new Promise(r => setTimeout(r, 500));
  await snap('05_secret_revealed_plaintext.png');

  // 6. Click Protect
  await page('Runtime.evaluate', {
    expression: `document.querySelector('.yg-btn-protect').click()`
  });
  await new Promise(r => setTimeout(r, 900));
  await snap('06_scramble_and_vault_protect.png');

  await send('Target.closeTarget', { targetId });
  ws.close();
  console.log('Done!');
}

main().catch(console.error);
