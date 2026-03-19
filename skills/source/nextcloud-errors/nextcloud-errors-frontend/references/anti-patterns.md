# Frontend Anti-Patterns

## Import and Package Anti-Patterns

### AP-1: Using Raw axios or fetch for Nextcloud API Calls

**NEVER** use raw `axios` or `fetch()` for requests to Nextcloud endpoints. These do not include CSRF tokens, session authentication, or the `OCS-APIRequest` header.

```typescript
// WRONG: No CSRF token, no auth headers
import axios from 'axios'
const resp = await axios.get('/apps/myapp/api/items')

// WRONG: Same problem with fetch
const resp = await fetch('/apps/myapp/api/items')

// CORRECT: @nextcloud/axios handles everything
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'
const resp = await axios.get(generateUrl('/apps/myapp/api/items'))
```

### AP-2: Using OC.generateUrl() in New Code

**NEVER** use `OC.generateUrl()` or any other `OC.*` global in new code. These globals are deprecated, may not be available in webpack-bundled modules, and have modern `@nextcloud/*` package replacements.

```typescript
// WRONG: Deprecated global
const url = OC.generateUrl('/apps/myapp/api/items')

// CORRECT: Modern package
import { generateUrl } from '@nextcloud/router'
const url = generateUrl('/apps/myapp/api/items')
```

### AP-3: Forgetting @nextcloud/dialogs CSS Import

**NEVER** use `@nextcloud/dialogs` functions without importing the CSS file. Toasts and dialogs will render but be invisible or completely unstyled.

```typescript
// WRONG: Functions work but UI is broken
import { showSuccess } from '@nextcloud/dialogs'
showSuccess('Saved')  // Renders as unstyled element

// CORRECT: Import CSS once at entry point
import '@nextcloud/dialogs/style.css'
import { showSuccess } from '@nextcloud/dialogs'
showSuccess('Saved')  // Renders with proper styling
```

### AP-4: Using Barrel Imports for Large Component Sets

**NEVER** use barrel imports from `@nextcloud/vue` when you only need a few components. Barrel imports include the ENTIRE library in your bundle.

```typescript
// WRONG: Imports entire library (~500KB+ gzipped)
import { NcButton, NcDialog } from '@nextcloud/vue'

// CORRECT for v8.x: Direct imports (tree-shakeable)
import NcButton from '@nextcloud/vue/dist/Components/NcButton.js'
import NcDialog from '@nextcloud/vue/dist/Components/NcDialog.js'

// CORRECT for v9.x: Direct imports (tree-shakeable)
import NcButton from '@nextcloud/vue/components/NcButton'
import NcDialog from '@nextcloud/vue/components/NcDialog'
```

### AP-5: Using npm link for @nextcloud/vue Development

**NEVER** use `npm link` to test local `@nextcloud/vue` changes with your app. It causes dependency resolution issues where two copies of Vue are loaded simultaneously, breaking component registration.

```bash
# WRONG: Creates duplicate Vue instances
cd nextcloud-vue && npm link
cd ../myapp && npm link @nextcloud/vue

# CORRECT: Use npm pack and install the tarball
cd nextcloud-vue && npm pack
cd ../myapp && npm install ../nextcloud-vue/nextcloud-vue-8.0.0.tgz
```

---

## State Management Anti-Patterns

### AP-6: Calling loadState() Without a Fallback

**NEVER** call `loadState()` without providing a fallback value as the third argument. The function throws an Error when the key is not found in the DOM, crashing your app before Vue mounts.

```typescript
// WRONG: Throws if key is missing from DOM
const config = loadState('myapp', 'app_config')

// CORRECT: Returns fallback on missing key
const config = loadState('myapp', 'app_config', { maxItems: 50 })
```

### AP-7: Using provideInitialState for Large Datasets

**NEVER** use `provideInitialState()` for large or expensive data that may not be needed. Initial state is serialized into the HTML page on every request, increasing page load time.

