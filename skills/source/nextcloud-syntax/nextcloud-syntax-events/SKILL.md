---
name: nextcloud-syntax-events
description: >
  Use when creating event listeners, dispatching events, hooking into file/user/share operations, or implementing cross-component communication.
  Prevents using deprecated hook system instead of typed events, and incorrect listener registration timing.
  Covers IEventDispatcher, typed events, IEventListener interface, event registration via IRegistrationContext, Before/After naming pattern, built-in event catalog, custom event creation, and frontend @nextcloud/event-bus.
  Keywords: IEventDispatcher, IEventListener, IRegistrationContext, BeforeNodeCreated, NodeWritten, event-bus, typed events.
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-syntax-events

## Quick Reference

### Core Interfaces

| Interface / Class | Namespace | Role |
|-------------------|-----------|------|
| `IEventDispatcher` | `OCP\EventDispatcher` | Central dispatch service (inject via DI) |
| `IEventListener` | `OCP\EventDispatcher` | Interface for class-based listeners |
| `Event` | `OCP\EventDispatcher` | Base class for ALL typed events |
| `IRegistrationContext` | `OCP\AppFramework\Bootstrap` | Register listeners in `Application::register()` |

### IEventDispatcher Methods

| Method | Purpose |
|--------|---------|
| `addListener(string $eventName, callable $listener, int $priority = 0): void` | Register inline callback listener |
| `addServiceListener(string $eventName, string $className, int $priority = 0): void` | Register DI-resolved class listener |
| `dispatchTyped(Event $event): void` | Dispatch a typed event object |

### IEventListener Interface

```php
interface IEventListener {
    public function handle(Event $event): void;
}
```

### Event Naming Conventions

| Pattern | Timing | Purpose |
|---------|--------|---------|
| `Before{Action}Event` | Before the action | Allows cancellation or modification |
| `{Action}Event` | After the action | Informational / react to completed action |

**ALWAYS** end event class names with `Event`.

### Frontend Event Bus (`@nextcloud/event-bus`)

| Function | Signature | Purpose |
|----------|-----------|---------|
| `subscribe` | `subscribe(name: string, handler: Function): void` | Listen for events |
| `emit` | `emit(name: string, data: any): void` | Dispatch event to all subscribers |
| `unsubscribe` | `unsubscribe(name: string, handler: Function): void` | Remove a specific handler |

**Frontend event naming convention:** `app-id:object:verb` (e.g., `files:node:uploaded`)

### Critical Warnings

**NEVER** use deprecated hooks (`$userManager->listen(...)`) -- ALWAYS use typed events with `IEventDispatcher` or `IRegistrationContext::registerEventListener()`.

**NEVER** use `GenericEvent` -- deprecated since NC 22. ALWAYS create typed event classes extending `OCP\EventDispatcher\Event`.

**NEVER** skip the `instanceof` check in `handle()` -- the interface types the parameter as base `Event`, not your specific event class.

**NEVER** dispatch events in constructors -- services may not be fully initialized during construction.

**NEVER** forget to call `parent::__construct()` in custom event classes.

**NEVER** register event listeners in `boot()` -- ALWAYS use `register()` method via `IRegistrationContext::registerEventListener()` for lazy resolution.

**ALWAYS** register listeners via `IRegistrationContext::registerEventListener()` in `Application::register()` -- this is the recommended NC 28+ approach.

**ALWAYS** use `dispatchTyped()` for dispatching events -- NEVER use string-based event names with typed event objects.

**ALWAYS** use `@nextcloud/event-bus` for frontend cross-component communication -- NEVER use custom DOM events or global variables.

**ALWAYS** unsubscribe frontend event handlers when the component is destroyed -- failure to do so causes memory leaks.

---

## Decision Tree: Choosing Your Event Pattern

```
Need to react to something happening in Nextcloud?
|
+-- Is it a PHP backend event?
|   |
|   +-- Is there a built-in event for this? (see references/methods.md)
|   |   |
|   |   +-- YES --> Register listener for that event class
|   |   +-- NO  --> Create a custom event class extending Event
|   |
|   +-- How to register the listener?
|       |
|       +-- In an app (recommended) --> IRegistrationContext::registerEventListener()
|       +-- Quick inline logic        --> IEventDispatcher::addListener() with closure
|       +-- DI-resolved class         --> IEventDispatcher::addServiceListener()
|
+-- Is it a frontend (JavaScript/TypeScript) event?
    |
    +-- Cross-component communication --> @nextcloud/event-bus (subscribe/emit)
    +-- Reacting to Files app actions --> subscribe to 'files:node:*' events
```

---

## Essential Patterns

### Pattern 1: Register a Listener in Application (Recommended)

```php
namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Listener\NodeCreatedListener;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\Files\Events\Node\NodeCreatedEvent;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        $context->registerEventListener(
            NodeCreatedEvent::class,
            NodeCreatedListener::class
        );
    }

    public function boot(IBootContext $context): void {
    }
}
```

### Pattern 2: Implement IEventListener

