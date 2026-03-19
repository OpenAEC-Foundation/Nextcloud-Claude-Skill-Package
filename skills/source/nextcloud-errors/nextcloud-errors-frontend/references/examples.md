# Frontend Error Scenarios with Complete Fixes

## Scenario 1: loadState() Crashes App on Missing Initial State

### Symptom
```
Uncaught Error: Could not find initial state "myapp" "user_preferences"
    at loadState (nextcloud-initial-state.js:12)
    at main.js:5
```
The app fails to mount. The error is thrown before Vue initializes.

### Root Cause
The PHP controller does not call `provideInitialState('user_preferences', ...)` on this route, or the key name is misspelled. `loadState()` without a fallback throws when the key is absent from the DOM.

### Fix

**Frontend -- add a fallback value:**

```typescript
import { loadState } from '@nextcloud/initial-state'

// Before (broken) -- throws if key missing
const prefs = loadState('myapp', 'user_preferences')

// After (working) -- returns default if key missing
const prefs = loadState('myapp', 'user_preferences', {
    theme: 'auto',
    pageSize: 25,
})
```

**Backend -- ensure state is provided on every route serving the frontend:**

```php
use OCP\AppFramework\Services\IInitialState;

class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private IInitialState $initialState,
        private IConfig $config,
    ) {
        parent::__construct($appName, $request);
    }

    /**
     * @NoAdminRequired
     * @NoCSRFRequired
     */
    public function index(): TemplateResponse {
        // ALWAYS provide state before returning template
        $this->initialState->provideInitialState(
            'user_preferences',
            $this->config->getUserValue($this->userId, 'myapp', 'preferences', '{}')
        );
        return new TemplateResponse('myapp', 'main');
    }
}
```

**For large or conditional data, use lazy loading:**

```php
// Only serialized if frontend actually calls loadState()
$this->initialState->provideLazyInitialState('heavy_data', function () {
    return $this->service->getExpensiveData();
});
```

---

## Scenario 2: CSRF Failure on Frontend API Call

### Symptom
```
POST https://cloud.example.com/apps/myapp/api/items 401 (Unauthorized)
```
Or in the response body:
```json
{"message": "CSRF check failed"}
```

### Root Cause
The frontend code uses raw `axios` or `fetch()` instead of `@nextcloud/axios`. Raw HTTP clients do not include the Nextcloud CSRF token (`requesttoken`) or session cookies in the correct format.

### Fix

```typescript
// Before (broken) -- raw axios has no CSRF token
import axios from 'axios'
import { generateUrl } from '@nextcloud/router'

const resp = await axios.post(generateUrl('/apps/myapp/api/items'), {
    name: 'New Item',
})

// After (working) -- @nextcloud/axios adds CSRF token automatically
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'

const resp = await axios.post(generateUrl('/apps/myapp/api/items'), {
    name: 'New Item',
})
```

**NEVER** manually set the `requesttoken` header. The `@nextcloud/axios` library handles this. Manual token management is fragile and breaks when tokens rotate.

---

## Scenario 3: CORS Error When Calling Nextcloud API from External App

### Symptom
Browser console:
```
Access to XMLHttpRequest at 'https://cloud.example.com/apps/myapp/api/data'
from origin 'https://external-app.example.com' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

### Root Cause
The backend controller extends `Controller` or `OCSController`, neither of which sets CORS headers. Only `ApiController` provides CORS support.

### Fix

**Backend change required -- switch to ApiController:**

```php
// Before (broken) -- Controller has no CORS support
class DataController extends Controller {
    #[NoAdminRequired]
    public function getData(): JSONResponse {
        return new JSONResponse($this->service->findAll());
    }
}

// After (working) -- ApiController with CORS configuration
use OCP\AppFramework\ApiController;

class DataController extends ApiController {
    public function __construct(
        string $appName,
        IRequest $request,
        private DataService $service,
    ) {
        parent::__construct(
            $appName,
            $request,
            'GET, POST, PUT, DELETE',       // allowed methods
            'Authorization, Content-Type',   // allowed headers
            86400                            // preflight cache (seconds)
        );
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]  // REQUIRED -- browsers cannot send CSRF cross-origin
    public function getData(): JSONResponse {
        return new JSONResponse($this->service->findAll());
    }
}
```

**ALWAYS** add `#[NoCSRFRequired]` to CORS-enabled endpoints. Cross-origin preflight requests (OPTIONS) cannot carry CSRF tokens.

---

## Scenario 4: Toasts Render as Unstyled Text

### Symptom
Calling `showSuccess('Item saved')` renders a plain white rectangle with unstyled text, or the toast appears but is invisible (positioned off-screen or transparent).

### Root Cause
The `@nextcloud/dialogs` CSS file was not imported. The JavaScript functions work independently of the styles, so no error is thrown -- the UI is simply broken.

### Fix

```typescript
// main.js or main.ts -- app entry point

// Before (broken) -- no style import
import { showSuccess, showError } from '@nextcloud/dialogs'

// After (working) -- import CSS once at entry point
import '@nextcloud/dialogs/style.css'
import { showSuccess, showError } from '@nextcloud/dialogs'
```