```php
// WRONG: Always serialized, even if frontend never reads it
$this->initialState->provideInitialState('all_users', $this->userService->findAll());

// CORRECT: Only serialized when frontend calls loadState()
$this->initialState->provideLazyInitialState('all_users', function () {
    return $this->userService->findAll();
});
```

---

## Theming and Styling Anti-Patterns

### AP-8: Hardcoding Colors

**NEVER** hardcode color values in CSS or JavaScript. Hardcoded colors break dark mode, custom themes, and high-contrast accessibility mode.

```css
/* WRONG: Breaks in dark mode and custom themes */
.my-component {
    background-color: #ffffff;
    color: #222222;
    border: 1px solid #0082C9;
}

/* CORRECT: Respects user's theme settings */
.my-component {
    background-color: var(--color-main-background);
    color: var(--color-main-text);
    border: 1px solid var(--color-primary-element);
}
```

### AP-9: Accessing OCA.Theming Without Null Check

**NEVER** access `OCA.Theming` properties without first checking that the object exists. The theming app may be disabled, making `OCA.Theming` undefined.

```typescript
// WRONG: TypeError if theming app is disabled
const brandColor = OCA.Theming.color
const instanceName = OCA.Theming.name

// CORRECT: Guard with optional chaining and fallback
const brandColor = OCA?.Theming?.color ?? '#0082C9'
const instanceName = OCA?.Theming?.name ?? 'Nextcloud'

// BEST: Use CSS custom properties instead of JavaScript theming API
// In CSS: var(--color-primary-element) -- always available
```

---

## Build and Configuration Anti-Patterns

### AP-10: Writing webpack Config from Scratch

**NEVER** write a webpack configuration from scratch for a Nextcloud app. The `@nextcloud/webpack-vue-config` package provides a battle-tested base that handles Vue SFC compilation, Babel transpilation, CSS extraction, and correct output paths.

```javascript
// WRONG: Custom config that misses Nextcloud-specific requirements
module.exports = {
    entry: './src/main.js',
    module: {
        rules: [
            { test: /\.vue$/, use: 'vue-loader' },
            // Missing many required loaders and plugins
        ],
    },
}

// CORRECT: Extend the official base config
const webpackConfig = require('@nextcloud/webpack-vue-config')
module.exports = webpackConfig
```

### AP-11: Overriding webpack module.rules Entirely

**NEVER** replace the `module.rules` array from `@nextcloud/webpack-vue-config`. This removes loaders for Vue, CSS, SCSS, images, and fonts.

```javascript
// WRONG: Replaces all built-in loaders
const webpackConfig = require('@nextcloud/webpack-vue-config')
webpackConfig.module.rules = [
    { test: /\.vue$/, use: 'vue-loader' },
]
module.exports = webpackConfig

// CORRECT: Add new rules without removing existing ones
const webpackConfig = require('@nextcloud/webpack-vue-config')
webpackConfig.module.rules.push({
    test: /\.md$/,
    use: 'raw-loader',
})
module.exports = webpackConfig
```

---

## Version Compatibility Anti-Patterns

### AP-12: Mixing Vue 2 and Vue 3 Libraries

**NEVER** install `@nextcloud/vue` v9 (Vue 3) in a project that uses Vue 2, or v8 (Vue 2) in a Vue 3 project. The internal component APIs are incompatible.

```bash
# WRONG: v9 requires Vue 3 but project has Vue 2
npm install vue@^2.7 @nextcloud/vue@^9

# CORRECT: Match library version to Vue version
npm install vue@^2.7 @nextcloud/vue@^8    # NC 28-30
npm install vue@^3 @nextcloud/vue@^9      # NC 31+
```

### AP-13: Using Vue 3 Bootstrap Pattern in Vue 2 Project

**NEVER** use `createApp()` in a Vue 2 project. Vue 2 uses the `new Vue()` constructor.

