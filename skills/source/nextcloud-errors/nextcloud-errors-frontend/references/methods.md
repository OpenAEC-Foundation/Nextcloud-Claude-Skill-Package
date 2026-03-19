# Frontend Error Types, Package Versions, and Import Paths

## @nextcloud/* Package Version Matrix

### Core Packages for NC 28+

| Package | Purpose | NC 28-30 Version | NC 31+ Version |
|---------|---------|-------------------|-----------------|
| `@nextcloud/vue` | UI component library | v8.x (Vue 2) | v9.x (Vue 3) |
| `@nextcloud/axios` | HTTP client with auth | Latest | Latest |
| `@nextcloud/router` | URL generation | Latest | Latest |
| `@nextcloud/initial-state` | Server-to-client state | Latest | Latest |
| `@nextcloud/dialogs` | Toasts, file picker | Latest | Latest |
| `@nextcloud/files` | File/folder classes | v3.x | v4.x (NC 33+) |
| `@nextcloud/event-bus` | Frontend events | Latest | Latest |
| `@nextcloud/auth` | Current user info | Latest | Latest |
| `@nextcloud/l10n` | Translation functions | Latest | Latest |

### Build Dependencies

| Package | NC 28-30 (Vue 2) | NC 31+ (Vue 3) |
|---------|-------------------|-----------------|
| `vue` | ^2.7 | ^3.0 |
| `vue-loader` | `vue-loader@legacy` | ^17.0 |
| `@nextcloud/webpack-vue-config` | Latest | Latest |

---

## Frontend Error Categories

### Category 1: Build Errors (Compile Time)

These errors occur during `npm run build` or `npm run dev`.

| Error Type | Typical Message | Root Cause |
|-----------|-----------------|------------|
| Module resolution | `Module not found: Can't resolve '@nextcloud/vue/...'` | Wrong import path for package version |
| Vue version | `Can't resolve 'vue'` | Vue not installed or wrong major version |
| Loader missing | `Module parse failed: Unexpected token` | vue-loader not configured or wrong version |
| Entry point | `Entry module not found` | webpack.config.js entry path incorrect |
| TypeScript | `TS2307: Cannot find module` | Missing type declarations for @nextcloud packages |

### Category 2: Runtime Errors (Browser Console)

These errors occur in the browser after the app loads.

| Error Type | Typical Message | Root Cause |
|-----------|-----------------|------------|
| Initial state | `Error: Could not find initial state "appid" "key"` | Missing fallback in loadState() call |
| CSRF failure | HTTP 997 or "CSRF check failed" | Using raw axios/fetch instead of @nextcloud/axios |
| Global undefined | `ReferenceError: OC is not defined` | Using deprecated OC global in bundled code |
| Theming access | `TypeError: Cannot read properties of undefined` | Accessing OCA.Theming without null check |
| Style missing | Toasts/dialogs render unstyled | @nextcloud/dialogs CSS not imported |

### Category 3: API Communication Errors (Network)

These errors appear in the browser's Network tab.

| Error Type | HTTP Status | Root Cause |
|-----------|-------------|------------|
| CORS blocked | Preflight fails | Backend uses Controller instead of ApiController |
| Auth failure | 401 | CSRF token missing (not using @nextcloud/axios) |
| CSRF rejection | 997 | OCS-APIRequest header missing |
| Not found | 404 | Wrong URL -- not using generateUrl() from @nextcloud/router |

### Category 4: Version Mismatch Errors

These errors occur when package versions are incompatible.

| Mismatch | Symptom | Resolution |
|----------|---------|------------|
| @nextcloud/vue v9 + Vue 2 | Components fail to mount, internal errors | Downgrade to @nextcloud/vue@^8 |
| @nextcloud/vue v8 + Vue 3 | `Vue.component is not a function` | Upgrade to @nextcloud/vue@^9 |
| @nextcloud/files v4 + NC 28 | Missing APIs, import errors | Downgrade to @nextcloud/files@^3 |
| vue-loader@17 + Vue 2 | SFC parsing failures | Use vue-loader@legacy for Vue 2 |

---

## Import Path Reference

### @nextcloud/vue v8.x (NC 28-30, Vue 2)

