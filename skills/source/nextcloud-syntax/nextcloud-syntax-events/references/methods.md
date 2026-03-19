# Event System Methods & Built-In Events Catalog

## IEventDispatcher Interface

**Namespace:** `OCP\EventDispatcher\IEventDispatcher`

### Methods

#### addListener

```php
public function addListener(
    string $eventName,
    callable $listener,
    int $priority = 0
): void;
```

Register an inline callback listener. Higher `$priority` values execute first. Use for simple, one-off handlers that do not need DI.

#### addServiceListener

```php
public function addServiceListener(
    string $eventName,
    string $className,
    int $priority = 0
): void;
```

Register a class-based listener resolved via DI container. The class MUST implement `IEventListener`. Preferred over `addListener` when the listener needs injected services.

#### dispatchTyped

```php
public function dispatchTyped(Event $event): void;
```

Dispatch a typed event object. All registered listeners matching the event's class name are invoked. ALWAYS use this method for dispatching -- NEVER use string-based dispatch with typed events.

---

## IEventListener Interface

**Namespace:** `OCP\EventDispatcher\IEventListener`

```php
interface IEventListener {
    public function handle(Event $event): void;
}
```

- The `$event` parameter is typed as base `Event`, NOT your specific event class.
- ALWAYS perform an `instanceof` check as the first line of `handle()`.
- Constructor injection works -- the listener is resolved via DI.

---

## Event Base Class

**Namespace:** `OCP\EventDispatcher\Event`

```php
class Event {
    public function __construct() {}
    public function stopPropagation(): void {}
    public function isPropagationStopped(): bool {}
}
```

- ALWAYS extend this class for custom events.
- ALWAYS call `parent::__construct()` in your event's constructor.
- `stopPropagation()` prevents subsequent listeners from being called.

---

## IRegistrationContext::registerEventListener

```php
public function registerEventListener(
    string $event,
    string $listener,
    int $priority = 0
): void;
```

Register a listener during app bootstrap. ALWAYS use this in `Application::register()`. The listener class is lazily resolved -- it is only instantiated when the event is actually dispatched.

---

## Built-In Events Catalog

### File Operations (`OCP\Files\Events\Node\`)

| Event Class | Trigger | Available Data |
|-------------|---------|----------------|
| `BeforeNodeCreatedEvent` | Before file/folder creation | `getNode(): Node` |
| `NodeCreatedEvent` | After file/folder creation | `getNode(): Node` |
| `BeforeNodeDeletedEvent` | Before deletion | `getNode(): Node` |
| `NodeDeletedEvent` | After deletion | `getNode(): Node` |
| `BeforeNodeWrittenEvent` | Before content write | `getNode(): Node` |
| `NodeWrittenEvent` | After content write | `getNode(): Node` |
| `BeforeNodeRenamedEvent` | Before rename/move | `getSource(): Node`, `getTarget(): Node` |
| `NodeRenamedEvent` | After rename/move | `getSource(): Node`, `getTarget(): Node` |
| `BeforeNodeCopiedEvent` | Before copy | `getSource(): Node`, `getTarget(): Node` |
| `NodeCopiedEvent` | After copy | `getSource(): Node`, `getTarget(): Node` |

### User Management (`OCP\User\Events\`)

| Event Class | Trigger | Available Data |
|-------------|---------|----------------|
| `BeforeUserCreatedEvent` | Before user creation | `getUid(): string`, `getPassword(): string` |
| `UserCreatedEvent` | After user creation | `getUser(): IUser` |
| `BeforeUserDeletedEvent` | Before user deletion | `getUser(): IUser` |
| `UserDeletedEvent` | After user deletion | `getUser(): IUser` |
| `BeforePasswordUpdatedEvent` | Before password change | `getUser(): IUser` |
| `PasswordUpdatedEvent` | After password change | `getUser(): IUser` |
| `UserLoggedInEvent` | After login | `getUser(): IUser` |
| `UserLoggedOutEvent` | After logout | (no user data -- session already ended) |
| `UserFirstTimeLoggedInEvent` | First-ever login (NC 28+) | `getUser(): IUser` |
| `UserChangedEvent` | User attribute changed | `getUser(): IUser`, `getFeature(): string`, `getValue(): mixed` |

### Sharing (`OCP\Share\Events\`)

| Event Class | Trigger | Available Data |
|-------------|---------|----------------|
| `BeforeShareCreatedEvent` | Before share creation | `getShare(): IShare` |
| `ShareCreatedEvent` | After share creation | `getShare(): IShare` |
| `BeforeShareDeletedEvent` | Before share deletion | `getShare(): IShare` |
| `ShareDeletedEvent` | After share deletion | `getShare(): IShare` |

### Group Management (`OCP\Group\Events\`)

