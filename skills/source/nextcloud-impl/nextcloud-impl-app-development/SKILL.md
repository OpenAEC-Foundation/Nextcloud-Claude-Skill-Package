---
name: nextcloud-impl-app-development
description: "Guides full-stack Nextcloud app development workflow including creating controllers with routes, implementing service layer with DI, database entities and mappers, Vue.js frontend with @nextcloud packages, initial state bridge between PHP and JavaScript, and the development lifecycle. Activates when building a complete Nextcloud app, connecting PHP backend to Vue.js frontend, or implementing CRUD operations."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-impl-app-development

## Quick Reference

### Full-Stack App Layer Map

| Layer | PHP (Backend) | Vue.js (Frontend) |
|-------|--------------|-------------------|
| Entry point | `lib/AppInfo/Application.php` | `src/main.js` |
| Routing | `appinfo/routes.php` | `@nextcloud/router` |
| Controllers | `lib/Controller/*.php` | N/A |
| Services | `lib/Service/*.php` | `src/services/*.js` |
| Data access | `lib/Db/Entity.php` + `Mapper.php` | `@nextcloud/axios` |
| State bridge | `IInitialState::provideInitialState()` | `loadState()` |
| UI components | N/A | `@nextcloud/vue` |
| Notifications | N/A | `@nextcloud/dialogs` |

### Development Commands

| Command | Purpose |
|---------|---------|
| `npm run dev` | Build frontend for development |
| `npm run build` | Build frontend for production |
| `npm run watch` | Rebuild on file changes |
| `npm run serve` | Dev server with HMR |
| `php occ app:enable myapp` | Enable the app |
| `php occ app:disable myapp` | Disable the app |
| `php occ migrations:migrate myapp` | Run database migrations |

### Critical Warnings

**ALWAYS** set `<namespace>` in `appinfo/info.xml` -- auto-wiring and autoloading depend on it.

**ALWAYS** use `@nextcloud/axios` for HTTP requests -- it handles CSRF tokens and authentication automatically.

**ALWAYS** use `provideInitialState()` in PHP and `loadState()` in JS for server-to-client data -- NEVER inject data via inline scripts or global variables.

**ALWAYS** use CSS custom properties (`--color-*`) for colors -- NEVER hardcode colors (breaks dark mode and theming).

**ALWAYS** use direct component imports (`@nextcloud/vue/components/NcButton`) -- barrel imports increase bundle size.

**NEVER** use `\OCP\Server::get()` for service resolution -- use constructor injection for testability.

**NEVER** use `OCP\ILogger` -- deprecated since NC 24. Use `Psr\Log\LoggerInterface`.

**NEVER** use raw `fetch()` or plain `axios` -- use `@nextcloud/axios` which handles auth headers automatically.

**NEVER** call `loadState()` without a fallback for optional data -- it throws on missing keys.

**NEVER** modify existing migration files -- create new migrations for schema changes.

---

## Decision Tree: Route Type Selection

```
Is this endpoint consumed by external clients or other apps?
├── YES: Will responses need the OCS JSON/XML envelope?
│   ├── YES → Use OCS route + OCSController
│   │   Route: 'ocs' => [['name' => 'api#method', 'url' => '/api/v1/...']]
│   └── NO → Use regular route + ApiController (adds CORS)
│       Route: 'routes' => [['name' => 'api#method', 'url' => '/api/...']]
└── NO: Internal app use only
    ├── Page rendering? → Use Controller + TemplateResponse
    │   Route: 'routes' => [['name' => 'page#index', 'url' => '/']]
    ├── CRUD resource? → Use resource routes
    │   Route: 'resources' => ['item' => ['url' => '/items']]
    └── AJAX from Vue frontend? → Use regular route + JSONResponse
        Route: 'routes' => [['name' => 'item#create', 'url' => '/items']]
```

---

## Essential Patterns

### Pattern 1: Full-Stack App Creation (Step-by-Step)

