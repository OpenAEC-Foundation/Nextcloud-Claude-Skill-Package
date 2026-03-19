# Deep Research — Nextcloud Frontend & Events (Part 2 of 3)

Research Date: 2026-03-19
Scope: Vue.js Frontend, Data Fetching, Event System, DI, App Structure & Bootstrap

---

## §7: Vue.js Frontend Development

### Overview

Nextcloud provides a comprehensive Vue.js component library (`@nextcloud/vue`) and build tooling (`@nextcloud/webpack-vue-config`) for developing app frontends. As of NC 28+, the ecosystem supports both Vue 2 (v8.x of the component library) and Vue 3 (v9.x). The component library ensures visual consistency across all Nextcloud apps by providing pre-styled, accessible UI components that automatically support theming and dark mode.

### Key Interfaces/APIs

#### @nextcloud/vue Version Compatibility

| Library Version | Vue Version | Nextcloud Version | Status |
|----------------|-------------|-------------------|--------|
| v9.x (main)   | Vue 3       | NC 31+            | Current |
| v8.x (stable8) | Vue 2      | NC 28+            | Stable  |
| v7.x (stable7) | Vue 2      | NC 25-27          | Legacy  |

#### Core Components

The `@nextcloud/vue` library provides these key components (prefixed with `Nc`):

**Layout Components:**
- `NcContent` — Root wrapper for app content area
- `NcAppContent` — Main content panel
- `NcAppNavigation` — Left sidebar navigation
- `NcAppSidebar` — Right detail sidebar
- `NcAppNavigationItem` — Navigation list entry

**Interactive Components:**
- `NcButton` — Styled button with icon support
- `NcActionButton` — Button inside action menus
- `NcActions` — Dropdown action menu container
- `NcDialog` — Modal dialog wrapper
- `NcModal` — Full modal overlay
- `NcSelect` — Dropdown select input
- `NcTextField` — Text input field

**Display Components:**
- `NcListItem` — Standardized list entry
- `NcAvatar` — User avatar with fallback
- `NcBreadcrumbs` — Path breadcrumb navigation
- `NcEmptyContent` — Placeholder for empty states
- `NcProgressBar` — Progress indicator
- `NcRichText` — Markdown/rich text renderer
- `NcDashboardWidget` — Dashboard card widget
- `NcSettingsSection` — Settings page section wrapper

#### Import Patterns

```typescript
// RECOMMENDED: Direct component import (tree-shakeable, smaller bundles)
import NcButton from '@nextcloud/vue/components/NcButton'
import { useHotKey } from '@nextcloud/vue/composables/useHotKey'

// ALTERNATIVE: Barrel import (impacts bundle size)
import { NcButton, useHotKey } from '@nextcloud/vue'
```

#### Installation

```bash
# For NC 28+ (Vue 2)
npm i @nextcloud/vue@^8.0.0

# For NC 31+ (Vue 3)
npm i @nextcloud/vue@next
```

### Frontend App Structure

Standard Nextcloud app frontend directory layout:

```
myapp/
├── src/
│   ├── main.js          # Vue app entry point
│   ├── App.vue          # Root Vue component
│   ├── components/      # Reusable Vue components
│   ├── views/           # Page-level components
│   ├── store/           # Vuex/Pinia store
│   └── services/        # API service layer
├── css/                 # Global stylesheets
├── js/                  # Compiled output (generated)
├── webpack.config.js    # Build configuration
└── package.json
```

#### Vue App Mounting (main.js)

```javascript
import Vue from 'vue'
import App from './App.vue'

const appElement = document.getElementById('content')

new Vue({
    el: appElement,
    render: h => h(App),
})
```

### Webpack Configuration

Nextcloud provides `@nextcloud/webpack-vue-config` as a pre-configured webpack base:

```javascript
// webpack.config.js — minimal setup
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

**Extending with custom entry points:**

```javascript
const path = require('path')
const webpackConfig = require('@nextcloud/webpack-vue-config')

webpackConfig.entry['custom-entry'] = path.join(__dirname, 'src', 'custom.js')