| Event Class | Trigger | Available Data |
|-------------|---------|----------------|
| `BeforeGroupCreatedEvent` | Before group creation | `getName(): string` |
| `GroupCreatedEvent` | After group creation | `getGroup(): IGroup` |
| `BeforeGroupDeletedEvent` | Before group deletion | `getGroup(): IGroup` |
| `GroupDeletedEvent` | After group deletion | `getGroup(): IGroup` |
| `BeforeUserAddedEvent` | Before adding user to group | `getGroup(): IGroup`, `getUser(): IUser` |
| `UserAddedEvent` | After adding user to group | `getGroup(): IGroup`, `getUser(): IUser` |
| `BeforeUserRemovedEvent` | Before removing user from group | `getGroup(): IGroup`, `getUser(): IUser` |
| `UserRemovedEvent` | After removing user from group | `getGroup(): IGroup`, `getUser(): IUser` |

### Calendar & Contacts (`OCA\DAV\Events\`)

| Event Class | Trigger | Available Data |
|-------------|---------|----------------|
| `CalendarCreatedEvent` | Calendar created | `getCalendarId(): int`, `getCalendarData(): array` |
| `CalendarObjectCreatedEvent` | Calendar entry created | `getCalendarId(): int`, `getObjectData(): array` |
| `CalendarObjectUpdatedEvent` | Calendar entry updated | `getCalendarId(): int`, `getObjectData(): array` |
| `CalendarObjectDeletedEvent` | Calendar entry deleted | `getCalendarId(): int`, `getObjectData(): array` |
| `CardCreatedEvent` | Contact card created | `getAddressBookId(): int`, `getCardData(): array` |
| `CardUpdatedEvent` | Contact card updated | `getAddressBookId(): int`, `getCardData(): array` |
| `CardDeletedEvent` | Contact card deleted | `getAddressBookId(): int`, `getCardData(): array` |
| `AddressBookCreatedEvent` | Address book created | `getAddressBookId(): int`, `getAddressBookData(): array` |

### Authentication (`OCP\Authentication\Events\`)

| Event Class | Trigger | Available Data |
|-------------|---------|----------------|
| `LoginFailedEvent` | Login attempt failed | `getLoginName(): string` |
| `AnyLoginFailedEvent` | Any login method failed (NC 26+) | `getLoginName(): string` |

### App Lifecycle (`OCP\App\Events\`)

| Event Class | Trigger | Available Data |
|-------------|---------|----------------|
| `AppEnableEvent` | App enabled | `getAppId(): string` |
| `AppDisableEvent` | App disabled | `getAppId(): string` |
| `AppUpdateEvent` | App updated | `getAppId(): string` |

### Template Rendering (`OCP\AppFramework\Http\Events\`)

| Event Class | Trigger | Available Data |
|-------------|---------|----------------|
| `BeforeTemplateRenderedEvent` | Before template output | `isLoggedIn(): bool`, `getResponse(): TemplateResponse` |
| `BeforeLoginTemplateRenderedEvent` | Before login page render | `getResponse(): TemplateResponse` |

---

## Frontend Event Bus API (`@nextcloud/event-bus`)

### Installation

```bash
npm install @nextcloud/event-bus
```

### Functions

#### subscribe

```typescript
function subscribe(name: string, handler: (...args: any[]) => void): void
```

Register a handler for the named event. The same handler can be subscribed multiple times -- each subscription results in one invocation per emit.

#### emit

```typescript
function emit(name: string, ...args: any[]): void
```

Dispatch an event to all registered handlers. Handlers are called synchronously in registration order.

#### unsubscribe

```typescript
function unsubscribe(name: string, handler: (...args: any[]) => void): void
```

Remove a previously registered handler. MUST pass the exact same function reference used in `subscribe`.

### Common Built-In Frontend Events

| Event Name | Payload | Source |
|------------|---------|--------|
| `files:node:created` | `Node` | Files app -- file created |
| `files:node:uploaded` | `Node` | Files app -- upload complete |
| `files:node:deleted` | `Node` | Files app -- file deleted |
| `files:node:updated` | `Node` | Files app -- file modified |
| `files:node:uploading` | `{ node: Node, progress: number }` | Files app -- upload in progress |
| `nextcloud:unified-search:closed` | (none) | Unified search closed |
| `calendar:event:created` | event data | Calendar app |
| `contacts:contact:deleted` | contact data | Contacts app |

### TypeScript Type Augmentation

```typescript
declare module '@nextcloud/event-bus' {
    interface NextcloudEvents {
        'myapp:item:created': { id: number; name: string }
        'myapp:item:deleted': { id: number }
    }
}
export {}
```

After declaring this module augmentation, `subscribe` and `emit` calls for these event names receive full type checking and autocompletion.