**Step 1: App manifest (`appinfo/info.xml`)**
```xml
<?xml version="1.0"?>
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>taskboard</id>
    <name>Task Board</name>
    <summary>Simple task management</summary>
    <description>A task board for managing project tasks</description>
    <version>1.0.0</version>
    <licence>AGPL-3.0-or-later</licence>
    <author>Developer Name</author>
    <namespace>TaskBoard</namespace>
    <category>organization</category>
    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
    </dependencies>
    <navigations>
        <navigation>
            <name>Task Board</name>
            <route>taskboard.page.index</route>
            <icon>app.svg</icon>
        </navigation>
    </navigations>
</info>
```

**Step 2: Application bootstrap (`lib/AppInfo/Application.php`)**
```php
<?php
namespace OCA\TaskBoard\AppInfo;

use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
    public const APP_ID = 'taskboard';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        // Register listeners, middleware, service aliases here
    }

    public function boot(IBootContext $context): void {
        // Cross-app initialization here
    }
}
```

**Step 3: Routes (`appinfo/routes.php`)**
```php
<?php
return [
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
    ],
    'ocs' => [
        ['name' => 'task_api#index', 'url' => '/api/v1/tasks', 'verb' => 'GET'],
        ['name' => 'task_api#show', 'url' => '/api/v1/tasks/{id}', 'verb' => 'GET'],
        ['name' => 'task_api#create', 'url' => '/api/v1/tasks', 'verb' => 'POST'],
        ['name' => 'task_api#update', 'url' => '/api/v1/tasks/{id}', 'verb' => 'PUT'],
        ['name' => 'task_api#destroy', 'url' => '/api/v1/tasks/{id}', 'verb' => 'DELETE'],
    ],
];
```

**Step 4-8: See** [references/examples.md](references/examples.md) for the complete Entity, Mapper, Service, Controller, and Vue.js implementation.

### Pattern 2: Initial State Bridge (PHP to JavaScript)

**PHP side -- provide data in controller:**
```php
use OCP\AppFramework\Services\IInitialState;

class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private IInitialState $initialState,
        private TaskService $service,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        // Eager: always serialized
        $this->initialState->provideInitialState(
            'tasks',
            $this->service->findAll($this->userId)
        );

        // Lazy: only serialized when loaded by frontend
        $this->initialState->provideLazyInitialState(
            'config',
            fn () => $this->service->getConfig()
        );

        return new TemplateResponse('taskboard', 'main');
    }
}
```

**JavaScript side -- consume data:**
```javascript
import { loadState } from '@nextcloud/initial-state'

// ALWAYS provide fallback for optional data
const tasks = loadState('taskboard', 'tasks', [])
const config = loadState('taskboard', 'config', { maxTasks: 100 })
```

### Pattern 3: Frontend API Service Layer

```javascript
// src/services/TaskService.js
import axios from '@nextcloud/axios'
import { generateOcsUrl } from '@nextcloud/router'

const baseUrl = generateOcsUrl('/apps/taskboard/api/v1')

export async function fetchTasks() {
    const response = await axios.get(`${baseUrl}/tasks`)
    return response.data.ocs.data
}

export async function createTask(title, description) {
    const response = await axios.post(`${baseUrl}/tasks`, { title, description })
    return response.data.ocs.data
}

export async function updateTask(id, data) {
    const response = await axios.put(`${baseUrl}/tasks/${id}`, data)
    return response.data.ocs.data
}

export async function deleteTask(id) {
    await axios.delete(`${baseUrl}/tasks/${id}`)
}
```

### Pattern 4: Vue.js App Entry Point

```javascript
// src/main.js
import Vue from 'vue'
import App from './App.vue'

const appElement = document.getElementById('content')
new Vue({
    el: appElement,
    render: h => h(App),
})
```

```html
<!-- templates/main.php -->
<?php
script('taskboard', 'taskboard-main');
style('taskboard', 'main');
?>
<div id="content"></div>
```

### Pattern 5: Vue Component with Nextcloud UI