module.exports = webpackConfig
```

**Vue version notes:** Vue 3 is the default for the webpack config. For Vue 2 support (NC 28-30), install `npm i -D vue-loader@legacy`.

**Hot Module Replacement:** Supported via the `serve` command. Requires the HMREnabler Nextcloud app to adjust Content Security Policy headers for the dev server.

### CSS/SCSS Patterns

#### SCSS Native Support

Nextcloud compiles SCSS natively — rename `.css` to `.scss` and the server handles compilation and caching. When both `.css` and `.scss` exist with the same name, SCSS takes priority.

```php
// Include in PHP template
style('myapp', 'style');          // loads css/style.(s)css
style('myapp', ['style', 'nav']); // multiple files
vendor_style('myapp', 'lib');     // loads vendor/lib.(s)css
```

#### CSS Custom Properties (Theming Variables)

Nextcloud provides server-side CSS custom properties that MUST be used for consistent theming:

| Variable | Purpose | Light Default | Dark Default |
|----------|---------|---------------|--------------|
| `--color-primary-element` | Primary brand color | #0082C9 | #0082C9 |
| `--color-main-background` | Main background | #FFFFFF | #181818 |
| `--color-main-text` | Primary text | #222222 | #D8D8D8 |
| `--color-text-maxcontrast` | Secondary/muted text | #767676 | #8C8C8C |
| `--color-info` | Info status | #006AA3 | #006AA3 |
| `--color-success` | Success status | #46BA61 | #46BA61 |
| `--color-warning` | Warning status | #ECA700 | #ECA700 |
| `--color-error` | Error status | #E9322D | #E9322D |

**Usage example:**

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

#### JavaScript Theming API

When the theming app is enabled:

```javascript
if (OCA.Theming) {
    console.log(OCA.Theming.color)    // Primary color
    console.log(OCA.Theming.name)     // Instance name
    console.log(OCA.Theming.slogan)   // Instance slogan
    console.log(OCA.Theming.inverted) // Boolean: bright theme needing contrast
}
```

### Anti-Patterns

- **NEVER hardcode colors** — ALWAYS use CSS custom properties (`--color-*`). Hardcoded colors break dark mode and custom themes.
- **NEVER use barrel imports in production** when you only need a few components. Use direct imports (`@nextcloud/vue/components/NcButton`) for smaller bundle sizes.
- **NEVER use `npm link`** for testing `@nextcloud/vue` changes with an app — use `npm pack` and install the tarball instead, as `npm link` causes dependency resolution issues.
- **NEVER access `OCA.Theming` without checking existence first** — the theming app may not be enabled.

### Version Notes

- **NC 28+**: Vue 2 + `@nextcloud/vue` v8.x is the standard frontend stack
- **NC 31+**: Vue 3 migration with `@nextcloud/vue` v9.x
- The primary color (#0082C9) can be customized by admins through the theming app; apps MUST use CSS variables to respect this

---

## §8: Frontend Data Fetching

### Overview

Nextcloud provides a suite of `@nextcloud/*` npm packages for frontend data operations: HTTP requests (`@nextcloud/axios`), URL generation (`@nextcloud/router`), server-to-client state transfer (`@nextcloud/initial-state`), file operations (`@nextcloud/files`), user notifications (`@nextcloud/dialogs`), and cross-component communication (`@nextcloud/event-bus`).

### Key Interfaces/APIs

#### @nextcloud/axios

A TypeScript wrapper around Axios that automatically sends authentication headers for Nextcloud requests.

```bash
npm install @nextcloud/axios
```

```typescript
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'

// Basic GET request (auth headers automatically included)
const response = await axios.get(generateUrl('/apps/myapp/api/items'))

// Set base URL for all requests
axios.defaults.baseURL = generateUrl('/apps/myapp/api')
const items = await axios.get('/items')

// Retry during maintenance mode
const data = await axios.get('/apps/myapp/api/data', {
    retryIfMaintenanceMode: true,
})

// Auto-reload on expired session
const result = await axios.get('/apps/myapp/api/secure', {
    reloadExpiredSession: true,
})
```

#### @nextcloud/router — URL Generation

```bash
npm install @nextcloud/router
```

Key functions (based on legacy `OC.generateUrl` patterns):

```javascript
import { generateUrl } from '@nextcloud/router'

// Generate app API URL
const url = generateUrl('/apps/myapp/api/items/{id}', { id: 42 })

// OCS API URL
import { generateOcsUrl } from '@nextcloud/router'
const ocsUrl = generateOcsUrl('/apps/myapp/api/v1/items')

// Remote endpoint URL (for WebDAV)
import { generateRemoteUrl } from '@nextcloud/router'
const davUrl = generateRemoteUrl('dav')

// File path URL
import { generateFilePath } from '@nextcloud/router'
const filePath = generateFilePath('myapp', 'img', 'icon.svg')
```

Legacy equivalent (still works but avoid in new code):

```javascript
const url = OC.generateUrl('/apps/myapp/authors/1')
```

#### @nextcloud/initial-state — Server-Side Data Injection

This is the primary mechanism for passing data from PHP to the JavaScript frontend.

**PHP side (controller or middleware):**

```php
use OCP\AppFramework\Services\IInitialState;

class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private IInitialState $initialState
    ) {
        parent::__construct($appName, $request);
    }

    /**
     * @NoCSRFRequired
     * @NoAdminRequired
     */
    public function index(): TemplateResponse {
        // Eager: always serialized (use for data that's always needed)
        $this->initialState->provideInitialState('user_preference', $preference);

        // Lazy: only serialized if actually loaded (use for conditional data)
        $this->initialState->provideLazyInitialState('heavy_data', function() {
            return $this->service->getExpensiveData();
        });

        return new TemplateResponse('myapp', 'main');
    }
}
```

**JavaScript/TypeScript side:**

```typescript
import { loadState } from '@nextcloud/initial-state'

// Basic usage
const preference = loadState('myapp', 'user_preference')

// With fallback (prevents throw on missing key)
const fallback = loadState('myapp', 'user_preference', 'default_value')

// TypeScript typed
interface AppConfig {
    refreshInterval: number
    maxItems: number
}

