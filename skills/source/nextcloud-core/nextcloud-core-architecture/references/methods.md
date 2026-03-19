# nextcloud-core-architecture — Methods Reference

## OCP\AppFramework\App

Base class for all Nextcloud app entry points.

```php
namespace OCP\AppFramework;

class App {
    public function __construct(string $appName, array $urlParams = []);
    public function getContainer(): IAppContainer;
}
```

**Usage**: ALWAYS extend this class in `lib/AppInfo/Application.php`. Pass the app ID (matching `<id>` in `info.xml`) to the parent constructor.

---

## OCP\AppFramework\Bootstrap\IBootstrap

Interface for apps that need registration and boot phases. Implement this on your `Application` class.

```php
namespace OCP\AppFramework\Bootstrap;

interface IBootstrap {
    public function register(IRegistrationContext $context): void;
    public function boot(IBootContext $context): void;
}
```

| Method | Phase | Safe Operations |
|--------|-------|-----------------|
| `register()` | Early (lazy) | ONLY `IRegistrationContext` methods — register services, listeners, middleware, parameters, aliases |
| `boot()` | Late (after all apps registered) | Full DI available — query any service, register with managers, cross-app integration |

---

## OCP\AppFramework\Bootstrap\IRegistrationContext

Available ONLY inside `register()`. Provides lazy registration methods.

| Method | Signature | Purpose |
|--------|-----------|---------|
| `registerService` | `(string $name, Closure $factory, bool $shared = true): void` | Register a service with explicit factory |
| `registerServiceAlias` | `(string $alias, string $target): void` | Bind interface to implementation |
| `registerParameter` | `(string $name, mixed $value): void` | Register a primitive value |
| `registerEventListener` | `(string $event, string $listener, int $priority = 0): void` | Register typed event listener class |
| `registerMiddleware` | `(string $class, bool $global = false): void` | Register middleware (global = all apps, NC 26+) |
| `registerSearchProvider` | `(string $class): void` | Register unified search provider |
| `registerAlternativeLogin` | `(string $class): void` | Register alternative login mechanism |
| `registerDashboardWidget` | `(string $class): void` | Register dashboard widget |
| `registerNotifierService` | `(string $class): void` | Register notification handler |
| `registerTwoFactorProvider` | `(string $class): void` | Register 2FA provider |
| `registerCalendarProvider` | `(string $class): void` | Register calendar provider |
| `registerProfileLinkAction` | `(string $class): void` | Register profile link action |
| `registerSetupCheck` | `(string $class): void` | Register admin setup check |
| `registerDeclarativeSettings` | `(string $class): void` | Register declarative settings schema |

---

## OCP\AppFramework\Bootstrap\IBootContext

Available ONLY inside `boot()`. Provides access to the full DI container.

| Method | Signature | Purpose |
|--------|-----------|---------|
| `getAppContainer` | `(): IAppContainer` | Get the app's DI container |
| `getServerContainer` | `(): IServerContainer` | Get the server-wide DI container |
| `injectFn` | `(Closure $fn): void` | Execute a closure with auto-injected parameters |

**`injectFn` pattern**: The closure's parameters are resolved via DI:

```php
public function boot(IBootContext $context): void {
    $context->injectFn(function (IUserManager $userManager, IConfig $config) {
        // Both parameters auto-injected from DI container
    });
}
```

---

## Core Injectable Services

### Database

| Interface | Purpose |
|-----------|---------|
| `OCP\IDBConnection` | Database abstraction — query builder, transactions, schema |

Key methods on `IDBConnection`:
- `getQueryBuilder(): IQueryBuilder` — Create query builder instance
- `beginTransaction(): void` — Start transaction
- `commit(): void` — Commit transaction
- `rollBack(): void` — Rollback transaction
- `insertIfNotExist(string $table, array $input, ?array $compare = null): int`

### Configuration

| Interface | Purpose |
|-----------|---------|
| `OCP\IConfig` | System config (`config.php`) and user preferences |
| `OCP\IAppConfig` | App-specific key-value configuration |

