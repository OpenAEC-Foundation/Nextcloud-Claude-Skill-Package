# Error Types, Exception Classes & Diagnostic Methods

## Nextcloud Exception Classes

### App Framework Exceptions

| Exception | Namespace | Trigger |
|-----------|-----------|---------|
| `QueryException` | `OCP\AppFramework` | DI container cannot resolve a class or parameter |
| `DoesNotExistException` | `OCP\AppFramework\Db` | `findEntity()` returns zero rows |
| `MultipleObjectsReturnedException` | `OCP\AppFramework\Db` | `findEntity()` returns more than one row |

### File System Exceptions

| Exception | Namespace | Trigger |
|-----------|-----------|---------|
| `NotFoundException` | `OCP\Files` | File or folder does not exist at given path |
| `NotPermittedException` | `OCP\Files` | Insufficient permissions for operation |
| `InvalidPathException` | `OCP\Files` | Path contains invalid characters or format |
| `StorageNotAvailableException` | `OCP\Files` | External storage backend is unreachable |
| `LockedException` | `OCP\Lock` | File is locked by another process |

### General Exceptions

| Exception | Namespace | Trigger |
|-----------|-----------|---------|
| `AppConfigUnknownKeyException` | `OCP\Exceptions` | `IAppConfig::getValueString()` with unknown key and no default |
| `HintException` | `OCP` | Exception with a user-facing hint message |

## Diagnostic Methods

### OCC Commands for Debugging

```bash
# Check app status and errors
occ app:list                    # List all apps with enabled/disabled status
occ app:check-code myapp        # Validate app code against API rules
occ integrity:check-app myapp   # Verify app signature integrity

# Check migration status
occ migrations:status myapp     # Show migration execution status
occ migrations:execute myapp Version1000Date20240101000000  # Run specific migration

# Debug logging
occ config:system:set loglevel --value=0 --type=integer  # Set to DEBUG
occ log:manage --level=debug    # Alternative syntax
occ log:file                    # Show log file location
```

### Log File Analysis

Default log location: `{datadirectory}/nextcloud.log`

Key log entries for app errors:

| Log Pattern | Indicates |
|------------|-----------|
| `Could not resolve` | DI container failure |
| `Class ... not found` | Autoloading failure |
| `already executed` | Migration re-run attempt |
| `is deprecated` | Deprecated API usage |
| `CSRF check failed` | Missing CSRF token or OCS-APIRequest header |

### PHP Error Patterns

| PHP Error | Nextcloud Cause |
|-----------|----------------|
| `Fatal error: Class not found` | Missing namespace in info.xml or wrong directory structure |
| `TypeError: Argument #N must be of type X, null given` | DI resolved null for non-nullable parameter |
| `ArgumentCountError: Too few arguments` | Constructor has unresolvable parameters |
| `Error: Cannot instantiate interface` | Missing registerServiceAlias for interface |

## Bootstrap Lifecycle Phases

Understanding when errors occur helps diagnosis:

| Phase | What Runs | Common Errors |
|-------|-----------|---------------|
| 1. App Discovery | info.xml parsed | XML validation errors, missing fields |
| 2. Autoloader Setup | Namespace mapped to lib/ | Class not found if namespace wrong |
| 3. register() | IRegistrationContext methods | Service locator calls fail |
| 4. boot() | Cross-app initialization | Missing services from disabled apps |
| 5. Routing | URL matched to controller | Route not found, wrong controller name |
| 6. DI Resolution | Controller instantiated | QueryException, unresolvable params |
| 7. Execution | Controller method runs | Runtime errors, deprecated API calls |

## IRegistrationContext Methods (Safe for register())

These methods are the ONLY ones safe to call during `register()`:

| Method | Purpose |
|--------|---------|
| `registerService(string, Closure)` | Factory registration |
| `registerServiceAlias(string, string)` | Interface binding |
| `registerParameter(string, mixed)` | Primitive value registration |
| `registerEventListener(string, string)` | Event listener |
| `registerMiddleware(string)` | Middleware class |
| `registerSearchProvider(string)` | Unified search provider |
| `registerDashboardWidget(string)` | Dashboard widget |
| `registerNotifierService(string)` | Notification handler |
| `registerCalendarProvider(string)` | Calendar provider |
| `registerUserMigrator(string)` | User data export |

## Predefined DI Parameters

These parameter names are auto-resolved without explicit registration:

| Parameter Name | Type | Value |
|---------------|------|-------|
| `$appName` | `string` | The app ID from info.xml |
| `$userId` | `?string` | Current user ID (null if no session) |
| `$webRoot` | `string` | Nextcloud installation web path |

## Core Injectable Services

These type hints are always resolvable via auto-wiring:

| Type Hint | Purpose |
|-----------|---------|
| `\OCP\IRequest` | Current HTTP request |
| `\OCP\IDBConnection` | Database connection |
| `\OCP\IConfig` | System and app configuration |
| `\OCP\IAppConfig` | App-specific configuration (NC 28+) |
| `\OCP\IUserManager` | User CRUD operations |
| `\OCP\IUserSession` | Current user session |
| `\OCP\Files\IRootFolder` | Filesystem root |
| `\OCP\IL10N` | Localization |
| `\OCP\IURLGenerator` | URL generation |
| `\OCP\ICacheFactory` | Cache factory |
| `\OCP\Security\ICrypto` | Encryption utilities |
| `\Psr\Log\LoggerInterface` | PSR-3 logger |
| `\Psr\Container\ContainerInterface` | DI container |
| `\OCP\AppFramework\Services\IInitialState` | Frontend state injection |
| `\OCP\EventDispatcher\IEventDispatcher` | Event dispatch |
