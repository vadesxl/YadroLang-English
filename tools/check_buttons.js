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
  await page('Page.navigate', { url: 'http://localhost:8765/preview.html?v=' + Date.now() });
  await new Promise(r => setTimeout(r, 2000));
  const res = await page('Runtime.evaluate', {
    expression: 'Array.from(document.querySelectorAll("button")).map(b => b.innerText.trim())'
  });
  console.log('ALL BUTTONS:\n', res.result.value);
  await send('Target.closeTarget', { targetId });
  ws.close();
}

main().catch(console.error);