const config = loadState<AppConfig>('myapp', 'app_config', {
    refreshInterval: 15000,
    maxItems: 50,
})
```

**IMPORTANT:** `loadState()` throws an `Error` if the key is not found and no fallback is provided. ALWAYS provide a fallback for optional state or wrap in try/catch.

#### @nextcloud/files — File/Folder Classes & DAV Client

```bash
npm install @nextcloud/files
```

**Version compatibility:**
| @nextcloud/files | Nextcloud |
|-----------------|-----------|
| v4.x           | NC 33+    |
| v3.x           | NC 26-32  |

**WebDAV operations from frontend:**

```typescript
import { getClient, getDefaultPropfind, resultToNode } from '@nextcloud/files/dav'

// Get authenticated WebDAV client
const client = getClient()

// List directory contents
const results = await client.getDirectoryContents('/files/username/Documents', {
    details: true,
    data: getDefaultPropfind(),
})

// Convert to typed Node objects
const nodes = results.data.map(r => resultToNode(r))

// Get favorites
import { getFavoriteNodes } from '@nextcloud/files/dav'
const favorites = await getFavoriteNodes(client)
```

**Permission enum:**

```typescript
import { Permission } from '@nextcloud/files'

Permission.READ    // 1
Permission.UPDATE  // 2
Permission.CREATE  // 4
Permission.DELETE  // 8
Permission.SHARE   // 16
```

**Files app integration — register "New" menu entry:**

```typescript
import type { Entry } from '@nextcloud/files'
import { addNewFileMenuEntry } from '@nextcloud/files'

const entry: Entry = {
    id: 'my-app-new-doc',
    displayName: t('myapp', 'New Document'),
    iconSvgInline: '<svg>...</svg>',
    handler(context, content) {
        // Create new file in context folder
    },
}
addNewFileMenuEntry(entry)
```

**Sidebar tab registration:**

```typescript
import { getSidebar } from '@nextcloud/files'

getSidebar().registerTab({
    id: 'my-app-tab',
    displayName: 'My Tab',
    iconSvgInline: '<svg>...</svg>',
    order: 50,
    tagName: 'my-app-sidebar-tab',  // custom web component
    enabled({ node, folder, view }) {
        return node.mime === 'application/pdf'
    },
})
```

#### @nextcloud/dialogs — Toasts & File Picker

```bash
npm install @nextcloud/dialogs
```

**Toast notifications:**

```typescript
import { showSuccess, showError, showWarning, showInfo, showMessage } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'  // REQUIRED: import styles

showSuccess('Item saved successfully')
showError('Failed to save item')
showWarning('Connection unstable')
showInfo('New version available')

// Persistent toast (no auto-dismiss)
showError('Critical error occurred', { timeout: -1 })
```

**File picker:**

```typescript
import { getFilePickerBuilder } from '@nextcloud/dialogs'

const picker = getFilePickerBuilder('Select a text file')
    .addMimeTypeFilter('text/plain')
    .addButton({
        label: 'Pick',
        callback: (nodes) => console.log('Selected:', nodes),
    })
    .build()

const paths = await picker.pick()
```

#### @nextcloud/event-bus — Frontend Event Communication

```bash
npm install @nextcloud/event-bus
```

```typescript
import { emit, subscribe, unsubscribe } from '@nextcloud/event-bus'

// Subscribe to events
const handler = (event) => console.log('File uploaded:', event)
subscribe('files:node:uploaded', handler)

// Emit events
emit('files:node:updated', updatedNode)

// Unsubscribe when done
unsubscribe('files:node:uploaded', handler)
```

**Event naming convention:** `app-id:object:verb`

Common built-in events:
- `files:node:uploading` / `files:node:uploaded` / `files:node:deleted`
- `nextcloud:unified-search:closed`
- `calendar:event:created`
- `contacts:contact:deleted`

**TypeScript typed events:**

```typescript
// In a .d.ts file
declare module '@nextcloud/event-bus' {
    interface NextcloudEvents {
        'myapp:item:created': { id: number; name: string }
        'myapp:item:deleted': { id: number }
    }
}
export {}

