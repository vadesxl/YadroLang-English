const fs = require('fs');
const path = require('path');

const ARTIFACT_DIR = 'C:\\Users\\vades\\.gemini\\antigravity-ide\\brain\\51af84ca-a1bf-41b6-a144-6cce96eb7193';

async function main() {
  const versionRes = await fetch('http://localhost:9222/json/version');
  const versionData = await versionRes.json();
  const browserWsUrl = versionData.webSocketDebuggerUrl;
  console.log('Connecting to Chrome CDP:', browserWsUrl);

  const ws = new WebSocket(browserWsUrl);
  let id = 1;
  const pending = new Map();

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const msgId = id++;
      pending.set(msgId, { resolve, reject });
      ws.send(JSON.stringify({ id: msgId, method, params }));
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

  // Create page
  const { targetId } = await send('Target.createTarget', { url: 'http://localhost:8765/preview.html?v=20261020_0200' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });

  function sendPage(method, params = {}) {
    return new Promise((resolve, reject) => {
      const msgId = id++;
      pending.set(msgId, { resolve, reject });
      ws.send(JSON.stringify({ id: msgId, sessionId, method, params }));
    });
  }

  await sendPage('Emulation.setDeviceMetricsOverride', {
    width: 1920,
    height: 1080,
    deviceScaleFactor: 1,
    mobile: false
  });

  await sendPage('Page.enable');
  await sendPage('Runtime.enable');

  console.log('Waiting for page render...');
  await new Promise(r => setTimeout(r, 2000));

  async function takeSnap(name) {
    const { data } = await sendPage('Page.captureScreenshot', { format: 'png' });
    const filePath = path.join(ARTIFACT_DIR, name);
    fs.writeFileSync(filePath, Buffer.from(data, 'base64'));
    console.log('Saved snapshot:', filePath);
  }

  // 1. Initial State: Decision Center + Master Switch (Fail-Closed Active)
  await takeSnap('01_decision_center_active.png');

  // 2. Open Master Switch dropdown
  await sendPage('Runtime.evaluate', {
    expression: `document.querySelector('.yg-master-btn').click()`
  });
  await new Promise(r => setTimeout(r, 500));
  await takeSnap('02_master_switch_dropdown.png');

  // 3. Click 'Приостановить на 5 минут'
  await sendPage('Runtime.evaluate', {
    expression: `Array.from(document.querySelectorAll('.yg-master-item')).find(el => el.innerText.includes('5 минут')).click()`
  });
  await new Promise(r => setTimeout(r, 600));
  await takeSnap('03_guard_paused_5min_banner.png');

  // 4. Click '▶ Включить защиту сейчас' on banner
  await sendPage('Runtime.evaluate', {
    expression: `Array.from(document.querySelectorAll('button')).find(el => el.innerText.includes('Включить защиту сейчас')).click()`
  });
  await new Promise(r => setTimeout(r, 600));
  await takeSnap('04_guard_reactivated.png');

  // 5. Reveal Secret Value (Eye button)
  await sendPage('Runtime.evaluate', {
    expression: `Array.from(document.querySelectorAll('.yg-breakdown-cell button')).find(el => el.innerText.includes('Показать')).click()`
  });
  await new Promise(r => setTimeout(r, 500));
  await takeSnap('05_secret_revealed_plaintext.png');

  // 6. Click '[ 🛡️ ЗАЩИТИТЬ ТОКЕНОМ И ОТПРАВИТЬ ]'
  await sendPage('Runtime.evaluate', {
    expression: `document.querySelector('.yg-btn-protect').click()`
  });
  // Wait during hacker scramble animation
  await new Promise(r => setTimeout(r, 850));
  await takeSnap('06_scramble_and_vault_protect.png');

  await send('Target.closeTarget', { targetId });
  ws.close();
  console.log('All tests completed successfully!');
}

main().catch(console.error);