```php
namespace OCA\MyApp\Listener;

use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeCreatedEvent;
use Psr\Log\LoggerInterface;

class NodeCreatedListener implements IEventListener {
    public function __construct(
        private LoggerInterface $logger,
    ) {
    }

    public function handle(Event $event): void {
        if (!($event instanceof NodeCreatedEvent)) {
            return;
        }

        $node = $event->getNode();
        $this->logger->info('File created: ' . $node->getPath());
    }
}
```

### Pattern 3: Create and Dispatch a Custom Event

```php
// lib/Event/ItemCreatedEvent.php
namespace OCA\MyApp\Event;

use OCP\EventDispatcher\Event;

class ItemCreatedEvent extends Event {
    public function __construct(
        private string $itemId,
        private string $userId,
        private array $data,
    ) {
        parent::__construct();
    }

    public function getItemId(): string {
        return $this->itemId;
    }

    public function getUserId(): string {
        return $this->userId;
    }

    public function getData(): array {
        return $this->data;
    }
}
```

```php
// lib/Service/ItemService.php
namespace OCA\MyApp\Service;

use OCA\MyApp\Event\ItemCreatedEvent;
use OCP\EventDispatcher\IEventDispatcher;

class ItemService {
    public function __construct(
        private IEventDispatcher $dispatcher,
    ) {
    }

    public function createItem(string $userId, array $data): void {
        // ... create the item ...

        $this->dispatcher->dispatchTyped(
            new ItemCreatedEvent($itemId, $userId, $data)
        );
    }
}
```

### Pattern 4: Inline Callback Listener (Simple Cases Only)

```php
use OCP\EventDispatcher\IEventDispatcher;
use OCP\Files\Events\Node\NodeDeletedEvent;

$dispatcher = $container->get(IEventDispatcher::class);
$dispatcher->addListener(
    NodeDeletedEvent::class,
    function (NodeDeletedEvent $event) {
        // Quick inline handling
        $path = $event->getNode()->getPath();
    }
);
```

### Pattern 5: Frontend Event Bus

```typescript
import { emit, subscribe, unsubscribe } from '@nextcloud/event-bus'

// Subscribe to a built-in event
const handler = (node: Node) => {
    console.log('File uploaded:', node.path)
}
subscribe('files:node:uploaded', handler)

// Emit a custom event
emit('myapp:item:created', { id: 42, name: 'New Item' })

// ALWAYS unsubscribe on component teardown
// In Vue Options API:
beforeDestroy() {
    unsubscribe('files:node:uploaded', handler)
}

// In Vue Composition API:
onBeforeUnmount(() => {
    unsubscribe('files:node:uploaded', handler)
})
```

### Pattern 6: TypeScript Typed Frontend Events

```typescript
// In a .d.ts file (e.g., src/events.d.ts)
declare module '@nextcloud/event-bus' {
    interface NextcloudEvents {
        'myapp:item:created': { id: number; name: string }
        'myapp:item:deleted': { id: number }
        'myapp:settings:changed': { key: string; value: unknown }
    }
}
export {}

// Usage -- TypeScript infers event payload types automatically
subscribe('myapp:item:created', (event) => {
    console.log(event.id)   // TypeScript knows: number
    console.log(event.name) // TypeScript knows: string
})

emit('myapp:item:created', { id: 1, name: 'Test' })
```

---

## Built-In Events (Summary)

See [references/methods.md](references/methods.md) for the complete catalog.

| Category | Namespace | Key Events |
|----------|-----------|------------|
| File operations | `OCP\Files\Events\Node\` | `NodeCreatedEvent`, `NodeDeletedEvent`, `NodeWrittenEvent`, `NodeRenamedEvent`, `NodeCopiedEvent` + Before variants |
| User management | `OCP\User\Events\` | `UserCreatedEvent`, `UserDeletedEvent`, `UserLoggedInEvent`, `UserLoggedOutEvent`, `PasswordUpdatedEvent` + Before variants |
| Sharing | `OCP\Share\Events\` | `ShareCreatedEvent`, `ShareDeletedEvent` + Before variants |
| Groups | `OCP\Group\Events\` | `GroupCreatedEvent`, `UserAddedEvent`, `UserRemovedEvent` + Before variants |
| Calendar/Contacts | `OCA\DAV\Events\` | `CalendarObjectCreatedEvent`, `CardCreatedEvent`, `AddressBookCreatedEvent` |
| Authentication | `OCP\Authentication\Events\` | `LoginFailedEvent`, `AnyLoginFailedEvent` |
| App lifecycle | `OCP\App\Events\` | `AppEnableEvent`, `AppDisableEvent`, `AppUpdateEvent` |
| Templates | `OCP\AppFramework\Http\Events\` | `BeforeTemplateRenderedEvent`, `BeforeLoginTemplateRenderedEvent` |

---

## Reference Links

- [references/methods.md](references/methods.md) -- Complete built-in events catalog, IEventDispatcher API, IEventListener interface
- [references/examples.md](references/examples.md) -- Custom events, listeners, dispatching, frontend event-bus patterns
- [references/anti-patterns.md](references/anti-patterns.md) -- Common event system mistakes

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/basics/events.html
- https://github.com/nextcloud-libraries/nextcloud-event-bus