// Usage with full type inference
subscribe('myapp:item:created', (event) => {
    console.log(event.id)   // TypeScript knows this is number
    console.log(event.name) // TypeScript knows this is string
})
```

### Anti-Patterns

- **NEVER use `OC.generateUrl()` in new code** — use `import { generateUrl } from '@nextcloud/router'` instead. The `OC.*` global API is legacy.
- **NEVER forget to import `@nextcloud/dialogs/style.css`** — toasts will render without styling.
- **NEVER call `loadState()` without a fallback for optional data** — it throws on missing keys.
- **NEVER use raw `fetch()` or plain `axios`** — use `@nextcloud/axios` which handles authentication headers and CSRF tokens automatically.
- **NEVER forget CSRF token in non-jQuery requests** — if not using `@nextcloud/axios`, set the `requesttoken` header from `OC.requestToken`.
- **NEVER use `provideInitialState` for large datasets** — use `provideLazyInitialState` with a closure so it's only serialized when the frontend actually loads it.

### Version Notes

- **NC 28+**: All `@nextcloud/*` packages listed above are the standard approach
- **NC 25+**: `OCP.Accessibility.disableKeyboardShortcuts()` available for accessibility compliance
- `@nextcloud/files` v3.x covers NC 26-32; v4.x targets NC 33+. For NC 28 target, use v3.x

---

## §9: Event System

### Overview

Nextcloud's PHP event system enables decoupled communication between apps and core components. The modern approach uses typed event objects extending `\OCP\EventDispatcher\Event`, dispatched via `IEventDispatcher`. This replaced the deprecated hooks system (pre-NC 17) and deprecated `GenericEvent` (pre-NC 22). Events follow a Before/After naming pattern for lifecycle interception.

### Key Interfaces/APIs

#### IEventDispatcher

The central dispatch service, injected via DI:

```php
use OCP\EventDispatcher\IEventDispatcher;
```

Methods:
- `addListener(string $eventName, callable $listener, int $priority = 0): void`
- `addServiceListener(string $eventName, string $className, int $priority = 0): void`
- `dispatchTyped(Event $event): void`

#### IEventListener

Interface for class-based event listeners:

```php
namespace OCP\EventDispatcher;

interface IEventListener {
    public function handle(Event $event): void;
}
```

#### Event Base Class

All typed events extend:

```php
namespace OCP\EventDispatcher;

class Event {
    // Base class — no required methods beyond constructor
}
```

### Code Examples

#### Creating a Custom Event

```php
<?php
namespace OCA\MyApp\Event;

use OCP\EventDispatcher\Event;
use OCP\IUser;

class ItemCreatedEvent extends Event {
    public function __construct(
        private IUser $user,
        private string $itemId,
        private array $data
    ) {
        parent::__construct();
    }

    public function getUser(): IUser {
        return $this->user;
    }

    public function getItemId(): string {
        return $this->itemId;
    }

    public function getData(): array {
        return $this->data;
    }
}
```

#### Registering a Class-Based Listener (Recommended)

```php
<?php
namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Event\ItemCreatedEvent;
use OCA\MyApp\Listener\ItemCreatedListener;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        $context->registerEventListener(
            ItemCreatedEvent::class,
            ItemCreatedListener::class
        );
    }

    public function boot(IBootContext $context): void {
        // Nothing needed here for events
    }
}
```

#### Implementing the Listener

```php
<?php
namespace OCA\MyApp\Listener;

use OCA\MyApp\Event\ItemCreatedEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use Psr\Log\LoggerInterface;

class ItemCreatedListener implements IEventListener {
    public function __construct(
        private LoggerInterface $logger
    ) {
    }

    public function handle(Event $event): void {
        if (!($event instanceof ItemCreatedEvent)) {
            return;
        }

        $this->logger->info('Item created: ' . $event->getItemId(), [
            'user' => $event->getUser()->getUID(),
        ]);
    }
}
```

**Key advantage:** Service listeners are resolved via DI, so constructor injection works for any registered service.

#### Dispatching an Event

```php
<?php
namespace OCA\MyApp\Service;

use OCA\MyApp\Event\ItemCreatedEvent;
use OCP\EventDispatcher\IEventDispatcher;
use OCP\IUserSession;

class ItemService {
    public function __construct(
        private IEventDispatcher $dispatcher,
        private IUserSession $userSession
    ) {
    }

    public function createItem(array $data): void {
        // ... create the item ...

        $event = new ItemCreatedEvent(
            $this->userSession->getUser(),
            $itemId,
            $data
        );
        $this->dispatcher->dispatchTyped($event);
    }
}
```

#### Callback Listener (Simple Cases)

```php
$dispatcher = $container->get(IEventDispatcher::class);
$dispatcher->addListener(ItemCreatedEvent::class, function (ItemCreatedEvent $event) {
    // Quick inline handling
});
```

### Built-In Event Classes

#### File Operations (`OCP\Files\Events\Node\`)
| Event | Trigger |
|-------|---------|
| `BeforeNodeCreatedEvent` | Before file/folder creation |
| `NodeCreatedEvent` | After file/folder creation |
| `BeforeNodeDeletedEvent` | Before deletion |
| `NodeDeletedEvent` | After deletion |
| `BeforeNodeWrittenEvent` | Before content write |
| `NodeWrittenEvent` | After content write |
| `BeforeNodeRenamedEvent` | Before rename/move |
| `NodeRenamedEvent` | After rename/move |
| `BeforeNodeCopiedEvent` | Before copy |
| `NodeCopiedEvent` | After copy |

#### User Management (`OCP\User\Events\`)
| Event | Trigger |
|-------|---------|
| `BeforeUserCreatedEvent` | Before user creation |
| `UserCreatedEvent` | After user creation |
| `BeforeUserDeletedEvent` | Before user deletion |
| `UserDeletedEvent` | After user deletion |
| `BeforePasswordUpdatedEvent` | Before password change |
| `PasswordUpdatedEvent` | After password change |
| `UserLoggedInEvent` | After login |
| `UserLoggedOutEvent` | After logout |

#### Sharing (`OCP\Share\Events\`)
| Event | Trigger |
|-------|---------|
| `BeforeShareCreatedEvent` | Before share creation |
| `ShareCreatedEvent` | After share creation |
| `BeforeShareDeletedEvent` | Before share deletion |
| `ShareDeletedEvent` | After share deletion |

#### Calendar/Contacts (`OCA\DAV\Events\`)
| Event | Trigger |
|-------|---------|
| `CalendarObjectCreatedEvent` | Calendar entry created |
| `CalendarObjectUpdatedEvent` | Calendar entry updated |
| `CardCreatedEvent` | Contact card created |
| `AddressBookCreatedEvent` | Address book created |

#### Authentication (`OCP\Authentication\Events\`)
| Event | Trigger |
|-------|---------|
| `LoginFailedEvent` | Login attempt failed |
| `AnyLoginFailedEvent` | Any login method failed |

#### Group Management (`OCP\Group\Events\`)
| Event | Trigger |
|-------|---------|
| `BeforeGroupCreatedEvent` / `GroupCreatedEvent` | Group lifecycle |
| `BeforeUserAddedEvent` / `UserAddedEvent` | User-group membership |

#### App Lifecycle (`OCP\App\Events\`)
| Event | Trigger |
|-------|---------|
| `AppEnableEvent` | App enabled |
| `AppDisableEvent` | App disabled |
| `AppUpdateEvent` | App updated |

#### Template Rendering (`OCP\AppFramework\Http\Events\`)
| Event | Trigger |
|-------|---------|
| `BeforeTemplateRenderedEvent` | Before template output |
| `BeforeLoginTemplateRenderedEvent` | Before login page render |

### Naming Conventions

- Event class names ALWAYS end with `Event`
- Events dispatched **after** an action: `{Action}Event` (e.g., `UserCreatedEvent`)
- Events dispatched **before** an action: `Before{Action}Event` (e.g., `BeforeUserCreatedEvent`)
- Before-events allow cancellation/modification; After-events are informational

### Anti-Patterns

- **NEVER use deprecated hooks** (`$userManager->listen(...)`) — use typed events with `IEventDispatcher` or `IRegistrationContext::registerEventListener()`.
- **NEVER use `GenericEvent`** — deprecated since NC 22. ALWAYS create typed event classes.
- **NEVER skip the `instanceof` check** in `handle()` — the interface types the parameter as base `Event`, not your specific event class.
- **NEVER dispatch events in constructors** — services may not be fully initialized.
- **NEVER forget to call `parent::__construct()`** in custom event classes.
- **NEVER register event listeners in `boot()`** — ALWAYS use `register()` method or `IRegistrationContext::registerEventListener()` for lazy resolution.

### Version Notes

- **NC 17+**: Typed events introduced
- **NC 20+**: `IBootstrap` with `registerEventListener()` in `register()` method (recommended)
- **NC 22+**: `GenericEvent` deprecated
- **NC 28+**: All apps should use exclusively typed events; hook system is considered legacy

---

## §10: Services & Dependency Injection

### Overview

Nextcloud uses a PSR-11 compatible dependency injection container. Modern apps rely on auto-wiring (constructor parameter type analysis via reflection) rather than explicit service registration. The `IRegistrationContext` interface in `Application.php` provides methods for cases where auto-wiring is insufficient. Constructor injection is the primary pattern for controllers, services, and mappers.

### Key Interfaces/APIs

#### IRegistrationContext Methods

| Method | Purpose |
|--------|---------|
| `registerService(string $class, Closure $factory)` | Explicit factory registration |
| `registerParameter(string $name, $value)` | Register primitive values |
| `registerServiceAlias(string $interface, string $impl)` | Interface-to-implementation binding |
| `registerEventListener(string $event, string $listener)` | Event listener registration |
| `registerMiddleware(string $class)` | Middleware registration |

#### Predefined Injectable Services

**By parameter name (auto-resolved):**
- `$appName` — Application ID string
- `$userId` — Current user ID (nullable if no user session)
- `$webRoot` — Nextcloud installation path

**By type hint (core services):**

| Interface | Purpose |
|-----------|---------|
| `\OCP\IRequest` | Current HTTP request |
| `\OCP\IDBConnection` | Database connection |
| `\OCP\IConfig` | System and app configuration |
| `\OCP\IUserManager` | User CRUD operations |
| `\OCP\IUserSession` | Current user session |
| `\OCP\Files\IRootFolder` | Filesystem root access |
| `\OCP\IL10N` | Localization/translation |
| `\Psr\Log\LoggerInterface` | PSR-3 logger (recommended) |
| `\OCP\Security\ICrypto` | Encryption utilities |
| `\OCP\IURLGenerator` | URL generation |
| `\OCP\IAppConfig` | App-specific configuration |
| `\OCP\ICacheFactory` | Cache factory |

### Code Examples

#### Auto-Wiring (Recommended for NC 28+)

No explicit registration needed — Nextcloud resolves dependencies by analyzing constructor parameter types:

**Requirements:**
1. `<namespace>` declared in `appinfo/info.xml`:

```xml
<info>
    <id>myapp</id>
    <namespace>MyApp</namespace>
    <!-- ... -->
</info>
```

2. Array-style routes in `appinfo/routes.php`:

```php
<?php
return ['routes' => [
    ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
    ['name' => 'api#list', 'url' => '/api/items', 'verb' => 'GET'],
]];
```

3. Type-hinted constructor parameters:

```php
<?php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\IRequest;
use OCA\MyApp\Service\ItemService;

class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private ItemService $itemService
    ) {
        parent::__construct($appName, $request);
    }

    public function index(): TemplateResponse {
        $items = $this->itemService->findAll();
        return new TemplateResponse('myapp', 'main');
    }
}
```

#### Explicit Registration (When Auto-Wiring Fails)

```php
<?php
namespace OCA\MyApp\AppInfo;

use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\IDBConnection;
use Psr\Container\ContainerInterface;
use OCA\MyApp\Service\AuthorService;
use OCA\MyApp\Db\AuthorMapper;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        // Explicit factory when auto-wiring can't determine parameters
        $context->registerService(AuthorService::class,
            function (ContainerInterface $c): AuthorService {
                return new AuthorService($c->get(AuthorMapper::class));
            }
        );

        // Register primitive value
        $context->registerParameter('TableName', 'my_app_authors');

        // Interface binding
        $context->registerServiceAlias(IAuthorMapper::class, AuthorMapper::class);
    }

    public function boot(IBootContext $context): void {
        // Post-registration initialization
    }
}
```

#### Service Layer Pattern

```php
<?php
namespace OCA\MyApp\Service;

use OCA\MyApp\Db\ItemMapper;
use OCP\AppFramework\Db\DoesNotExistException;
use Psr\Log\LoggerInterface;

class ItemService {
    public function __construct(
        private ItemMapper $mapper,
        private LoggerInterface $logger
    ) {
    }

    public function findAll(string $userId): array {
        return $this->mapper->findAll($userId);
    }

    public function find(int $id, string $userId): ?Item {
        try {
            return $this->mapper->find($id, $userId);
        } catch (DoesNotExistException $e) {
            $this->logger->warning('Item not found', [
                'id' => $id,
                'user' => $userId,
            ]);
            return null;
        }
    }
}
```

#### Optional Dependencies

```php
<?php
namespace OCA\MyApp\Service;

use OCA\OptionalApp\Service\OptionalService;

class MyService {
    public function __construct(
        private ?OptionalService $optionalService
    ) {
    }

    public function doSomething(): void {
        if ($this->optionalService !== null) {
            $this->optionalService->integrate();
        }
    }
}
```

#### Logger: PSR-3 LoggerInterface (Recommended)

```php
<?php
use Psr\Log\LoggerInterface;

class MyService {
    public function __construct(
        private LoggerInterface $logger
    ) {
    }

    public function process(): void {
        $this->logger->info('Processing started');
        $this->logger->error('Processing failed', ['exception' => $e]);
        $this->logger->debug('Debug data', ['key' => $value]);
    }
}
```

**IMPORTANT:** Use `Psr\Log\LoggerInterface`, NOT `OCP\ILogger` (deprecated since NC 24).

### Anti-Patterns

- **NEVER use `\OCP\Server::get()` for service resolution in new code** — it's a service locator anti-pattern that makes testing difficult. Use constructor injection.
- **NEVER use `OCP\ILogger`** — deprecated since NC 24. ALWAYS use `Psr\Log\LoggerInterface`.
- **NEVER inject services you don't need** — only inject what the class actually uses.
- **NEVER perform I/O or side effects in constructors** — constructors should only assign dependencies.
- **NEVER register services explicitly when auto-wiring works** — it adds unnecessary complexity. Only use `registerService()` for ambiguous cases.
- **NEVER forget the `<namespace>` element in `info.xml`** — auto-wiring requires it to map `OCA\{Namespace}\*` classes.

### Version Notes

- **NC 20+**: `IBootstrap` interface with `register()` and `boot()` lifecycle
- **NC 24+**: `OCP\ILogger` deprecated in favor of `Psr\Log\LoggerInterface`
- **NC 28+**: Auto-wiring is mature and handles most cases; explicit registration rarely needed

---

## §11: App Structure & Bootstrap

### Overview

Every Nextcloud app follows a standardized directory structure with `appinfo/info.xml` as the manifest, `lib/AppInfo/Application.php` as the bootstrap entry point, and clear conventions for PHP (lib/) and frontend (src/) code. The `IBootstrap` interface (NC 20+) provides a two-phase lifecycle: `register()` for lazy DI setup and `boot()` for post-registration initialization.

### App Directory Layout

```
myapp/
├── appinfo/
│   ├── info.xml              # App manifest (REQUIRED)
│   ├── routes.php            # Route definitions
│   └── database.xml          # Database schema (legacy, prefer migrations)
├── lib/
│   ├── AppInfo/
│   │   └── Application.php   # Bootstrap entry point
│   ├── Controller/            # HTTP controllers
│   ├── Service/               # Business logic layer
│   ├── Db/                    # Entity classes and mappers
│   ├── Listener/              # Event listeners
│   ├── Middleware/             # Request middleware
│   ├── Migration/             # Database migrations
│   └── Command/               # OCC CLI commands
├── src/                       # Vue.js frontend source
│   ├── main.js
│   ├── App.vue
│   └── components/
├── css/                       # Stylesheets (CSS/SCSS)
├── img/                       # Icons and images
│   └── app.svg               # App icon (auto-used for favicon)
├── js/                        # Compiled JS output
├── templates/                 # PHP templates
│   └── main.php              # Main template
├── tests/                     # PHPUnit tests
├── l10n/                      # Translation files
├── CHANGELOG.md               # App store changelog
├── webpack.config.js          # Build configuration
├── package.json               # NPM dependencies
├── composer.json               # PHP dependencies
└── LICENSE
```

### info.xml Manifest

#### Minimal Required Fields

```xml
<?xml version="1.0"?>
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>myapp</id>
    <name>My Application</name>
    <summary>Short description for app listing</summary>
    <description>Full description with **Markdown** support</description>
    <version>1.0.0</version>
    <licence>AGPL-3.0-or-later</licence>
    <author mail="dev@example.com" homepage="https://example.com">Developer Name</author>
    <namespace>MyApp</namespace>
    <category>tools</category>
    <bugs>https://github.com/org/myapp/issues</bugs>
    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
        <php min-version="8.1"/>
    </dependencies>
</info>
```

#### Complete info.xml with All Optional Features

```xml
<?xml version="1.0"?>
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>myapp</id>
    <name>My Application</name>
    <name lang="de">Meine Anwendung</name>
    <summary>Short description</summary>
    <description><![CDATA[Full **markdown** description]]></description>
    <version>1.0.0</version>
    <licence>AGPL-3.0-or-later</licence>
    <author mail="dev@example.com">Dev Name</author>
    <namespace>MyApp</namespace>
    <category>tools</category>
    <category>integration</category>
    <website>https://example.com</website>
    <bugs>https://github.com/org/myapp/issues</bugs>
    <repository type="git">https://github.com/org/myapp</repository>
    <screenshot small-thumbnail="https://example.com/thumb.png">
        https://example.com/screenshot.png
    </screenshot>

    <documentation>
        <user>https://docs.example.com/user</user>
        <admin>https://docs.example.com/admin</admin>
        <developer>https://docs.example.com/dev</developer>
    </documentation>

    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
        <php min-version="8.1" max-version="8.3"/>
        <database>pgsql</database>
        <database>mysql</database>
        <database>sqlite</database>
        <lib min-version="1.0">curl</lib>
        <command>ffmpeg</command>
    </dependencies>

    <!-- Navigation entry -->
    <navigations>
        <navigation>
            <name>My App</name>
            <route>myapp.page.index</route>
            <icon>app.svg</icon>
            <order>10</order>
        </navigation>
    </navigations>

    <!-- Background jobs -->
    <background-jobs>
        <job>OCA\MyApp\Cron\CleanupJob</job>
    </background-jobs>

    <!-- Database repair/migration steps -->
    <repair-steps>
        <install>
            <step>OCA\MyApp\Migration\InstallStep</step>
        </install>
        <post-migration>
            <step>OCA\MyApp\Migration\PostMigrationStep</step>
        </post-migration>
        <uninstall>
            <step>OCA\MyApp\Migration\UninstallStep</step>
        </uninstall>
    </repair-steps>

    <!-- OCC commands -->
    <commands>
        <command>OCA\MyApp\Command\ProcessQueue</command>
    </commands>

    <!-- Settings pages -->
    <settings>
        <admin>OCA\MyApp\Settings\Admin</admin>
        <admin-section>OCA\MyApp\Settings\AdminSection</admin-section>
    </settings>

    <!-- Activity app integration -->
    <activity>
        <settings>
            <setting>OCA\MyApp\Activity\Setting</setting>
        </settings>
        <providers>
            <provider>OCA\MyApp\Activity\Provider</provider>
        </providers>
    </activity>
</info>
```

#### info.xml Field Constraints

| Field | Constraint |
|-------|-----------|
| `id` | Lowercase ASCII + underscore only |
| `version` | Semantic versioning, no build metadata |
| `licence` | SPDX identifiers only |
| `screenshot` | HTTPS URL required |
| `dependencies/nextcloud` | Both `min-version` and `max-version` required |
| Valid categories | customization, files, games, integration, monitoring, multimedia, office, organization, security, social, tools |

**Deprecated fields (cause validation failure):** standalone, default_enable, shipped, public, remote, requiremin, requiremax

### Application.php — IBootstrap Interface

```php
<?php
namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Listener\UserDeletedListener;
use OCA\MyApp\Middleware\AuthMiddleware;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\User\Events\BeforeUserDeletedEvent;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    /**
     * Phase 1: Register services, listeners, middleware LAZILY.
     * Called early — other apps' services NOT yet available.
     * ONLY use $context API methods here.
     */
    public function register(IRegistrationContext $context): void {
        // Include Composer autoloader if needed
        include_once __DIR__ . '/../../vendor/autoload.php';

        // Register event listeners
        $context->registerEventListener(
            BeforeUserDeletedEvent::class,
            UserDeletedListener::class
        );

        // Register middleware
        $context->registerMiddleware(AuthMiddleware::class);

        // Register service aliases
        $context->registerServiceAlias(IMyInterface::class, MyImplementation::class);
    }

    /**
     * Phase 2: Execute initialization code.
     * Called AFTER all apps have completed register().
     * All services are now available via DI.
     */
    public function boot(IBootContext $context): void {
        $context->injectFn(function (IFooManager $manager) {
            $manager->registerCustomFoo(MyFooImpl::class);
        });
    }
}
```

### Bootstrap Sequence (NC 20+)

1. Nextcloud scans enabled apps for `lib/AppInfo/Application.php`
2. Apps with `IBootstrap` → `register()` called (in order of app dependencies)
3. App load groups processed (filesystem, session, etc.) in priority order
4. All `Application` classes fully instantiated
5. All `boot()` methods called — prior registrations guaranteed complete
6. Request routing begins

**Critical rule:** In `register()`, ONLY use the `IRegistrationContext` API. Do NOT query other services — they may not be registered yet.

### Namespace Conventions and Autoloading

Nextcloud autoloads app classes from the `OCA\{Namespace}` prefix:

| info.xml namespace | PHP namespace | File path |
|-------------------|---------------|-----------|
| `<namespace>MyApp</namespace>` | `OCA\MyApp\Controller\PageController` | `lib/Controller/PageController.php` |
| | `OCA\MyApp\Service\ItemService` | `lib/Service/ItemService.php` |
| | `OCA\MyApp\Db\ItemMapper` | `lib/Db/ItemMapper.php` |
| | `OCA\MyApp\AppInfo\Application` | `lib/AppInfo/Application.php` |

The namespace in `info.xml` determines the `OCA\{Namespace}` prefix. Nextcloud's autoloader maps this to the `lib/` directory automatically.

### App Scaffolding

Use the official app generator: https://apps.nextcloud.com/developer/apps/generate

This creates a downloadable skeleton with the correct directory structure, info.xml, Application.php, and basic controller setup without publishing to the app store.

### Anti-Patterns

- **NEVER query services in `register()`** — other apps' registrations are not yet complete. Only use `IRegistrationContext` methods.
- **NEVER omit `<namespace>` from info.xml** — the autoloader and DI container depend on it.
- **NEVER use deprecated `requiremin`/`requiremax`** — use `<dependencies><nextcloud min-version="" max-version=""/>` instead.
- **NEVER omit `min-version` or `max-version`** in the nextcloud dependency — both are required for app store validation.
- **NEVER put business logic in Application.php** — keep it in Service/ classes. Application.php should only contain registration and boot wiring.
- **NEVER use `database.xml`** for new apps — use migrations in `lib/Migration/` instead.
- **NEVER include sensitive data in info.xml** — it's publicly readable.

### Version Notes

- **NC 20+**: `IBootstrap` with two-phase `register()`/`boot()` lifecycle
- **NC 28+**: All apps MUST use `IBootstrap`; legacy `Application` constructors with service resolution are discouraged
- **NC 29+**: `CHANGELOG.language.md` support for localized changelogs in the update notification app
- **NC 31+**: `@nextcloud/vue` v9.x with Vue 3; v8.x (Vue 2) remains supported for NC 28-30

---

## Sources Consulted

| URL | Status | Content |
|-----|--------|---------|
| https://docs.nextcloud.com/server/latest/developer_manual/client_apis/OCS/index.html | OK | OCS API index |
| https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end.html | 404 | Not found |
| https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/js.html | OK | Frontend JS guide |
| https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/css.html | OK | CSS/SCSS guide |
| https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/theming.html | OK | Theming guide |
| https://docs.nextcloud.com/server/latest/developer_manual/design/foundations.html | OK | CSS variables |
| https://docs.nextcloud.com/server/latest/developer_manual/basics/events.html | OK | Event system |
| https://docs.nextcloud.com/server/latest/developer_manual/basics/dependency_injection.html | OK | DI guide |
| https://docs.nextcloud.com/server/latest/developer_manual/app_development/intro.html | OK | App structure |
| https://docs.nextcloud.com/server/latest/developer_manual/app_development/bootstrap.html | OK | Bootstrap guide |
| https://docs.nextcloud.com/server/latest/developer_manual/app_development/info.html | OK | info.xml manifest |
| https://docs.nextcloud.com/server/latest/developer_manual/basics/info.html | 404 | Redirects to above |
| https://docs.nextcloud.com/server/latest/developer_manual/basics/bootstrapping.html | 404 | Redirects to above |
| https://github.com/nextcloud-libraries/nextcloud-vue | OK | Component library |
| https://github.com/nextcloud-libraries/nextcloud-axios | OK | HTTP client |
| https://github.com/nextcloud-libraries/nextcloud-router | Partial | URL generation |
| https://github.com/nextcloud-libraries/nextcloud-dialogs | OK | Toasts & FilePicker |
| https://github.com/nextcloud-libraries/nextcloud-files | OK | File/Folder classes |
| https://github.com/nextcloud-libraries/nextcloud-initial-state | OK | Initial state |
| https://github.com/nextcloud-libraries/nextcloud-event-bus | OK | Frontend events |
| https://github.com/nextcloud-libraries/webpack-vue-config | OK | Webpack config |
| https://www.npmjs.com/package/@nextcloud/axios | 403 | Blocked |
| https://www.npmjs.com/package/@nextcloud/router | 403 | Blocked |
