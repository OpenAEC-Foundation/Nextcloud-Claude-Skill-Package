# nextcloud-core-architecture — Code Examples

## Complete Application.php with IBootstrap

```php
<?php
namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Listener\UserDeletedListener;
use OCA\MyApp\Listener\ItemCreatedListener;
use OCA\MyApp\Event\ItemCreatedEvent;
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

    public function register(IRegistrationContext $context): void {
        // Include Composer autoloader if needed
        include_once __DIR__ . '/../../vendor/autoload.php';

        // Event listeners
        $context->registerEventListener(
            BeforeUserDeletedEvent::class,
            UserDeletedListener::class
        );
        $context->registerEventListener(
            ItemCreatedEvent::class,
            ItemCreatedListener::class
        );

        // Middleware
        $context->registerMiddleware(AuthMiddleware::class);

        // Interface binding (when auto-wiring cannot determine implementation)
        $context->registerServiceAlias(IMyInterface::class, MyImplementation::class);

        // Primitive parameter
        $context->registerParameter('TableName', 'my_app_items');
    }

    public function boot(IBootContext $context): void {
        // Safe to query cross-app services here
        $context->injectFn(function (IFooManager $manager) {
            $manager->registerCustomFoo(MyFooImpl::class);
        });
    }
}
```

---

## Dependency Injection Patterns

### Auto-Wiring (Preferred — No Registration Needed)

Controller with auto-wired dependencies:

```php
<?php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
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

The DI container resolves `$appName` by parameter name, `IRequest` and `ItemService` by type hint — no explicit registration required.

### Explicit Service Registration (When Auto-Wiring Fails)

Use `registerService()` when the container cannot determine which implementation to inject (e.g., interfaces, primitives, or ambiguous constructors):

```php
public function register(IRegistrationContext $context): void {
    $context->registerService(AuthorService::class,
        function (ContainerInterface $c): AuthorService {
            return new AuthorService(
                $c->get(AuthorMapper::class),
                $c->get('TableName')
            );
        }
    );
}
```

### Interface-to-Implementation Binding

```php
public function register(IRegistrationContext $context): void {
    $context->registerServiceAlias(IAuthorMapper::class, AuthorMapper::class);
}
```

Now any constructor requesting `IAuthorMapper` receives an `AuthorMapper` instance.

### Optional Dependencies (NC 28+)

Use nullable types for services from optional apps:

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

---

## Service Layer Pattern

### Service Class

```php
<?php
namespace OCA\MyApp\Service;

use OCA\MyApp\Db\Item;
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

    public function create(string $title, string $userId): Item {
        $item = new Item();
        $item->setTitle($title);
        $item->setUserId($userId);
        return $this->mapper->insert($item);
    }

    public function delete(int $id, string $userId): ?Item {
        try {
            $item = $this->mapper->find($id, $userId);
            return $this->mapper->delete($item);
        } catch (DoesNotExistException $e) {
            return null;
        }
    }
}
```

### Controller Using Service Layer

```php
<?php
namespace OCA\MyApp\Controller;

use OCA\MyApp\Service\ItemService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class ItemController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private ItemService $service,
        private ?string $userId
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function index(): JSONResponse {
        return new JSONResponse($this->service->findAll($this->userId));
    }

    #[NoAdminRequired]
    public function show(int $id): JSONResponse {
        $item = $this->service->find($id, $this->userId);
        if ($item === null) {
            return new JSONResponse([], Http::STATUS_NOT_FOUND);
        }
        return new JSONResponse($item);
    }

    #[NoAdminRequired]
    public function create(string $title): JSONResponse {
        $item = $this->service->create($title, $this->userId);
        return new JSONResponse($item, Http::STATUS_CREATED);
    }

    #[NoAdminRequired]
    public function destroy(int $id): JSONResponse {
        $item = $this->service->delete($id, $this->userId);
        if ($item === null) {
            return new JSONResponse([], Http::STATUS_NOT_FOUND);
        }
        return new JSONResponse($item);
    }
}
```

---

## Route Definitions

### appinfo/routes.php

```php
<?php
return [
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
        ['name' => 'item#index', 'url' => '/api/items', 'verb' => 'GET'],
        ['name' => 'item#show', 'url' => '/api/items/{id}', 'verb' => 'GET'],
        ['name' => 'item#create', 'url' => '/api/items', 'verb' => 'POST'],
        ['name' => 'item#destroy', 'url' => '/api/items/{id}', 'verb' => 'DELETE'],
    ],
];
```

Route name resolution: `item#create` resolves to `ItemController::create()`.

---

## info.xml Minimal Example

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
    <author mail="dev@example.com">Developer Name</author>
    <namespace>MyApp</namespace>
    <category>tools</category>
    <bugs>https://github.com/org/myapp/issues</bugs>
    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
        <php min-version="8.1"/>
    </dependencies>
    <navigations>
        <navigation>
            <name>My App</name>
            <route>myapp.page.index</route>
            <icon>app.svg</icon>
            <order>10</order>
        </navigation>
    </navigations>
</info>
```

---

## Vue.js Frontend Entry Point

### src/main.js

```javascript
import Vue from 'vue'
import App from './App.vue'

const appElement = document.getElementById('content')

new Vue({
    el: appElement,
    render: h => h(App),
})
```

### PHP Template (templates/main.php)

```php
<?php
script('myapp', 'myapp-main');  // loads js/myapp-main.js
style('myapp', 'style');         // loads css/style.(s)css
?>

<div id="content"></div>
```

---

## Server-to-Frontend Data Transfer

### PHP Side (Controller)

```php
use OCP\AppFramework\Services\IInitialState;

class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private IInitialState $initialState,
        private ItemService $service,
        private ?string $userId
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        // Eager: always serialized
        $this->initialState->provideInitialState('items', $this->service->findAll($this->userId));

        // Lazy: only serialized if frontend loads it
        $this->initialState->provideLazyInitialState('settings', function () {
            return $this->service->getSettings();
        });

        return new TemplateResponse('myapp', 'main');
    }
}
```

### JavaScript Side

```typescript
import { loadState } from '@nextcloud/initial-state'

// ALWAYS provide a fallback for optional state
const items = loadState('myapp', 'items', [])
const settings = loadState('myapp', 'settings', { theme: 'default' })
```
