---
name: nextcloud-syntax-frontend
description: >
  Use when building Nextcloud app frontends, using Vue components, making API calls from JavaScript, or styling with Nextcloud design system.
  Prevents importing from wrong @nextcloud/* package versions, missing dark mode support, and bypassing the design system.
  Covers @nextcloud/vue component library, @nextcloud/axios HTTP client, @nextcloud/router URL generation, @nextcloud/initial-state data injection, @nextcloud/dialogs toasts and file picker, @nextcloud/files DAV client, Webpack configuration, CSS custom properties, and dark mode support.
  Keywords: @nextcloud/vue, @nextcloud/axios, @nextcloud/router, @nextcloud/initial-state, NcButton, Webpack, Vue.js, dark mode, Vue components, API call from JS, dark mode, design system, frontend setup, Webpack..
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-syntax-frontend

## Quick Reference

### @nextcloud/vue Version Compatibility

| Library Version | Vue Version | Nextcloud Version | Status |
|----------------|-------------|-------------------|--------|
| v9.x (main)   | Vue 3       | NC 31+            | Current |
| v8.x (stable8) | Vue 2      | NC 28-30          | Stable  |

### Core Component Library (@nextcloud/vue)

**Layout Components:**

| Component | Purpose |
|-----------|---------|
| `NcContent` | Root wrapper for app content area |
| `NcAppContent` | Main content panel |
| `NcAppNavigation` | Left sidebar navigation |
| `NcAppSidebar` | Right detail sidebar |
| `NcAppNavigationItem` | Navigation list entry |

**Interactive Components:**

| Component | Purpose |
|-----------|---------|
| `NcButton` | Styled button with icon support |
| `NcActions` | Dropdown action menu container |
| `NcActionButton` | Button inside action menus |
| `NcDialog` | Modal dialog wrapper |
| `NcModal` | Full modal overlay |
| `NcSelect` | Dropdown select input |
| `NcTextField` | Text input field |

**Display Components:**

| Component | Purpose |
|-----------|---------|
| `NcListItem` | Standardized list entry |
| `NcAvatar` | User avatar with fallback |
| `NcBreadcrumbs` | Path breadcrumb navigation |
| `NcEmptyContent` | Placeholder for empty states |
| `NcProgressBar` | Progress indicator |
| `NcRichText` | Markdown/rich text renderer |
| `NcDashboardWidget` | Dashboard card widget |
| `NcSettingsSection` | Settings page section wrapper |

### Import Patterns

```typescript
// ALWAYS: Direct component import (tree-shakeable, smaller bundles)
import NcButton from '@nextcloud/vue/components/NcButton'
import { useHotKey } from '@nextcloud/vue/composables/useHotKey'

// AVOID in production: Barrel import (larger bundles)
import { NcButton, useHotKey } from '@nextcloud/vue'
```

### @nextcloud/* Package Summary

| Package | Purpose | Key Exports |
|---------|---------|-------------|
| `@nextcloud/axios` | Authenticated HTTP client | `axios` (default) |
| `@nextcloud/router` | URL generation | `generateUrl`, `generateOcsUrl`, `generateRemoteUrl`, `generateFilePath` |
| `@nextcloud/initial-state` | Server-to-client data | `loadState` |
| `@nextcloud/dialogs` | Toasts and file picker | `showSuccess`, `showError`, `getFilePickerBuilder` |
| `@nextcloud/files` | DAV client, file types | `getClient`, `Permission`, `addNewFileMenuEntry` |
| `@nextcloud/event-bus` | Cross-component events | `emit`, `subscribe`, `unsubscribe` |

### CSS Custom Properties (Theming)

| Variable | Purpose |
|----------|---------|
| `--color-primary-element` | Primary brand color |
| `--color-main-background` | Main background |
| `--color-main-text` | Primary text |
| `--color-text-maxcontrast` | Secondary/muted text |
| `--color-info` | Info status |
| `--color-success` | Success status |
| `--color-warning` | Warning status |
| `--color-error` | Error status |

### Critical Warnings

**NEVER** hardcode colors in CSS -- ALWAYS use CSS custom properties (`--color-*`). Hardcoded colors break dark mode and custom themes.

**NEVER** use barrel imports (`from '@nextcloud/vue'`) in production when you only need a few components -- use direct imports (`from '@nextcloud/vue/components/NcButton'`) for smaller bundles.

**NEVER** use raw `fetch()` or plain `axios` for HTTP requests -- ALWAYS use `@nextcloud/axios` which handles authentication headers and CSRF tokens automatically.

**NEVER** call `loadState()` without a fallback for optional data -- it throws an `Error` if the key is not found and no fallback is provided.

**NEVER** forget to import `@nextcloud/dialogs/style.css` when using toast notifications -- toasts render without styling.

**NEVER** use `OC.generateUrl()` or other `OC.*` globals in new code -- use the `@nextcloud/router` package instead.

**ALWAYS** use `provideInitialState` (PHP) + `loadState` (JS) for passing server data to the frontend -- NEVER embed data in templates or global variables.

**ALWAYS** use `provideLazyInitialState` with a closure for large or conditional datasets -- eager state is always serialized even if the frontend never reads it.

**ALWAYS** install `@nextcloud/webpack-vue-config` and extend it rather than writing webpack config from scratch.

---

## Decision Trees

### Which HTTP Method to Use from Frontend?

```
Need to make an API call?
--> Use @nextcloud/axios (auto-handles auth + CSRF)
    --> Need URL for app route? --> generateUrl('/apps/myapp/api/items')
    --> Need URL for OCS endpoint? --> generateOcsUrl('/apps/myapp/api/v1/items')
    --> Need URL for WebDAV? --> generateRemoteUrl('dav')
```

### Which Data Transfer Pattern?

```
Need to pass data from PHP to JavaScript?
--> Data always needed on page load? --> provideInitialState (eager)
--> Data conditionally needed? --> provideLazyInitialState (lazy closure)
--> Data changes after page load? --> API call via @nextcloud/axios
```

### Which @nextcloud/files Version?

```
Target Nextcloud version?
--> NC 28-32: @nextcloud/files v3.x
--> NC 33+: @nextcloud/files v4.x
```

---

## Essential Patterns

### Pattern 1: Vue App Entry Point (main.js)

```javascript
import Vue from 'vue'
import App from './App.vue'

const appElement = document.getElementById('content')

new Vue({
    el: appElement,
    render: h => h(App),
})
```

### Pattern 2: Authenticated API Calls

```typescript
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'

// GET request (auth headers automatically included)
const response = await axios.get(generateUrl('/apps/myapp/api/items'))

// POST with data
await axios.post(generateUrl('/apps/myapp/api/items'), {
    title: 'New Item',
    content: 'Body text',
})

// Retry during maintenance mode
const data = await axios.get(generateUrl('/apps/myapp/api/data'), {
    retryIfMaintenanceMode: true,
})
```

### Pattern 3: Initial State (PHP to JavaScript)

**PHP side (in controller):**

```php
use OCP\AppFramework\Services\IInitialState;

public function __construct(
    string $appName,
    IRequest $request,
    private IInitialState $initialState,
) {
    parent::__construct($appName, $request);
}

public function index(): TemplateResponse {
    $this->initialState->provideInitialState('config', $config);
    $this->initialState->provideLazyInitialState('heavy_data', function() {
        return $this->service->getExpensiveData();
    });
    return new TemplateResponse('myapp', 'main');
}
```

**JavaScript side:**

```typescript
import { loadState } from '@nextcloud/initial-state'

// With fallback (ALWAYS provide for optional state)
const config = loadState('myapp', 'config', { refreshInterval: 15000 })

// TypeScript typed
interface AppConfig { refreshInterval: number; maxItems: number }
const typedConfig = loadState<AppConfig>('myapp', 'config', {
    refreshInterval: 15000,
    maxItems: 50,
})
```

### Pattern 4: Toast Notifications

```typescript
import { showSuccess, showError, showWarning, showInfo } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'  // REQUIRED

showSuccess('Item saved successfully')
showError('Failed to save item')

// Persistent toast (no auto-dismiss)
showError('Critical error occurred', { timeout: -1 })
```

### Pattern 5: Webpack Configuration

```javascript
// webpack.config.js -- minimal setup
const webpackConfig = require('@nextcloud/webpack-vue-config')
module.exports = webpackConfig
```

```json
// package.json scripts
{
  "scripts": {
    "build": "webpack --node-env production --progress",
    "dev": "webpack --node-env development --progress",
    "watch": "webpack --node-env development --progress --watch",
    "serve": "webpack --node-env development serve --progress"
  }
}
```

### Pattern 6: CSS Theming

```css
.my-component {
    background-color: var(--color-main-background);
    color: var(--color-main-text);
    border: 1px solid var(--color-primary-element);
}

.my-secondary-text {
    color: var(--color-text-maxcontrast);
}
```

---

## Frontend App Structure

```
myapp/
├── src/
│   ├── main.js          # Vue app entry point
│   ├── App.vue          # Root Vue component
│   ├── components/      # Reusable Vue components
│   ├── views/           # Page-level components
│   ├── store/           # Vuex/Pinia store
│   └── services/        # API service layer
├── css/                 # Global stylesheets (SCSS supported natively)
├── js/                  # Compiled output (generated by webpack)
├── webpack.config.js    # Extends @nextcloud/webpack-vue-config
└── package.json
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- @nextcloud/vue components, @nextcloud/* package APIs
- [references/examples.md](references/examples.md) -- Vue app setup, data fetching, component usage
- [references/anti-patterns.md](references/anti-patterns.md) -- Frontend mistakes

### Official Sources

- https://github.com/nextcloud-libraries/nextcloud-vue
- https://github.com/nextcloud-libraries/nextcloud-axios
- https://github.com/nextcloud-libraries/nextcloud-router
- https://github.com/nextcloud-libraries/nextcloud-initial-state
- https://github.com/nextcloud-libraries/nextcloud-dialogs
- https://github.com/nextcloud-libraries/nextcloud-files
- https://github.com/nextcloud-libraries/nextcloud-event-bus
- https://github.com/nextcloud-libraries/webpack-vue-config
- https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/js.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/css.html
- https://docs.nextcloud.com/server/latest/developer_manual/design/foundations.html
