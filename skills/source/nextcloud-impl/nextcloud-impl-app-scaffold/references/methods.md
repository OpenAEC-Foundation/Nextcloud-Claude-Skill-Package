# methods.md -- info.xml Fields, Application.php API, Namespace Mapping

## info.xml Field Reference

### Required Fields

| Field | Type | Constraints | Example |
|-------|------|-------------|---------|
| `id` | string | Lowercase ASCII + underscore only. MUST match the app directory name. | `myapp` |
| `name` | string | Human-readable. Optional `lang` attribute for translations. | `My Application` |
| `summary` | string | Short description for app store listing. Max ~120 chars recommended. | `A tool for managing tasks` |
| `description` | string | Full description. Supports Markdown via `<![CDATA[]]>`. | `<![CDATA[Full **markdown** description]]>` |
| `version` | string | Semantic versioning. No build metadata. | `1.0.0` |
| `licence` | string | SPDX identifier. | `AGPL-3.0-or-later`, `MIT` |
| `author` | string | Developer name. Attributes: `mail`, `homepage`. | `<author mail="a@b.com">Dev</author>` |
| `namespace` | string | PascalCase. Maps to `OCA\{Namespace}\`. | `MyApp` |
| `category` | string | One valid category value. Multiple `<category>` elements allowed. | `tools` |
| `dependencies/nextcloud` | element | BOTH `min-version` AND `max-version` attributes required. | `<nextcloud min-version="28" max-version="32"/>` |

### Optional Fields

| Field | Type | Constraints | Purpose |
|-------|------|-------------|---------|
| `bugs` | URL | Valid URL | Issue tracker link |
| `repository` | URL | `type` attribute required (e.g., `git`) | Source code URL |
| `website` | URL | Valid URL | Project homepage |
| `screenshot` | URL | HTTPS required. Optional `small-thumbnail` attribute. | App store screenshot |
| `documentation/user` | URL | Valid URL | User documentation |
| `documentation/admin` | URL | Valid URL | Admin documentation |
| `documentation/developer` | URL | Valid URL | Developer documentation |
| `dependencies/php` | element | Optional `min-version`, `max-version` | PHP version constraint |
| `dependencies/database` | string | Database engine name | Required database engine |
| `dependencies/lib` | string | Optional `min-version` attribute | Required PHP extension |
| `dependencies/command` | string | Binary name | Required system command |

### Registration Fields (in info.xml)

| Field | Child Element | Value | Purpose |
|-------|--------------|-------|---------|
| `navigations/navigation` | `name`, `route`, `icon`, `order` | See navigation section | Top-level nav entry |
| `background-jobs` | `job` | Fully qualified class name | Cron job registration |
| `repair-steps/install` | `step` | Fully qualified class name | Install repair step |
| `repair-steps/post-migration` | `step` | Fully qualified class name | Post-migration repair step |
| `repair-steps/uninstall` | `step` | Fully qualified class name | Uninstall cleanup step |
| `commands` | `command` | Fully qualified class name | OCC command registration |
| `settings/admin` | -- | Fully qualified class name | Admin settings page |
| `settings/admin-section` | -- | Fully qualified class name | Admin settings section |
| `settings/personal` | -- | Fully qualified class name | Personal settings page |
| `settings/personal-section` | -- | Fully qualified class name | Personal settings section |
| `activity/settings` | `setting` | Fully qualified class name | Activity app setting |
| `activity/providers` | `provider` | Fully qualified class name | Activity app provider |

### Deprecated Fields (NEVER Use)

| Field | Replacement |
|-------|-------------|
| `requiremin` | `<dependencies><nextcloud min-version="X"/>` |
| `requiremax` | `<dependencies><nextcloud max-version="X"/>` |
| `standalone` | Removed -- no replacement |
| `default_enable` | Removed -- no replacement |
| `shipped` | Removed -- core-only field |
| `public` | Removed -- no replacement |
| `remote` | Removed -- no replacement |

---

## Navigation Entry Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | string | Display name in navigation bar |
| `route` | Yes | string | Route name: `{appid}.{controller}.{method}` |
| `icon` | No | string | Icon filename from `img/` directory (default: `app.svg`) |
| `order` | No | int | Sort order in navigation (lower = higher position) |

---

## Application.php -- IBootstrap API

### Interface: `OCP\AppFramework\Bootstrap\IBootstrap`

```php
interface IBootstrap {
    public function register(IRegistrationContext $context): void;
    public function boot(IBootContext $context): void;
}
```

### IRegistrationContext Methods

| Method | Parameters | Purpose |
|--------|-----------|---------|
| `registerEventListener` | `string $event, string $listener, int $priority = 0` | Register typed event listener class |
| `registerMiddleware` | `string $class` | Register middleware class |
| `registerService` | `string $name, Closure $factory, bool $shared = true` | Explicit service factory |
| `registerServiceAlias` | `string $alias, string $target` | Interface-to-implementation binding |
| `registerParameter` | `string $name, mixed $value` | Register primitive value for DI |
| `registerCapability` | `string $capability` | Register OCS capabilities provider |
| `registerCrashReporter` | `string $class` | Register crash reporter |
| `registerDashboardWidget` | `string $class` | Register dashboard widget |
| `registerNotifierService` | `string $class` | Register notification handler |
| `registerSearchProvider` | `string $class` | Register unified search provider |
| `registerCalendarProvider` | `string $class` | Register calendar provider |
| `registerCalendarRoomBackend` | `string $class` | Register calendar room backend |
| `registerCalendarResourceBackend` | `string $class` | Register calendar resource backend |
| `registerTextProcessingProvider` | `string $class` | Register text processing provider |
| `registerUserMigrator` | `string $class` | Register user data migrator |

### IBootContext Methods

| Method | Parameters | Purpose |
|--------|-----------|---------|
| `injectFn` | `Closure $fn` | Execute closure with auto-injected DI parameters |
| `getAppContainer` | -- | Get the app's DI container |
| `getServerContainer` | -- | Get the server-level DI container |

---

## Namespace Mapping Rules

### Rule: `<namespace>` in info.xml determines autoloading

The `OCA\{Namespace}\` prefix maps to the `lib/` directory of the app.

**Formula:** `OCA\{Namespace}\{SubNamespace}\{ClassName}` resolves to `lib/{SubNamespace}/{ClassName}.php`

### Standard Subdirectory Conventions

| PHP Namespace Suffix | Directory | Purpose |
|---------------------|-----------|---------|
| `AppInfo\` | `lib/AppInfo/` | Application bootstrap |
| `Controller\` | `lib/Controller/` | HTTP controllers |
| `Service\` | `lib/Service/` | Business logic |
| `Db\` | `lib/Db/` | Entities and mappers |
| `Listener\` | `lib/Listener/` | Event listeners |
| `Middleware\` | `lib/Middleware/` | Request middleware |
| `Migration\` | `lib/Migration/` | Database migrations |
| `Command\` | `lib/Command/` | OCC CLI commands |
| `Cron\` | `lib/Cron/` | Background job classes |
| `Settings\` | `lib/Settings/` | Settings page classes |
| `Notification\` | `lib/Notification/` | Notification handlers |
| `Search\` | `lib/Search/` | Search providers |
| `Event\` | `lib/Event/` | Custom event classes |
| `Exception\` | `lib/Exception/` | Custom exception classes |

### Auto-Wiring Requirements

For Nextcloud's auto-wiring to work:
1. `<namespace>` MUST be declared in `info.xml`
2. Routes MUST use array-style definition in `appinfo/routes.php`
3. Constructor parameters MUST use type hints for interfaces/classes
4. The following parameter names are auto-resolved: `$appName` (app ID), `$userId` (current user, nullable), `$webRoot` (installation path)

### Composer Autoloading (for third-party dependencies)

When an app uses Composer dependencies, include the autoloader in `Application.php`:

```php
public function register(IRegistrationContext $context): void {
    include_once __DIR__ . '/../../vendor/autoload.php';
}
```

The `vendor/` directory sits at the app root alongside `lib/`.

---

## Valid Category Values

| Category | Description |
|----------|-------------|
| `customization` | Theming, appearance, branding |
| `files` | File management, storage |
| `games` | Games and entertainment |
| `integration` | Third-party service integration |
| `monitoring` | System monitoring, logging |
| `multimedia` | Audio, video, image processing |
| `office` | Productivity, documents, collaboration |
| `organization` | Calendar, contacts, project management |
| `security` | Authentication, encryption, access control |
| `social` | Communication, social features |
| `tools` | Utilities, developer tools |
