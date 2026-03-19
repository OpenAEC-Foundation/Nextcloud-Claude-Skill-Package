# Event System Anti-Patterns

## AP-1: Using Deprecated Hooks

**NEVER** use the legacy hook system (`$userManager->listen(...)`, `OC_Hook`, or `\OC::$server->getEventDispatcher()` with string event names).

```php
// WRONG -- deprecated hooks
\OC::$server->getUserManager()->listen('\OC\User', 'postLogin', function ($user) {
    // This uses the legacy hook system
});

// CORRECT -- typed event with IRegistrationContext
$context->registerEventListener(
    \OCP\User\Events\UserLoggedInEvent::class,
    MyLoginListener::class
);
```

**Why:** Legacy hooks are undocumented, untyped, and will be removed in future NC versions. Typed events provide IDE support, type safety, and are the only supported mechanism since NC 28.

---

## AP-2: Using GenericEvent

**NEVER** use `OCP\EventDispatcher\GenericEvent` -- it has been deprecated since NC 22.

```php
// WRONG -- GenericEvent
use OCP\EventDispatcher\GenericEvent;

$event = new GenericEvent(null, ['user' => $userId, 'path' => $path]);
$dispatcher->dispatch('myapp.file.created', $event);

// CORRECT -- typed event
use OCA\MyApp\Event\FileProcessedEvent;

$event = new FileProcessedEvent($userId, $path);
$dispatcher->dispatchTyped($event);
```

**Why:** `GenericEvent` provides no type safety, no IDE autocompletion, and no guaranteed structure. Typed events make the contract explicit and prevent runtime errors.

---

## AP-3: Missing instanceof Check in handle()

**NEVER** skip the `instanceof` check at the start of `handle()`.

```php
// WRONG -- no type check
public function handle(Event $event): void {
    $node = $event->getNode(); // Fatal error if wrong event type
}

// CORRECT -- always check
public function handle(Event $event): void {
    if (!($event instanceof NodeCreatedEvent)) {
        return;
    }
    $node = $event->getNode(); // Safe -- type is verified
}
```

**Why:** The `IEventListener::handle()` signature accepts the base `Event` type. If the dispatcher ever calls your listener with an unexpected event (e.g., due to misconfiguration), the `instanceof` check prevents fatal errors.

---

## AP-4: Registering Listeners in boot()

**NEVER** register event listeners in `Application::boot()`.

```php
// WRONG -- registering in boot()
public function boot(IBootContext $context): void {
    $context->injectFn(function (IEventDispatcher $dispatcher) {
        $dispatcher->addListener(NodeCreatedEvent::class, function ($event) {
            // This listener is NOT lazily resolved
        });
    });
}

// CORRECT -- registering in register()
public function register(IRegistrationContext $context): void {
    $context->registerEventListener(
        NodeCreatedEvent::class,
        NodeCreatedListener::class
    );
}
```

**Why:** Listeners registered in `register()` via `IRegistrationContext` are lazily resolved -- the listener class is only instantiated when the event actually fires. Listeners registered in `boot()` via `IEventDispatcher` are eagerly instantiated, wasting resources if the event never fires.

---

## AP-5: Dispatching Events in Constructors

**NEVER** dispatch events inside a constructor.

```php
// WRONG -- dispatch in constructor
class ItemService {
    public function __construct(
        private IEventDispatcher $dispatcher,
    ) {
        $this->dispatcher->dispatchTyped(new ServiceInitializedEvent());
        // Other services may not be initialized yet
    }
}

// CORRECT -- dispatch in a method
class ItemService {
    public function __construct(
        private IEventDispatcher $dispatcher,
    ) {
    }

    public function initialize(): void {
        $this->dispatcher->dispatchTyped(new ServiceInitializedEvent());
    }
}
```

**Why:** During construction, the DI container may still be resolving dependencies. Dispatching events can trigger listeners that depend on services not yet instantiated, causing circular dependency errors or undefined behavior.

---

## AP-6: Forgetting parent::__construct() in Custom Events

**NEVER** omit `parent::__construct()` in custom event classes.

```php
// WRONG -- missing parent constructor
class ItemCreatedEvent extends Event {
    public function __construct(
        private int $itemId,
    ) {
        // Missing parent::__construct()
    }
}

// CORRECT
class ItemCreatedEvent extends Event {
    public function __construct(
        private int $itemId,
    ) {
        parent::__construct();
    }
}
```

**Why:** The base `Event` class initializes propagation state. Omitting the parent constructor may cause `stopPropagation()` and `isPropagationStopped()` to behave unpredictably.

---

## AP-7: Using String-Based Event Names with dispatchTyped

**NEVER** mix string-based event names with `dispatchTyped()`.

```php
// WRONG -- string name with dispatchTyped
$dispatcher->dispatchTyped('myapp.item.created'); // Wrong argument type

// WRONG -- dispatch() with typed event (legacy API)
$dispatcher->dispatch(ItemCreatedEvent::class, $event);

// CORRECT -- dispatchTyped with Event object
$dispatcher->dispatchTyped(new ItemCreatedEvent($id));
```

**Why:** `dispatchTyped()` expects an `Event` object and uses its class name for listener matching. Passing a string will cause a type error.

---

## AP-8: Not Unsubscribing Frontend Event Handlers

**NEVER** subscribe to frontend events without unsubscribing on component teardown.

```javascript
// WRONG -- memory leak
export default {
    created() {
        subscribe('files:node:uploaded', (node) => {
            // Anonymous function cannot be unsubscribed
            this.handleUpload(node)
        })
    },
}

// CORRECT -- store reference and unsubscribe
export default {
    created() {
        this._handleUpload = (node) => {
            this.handleUpload(node)
        }
        subscribe('files:node:uploaded', this._handleUpload)
    },
    beforeDestroy() {
        unsubscribe('files:node:uploaded', this._handleUpload)
    },
}
```

**Why:** Anonymous functions cannot be unsubscribed because `unsubscribe` requires the exact same function reference. Leaked subscriptions accumulate with each component mount, causing duplicate handler calls and memory leaks.

---

## AP-9: Using Custom DOM Events Instead of Event Bus

**NEVER** use `CustomEvent` or `dispatchEvent` for cross-component communication in Nextcloud.

```javascript
// WRONG -- raw DOM events
document.dispatchEvent(new CustomEvent('myapp:updated', { detail: data }))
document.addEventListener('myapp:updated', handler)

// CORRECT -- @nextcloud/event-bus
import { emit, subscribe } from '@nextcloud/event-bus'
emit('myapp:item:updated', data)
subscribe('myapp:item:updated', handler)
```

**Why:** `@nextcloud/event-bus` provides a centralized, typed event system that works across iframes, supports TypeScript augmentation, and follows Nextcloud conventions. DOM events are not discoverable and break when components are in different contexts.

---

## AP-10: Heavy Processing in Event Listeners

**NEVER** perform long-running operations synchronously in event listeners.

```php
// WRONG -- blocking operation in listener
public function handle(Event $event): void {
    if (!($event instanceof NodeCreatedEvent)) {
        return;
    }
    // This blocks the entire request
    $this->externalApi->uploadToThirdParty($event->getNode());
    sleep(5); // Waiting for external response
}

// CORRECT -- queue a background job
public function handle(Event $event): void {
    if (!($event instanceof NodeCreatedEvent)) {
        return;
    }
    $this->jobList->add(ProcessFileJob::class, [
        'fileId' => $event->getNode()->getId(),
    ]);
}
```

**Why:** Event listeners run synchronously during the request. Long-running operations block the response and can cause timeouts. ALWAYS delegate heavy work to background jobs (`IJobList`).
