# Frontend Anti-Patterns

## AP-01: Hardcoded Colors

**NEVER** hardcode color values in CSS or inline styles.

```css
/* WRONG -- breaks dark mode and custom themes */
.my-element {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #0082c9;
}

/* CORRECT -- uses Nextcloud CSS custom properties */
.my-element {
    background-color: var(--color-main-background);
    color: var(--color-main-text);
    border: 1px solid var(--color-primary-element);
}
```

**Why:** Nextcloud supports dark mode and admin-customizable themes. CSS custom properties automatically update based on the active theme. Hardcoded colors create visual inconsistencies and accessibility issues.

---

## AP-02: Barrel Imports in Production

**NEVER** use barrel imports when you only need a few components.

```javascript
// WRONG -- imports the entire library, increasing bundle size significantly
import { NcButton, NcDialog } from '@nextcloud/vue'

// CORRECT -- tree-shakeable direct imports
import NcButton from '@nextcloud/vue/components/NcButton'
import NcDialog from '@nextcloud/vue/components/NcDialog'
```

**Why:** Barrel imports (`from '@nextcloud/vue'`) pull in the entire component library regardless of what you use. Direct imports allow webpack to tree-shake unused code, reducing bundle size by 50-80%.

---

## AP-03: Raw fetch() or Plain axios

**NEVER** use the browser `fetch()` API or a standalone `axios` instance for Nextcloud API calls.

```javascript
// WRONG -- no auth headers, no CSRF token, no session handling
const response = await fetch('/apps/myapp/api/items')
const data = await response.json()

// WRONG -- plain axios without Nextcloud auth
import axios from 'axios'
const response = await axios.get('/apps/myapp/api/items')

// CORRECT -- @nextcloud/axios handles everything
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'
const response = await axios.get(generateUrl('/apps/myapp/api/items'))
```

**Why:** `@nextcloud/axios` automatically includes authentication headers, CSRF tokens, and handles session expiry. Raw HTTP clients will produce 401/403 errors or CSRF failures.

---

## AP-04: loadState Without Fallback

**NEVER** call `loadState()` without a fallback value for state that might not exist.

```javascript
// WRONG -- throws Error if 'optional_config' was not provided by PHP
const config = loadState('myapp', 'optional_config')

// CORRECT -- returns default value if key not found
const config = loadState('myapp', 'optional_config', { enabled: false })

// CORRECT -- wrap in try/catch if you need error handling
try {
    const config = loadState('myapp', 'required_config')
} catch (e) {
    console.error('Required config missing:', e)
}
```

**Why:** `loadState()` throws an `Error` when the key is not found in the DOM. This crashes the entire Vue app if uncaught. ALWAYS provide a fallback for state that the PHP side might not have provided.

---

## AP-05: Missing Dialog Styles

**NEVER** use `@nextcloud/dialogs` toast functions without importing the stylesheet.

```javascript
// WRONG -- toasts render without any styling
import { showSuccess, showError } from '@nextcloud/dialogs'
showSuccess('Saved')

// CORRECT -- import styles once in your app
import { showSuccess, showError } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'  // REQUIRED
showSuccess('Saved')
```

**Why:** The `@nextcloud/dialogs` package does not automatically inject its CSS. Without the stylesheet import, toast notifications appear as unstyled text blocks, often invisible or unreadable.

---

## AP-06: Legacy OC.* Global API

**NEVER** use `OC.generateUrl()`, `OC.requestToken`, or other `OC.*` globals in new code.

```javascript
// WRONG -- legacy global API
const url = OC.generateUrl('/apps/myapp/api/items')
const token = OC.requestToken

// CORRECT -- use @nextcloud/* packages
import { generateUrl } from '@nextcloud/router'
const url = generateUrl('/apps/myapp/api/items')
// CSRF is handled automatically by @nextcloud/axios
```

**Why:** The `OC.*` global namespace is a legacy API. The `@nextcloud/*` packages provide TypeScript types, tree-shaking, and are the maintained path forward. Global APIs may be removed in future Nextcloud versions.

---

## AP-07: Eager Initial State for Large Data

**NEVER** use `provideInitialState` (eager) for large datasets or data that might not be needed.