```vue
<!-- src/App.vue -->
<template>
    <NcContent app-name="taskboard">
        <NcAppNavigation>
            <NcAppNavigationItem v-for="task in tasks"
                :key="task.id"
                :name="task.title"
                @click="selectTask(task)" />
        </NcAppNavigation>
        <NcAppContent>
            <NcEmptyContent v-if="!selectedTask"
                name="No task selected"
                description="Select a task from the sidebar">
            </NcEmptyContent>
            <div v-else class="task-detail">
                <h2>{{ selectedTask.title }}</h2>
                <p>{{ selectedTask.description }}</p>
            </div>
        </NcAppContent>
    </NcContent>
</template>

<script>
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'
import NcAppNavigation from '@nextcloud/vue/components/NcAppNavigation'
import NcAppNavigationItem from '@nextcloud/vue/components/NcAppNavigationItem'
import NcEmptyContent from '@nextcloud/vue/components/NcEmptyContent'
import { loadState } from '@nextcloud/initial-state'
import { showSuccess, showError } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'
import { fetchTasks, deleteTask } from './services/TaskService'

export default {
    name: 'App',
    components: {
        NcContent,
        NcAppContent,
        NcAppNavigation,
        NcAppNavigationItem,
        NcEmptyContent,
    },
    data() {
        return {
            tasks: loadState('taskboard', 'tasks', []),
            selectedTask: null,
        }
    },
    methods: {
        selectTask(task) {
            this.selectedTask = task
        },
    },
}
</script>

<style scoped>
.task-detail {
    padding: 20px;
    color: var(--color-main-text);
}
</style>
```

### Pattern 6: Webpack Configuration

```javascript
// webpack.config.js
const webpackConfig = require('@nextcloud/webpack-vue-config')
module.exports = webpackConfig
```

```json
// package.json (relevant sections)
{
    "scripts": {
        "build": "webpack --node-env production --progress",
        "dev": "webpack --node-env development --progress",
        "watch": "webpack --node-env development --progress --watch",
        "serve": "webpack --node-env development serve --progress"
    },
    "dependencies": {
        "@nextcloud/axios": "^2.0.0",
        "@nextcloud/dialogs": "^5.0.0",
        "@nextcloud/initial-state": "^2.0.0",
        "@nextcloud/router": "^3.0.0",
        "@nextcloud/vue": "^8.0.0",
        "vue": "^2.7.0"
    },
    "devDependencies": {
        "@nextcloud/webpack-vue-config": "^6.0.0"
    }
}
```

---

## Development Lifecycle

### New App Checklist

1. **Scaffold** -- Use https://apps.nextcloud.com/developer/apps/generate or create manually
2. **Configure** -- Set `info.xml` with correct `<namespace>`, `<dependencies>`, `<navigations>`
3. **Backend** -- Create Entity, Mapper, Service, Controller chain
4. **Database** -- Create migration in `lib/Migration/`
5. **Routes** -- Define in `appinfo/routes.php`
6. **Frontend** -- Set up `src/main.js`, `App.vue`, webpack config
7. **Bridge** -- Connect PHP and JS via `IInitialState` / `loadState()`
8. **Build** -- Run `npm install && npm run build`
9. **Enable** -- Run `php occ app:enable myapp`
10. **Test** -- Verify in browser, check browser console and Nextcloud log

### File Naming Conventions

| Layer | Convention | Example |
|-------|-----------|---------|
| Entity | Singular PascalCase | `lib/Db/Task.php` |
| Mapper | Entity + `Mapper` | `lib/Db/TaskMapper.php` |
| Service | Entity + `Service` | `lib/Service/TaskService.php` |
| Controller | Entity + `Controller` or `ApiController` | `lib/Controller/TaskApiController.php` |
| Migration | `Version{MMDD}Date{timestamp}` | `lib/Migration/Version1000Date20240101000000.php` |
| Vue component | PascalCase `.vue` | `src/components/TaskItem.vue` |
| JS service | PascalCase `.js` | `src/services/TaskService.js` |

---

## Reference Links

- [references/methods.md](references/methods.md) -- Full-stack development patterns and API reference
- [references/examples.md](references/examples.md) -- Complete app example: Entity, Mapper, Service, Controller, Vue.js
- [references/anti-patterns.md](references/anti-patterns.md) -- Development workflow mistakes

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/app_development/intro.html
- https://docs.nextcloud.com/server/latest/developer_manual/app_development/bootstrap.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/controllers.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/storage/database.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/js.html
- https://github.com/nextcloud-libraries/nextcloud-vue