Key methods on `IConfig`:
- `getSystemValue(string $key, mixed $default = ''): mixed`
- `getAppValue(string $appName, string $key, string $default = ''): string`
- `setAppValue(string $appName, string $key, string $value): void`
- `getUserValue(string $userId, string $appName, string $key, string $default = ''): string`

### User Management

| Interface | Purpose |
|-----------|---------|
| `OCP\IUserManager` | User CRUD — create, search, count, iterate |
| `OCP\IUserSession` | Current user session — get logged-in user, login/logout |
| `OCP\IGroupManager` | Group CRUD and membership |

Key methods on `IUserManager`:
- `get(string $uid): ?IUser`
- `userExists(string $uid): bool`
- `search(string $pattern, ?int $limit = null, ?int $offset = null): array`
- `createUser(string $uid, string $password): IUser`

Key methods on `IUserSession`:
- `getUser(): ?IUser` — Returns null if no user logged in
- `isLoggedIn(): bool`

### Filesystem

| Interface | Purpose |
|-----------|---------|
| `OCP\Files\IRootFolder` | Root of the virtual filesystem |

Key methods on `IRootFolder`:
- `getUserFolder(string $userId): Folder` — Get user's file root
- `get(string $path): Node` — Get node by path

### URL Generation

| Interface | Purpose |
|-----------|---------|
| `OCP\IURLGenerator` | Generate URLs for routes, assets, remote endpoints |

Key methods:
- `linkToRoute(string $routeName, array $arguments = []): string`
- `linkToRouteAbsolute(string $routeName, array $arguments = []): string`
- `imagePath(string $appName, string $file): string`
- `getAbsoluteURL(string $url): string`

### Logging

| Interface | Purpose |
|-----------|---------|
| `Psr\Log\LoggerInterface` | PSR-3 logger (ALWAYS use this, NOT `OCP\ILogger`) |

Standard PSR-3 methods:
- `emergency(string $message, array $context = []): void`
- `alert(string $message, array $context = []): void`
- `critical(string $message, array $context = []): void`
- `error(string $message, array $context = []): void`
- `warning(string $message, array $context = []): void`
- `info(string $message, array $context = []): void`
- `debug(string $message, array $context = []): void`

### Events

| Interface | Purpose |
|-----------|---------|
| `OCP\EventDispatcher\IEventDispatcher` | Dispatch and listen for typed events |

Key methods:
- `dispatchTyped(Event $event): void` — Dispatch a typed event
- `addListener(string $eventName, callable $listener, int $priority = 0): void`
- `addServiceListener(string $eventName, string $className, int $priority = 0): void`

### Security

| Interface | Purpose |
|-----------|---------|
| `OCP\Security\ICrypto` | Encrypt/decrypt, hash operations |
| `OCP\Security\ISecureRandom` | Cryptographically secure random generation |

### Caching

| Interface | Purpose |
|-----------|---------|
| `OCP\ICacheFactory` | Create distributed cache instances |

Key methods:
- `createDistributed(string $prefix = ''): ICache`
- `createLocal(string $prefix = ''): ICache`
- `isAvailable(): bool`

### Frontend State

| Interface | Purpose |
|-----------|---------|
| `OCP\AppFramework\Services\IInitialState` | Pass data from PHP to JavaScript frontend |

Key methods:
- `provideInitialState(string $key, mixed $data): void` — Eager: always serialized
- `provideLazyInitialState(string $key, Closure $closure): void` — Lazy: only when loaded

### Localization

| Interface | Purpose |
|-----------|---------|
| `OCP\IL10N` | Translation and localization |

Key methods:
- `t(string $text, array $parameters = []): string` — Translate string
- `n(string $textSingular, string $textPlural, int $count, array $parameters = []): string` — Pluralize

---

## Predefined DI Parameters

These are auto-resolved by parameter name (not type hint):

| Parameter Name | Type | Value |
|---------------|------|-------|
| `$appName` | `string` | The app ID from `info.xml` |
| `$userId` | `?string` | Current user ID, null if no user session |
| `$webRoot` | `string` | Nextcloud installation web path |