```php
// WRONG -- serializes the entire dataset on every page load, even if unused
$this->initialState->provideInitialState('all_users', $userService->findAll());

// CORRECT -- lazy state only serializes when loadState() is called
$this->initialState->provideLazyInitialState('all_users', function() use ($userService) {
    return $userService->findAll();
});
```

**Why:** Eager initial state is always serialized into the HTML page response, increasing page load time and memory usage even if the frontend never reads it. Lazy state defers serialization until `loadState()` is actually called.

---

## AP-08: OCA.Theming Without Existence Check

**NEVER** access `OCA.Theming` properties without checking if the theming app is enabled.

```javascript
// WRONG -- crashes if theming app is disabled
const primaryColor = OCA.Theming.color

// CORRECT -- guard against missing theming
const primaryColor = OCA.Theming?.color || '#0082C9'

// BETTER -- use CSS custom properties instead
// In CSS: var(--color-primary-element)
```

**Why:** The `OCA.Theming` object is only available when the theming app is enabled. Accessing it directly causes a `TypeError: Cannot read properties of undefined`. Prefer CSS custom properties which work regardless of the theming app's status.

---

## AP-09: npm link for @nextcloud/vue Development

**NEVER** use `npm link` to test local changes to `@nextcloud/vue` with an app.

```bash
# WRONG -- causes dependency resolution conflicts
cd nextcloud-vue
npm link
cd ../myapp
npm link @nextcloud/vue

# CORRECT -- use npm pack and install the tarball
cd nextcloud-vue
npm pack
cd ../myapp
npm install ../nextcloud-vue/nextcloud-vue-8.0.0.tgz
```

**Why:** `npm link` creates symlinks that bypass npm's dependency resolution, causing duplicate Vue instances, missing peer dependencies, and cryptic runtime errors. Using `npm pack` creates a proper tarball that installs like a real package.

---

## AP-10: Event Bus Subscription Leaks

**NEVER** subscribe to event bus events without cleaning up on component destruction.

```javascript
// WRONG -- handler persists after component is destroyed, causing memory leaks
export default {
    mounted() {
        subscribe('files:node:uploaded', (node) => {
            this.items.push(node)
        })
    },
}

// CORRECT -- store handler reference, unsubscribe on destroy
export default {
    mounted() {
        this._uploadHandler = (node) => {
            this.items.push(node)
        }
        subscribe('files:node:uploaded', this._uploadHandler)
    },
    beforeDestroy() {
        unsubscribe('files:node:uploaded', this._uploadHandler)
    },
}
```

**Why:** Event bus subscriptions are global. If a component subscribes in `mounted()` but never unsubscribes, the handler continues to fire after the component is destroyed. This causes memory leaks, stale references, and unexpected behavior when the component is re-created.

---

## AP-11: Writing Custom Webpack Config From Scratch

**NEVER** write a complete webpack configuration manually for a Nextcloud app.

```javascript
// WRONG -- missing Nextcloud-specific loaders, aliases, and optimizations
const path = require('path')
module.exports = {
    entry: './src/main.js',
    output: { path: path.resolve(__dirname, 'js') },
    module: { rules: [/* manual loader config */] },
}

// CORRECT -- extend the official base config
const webpackConfig = require('@nextcloud/webpack-vue-config')

// Add custom entry points if needed
webpackConfig.entry['admin'] = path.join(__dirname, 'src', 'admin.js')

module.exports = webpackConfig
```

**Why:** `@nextcloud/webpack-vue-config` includes Nextcloud-specific loaders, path aliases, chunk splitting, Vue compilation settings, and production optimizations. Writing your own config from scratch will miss critical configuration and produce incompatible builds.

---

## AP-12: Hardcoded URLs

**NEVER** hardcode Nextcloud instance URLs or paths in frontend code.

```javascript
// WRONG -- breaks on subdirectory installs and different domains
const url = '/index.php/apps/myapp/api/items'
const davUrl = '/remote.php/dav/files/username/'

// CORRECT -- use URL generation functions
import { generateUrl, generateRemoteUrl } from '@nextcloud/router'
const url = generateUrl('/apps/myapp/api/items')
const davUrl = generateRemoteUrl('dav') + '/files/username/'
```

**Why:** Nextcloud can be installed in a subdirectory (e.g., `/nextcloud/`), and the `index.php` part may be rewritten away. The `@nextcloud/router` functions automatically account for the correct base path and web root configuration.
