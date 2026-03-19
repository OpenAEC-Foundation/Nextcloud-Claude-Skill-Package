# examples.md -- Complete info.xml, Application.php, Directory Structure

## Example 1: Complete info.xml with All Features

```xml
<?xml version="1.0"?>
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>taskmanager</id>
    <name>Task Manager</name>
    <name lang="de">Aufgabenverwaltung</name>
    <summary>Manage tasks and projects within Nextcloud</summary>
    <description><![CDATA[
# Task Manager

A full-featured task management app for Nextcloud.

## Features
- Create and organize tasks
- Assign tasks to users
- Track progress with boards

**Requires Nextcloud 28 or later.**
    ]]></description>
    <version>1.0.0</version>
    <licence>AGPL-3.0-or-later</licence>
    <author mail="dev@example.com" homepage="https://example.com">Developer Name</author>
    <namespace>TaskManager</namespace>
    <category>organization</category>
    <category>tools</category>
    <website>https://example.com/taskmanager</website>
    <bugs>https://github.com/org/taskmanager/issues</bugs>
    <repository type="git">https://github.com/org/taskmanager</repository>
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
    </dependencies>

    <navigations>
        <navigation>
            <name>Tasks</name>
            <route>taskmanager.page.index</route>
            <icon>app.svg</icon>
            <order>10</order>
        </navigation>
    </navigations>

    <background-jobs>
        <job>OCA\TaskManager\Cron\CleanupJob</job>
        <job>OCA\TaskManager\Cron\ReminderJob</job>
    </background-jobs>

    <repair-steps>
        <install>
            <step>OCA\TaskManager\Migration\InstallStep</step>
        </install>
        <post-migration>
            <step>OCA\TaskManager\Migration\PostMigrationStep</step>
        </post-migration>
        <uninstall>
            <step>OCA\TaskManager\Migration\UninstallStep</step>
        </uninstall>
    </repair-steps>

    <commands>
        <command>OCA\TaskManager\Command\ProcessQueue</command>
    </commands>

    <settings>
        <admin>OCA\TaskManager\Settings\Admin</admin>
        <admin-section>OCA\TaskManager\Settings\AdminSection</admin-section>
        <personal>OCA\TaskManager\Settings\Personal</personal>
        <personal-section>OCA\TaskManager\Settings\PersonalSection</personal-section>
    </settings>

    <activity>
        <settings>
            <setting>OCA\TaskManager\Activity\Setting</setting>
        </settings>
        <providers>
            <provider>OCA\TaskManager\Activity\Provider</provider>
        </providers>
    </activity>
</info>
```

---

## Example 2: Minimal info.xml (Bare Minimum for a Working App)

```xml
<?xml version="1.0"?>
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>myapp</id>
    <name>My Application</name>
    <summary>A minimal Nextcloud app</summary>
    <description>A simple app to demonstrate the minimal required fields.</description>
    <version>0.1.0</version>
    <licence>AGPL-3.0-or-later</licence>
    <author>Developer Name</author>
    <namespace>MyApp</namespace>
    <category>tools</category>
    <bugs>https://github.com/org/myapp/issues</bugs>
    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
    </dependencies>
</info>
```

---

## Example 3: Complete Application.php

```php
<?php
declare(strict_types=1);

namespace OCA\TaskManager\AppInfo;

use OCA\TaskManager\Dashboard\TaskWidget;
use OCA\TaskManager\Listener\UserDeletedListener;
use OCA\TaskManager\Listener\FileCreatedListener;
use OCA\TaskManager\Middleware\TaskAuthMiddleware;
use OCA\TaskManager\Notification\Notifier;
use OCA\TaskManager\Search\TaskSearchProvider;
use OCA\TaskManager\Service\ITaskService;
use OCA\TaskManager\Service\TaskService;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\Files\Events\Node\NodeCreatedEvent;
use OCP\User\Events\UserDeletedEvent;

class Application extends App implements IBootstrap {
    public const APP_ID = 'taskmanager';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        // Include Composer autoloader for third-party dependencies
        include_once __DIR__ . '/../../vendor/autoload.php';

        // Event listeners
        $context->registerEventListener(
            UserDeletedEvent::class,
            UserDeletedListener::class
        );
        $context->registerEventListener(
            NodeCreatedEvent::class,
            FileCreatedListener::class
        );

        // Middleware
        $context->registerMiddleware(TaskAuthMiddleware::class);

        // Service alias (interface to implementation)
        $context->registerServiceAlias(ITaskService::class, TaskService::class);

        // Dashboard widget
        $context->registerDashboardWidget(TaskWidget::class);

        // Notification handler
        $context->registerNotifierService(Notifier::class);

        // Unified search provider
        $context->registerSearchProvider(TaskSearchProvider::class);
    }

    public function boot(IBootContext $context): void {
        // Post-registration: all services from all apps available
        // Use injectFn for DI-resolved initialization
    }
}
```

---

