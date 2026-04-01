# Nextcloud MCP Server

FastMCP server voor volledige Nextcloud integratie met Claude Code.

## 55 tools in 11 categorieen

| Categorie | Tools | Beschrijving |
|---|---|---|
| Server Info | 2 | Capabilities, monitoring |
| Files (WebDAV) | 12 | List, read, write, mkdir, delete, move, copy, search, favorites |
| Trashbin | 3 | List, restore, empty |
| Shares | 5 | List, get, create, update, delete |
| Users | 9 | List, get, create, update, enable, disable, delete, groups |
| Groups | 4 | List, create, members, delete |
| Apps | 4 | List, info, enable, disable |
| Notifications | 3 | List, delete, delete all |
| Activity | 1 | List with filters |
| User Status | 4 | Get, set, message, clear |
| Talk | 6 | Conversations, messages, send, delete |
| Groupfolders | 7 | List, get, create, delete, groups, quota |

## Setup

### 1. Installeer dependencies

```bash
cd mcp/
pip install -r requirements.txt
```

Of met een virtual environment:

```bash
cd mcp/
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt  # Windows
# .venv/bin/pip install -r requirements.txt    # Linux/macOS
```

### 2. Configureer credentials

```bash
cp credentials.example.json credentials.json
```

Vul je Nextcloud gegevens in:

```json
{
    "nextcloud_url": "https://jouw-nextcloud.nl",
    "username": "jouw-gebruikersnaam",
    "app_password": "jouw-app-wachtwoord"
}
```

**App-wachtwoord aanmaken in Nextcloud:**
Profiel > Persoonlijke instellingen > Beveiliging > Apparaten & sessies > Nieuw app-wachtwoord aanmaken

### 3. Test de server

```bash
python server.py
```

### 4. Configureer in Claude Code

De `.mcp.json` in de root van dit package configureert de server automatisch. Als je een custom Python pad nodig hebt, pas `.mcp.json` aan:

```json
{
  "mcpServers": {
    "nextcloud": {
      "type": "stdio",
      "command": "/pad/naar/.venv/Scripts/python.exe",
      "args": ["/pad/naar/mcp/server.py"]
    }
  }
}
```

## Authenticatie

Gebruikt Basic Auth met app-wachtwoorden (ondersteund door alle Nextcloud API's). Het app-wachtwoord heeft dezelfde rechten als het account waarmee het is aangemaakt. Voor admin-operaties (users, apps, server info) is een admin-account vereist.
