# 🔏 MITM — Proxy Shield

A **network-level ad blocking and content filtering system** built around Squid proxy + SquidGuard, with a Flask management API and a companion **Chrome Extension (MV3)** for per-tab telemetry, filter suggestions, and real-time proxy status monitoring.

---

## ✨ Features

### Proxy Management API (Flask)
- **Dynamic Blocklist Management** — Add/remove domains to `ads`, `streaming`, and `whitelist` categories via REST API. Changes are applied live without proxy restarts.
- **User Management** — Create and delete proxy authentication users (via `htpasswd`).
- **SquidGuard Config Sync** — Automatically regenerates and reloads the SquidGuard configuration after blocklist updates.
- **Telemetry Logging** — Stores browsing events and suggestion logs in a local JSON telemetry database.
- **Authenticated Admin API** — All management endpoints require HTTP Basic Auth.

### Chrome Extension (MV3)
- **Tab-Level Execution** — Content script runs at `document_start` across all frames to intercept requests early.
- **Proxy Shield Status** — Popup shows live proxy connection status.
- **DRM Detector** — Companion `drm-detector-extension` identifies DRM-protected content (EME/Widevine/PlayReady) on the page.
- **Telemetry Reporting** — Reports tab navigation events back to the management server.
- **Domain Suggestions** — Users can suggest domains for blocking/whitelisting directly from the extension popup.

---

## 🏗️ Architecture

```
MITM/
├── server_api.py               # Flask management API
├── extension/                  # Chrome MV3 Proxy Shield extension
│   ├── manifest.json
│   ├── background.js           # Service worker (WebNavigation events)
│   ├── content.js              # Content script (all_urls, document_start)
│   ├── cosmetic.css            # Cosmetic ad-hiding rules
│   ├── popup.html / popup.js   # Extension popup UI
│   └── icon.png
├── drm-detector-extension/     # DRM detection extension
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   ├── inject.js               # Injected page script (monitors EME API)
│   └── popup.html / popup.js
└── templates/
    └── index.html              # Admin dashboard web UI
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Proxy | Squid + SquidGuard |
| Management API | Python, Flask, Flask-CORS |
| Auth | HTTP Basic Auth (htpasswd) |
| Browser extension | Chrome MV3 (Manifest Version 3) |
| Telemetry storage | Local JSON file |

---

## 🚀 Deployment

### Prerequisites

- Linux server with Squid and SquidGuard installed
- Python 3.10+

### API Server

```bash
pip install flask flask-cors
python server_api.py
# Runs on http://0.0.0.0:5000
```

### Configure Squid

Point Squid to the blocklists managed by the API:

```
# /etc/squid/squid.conf
acl ads dstdomain "/etc/squid/dynamic_ads.txt"
acl streaming dstdomain "/etc/squid/streaming.txt"
http_access deny ads
```

### Load the Chrome Extension

1. Navigate to `chrome://extensions/`
2. Enable **Developer Mode**
3. Click **Load unpacked** → select `extension/`

---

## 📡 API Reference

### Blocklist Management

```http
GET  /list/<category>               # Get all domains in a category
POST /list/<category>/add           # Add domain(s) to a category
POST /list/<category>/remove        # Remove a domain from a category
```

### User Management

```http
POST /users/add                     # Create proxy user
POST /users/delete                  # Delete proxy user
```

### Telemetry

```http
GET  /telemetry                     # Retrieve all telemetry logs
POST /telemetry/log                 # Submit a browsing event
POST /telemetry/suggest             # Submit a domain block suggestion
```

### Admin UI

```http
GET  /                              # Admin dashboard (browser UI)
```

> [!IMPORTANT]
> All management endpoints except `/telemetry/log` and `/telemetry/suggest` require HTTP Basic Auth credentials.

---

## 🌐 Extension Permissions

| Permission | Purpose |
|-----------|---------|
| `activeTab` | Access currently active tab info |
| `scripting` | Inject content scripts dynamically |
| `tabs` | Monitor tab navigation events |
| `webNavigation` | Hook into navigation lifecycle |
| `storage` | Persist extension settings locally |
| `<all_urls>` | Apply content script on all sites |

---

## 📄 License

MIT License