## Example 4: Minimal Application.php (Simplest Working Form)

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\AppInfo;

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
        // Register services, listeners, middleware here
    }

    public function boot(IBootContext $context): void {
        // Post-registration initialization here
    }
}
```

---

## Example 5: Complete App Directory Structure (Full-Featured App)

```
taskmanager/
├── appinfo/
│   ├── info.xml                          # App manifest
│   └── routes.php                        # Route definitions
├── lib/
│   ├── AppInfo/
│   │   └── Application.php               # IBootstrap entry point
│   ├── Controller/
│   │   ├── PageController.php            # Page rendering controller
│   │   └── TaskApiController.php         # OCS API controller
│   ├── Service/
│   │   ├── ITaskService.php              # Service interface
│   │   └── TaskService.php               # Business logic
│   ├── Db/
│   │   ├── Task.php                      # Entity class
│   │   └── TaskMapper.php                # Database mapper
│   ├── Listener/
│   │   ├── UserDeletedListener.php       # Cleanup on user deletion
│   │   └── FileCreatedListener.php       # React to file creation
│   ├── Middleware/
│   │   └── TaskAuthMiddleware.php        # Custom auth middleware
│   ├── Migration/
│   │   ├── Version1000Date20240101.php   # Initial schema
│   │   └── Version1001Date20240201.php   # Schema update
│   ├── Command/
│   │   └── ProcessQueue.php              # OCC command
│   ├── Cron/
│   │   ├── CleanupJob.php                # Background cleanup
│   │   └── ReminderJob.php               # Reminder notifications
│   ├── Settings/
│   │   ├── Admin.php                     # Admin settings page
│   │   ├── AdminSection.php              # Admin settings section
│   │   ├── Personal.php                  # Personal settings page
│   │   └── PersonalSection.php           # Personal settings section
│   ├── Dashboard/
│   │   └── TaskWidget.php                # Dashboard widget
│   ├── Notification/
│   │   └── Notifier.php                  # Notification handler
│   ├── Search/
│   │   └── TaskSearchProvider.php        # Unified search provider
│   ├── Activity/
│   │   ├── Setting.php                   # Activity app setting
│   │   └── Provider.php                  # Activity app provider
│   ├── Event/
│   │   ├── TaskCreatedEvent.php          # Custom event
│   │   └── TaskCompletedEvent.php        # Custom event
│   └── Exception/
│       ├── TaskNotFoundException.php     # Custom exception
│       └── TaskForbiddenException.php    # Custom exception
├── src/
│   ├── main.js                           # Vue app entry point
│   ├── App.vue                           # Root Vue component
│   ├── components/
│   │   ├── TaskList.vue
│   │   └── TaskItem.vue
│   ├── views/
│   │   ├── Dashboard.vue
│   │   └── Settings.vue
│   ├── store/
│   │   └── tasks.js                      # Vuex/Pinia store
│   └── services/
│       └── TaskApi.js                    # API service layer
├── css/
│   └── style.scss                        # App styles (SCSS auto-compiled)
├── img/
│   └── app.svg                           # App icon (REQUIRED for navigation)
├── js/                                   # Compiled output (gitignored)
├── templates/
│   └── main.php                          # PHP template
├── tests/
│   ├── Unit/
│   │   └── Service/
│   │       └── TaskServiceTest.php
│   └── Integration/
│       └── Db/
│           └── TaskMapperTest.php
├── l10n/                                 # Translation files
├── webpack.config.js
├── package.json
├── composer.json
├── .gitignore
├── CHANGELOG.md
└── LICENSE
```

---

## Example 6: routes.php with All Route Types

```php
<?php
return [
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
        ['name' => 'page#settings', 'url' => '/settings', 'verb' => 'GET'],
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

---

## Example 7: Vue.js Entry Point (main.js)

```javascript
import Vue from 'vue'
import App from './App.vue'

const appElement = document.getElementById('content')

new Vue({
    el: appElement,
    render: h => h(App),
})
```

---

## Example 8: PHP Template (templates/main.php)

```php
<?php
script('taskmanager', 'taskmanager-main');  // loads js/taskmanager-main.js
style('taskmanager', 'style');              // loads css/style.(s)css
?>

<div id="app-content">
    <div id="content"></div>
</div>
```

---

## Example 9: webpack.config.js

```javascript
const webpackConfig = require('@nextcloud/webpack-vue-config')
module.exports = webpackConfig
```

---

## Example 10: package.json (Minimal)

```json
{
    "name": "taskmanager",
    "version": "1.0.0",
    "private": true,
    "scripts": {
        "build": "webpack --node-env production --progress",
        "dev": "webpack --node-env development --progress",
        "watch": "webpack --node-env development --progress --watch"
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

## Example 11: composer.json (Minimal)

```json
{
    "name": "org/taskmanager",
    "description": "Task management for Nextcloud",
    "license": "AGPL-3.0-or-later",
    "autoload": {
        "psr-4": {
            "OCA\\TaskManager\\": "lib/"
        }
    },
    "require": {
        "php": ">=8.1"
    }
}
```