```typescript
// Direct component import (tree-shakeable)
import NcButton from '@nextcloud/vue/dist/Components/NcButton.js'
import NcDialog from '@nextcloud/vue/dist/Components/NcDialog.js'
import NcAppContent from '@nextcloud/vue/dist/Components/NcAppContent.js'

// Barrel import (works but larger bundle)
import { NcButton, NcDialog, NcAppContent } from '@nextcloud/vue'
```

### @nextcloud/vue v9.x (NC 31+, Vue 3)

```typescript
// Direct component import (tree-shakeable)
import NcButton from '@nextcloud/vue/components/NcButton'
import NcDialog from '@nextcloud/vue/components/NcDialog'

// Composables
import { useHotKey } from '@nextcloud/vue/composables/useHotKey'

// Barrel import (works but larger bundle)
import { NcButton, NcDialog } from '@nextcloud/vue'
```

### Other @nextcloud/* Packages (Version Independent)

```typescript
// @nextcloud/axios
import axios from '@nextcloud/axios'

// @nextcloud/router
import { generateUrl, generateOcsUrl, generateRemoteUrl, generateFilePath } from '@nextcloud/router'

// @nextcloud/initial-state
import { loadState } from '@nextcloud/initial-state'

// @nextcloud/dialogs (ALWAYS import CSS too)
import { showSuccess, showError, showWarning, showInfo } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'

// @nextcloud/event-bus
import { emit, subscribe, unsubscribe } from '@nextcloud/event-bus'

// @nextcloud/files
import { Permission } from '@nextcloud/files'
import { getClient, resultToNode } from '@nextcloud/files/dav'

// @nextcloud/auth
import { getCurrentUser } from '@nextcloud/auth'

// @nextcloud/l10n
import { translate as t, translatePlural as n } from '@nextcloud/l10n'
```

---

## OC Global to @nextcloud/* Migration Map

| Legacy Global | Package | Modern Import |
|---------------|---------|---------------|
| `OC.generateUrl(path)` | @nextcloud/router | `generateUrl(path)` |
| `OC.generateOcsUrl(path)` | @nextcloud/router | `generateOcsUrl(path)` |
| `OC.generateFilePath(app, type, file)` | @nextcloud/router | `generateFilePath(app, type, file)` |
| `OC.generateRemoteUrl(service)` | @nextcloud/router | `generateRemoteUrl(service)` |
| `OC.requestToken` | @nextcloud/axios | Handled automatically |
| `OC.getCurrentUser()` | @nextcloud/auth | `getCurrentUser()` |
| `OC.isUserAdmin()` | @nextcloud/auth | `getCurrentUser()?.isAdmin` |
| `OC.webroot` | @nextcloud/router | Handled internally by generateUrl |
| `OC.L10N` / `t()` / `n()` | @nextcloud/l10n | `translate()` / `translatePlural()` |
| `OCA.Theming.color` | CSS | `var(--color-primary-element)` |
| `OCA.Theming.name` | No direct replacement | Check `if (OCA?.Theming)` then access |

---

## Webpack Configuration Reference

### Minimal Setup (Recommended)

```javascript
// webpack.config.js
const webpackConfig = require('@nextcloud/webpack-vue-config')
module.exports = webpackConfig
```

### Extended Setup with Custom Entries

```javascript
const path = require('path')
const webpackConfig = require('@nextcloud/webpack-vue-config')

// Add entry points (default entry is 'main' -> src/main.js)
webpackConfig.entry['admin-settings'] = path.join(__dirname, 'src', 'admin.js')
webpackConfig.entry['public-share'] = path.join(__dirname, 'src', 'public.js')

module.exports = webpackConfig
```

### Required package.json Scripts

```json
{
    "scripts": {
        "build": "webpack --node-env production --progress",
        "dev": "webpack --node-env development --progress",
        "watch": "webpack --node-env development --progress --watch",
        "serve": "webpack --node-env development serve --progress"
    }
}
```

**NEVER** override `module.rules`, `resolve.extensions`, or `output` from `@nextcloud/webpack-vue-config` unless you fully understand the implications. Extend arrays with `push()`, do not replace them.