Import the CSS file exactly ONCE in your app's entry point. Do NOT import it in individual components -- duplicate imports waste bundle space.

---

## Scenario 5: Vue 2 App Fails After Installing @nextcloud/vue v9

### Symptom
```
TypeError: Vue.component is not a function
```
Or:
```
[Vue warn]: Failed to mount component: template or render function not defined
```

### Root Cause
`@nextcloud/vue` v9.x requires Vue 3. Installing it in a Vue 2 project (NC 28-30) causes internal API mismatches because Vue 3 removed `Vue.component()`, `Vue.extend()`, and other Vue 2 APIs.

### Fix

```bash
# Check your current @nextcloud/vue version
npm ls @nextcloud/vue

# For NC 28-30 (Vue 2) -- downgrade to v8
npm install @nextcloud/vue@^8

# For NC 31+ (Vue 3) -- use v9
npm install @nextcloud/vue@^9
```

**Verify all related dependencies match:**

```bash
# NC 28-30 (Vue 2)
npm install vue@^2.7 vue-loader@legacy @nextcloud/vue@^8

# NC 31+ (Vue 3)
npm install vue@^3 vue-loader@^17 @nextcloud/vue@^9
```

---

## Scenario 6: webpack Build Fails with Module Parse Error

### Symptom
```
Module parse failed: Unexpected token (1:0)
You may need an appropriate loader to handle this file type.
| <template>
|   <div>
```

### Root Cause
webpack does not know how to process `.vue` files. Either `vue-loader` is not installed, not configured, or the wrong version is installed for the Vue version in use.

### Fix

**Step 1: Use the official webpack config.**

```javascript
// webpack.config.js
const webpackConfig = require('@nextcloud/webpack-vue-config')
module.exports = webpackConfig
```

**Step 2: Install the correct vue-loader.**

```bash
# For Vue 2 (NC 28-30)
npm install -D vue-loader@legacy

# For Vue 3 (NC 31+)
npm install -D vue-loader@^17
```

**Step 3: Ensure @nextcloud/webpack-vue-config is installed.**

```bash
npm install -D @nextcloud/webpack-vue-config
```

**NEVER** manually configure vue-loader rules when using `@nextcloud/webpack-vue-config`. The base config handles this automatically.

---

## Scenario 7: OC.generateUrl is Not Defined in Bundled Code

### Symptom
```
ReferenceError: OC is not defined
    at ItemService.fetchItems (services/ItemService.js:12)
```

### Root Cause
In webpack-bundled code, the `OC` global is not automatically available. It exists on `window.OC` at runtime in the browser, but webpack's module scope does not expose it. Even if accessed via `window.OC`, this is deprecated.

### Fix

```typescript
// Before (broken) -- legacy global
const url = OC.generateUrl('/apps/myapp/api/items/{id}', { id: 42 })

// After (working) -- modern package
import { generateUrl } from '@nextcloud/router'
const url = generateUrl('/apps/myapp/api/items/{id}', { id: 42 })
```

```bash
# Install if not present
npm install @nextcloud/router
```

---

## Scenario 8: File Picker Does Not Open or Renders Incorrectly

### Symptom
Calling `getFilePickerBuilder().build().pick()` opens a modal that is blank, unstyled, or immediately closes.

### Root Cause
Missing `@nextcloud/dialogs/style.css` import (same root cause as Scenario 4), or the `@nextcloud/files` package version is incompatible with the Nextcloud server version.

### Fix

```typescript
// Ensure CSS is imported at entry point
import '@nextcloud/dialogs/style.css'

// Verify correct @nextcloud/files version
// NC 28-32: @nextcloud/files@^3
// NC 33+:   @nextcloud/files@^4
```

```bash
# Check installed version
npm ls @nextcloud/files

# Fix for NC 28-32
npm install @nextcloud/files@^3
```

---

## Scenario 9: Event Bus Listener Never Fires

### Symptom
`subscribe('files:node:uploaded', handler)` is called but the handler function never executes, even after uploading a file.

### Root Cause
Multiple instances of `@nextcloud/event-bus` are bundled. Each instance has its own isolated event registry. Events emitted on one instance are invisible to listeners on another instance.

### Fix

Ensure `@nextcloud/event-bus` is listed as a **peer dependency**, not a direct dependency, so the app uses the same instance as the Nextcloud host:

```json
// package.json
{
    "peerDependencies": {
        "@nextcloud/event-bus": "^3.0.0"
    },
    "devDependencies": {
        "@nextcloud/event-bus": "^3.0.0"
    }
}
```

If the event bus must be bundled (e.g., for a standalone widget), use the webpack externals configuration to use the global instance:

```javascript
const webpackConfig = require('@nextcloud/webpack-vue-config')

webpackConfig.externals = {
    ...webpackConfig.externals,
    '@nextcloud/event-bus': 'commonjs @nextcloud/event-bus',
}

module.exports = webpackConfig
```

**NEVER** bundle your own copy of `@nextcloud/event-bus` when your app runs inside Nextcloud. The host provides the shared instance.