```javascript
// WRONG in Vue 2: createApp does not exist
import { createApp } from 'vue'
import App from './App.vue'
createApp(App).mount('#content')

// CORRECT for Vue 2 (NC 28-30)
import Vue from 'vue'
import App from './App.vue'
new Vue({
    el: '#content',
    render: h => h(App),
})

// CORRECT for Vue 3 (NC 31+)
import { createApp } from 'vue'
import App from './App.vue'
createApp(App).mount('#content')
```

### AP-14: Ignoring @nextcloud/files Version Compatibility

**NEVER** install `@nextcloud/files` v4 for projects targeting NC 28-32. APIs in v4 target NC 33+ and may be missing or behave differently on older servers.

```bash
# WRONG: v4 APIs not available on NC 28
npm install @nextcloud/files@^4

# CORRECT for NC 28-32
npm install @nextcloud/files@^3

# CORRECT for NC 33+
npm install @nextcloud/files@^4
```

---

## Event Bus Anti-Patterns

### AP-15: Bundling @nextcloud/event-bus as Direct Dependency

**NEVER** bundle your own copy of `@nextcloud/event-bus` when your app runs inside Nextcloud. Multiple instances create isolated event registries -- events emitted on one are invisible to listeners on the other.

```json
// WRONG: Bundles a separate copy
{
    "dependencies": {
        "@nextcloud/event-bus": "^3.0.0"
    }
}

// CORRECT: Use the host's shared instance
{
    "peerDependencies": {
        "@nextcloud/event-bus": "^3.0.0"
    },
    "devDependencies": {
        "@nextcloud/event-bus": "^3.0.0"
    }
}
```

### AP-16: Forgetting to Unsubscribe from Events

**NEVER** subscribe to events without unsubscribing when the component is destroyed. Leaked subscriptions cause memory leaks and handler execution on unmounted components.

```typescript
// WRONG: Leaks subscription when component unmounts
import { subscribe } from '@nextcloud/event-bus'

export default {
    mounted() {
        subscribe('files:node:uploaded', this.handleUpload)
    },
    // No cleanup -- handler persists after component is destroyed
}

// CORRECT: Unsubscribe on destroy
import { subscribe, unsubscribe } from '@nextcloud/event-bus'

export default {
    mounted() {
        subscribe('files:node:uploaded', this.handleUpload)
    },
    beforeDestroy() {  // Vue 2: beforeDestroy, Vue 3: beforeUnmount
        unsubscribe('files:node:uploaded', this.handleUpload)
    },
}
```

---

## CORS Anti-Patterns

### AP-17: Adding Manual CORS Headers Instead of Using ApiController

**NEVER** manually set `Access-Control-Allow-Origin` headers on controller responses. This is fragile, often incomplete (missing preflight handling), and does not handle origin validation.

```php
// WRONG: Manual CORS headers -- incomplete and fragile
class DataController extends Controller {
    public function getData(): JSONResponse {
        $response = new JSONResponse($data);
        $response->addHeader('Access-Control-Allow-Origin', '*');
        return $response;
    }
}

// CORRECT: ApiController handles CORS properly
class DataController extends ApiController {
    public function __construct(string $appName, IRequest $request) {
        parent::__construct($appName, $request, 'GET, POST', 'Authorization, Content-Type', 86400);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getData(): JSONResponse {
        return new JSONResponse($data);
    }
}
```

### AP-18: Forgetting NoCSRFRequired on CORS Endpoints

**NEVER** omit `#[NoCSRFRequired]` on endpoints that serve cross-origin requests. Browser preflight (OPTIONS) requests cannot carry CSRF tokens, causing the preflight to fail with a CSRF error.

```php
// WRONG: Preflight fails because it cannot send CSRF token
class ExternalApi extends ApiController {
    #[NoAdminRequired]
    public function getData(): JSONResponse {
        return new JSONResponse($data);
    }
}

// CORRECT: NoCSRFRequired allows preflight to pass
class ExternalApi extends ApiController {
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getData(): JSONResponse {
        return new JSONResponse($data);
    }
}
```
