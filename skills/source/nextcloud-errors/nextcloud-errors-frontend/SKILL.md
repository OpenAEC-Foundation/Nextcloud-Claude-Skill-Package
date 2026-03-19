---
name: nextcloud-errors-frontend
description: >
  Use when encountering frontend build errors, runtime JavaScript errors, or API call failures from the browser.
  Prevents @nextcloud/* version mismatches with server, using deprecated OC global, and missing CSRF requesttoken.
  Covers Vue/Webpack build failures, @nextcloud/* import path issues, CORS problems, CSRF token failures, missing dialog styles, deprecated OC global usage, version mismatches between @nextcloud packages and Nextcloud server, and initial state loading errors.
  Keywords: Webpack error, Vue build, @nextcloud version, OC global, CSRF, requesttoken, initial state, CORS, import path.
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-errors-frontend

## Diagnostic Quick Reference

### Build Errors

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Module not found: @nextcloud/vue/components/NcButton` | Wrong import path for library version | Use `@nextcloud/vue/dist/Components/NcButton.js` for v8.x |
| `Can't resolve 'vue'` in webpack build | Missing Vue dependency or wrong version | Install `vue@^2.7` for NC 28-30, `vue@^3` for NC 31+ |
| `vue-loader` errors during build | Missing or wrong vue-loader version | Install `vue-loader@legacy` for Vue 2 projects |
| `Module parse failed: Unexpected token` in `.vue` file | webpack config missing vue-loader | Use `@nextcloud/webpack-vue-config` as base config |
| `TypeError: Cannot read properties of undefined (reading 'component')` | Vue 2 / Vue 3 API mismatch | Check `@nextcloud/vue` version matches your Vue version |

### Runtime Errors

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `Error: Could not find initial state` thrown | `loadState()` called without fallback for missing key | ALWAYS pass a fallback as third argument |
| CSRF check failed on frontend API call | Using raw `axios` or `fetch` instead of `@nextcloud/axios` | Switch to `import axios from '@nextcloud/axios'` |
| Toasts render as unstyled text blobs | Missing `@nextcloud/dialogs` CSS import | Add `import '@nextcloud/dialogs/style.css'` |
| `OC is not defined` in console | Using legacy globals without checking existence | Use `@nextcloud/router` and `@nextcloud/initial-state` |
| `OCA.Theming` throws TypeError | Accessing theming object without existence check | ALWAYS check `if (OCA.Theming)` before access |
| CORS error in browser console | Backend controller extends `Controller` not `ApiController` | Extend `ApiController` for cross-origin endpoints |

### Version Mismatch Errors

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Components render incorrectly or throw Vue warnings | `@nextcloud/vue` v9 used with Vue 2 project | Use `@nextcloud/vue@^8` for NC 28-30 (Vue 2) |
| `@nextcloud/files` methods missing | Wrong major version for NC version | Use `@nextcloud/files@^3` for NC 28-32, `@^4` for NC 33+ |
| `createApp is not a function` | Vue 3 bootstrap code in Vue 2 project | Use `new Vue({...})` for Vue 2, `createApp()` for Vue 3 |

---

## Error 1: Import Path Errors with @nextcloud/* Packages

### What You See
- `Module not found: Error: Can't resolve '@nextcloud/vue/components/NcButton'`
- Build fails with unresolved module errors for `@nextcloud/vue` imports
- Tree-shaking imports work in one version but break in another

### Why It Happens
The `@nextcloud/vue` library changed its internal directory structure between major versions. Import paths that work in v9.x (Vue 3) do NOT work in v8.x (Vue 2), and vice versa. The barrel import (`import { NcButton } from '@nextcloud/vue'`) works in all versions but increases bundle size.

### How to Fix

**ALWAYS check which `@nextcloud/vue` version your project uses before writing imports.**

```typescript
// For @nextcloud/vue v8.x (NC 28-30, Vue 2) -- direct import
import NcButton from '@nextcloud/vue/dist/Components/NcButton.js'

// For @nextcloud/vue v9.x (NC 31+, Vue 3) -- direct import
import NcButton from '@nextcloud/vue/components/NcButton'

// SAFE for ALL versions (but larger bundle) -- barrel import
import { NcButton } from '@nextcloud/vue'
```

**NEVER** assume import paths are stable across major versions. When upgrading `@nextcloud/vue`, ALWAYS verify all direct import paths still resolve.

---

## Error 2: CSRF Token Missing on Frontend API Calls

### What You See
- HTTP 401 or 997 from API calls made in the browser
- `"CSRF check failed"` in response
- API calls work from curl but fail from your Vue component

### Why It Happens
Nextcloud requires CSRF tokens for authenticated requests. Raw `axios` and `fetch()` do NOT include the CSRF token or the `OCS-APIRequest` header. The `@nextcloud/axios` wrapper adds both automatically.

### How to Fix

**ALWAYS use `@nextcloud/axios` for HTTP requests from Nextcloud frontend code.**

```typescript
// WRONG: Raw axios -- no CSRF token, no OCS-APIRequest header
import axios from 'axios'
const resp = await axios.get('/ocs/v2.php/cloud/capabilities')

// WRONG: Raw fetch -- same problem
const resp = await fetch('/apps/myapp/api/items')

// CORRECT: @nextcloud/axios handles auth automatically
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'
const resp = await axios.get(generateUrl('/apps/myapp/api/items'))
```

If you MUST use raw `axios` (e.g., for external API calls that should NOT include Nextcloud auth), create a separate instance:

```typescript
import axios from 'axios'
const externalClient = axios.create()
const resp = await externalClient.get('https://external-api.example.com/data')
```

**NEVER** use raw `axios` or `fetch()` for requests to Nextcloud endpoints.

---

## Error 3: Missing @nextcloud/dialogs Styles

### What You See
- Toast notifications appear as unstyled plain text
- Dialog components render without backgrounds, borders, or proper positioning
- File picker looks broken or partially styled

### Why It Happens
The `@nextcloud/dialogs` package ships its CSS separately. Importing only the JavaScript functions does NOT include the styles. This is by design to allow tree-shaking, but causes invisible/broken UI when the CSS import is forgotten.

### How to Fix

**ALWAYS import the styles alongside the dialog functions.**

```typescript
// WRONG: Functions work but toasts have no styling
import { showSuccess, showError } from '@nextcloud/dialogs'

// CORRECT: Import styles ONCE at app entry point (main.js/main.ts)
import '@nextcloud/dialogs/style.css'
import { showSuccess, showError } from '@nextcloud/dialogs'
```

Import the CSS file ONCE in your app's entry point (`main.js` or `main.ts`). Do NOT import it in every component -- one import per app is sufficient.

---

## Error 4: Deprecated OC Global Usage

### What You See
- `ReferenceError: OC is not defined` in bundled JavaScript
- `TypeError: Cannot read properties of undefined (reading 'generateUrl')` on `OC.generateUrl`
- Console warnings about deprecated OC/OCA globals

### Why It Happens
The `OC` and `OCA` global objects are legacy APIs from before Nextcloud adopted npm packages. In webpack-bundled apps, these globals may not be available at module scope. Even when available, they are deprecated in favor of `@nextcloud/*` packages.

### How to Fix

**ALWAYS use the corresponding `@nextcloud/*` package instead of OC globals.**

| Deprecated Global | Modern Replacement |
|-------------------|--------------------|
| `OC.generateUrl()` | `import { generateUrl } from '@nextcloud/router'` |
| `OC.generateOcsUrl()` | `import { generateOcsUrl } from '@nextcloud/router'` |
| `OC.generateFilePath()` | `import { generateFilePath } from '@nextcloud/router'` |
| `OC.requestToken` | Use `@nextcloud/axios` (handles tokens automatically) |
| `OC.getCurrentUser()` | `import { getCurrentUser } from '@nextcloud/auth'` |
| `OCA.Theming.color` | Use CSS variable `var(--color-primary-element)` |
| `t()` / `n()` global | `import { translate as t, translatePlural as n } from '@nextcloud/l10n'` |

```typescript
// WRONG: Legacy globals
const url = OC.generateUrl('/apps/myapp/api/items')
const user = OC.getCurrentUser()

// CORRECT: Modern packages
import { generateUrl } from '@nextcloud/router'
import { getCurrentUser } from '@nextcloud/auth'

const url = generateUrl('/apps/myapp/api/items')
const user = getCurrentUser()
```

If you MUST access `OCA.Theming` (no npm equivalent for all properties):

```typescript
// WRONG: Crashes if theming app is disabled
const color = OCA.Theming.color

// CORRECT: Guard with existence check
const color = OCA?.Theming?.color ?? '#0082C9'
```

**NEVER** use `OC.generateUrl()` in new code. **NEVER** access `OCA.Theming` without a null check.

---

## Error 5: loadState() Throws on Missing Key

### What You See
- `Error: Could not find initial state "myapp" "some_key"` thrown at page load
- App crashes before Vue mounts because `loadState()` fails
- Works in development but crashes in production (missing state registration)

### Why It Happens
`loadState()` from `@nextcloud/initial-state` throws an `Error` when the requested key does not exist in the DOM. This happens when: (A) the PHP controller forgot to call `provideInitialState()`, (B) the key name has a typo, or (C) the state is conditionally provided but the frontend always expects it.

### How to Fix

**ALWAYS provide a fallback value as the third argument to `loadState()`.**

```typescript
import { loadState } from '@nextcloud/initial-state'

// WRONG: Throws if key is missing
const config = loadState('myapp', 'app_config')

// CORRECT: Falls back to default on missing key
const config = loadState('myapp', 'app_config', { refreshInterval: 15000 })

// CORRECT with TypeScript: Typed fallback
interface AppConfig {
    refreshInterval: number
    maxItems: number
}

const config = loadState<AppConfig>('myapp', 'app_config', {
    refreshInterval: 15000,
    maxItems: 50,
})
```

Ensure the PHP controller registers the state for EVERY route that loads the frontend:

```php
public function index(): TemplateResponse {
    $this->initialState->provideInitialState('app_config', $config);
    return new TemplateResponse('myapp', 'main');
}
```

**NEVER** call `loadState()` without a fallback for any state that might be absent.

---

## Error 6: Vue 2 vs Vue 3 Compatibility Errors

### What You See
- `createApp is not a function` or `Vue.component is not a function`
- `@nextcloud/vue` components render incorrectly or throw internal errors
- Composition API (`ref`, `computed`) unavailable or behaving differently

### Why It Happens
Nextcloud supports two Vue versions depending on the server version. Mixing Vue 2 code with Vue 3 libraries (or vice versa) causes runtime failures. The `@nextcloud/vue` component library ships separate major versions for each Vue version.

### How to Fix

**Match ALL dependencies to your target Nextcloud version.**

| Target | Vue | @nextcloud/vue | vue-loader | Entry Point Pattern |
|--------|-----|----------------|------------|---------------------|
| NC 28-30 | vue@^2.7 | @nextcloud/vue@^8 | vue-loader@legacy | `new Vue({ render: h => h(App) }).$mount('#content')` |
| NC 31+ | vue@^3 | @nextcloud/vue@^9 | vue-loader@^17 | `createApp(App).mount('#content')` |

```javascript
// Vue 2 entry point (NC 28-30)
import Vue from 'vue'
import App from './App.vue'

new Vue({
    el: '#content',
    render: h => h(App),
})

// Vue 3 entry point (NC 31+)
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#content')
```

**NEVER** install `@nextcloud/vue@^9` in a project targeting NC 28-30. **NEVER** install `@nextcloud/vue@^8` in a project targeting NC 31+.

---

## Error 7: Webpack Configuration Errors

### What You See
- Build fails with cryptic webpack errors
- `Module parse failed` on `.vue` files
- Entry point not found or wrong output directory

### Why It Happens
Custom webpack configs often break because they override settings that `@nextcloud/webpack-vue-config` expects to control. Common causes: wrong entry point path, missing vue-loader, or conflicting loader rules.

### How to Fix

**ALWAYS start from `@nextcloud/webpack-vue-config` and extend, NEVER write from scratch.**

```javascript
// webpack.config.js -- CORRECT minimal setup
const webpackConfig = require('@nextcloud/webpack-vue-config')
module.exports = webpackConfig

// webpack.config.js -- CORRECT with custom entry points
const path = require('path')
const webpackConfig = require('@nextcloud/webpack-vue-config')

webpackConfig.entry['admin-settings'] = path.join(__dirname, 'src', 'admin.js')

module.exports = webpackConfig
```

```json
// package.json scripts
{
    "scripts": {
        "build": "webpack --node-env production --progress",
        "dev": "webpack --node-env development --progress",
        "watch": "webpack --node-env development --progress --watch"
    }
}
```

**NEVER** write a webpack config from scratch for a Nextcloud app. **NEVER** override the `module.rules` array entirely -- extend it with `push()` if you need custom loaders.

---

## Error 8: CORS Errors on Frontend API Calls

### What You See
- Browser console: `Access to XMLHttpRequest blocked by CORS policy`
- API works from curl but fails from JavaScript on a different origin
- Preflight OPTIONS request returns 405 or has no CORS headers

### Why It Happens
Standard `Controller` and `OCSController` do NOT set CORS headers. Only `ApiController` includes CORS support. This error ONLY occurs when JavaScript runs on a different origin than the Nextcloud server.

### How to Fix

See [references/examples.md](references/examples.md) -- Scenario 3 for the complete backend fix.

For same-origin requests (your app's JavaScript running inside Nextcloud), CORS is NOT needed. **ALWAYS** use `@nextcloud/axios` for same-origin calls -- it handles authentication automatically.

For cross-origin requests, the backend controller MUST extend `ApiController`. This is a backend fix, not a frontend fix.

---

## Decision Tree: Diagnosing Frontend Errors

```
Frontend error occurs
|
+-- Is it a BUILD error (webpack/npm)?
|   |
|   +-- "Module not found" for @nextcloud/* import?
|   |   --> Check import path matches @nextcloud/vue version (v8 vs v9)
|   |   --> Try barrel import as fallback: import { X } from '@nextcloud/vue'
|   |
|   +-- "Can't resolve 'vue'"?
|   |   --> Install correct Vue version: vue@^2.7 (NC 28-30) or vue@^3 (NC 31+)
|   |
|   +-- "Module parse failed" on .vue files?
|   |   --> Use @nextcloud/webpack-vue-config as base
|   |   --> Install vue-loader@legacy for Vue 2 projects
|   |
|   +-- Other webpack error?
|       --> Start from @nextcloud/webpack-vue-config, extend minimally
|
+-- Is it a RUNTIME error (browser console)?
|   |
|   +-- "Could not find initial state"?
|   |   --> Add fallback to loadState(): loadState('app', 'key', defaultValue)
|   |   --> Verify PHP controller calls provideInitialState()
|   |
|   +-- "OC is not defined" or "OCA is not defined"?
|   |   --> Replace OC globals with @nextcloud/* packages
|   |   --> See Error 4 replacement table
|   |
|   +-- "CSRF check failed" or HTTP 997?
|   |   --> Use @nextcloud/axios instead of raw axios/fetch
|   |
|   +-- Toasts/dialogs unstyled?
|   |   --> Add: import '@nextcloud/dialogs/style.css'
|   |
|   +-- CORS error?
|       --> Backend must extend ApiController (not Controller)
|       --> Same-origin? Use @nextcloud/axios, no CORS needed
|
+-- Is it a VERSION MISMATCH error?
    |
    +-- Check @nextcloud/vue version matches Vue version
    +-- Check @nextcloud/files version matches NC version
    +-- Check entry point pattern matches Vue version
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- Frontend error types, package version matrix, import path reference
- [references/examples.md](references/examples.md) -- Error scenarios with complete fix examples
- [references/anti-patterns.md](references/anti-patterns.md) -- Common frontend mistakes and how to avoid them

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/js.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/css.html
- https://github.com/nextcloud-libraries/nextcloud-vue
- https://github.com/nextcloud-libraries/nextcloud-axios
- https://github.com/nextcloud-libraries/nextcloud-initial-state
- https://github.com/nextcloud-libraries/nextcloud-dialogs
- https://github.com/nextcloud-libraries/webpack-vue-config
