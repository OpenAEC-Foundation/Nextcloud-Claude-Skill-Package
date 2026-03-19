# Nextcloud Backend APIs — Deep Research (Part 1 of 3)

> Research date: 2026-03-19
> Sources: Official Nextcloud Developer Manual (docs.nextcloud.com/server/latest/developer_manual/)
> Scope: Platform architecture, OCS API, WebDAV, App Framework, Database, Authentication & Security

---

## §1: Platform Architecture

### Overview

Nextcloud is a PHP-based server application with a modular app architecture. All HTTP requests enter through `index.php`, which loads `lib/base.php`. This base file inspects HTTP headers, abstracts web server differences, and initializes core classes. The bootstrap sequence loads: (1) authentication backends, (2) filesystem, (3) logging. Then each installed app is loaded based on its `appinfo/info.xml`.

The request lifecycle proceeds as:
1. User authentication attempt
2. Load all apps' navigation and pre-configuration files
3. Load route definitions from each app's `appinfo/routes.php`
4. Execute the router to match the incoming request URL to a controller

### Key PHP Interfaces and Their Roles

| Interface | Role |
|-----------|------|
| `OCP\AppFramework\App` | Base class for app entry point (`Application`) |
| `OCP\AppFramework\Bootstrap\IBootstrap` | Interface for apps that need registration and boot phases |
| `OCP\AppFramework\Bootstrap\IRegistrationContext` | Service registration during app loading (lazy) |
| `OCP\AppFramework\Bootstrap\IBootContext` | Runtime operations after all apps registered |
| `OCP\IDBConnection` | Database abstraction layer |
| `OCP\IRequest` | HTTP request abstraction |
| `OCP\IUserManager` | User CRUD operations |
| `OCP\IUserSession` | Current user session management |
| `OCP\IConfig` | Server and app configuration |
| `OCP\IURLGenerator` | URL generation for routes and assets |
| `OCP\ICrypto` | Cryptographic operations |
| `Psr\Log\LoggerInterface` | PSR-3 compliant logging |
| `Psr\Container\ContainerInterface` | PSR-11 DI container |

### App Lifecycle: Loading, Bootstrapping, Registration

The `Application` class in `lib/AppInfo/Application.php` implements `IBootstrap`:

```php
<?php
namespace OCA\MyApp\AppInfo;

use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct(array $urlParams = []) {
        parent::__construct(self::APP_ID, $urlParams);
    }

    public function register(IRegistrationContext $context): void {
        // Lazy registration — called during app loading
        // Register services, middleware, listeners, etc.
        $context->registerMiddleware(MyMiddleware::class);
        $context->registerServiceAlias(IMyInterface::class, MyImplementation::class);
    }

    public function boot(IBootContext $context): void {
        // Called after ALL apps have been registered
        // Safe to query services from other apps here
    }
}
```

**Critical distinction**: `register()` is called lazily during app loading — you MUST NOT query services from other apps here. `boot()` is called after ALL apps have registered, so cross-app service queries are safe.

### Dependency Injection

Nextcloud uses auto-wiring as the primary DI mechanism. The container resolves constructor parameters by:
1. **Type hints**: `SomeType $param` resolves via `$container->get(SomeType::class)`
2. **Parameter names**: `$variable` resolves via `$container->get('variable')`

**Predefined parameters**: `appName`, `userId`, `webRoot`

**Manual registration** (for interfaces or primitives):
```php
public function register(IRegistrationContext $context): void {
    $context->registerParameter('TableName', 'my_app_table');
    $context->registerServiceAlias(IAuthorMapper::class, AuthorMapper::class);

    $context->registerService(AuthorController::class,
        function(ContainerInterface $c): AuthorController {
            return new AuthorController(
                $c->get('appName'),
                $c->get(Request::class),
                $c->get(AuthorService::class)
            );
        }
    );
}
```

**Optional dependencies** (NC 28+): Use nullable types for services that may not exist:
```php
class MyService {
    public function __construct(private ?SomeOptionalService $service) { }
}
```

**Auto-wiring requirement**: The `<namespace>` element MUST be set in `appinfo/info.xml`:
```xml
<namespace>MyBeautifulApp</namespace>
```

### Anti-Patterns

- **NEVER** use `\OCP\Server::get()` (legacy static access) — it breaks testability. Use constructor injection instead.
- **NEVER** query other apps' services inside `register()` — they may not be registered yet. Use `boot()` for cross-app dependencies.
- **NEVER** forget the `<namespace>` in `info.xml` — auto-wiring will silently fail.

### Version Notes

- NC 28+: Nullable constructor parameters for optional dependencies
- NC 26+: `#[UseSession]` attribute for session management
- NC 20+: `IBootstrap` interface with `register()`/`boot()` lifecycle

---

## §2: OCS API

### Overview

The OCS (Open Collaboration Services) REST API is Nextcloud's primary structured API. It uses a versioned endpoint system with an envelope response format. Two versions exist with different status code semantics.

### Endpoint Structure

| Version | Base Path | Success Status Code | Notes |
|---------|-----------|-------------------|-------|
| v1 | `/ocs/v1.php/` | 100 (in `statuscode` field) | Legacy, HTTP status always 200 |
| v2 | `/ocs/v2.php/` | 200 (in `statuscode` field) | Preferred, HTTP status mirrors OCS status |

App-specific OCS endpoints follow: `/ocs/v2.php/apps/<APPNAME>/api/v1/<endpoint>`

### Authentication Methods

1. **Basic Authentication**: `curl -u username:password` (supports app passwords)
2. **OIDC Bearer Token**: `Authorization: Bearer ID_TOKEN`
3. **Session cookies**: For browser-based requests

**Required header for ALL OCS requests**: `OCS-APIRequest: true`

### Response Format

The OCS envelope wraps all responses:

**XML (default)**:
```xml
<?xml version="1.0"?>
<ocs>
  <meta>
    <status>ok</status>
    <statuscode>200</statuscode>
    <message>OK</message>
  </meta>
  <data>
    <!-- actual response content -->
  </data>
</ocs>
```

**JSON** (request with `format=json` query parameter or `Accept: application/json`):
```json
{
  "ocs": {
    "meta": {
      "status": "ok",
      "statuscode": 200,
      "message": "OK"
    },
    "data": { }
  }
}
```

### Key Endpoints

#### Capabilities Discovery
```
GET /ocs/v1.php/cloud/capabilities
```
Returns server version, supported features, app capabilities, and theming data. Essential for client feature negotiation.

#### User Provisioning
```
GET /ocs/v1.php/cloud/users          # List all users (admin only)
GET /ocs/v1.php/cloud/users/USERID   # Get user details (since NC 11.0.2)
```

#### Share API (via files_sharing app)
Base: `/ocs/v2.php/apps/files_sharing/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/shares` | List all user's shares |
| GET | `/shares?path=/folder` | Shares for specific path |
| GET | `/shares/<id>` | Get single share |
| POST | `/shares` | Create share |
| PUT | `/shares/<id>` | Update share |
| DELETE | `/shares/<id>` | Delete share |

**Share types**: 0 (user), 1 (group), 3 (public link), 4 (email), 6 (federated), 7 (circle), 10 (Talk)

**Permissions bitmask**: 1 (read), 2 (update), 4 (create), 8 (delete), 16 (share), 31 (all)

**Create share parameters**: `path` (required), `shareType` (required), `shareWith` (required for user/group), `permissions`, `password`, `expireDate`, `publicUpload`, `note`, `label`, `attributes`

**Share attributes** (advanced JSON config):
```json
[{"scope": "permissions", "key": "download", "value": false}]
[{"scope": "fileRequest", "key": "enabled", "value": true}]
```

#### User Status API
Base: `/ocs/v2.php/apps/user_status/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/user_status` | Get current user's status |
| PUT | `/user_status/status` | Set status type (online/away/dnd/invisible/offline) |
| PUT | `/user_status/message/custom` | Set custom message with emoji |
| PUT | `/user_status/message/predefined` | Set predefined message |
| DELETE | `/user_status/message` | Clear message |
| GET | `/statuses` | List all user statuses |
| GET | `/statuses/{userId}` | Get specific user's status |

#### Federated Shares
```
GET    /remote_shares              # List accepted
GET    /remote_shares/pending      # List pending
POST   /remote_shares/pending/<id> # Accept
DELETE /remote_shares/pending/<id> # Decline
DELETE /remote_shares/<id>         # Remove
```

#### Other OCS APIs
- **Sharee API**: Search/recommend share recipients
- **User Preferences**: Set/delete user preferences
- **Translation API**: Available translations, translate strings
- **TaskProcessing API**: Schedule/retrieve AI tasks
- **Text-To-Image API**: Image generation
- **Out-of-Office API**: Manage absence data
- **Autocomplete**: `/ocs/v2.php/core/autocomplete/get` with `shareTypes[]`, `itemType`, `limit` params
- **Direct Download**: `POST /ocs/v2.php/apps/dav/api/v1/direct`

### Anti-Patterns

- **NEVER** omit the `OCS-APIRequest: true` header — requests will be rejected.
- **NEVER** assume HTTP status codes in v1 — the OCS `statuscode` field is authoritative. v1 always returns HTTP 200.
- **NEVER** parse XML responses when JSON is available — use `?format=json` for simpler parsing.
- **NEVER** hardcode capabilities — always check `/cloud/capabilities` first for feature detection.

### Version Notes

- NC 28+: OCS Status API with backup/restore functionality
- v2 endpoints map OCS status codes to HTTP status codes (200, 400, 404, etc.)
- `forceLanguage=en` parameter available to override locale per-request

---

## §3: WebDAV

### Overview

Nextcloud exposes file, calendar, and contact operations through WebDAV (RFC 4918). The primary endpoint is `/remote.php/dav/`. Public shares (NC 29+) use `/public.php/dav/files/{share_token}`.

### DAV Endpoint Structure

| Endpoint | Purpose |
|----------|---------|
| `/remote.php/dav/files/{username}/` | File operations |
| `/remote.php/dav/calendars/{username}/` | Calendar access (CalDAV) |
| `/remote.php/dav/addressbooks/users/{username}/` | Contacts (CardDAV) |
| `/remote.php/dav/uploads/{username}/` | Chunked upload staging |
| `/remote.php/dav/trashbin/{username}/` | Trash operations |
| `/remote.php/dav/versions/{username}/` | File version history |
| `/public.php/dav/files/{share_token}/` | Public share access (NC 29+) |

Public shares with passwords use basic auth: username=`anonymous`, password=share password.

### File Operations

#### PROPFIND — List/Get Properties
```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/folder' \
  --user username:password \
  --request PROPFIND \
  --header 'Depth: 1' \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
      <d:prop>
        <d:getlastmodified/>
        <d:getcontentlength/>
        <d:getcontenttype/>
        <oc:permissions/>
        <d:resourcetype/>
        <d:getetag/>
      </d:prop>
    </d:propfind>'
```

`Depth: 0` = folder only, `Depth: 1` = folder + immediate children, `Depth: infinity` = recursive (may be disabled).

#### GET — Download File
```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/file.txt' \
  --user username:password
```

**Folder download** (Nextcloud extension): Set `Accept: application/zip` to download folder as ZIP. Optionally filter files with `X-NC-Files` header or `files` query parameter (JSON array).

#### PUT — Upload File
```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/newfile.txt' \
  --user username:password \
  --request PUT \
  --upload-file localfile.txt
```

Use `X-NC-WebDAV-AutoMkcol: 1` to auto-create missing parent directories.

#### MKCOL — Create Folder
```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/newfolder' \
  --user username:password \
  --request MKCOL
```

#### MOVE — Rename/Move
```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/oldname.txt' \
  --user username:password \
  --request MOVE \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/newname.txt' \
  --header 'Overwrite: F'
```

#### COPY — Duplicate
```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/source.txt' \
  --user username:password \
  --request COPY \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/copy.txt'
```

#### DELETE — Remove
```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/file.txt' \
  --user username:password \
  --request DELETE
```

Recursively deletes folder contents when applied to directories.

### Property Namespaces

| URI | Prefix | Origin |
|-----|--------|--------|
| `DAV:` | `d` | WebDAV standard |
| `http://owncloud.org/ns` | `oc` | ownCloud legacy |
| `http://nextcloud.org/ns` | `nc` | Nextcloud-specific |
| `http://open-collaboration-services.org/ns` | `ocs` | OCS |
| `http://open-cloud-mesh.org/ns` | `ocm` | Open Cloud Mesh |

**Standard properties**: `d:getlastmodified`, `d:getetag`, `d:getcontenttype`, `d:resourcetype`, `d:getcontentlength`

**Nextcloud-specific properties**: `oc:fileid`, `oc:permissions`, `nc:has-preview`, `oc:favorite`, `oc:comments-unread`, `nc:mount-type`, `nc:is-encrypted`, `nc:lock`, `nc:share-attributes`

### Special Request Headers

| Header | Purpose | Direction |
|--------|---------|-----------|
| `X-OC-MTime` | Set modification timestamp (Unix) | Request |
| `X-OC-CTime` | Set creation timestamp | Request |
| `OC-Checksum` | Store checksum (MD5, SHA1, SHA256, SHA3-256, Adler32) | Request |
| `X-Hash` | Request server to compute hash | Request |
| `X-Hash-MD5/SHA1/SHA256` | Computed hash values | Response |
| `OC-Etag` | File etag on create/move/copy | Response |
| `OC-FileId` | File identifier (padded-id + instance-id) | Response |
| `OC-Total-Length` | Total file size for quota checks | Request |
| `X-NC-WebDAV-AutoMkcol` | Auto-create parent directories (set to `1`) | Request |

### Chunked Upload Protocol v2

Three-step process for reliable large file uploads:

**Step 1: Create upload directory (MKCOL)**
```bash
curl -X MKCOL -u user:pass \
  https://server/remote.php/dav/uploads/user/myapp-e1663913-4423-4efe-a9cd-26e7beeca3c0 \
  --header 'Destination: https://server/remote.php/dav/files/user/dest/file.zip'
```

**Step 2: Upload chunks (PUT)**
```bash
curl -X PUT -u user:pass \
  https://server/remote.php/dav/uploads/user/myapp-e1663913-4423-4efe-a9cd-26e7beeca3c0/00001 \
  --data-binary @chunk1 \
  --header 'Destination: https://server/remote.php/dav/files/user/dest/file.zip' \
  --header 'OC-Total-Length: 15000000'
```

**Step 3: Assemble (MOVE .file)**
```bash
curl -X MOVE -u user:pass \
  https://server/remote.php/dav/uploads/user/myapp-e1663913-4423-4efe-a9cd-26e7beeca3c0/.file \
  --header 'Destination: https://server/remote.php/dav/files/user/dest/file.zip' \
  --header 'OC-Total-Length: 15000000'
```

**Constraints**:
- Chunk names: numbers 1-10000
- Chunk size: 5MB–5GB (final chunk can be smaller)
- Upload directory expires after 24 hours of inactivity
- `Destination` header required on EVERY request
- `OC-Total-Length` triggers quota validation (returns 507 if insufficient)
- Optional `X-OC-Mtime` on MOVE to set modification time

**Abort upload**: `DELETE` the upload directory.

### Anti-Patterns

- **NEVER** omit the `Destination` header on MOVE/COPY — the request will fail.
- **NEVER** use `Depth: infinity` PROPFIND on large directories — it may time out or be rejected.
- **NEVER** skip checksum verification for important uploads — use `OC-Checksum` header.
- **NEVER** assume chunk order — chunks are assembled in numeric order regardless of upload order.

### Version Notes

- NC 29+: Public share WebDAV access via `/public.php/dav/files/{share_token}/`
- Chunked upload v2 supports direct upload to S3-compatible object storage

---

## §4: App Framework — Controllers & Routing

### Overview

Nextcloud's App Framework provides a structured MVC architecture with controllers, routing, middleware, and dependency injection. Controllers handle HTTP requests, routes map URLs to controller methods, and middleware provides cross-cutting concerns.

### Controller Types

#### Base Controller (`OCP\AppFramework\Controller`)
```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\IRequest;

class PageController extends Controller {
    public function __construct(string $appName, IRequest $request) {
        parent::__construct($appName, $request);
    }

    public function index(): TemplateResponse {
        return new TemplateResponse($this->appName, 'main');
    }
}
```

#### OCSController (`OCP\AppFramework\OCSController`)
For OCS API endpoints with automatic JSON/XML response formatting:
```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;

class ShareController extends OCSController {
    public function getShares(): DataResponse {
        return new DataResponse(['shares' => []]);
    }
}
```
Accessible via: `/ocs/v2.php/apps/<APPNAME>/api/v1/<endpoint>`

### Route Definition (`appinfo/routes.php`)

```php
<?php
return [
    // Standard routes (via /index.php/apps/myapp/...)
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
        ['name' => 'author#show', 'url' => '/authors/{id}', 'verb' => 'GET'],
        ['name' => 'author#create', 'url' => '/authors', 'verb' => 'POST'],
    ],

    // OCS routes (via /ocs/v2.php/apps/myapp/...)
    'ocs' => [
        ['name' => 'api#getData', 'url' => '/api/v1/data', 'verb' => 'GET'],
    ],

    // Resource routes (auto-generates 5 CRUD routes)
    'resources' => [
        'author' => ['url' => '/authors'],
    ],
];
```

**Route name resolution**: `author_api#some_method` resolves to `AuthorApiController::someMethod()`.

**Resource routes** auto-generate:
| Method | URL | Action |
|--------|-----|--------|
| GET | `/authors` | `index()` |
| GET | `/authors/{id}` | `show()` |
| POST | `/authors` | `create()` |
| PUT | `/authors/{id}` | `update()` |
| DELETE | `/authors/{id}` | `destroy()` |

**Optional route parameters**:
- `requirements`: Regex for URL segments (e.g., `['path' => '.+']` to match slashes)
- `defaults`: Default values (e.g., `['page' => 1]`)
- `postfix`: Suffix for route ID uniqueness

**Attribute-based routing** (NC 29+):
```php
#[FrontpageRoute(verb: 'GET', url: '/')]
public function index() { }

#[ApiRoute(verb: 'GET', url: '/api/v1/data')]
public function getData(): DataResponse { }
```

### URL Generation

```php
use OCP\IURLGenerator;

$url = $this->urlGenerator->linkToRoute('myapp.author_api.do_something', ['id' => 3]);
```
Route names use dots (`.`) and underscores replace hashes. App name is case-sensitive.

### Request Parameter Extraction

Parameters are automatically injected from URL path, query string, form data, or JSON body:

```php
// URL: /authors/{id}?name=john&job=writer
public function show(string $id, string $name = 'unknown', string $job = 'author'): Response {
    // $id from path, $name from query, $job from query (or default)
}
```

**Type casting** via type hints:
```php
/**
 * @param int $id
 * @param bool $doMore
 * @param float $value
 */
public function doSomething(int $id, bool $doMore, float $value): Response { }
```
Supported: `bool`, `boolean`, `int`, `integer`, `float`

**JSON body** (Content-Type: `application/json`): Top-level keys map directly to parameters:
```php
// Body: {"name": "test", "number": 3, "customFields": {...}}
public function create(string $name, int $number, array $customFields): Response { }
```

**Direct request access**:
```php
$type = $this->request->getHeader('Content-Type');
$cookie = $this->request->getCookie('myCookie');
$file = $this->request->getUploadedFile('myfile');
```

### Security Attributes (NC 27+)

| Attribute | Effect |
|-----------|--------|
| `#[NoAdminRequired]` | Allow non-admin authenticated users |
| `#[PublicPage]` | No login required |
| `#[NoCSRFRequired]` | Skip CSRF token validation |
| `#[NoTwoFactorRequired]` | Bypass 2FA requirement |
| `#[UserRateLimit(limit: 5, period: 100)]` | Rate limit for logged-in users |
| `#[AnonRateLimit(limit: 1, period: 100)]` | Rate limit for anonymous users |
| `#[BruteForceProtection(action: 'login')]` | Enable brute force throttling |

**Default security posture** (no attributes): admin-only, authenticated, 2FA required, CSRF validated.

**Legacy annotations** (pre-NC 27): `@NoAdminRequired`, `@NoCSRFRequired`, `@PublicPage`

**Brute force protection example**:
```php
#[BruteForceProtection(action: 'token')]
#[BruteForceProtection(action: 'password')]
public function getProtectedShare(string $token, string $password): TemplateResponse {
    $response = new TemplateResponse(/* ... */);
    if (!$this->shareManager->getByToken($token)) {
        $response->throttle(['action' => 'token']);
    }
    if (!$share->verifyPassword($password)) {
        $response->throttle(['action' => 'password']);
    }
    return $response;
}
```

### Response Types

| Class | Use Case |
|-------|----------|
| `TemplateResponse` | Render server-side PHP template |
| `PublicTemplateResponse` | Public page with header actions |
| `JSONResponse` | JSON data |
| `DataResponse` | Generic data (format determined by responder) |
| `RedirectResponse` | HTTP redirect |
| `DownloadResponse` | File download |
| `StreamResponse` | Stream file contents |

**Custom response**: Extend `Response`, implement `render()`:
```php
class XMLResponse extends Response {
    public function __construct(private array $xml) {
        $this->addHeader('Content-Type', 'application/xml');
    }
    public function render(): string { /* convert to XML */ }
}
```

**Responder system** for format negotiation: Priority: `?format=xml` > `Accept` header > defaults to `json`.

**Error handling**:
```php
use OCP\AppFramework\Http;

public function show(int $id) {
    try {
        return new JSONResponse($this->service->find($id));
    } catch (NotFoundException $ex) {
        return new JSONResponse([], Http::STATUS_NOT_FOUND);
    }
}
```

### Middleware Chain

Middleware follows Django's pattern with four hooks:

1. `beforeController($controller, $methodName)` — pre-execution (forward order)
2. `afterException($controller, $methodName, $exception)` — exception handling (reverse order)
3. `afterController($controller, $methodName, $response)` — post-execution (reverse order)
4. `beforeOutput($controller, $methodName, $output)` — output manipulation (reverse order)

**Custom middleware**:
```php
namespace OCA\MyApp\Middleware;

use OCP\AppFramework\Middleware;

class CensorMiddleware extends Middleware {
    public function beforeOutput($controller, $methodName, $output): string {
        return str_replace('bad words', '********', $output);
    }
}
```

**Registration**:
```php
// In Application::register()
$context->registerMiddleware(CensorMiddleware::class);

// Global middleware (NC 26+) — runs across ALL apps:
$context->registerMiddleware(MonitoringMiddleware::class, true);
```

**Annotation-aware middleware** using `IControllerMethodReflector`:
```php
public function afterController($controller, $methodName, Response $response): Response {
    if ($this->reflector->hasAnnotation('MyHeader')) {
        $response->addHeader('My-Header', 3);
    }
    return $response;
}
```

### Content Security Policy

```php
use OCP\AppFramework\Http\ContentSecurityPolicy;

$response = new TemplateResponse('myapp', 'main');
$csp = new ContentSecurityPolicy();
$csp->addAllowedImageDomain('*');
$csp->addAllowedMediaDomain('*');
$csp->addAllowedConnectDomain('https://api.example.com');
$response->setContentSecurityPolicy($csp);
```

Available CSP methods: `allowInlineScript()`, `allowInlineStyle()`, `allowEvalScript()`, `useStrictDynamic()`, `addAllowedScriptDomain()`, `addAllowedStyleDomain()`, `addAllowedFontDomain()`, `addAllowedImageDomain()`, `addAllowedConnectDomain()`, `addAllowedMediaDomain()`, `addAllowedObjectDomain()`, `addAllowedFrameDomain()`, `addAllowedChildSrcDomain()`.

### Anti-Patterns

- **NEVER** create controller methods without security attributes and assume they are public — the default is admin-only.
- **NEVER** use `@NoCSRFRequired` on state-changing endpoints without the `OCS-APIRequest: true` header alternative.
- **NEVER** forget to return the `$response` from `afterController()` middleware — the response will be lost.
- **NEVER** use uppercase-starting custom annotations in middleware — they must start with uppercase to be parsed.

### Version Notes

- NC 29+: `#[FrontpageRoute]` and `#[ApiRoute]` attribute-based routing
- NC 27+: PHP 8 attributes replace `@` annotations
- NC 26+: `#[UseSession]` attribute, global middleware registration

---

## §5: Database Layer

### Overview

Nextcloud provides a database abstraction through `OCP\IDBConnection` supporting MySQL, PostgreSQL, SQLite, and Oracle. The layer includes an Entity/Mapper pattern (similar to ORM), a query builder, migrations for schema management, and transaction support.

### Migration System

Migrations live in `lib/Migration/` and follow the naming pattern `Version{MajorMinor}Date{Timestamp}` (e.g., `Version2404Date20220903071748`). Version mapping: `1.0.x => 1000`, `2.34.x => 2034`.

**Three-step migration pattern** (rename column while preserving data):

**Step 1: Add new column**
```php
<?php
namespace OCA\MyApp\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

class Version1000Date20240101000000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
        /** @var ISchemaWrapper $schema */
        $schema = $schemaClosure();

        if (!$schema->hasTable('myapp_items')) {
            $table = $schema->createTable('myapp_items');
            $table->addColumn('id', \OCP\DB\Types::BIGINT, [
                'autoincrement' => true,
                'notnull' => true,
            ]);
            $table->addColumn('user_id', \OCP\DB\Types::STRING, [
                'notnull' => true,
                'length' => 64,
            ]);
            $table->addColumn('title', \OCP\DB\Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->setPrimaryKey(['id']);
            $table->addIndex(['user_id'], 'myapp_user_idx');
        }

        return $schema;
    }
}
```

**Step 2: Migrate data**
```php
public function postSchemaChange(IOutput $output, Closure $schemaClosure, array $options) {
    $query = $this->db->getQueryBuilder();
    $query->update('myapp_items')
        ->set('user_id', 'uid');
    $query->executeStatement();
}
```

**Step 3: Remove old column** (in a separate migration class)

**Dependency injection in migrations**:
```php
class Version2404Date20220903071748 extends SimpleMigrationStep {
    public function __construct(private IDBConnection $db) {}
}
```

**Migration metadata attributes** (NC 30+):
```php
#[CreateTable(table: 'new_table', description: 'Table description')]
#[AddColumn(table: 'existing_table', name: 'new_col', type: ColumnType::STRING)]
#[ModifyColumn(table: 'other_table', name: 'field', type: ColumnType::BIGINT)]
#[DropColumn(table: 'old_table', name: 'removed_col')]
#[AddIndex(table: 'my_table', name: 'my_index')]
#[DropIndex(table: 'my_table', name: 'old_index')]
#[DropTable(table: 'deprecated_table')]
class Version30000Date20240729185117 extends SimpleMigrationStep {}
```

**CRITICAL**: NEVER update existing migrations. Create new migration classes for changes, because Nextcloud tracks which migrations have executed.

**Index management for large tables** (non-blocking via event):
```php
class AddMissingIndicesListener implements IEventListener {
    public function handle(Event $event): void {
        if (!$event instanceof AddMissingIndicesEvent) return;
        $event->addMissingIndex('my_table', 'my_index', ['column_a', 'column_b']);
    }
}
```

**Replace indices atomically** (NC 29+):
```php
$event->replaceIndex('my_table', ['old_idx_1', 'old_idx_2'], 'new_index', ['col_a', 'col_b'], false);
```

### Entity System

Entities extend `OCP\AppFramework\Db\Entity` with automatic getter/setter generation:

```php
namespace OCA\MyApp\Db;

use OCP\AppFramework\Db\Entity;

class Author extends Entity {
    protected ?string $name = null;
    protected ?string $phoneNumber = null;
    protected ?int $age = null;

    public function __construct() {
        $this->addType('age', 'integer');
    }
}
```

- Property `$phoneNumber` auto-generates `getPhoneNumber()` / `setPhoneNumber()`
- Column mapping: camelCase property → snake_case column (`phoneNumber` → `phone_number`)
- Override `columnToProperty()` / `propertyToColumn()` for custom mapping

**Supported types** (`OCP\DB\Types`):
`INTEGER`, `FLOAT`, `BOOLEAN`, `STRING`, `BLOB`, `JSON`, `DATE`, `TIME`, `DATETIME`, `DATETIME_TZ`, `DATE_IMMUTABLE`, `TIME_IMMUTABLE`, `DATETIME_IMMUTABLE`, `DATETIME_TZ_IMMUTABLE`

### QBMapper

```php
namespace OCA\MyApp\Db;

use OCP\AppFramework\Db\QBMapper;
use OCP\IDBConnection;

class AuthorMapper extends QBMapper {
    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'myapp_authors'); // table name without oc_ prefix
    }

    public function find(int $id): Author {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('id', $qb->createNamedParameter($id)));
        return $this->findEntity($qb);
    }

    public function findAll(): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')->from($this->getTableName());
        return $this->findEntities($qb);
    }
}
```

**Key methods**: `findEntity()` (single, throws on 0 or 2+), `findEntities()` (array), `insert()`, `update()`, `delete()`

### Query Builder

```php
$qb = $this->db->getQueryBuilder();
$qb->select('a.id', 'a.name', 'b.title')
    ->from('myapp_authors', 'a')
    ->join('a', 'myapp_books', 'b', $qb->expr()->eq('a.id', 'b.author_id'))
    ->where($qb->expr()->eq('a.name', $qb->createNamedParameter('John')))
    ->orderBy('a.name', 'ASC')
    ->setMaxResults(10);

$result = $qb->executeQuery();
while ($row = $result->fetchAssociative()) {
    // process row
}
$result->closeCursor();
```

### Transaction Management

**TTransactional trait** (recommended):
```php
use OCP\DB\TTransactional;

class MyService {
    use TTransactional;

    public function doWork(): void {
        $this->atomic(function () {
            // All operations here are wrapped in a transaction
            // Automatic rollback on exception
        }, $this->db);
    }
}
```

**Manual transactions**:
```php
$this->db->beginTransaction();
try {
    // operations
    $this->db->commit();
} catch (\Exception $e) {
    $this->db->rollBack();
    throw $e;
}
```

### Database Constraints

**Table naming**: Max 23 characters (accounting for `oc_` prefix = 27 total for Oracle).

**Oracle-specific limits**:
- Column/index/FK names: max 30 characters
- No `NOT NULL` string columns with empty string defaults
- String columns: max 4,000 characters
- Boolean columns cannot be `NOT NULL`

**Galera Cluster**: All tables MUST have primary keys.

**Best practices**:
- ALWAYS include auto-incremented `id BIGINT` column
- ALWAYS define explicit primary keys
- ALWAYS use custom (globally unique) index names
- ALWAYS name indices for future manipulation

### Anti-Patterns

- **NEVER** modify an existing migration file — create a new migration instead.
- **NEVER** use raw SQL queries — always use the query builder for database portability.
- **NEVER** forget to close cursors on select queries (though `findEntity`/`findEntities` auto-close).
- **NEVER** exceed Oracle column name limits if you need to support it.
- **NEVER** create tables without primary keys — Galera Cluster will fail.

### Version Notes

- NC 30+: Migration metadata attributes (`#[CreateTable]`, etc.)
- NC 29+: `replaceIndex()` for atomic index replacement
- NC 28+: `AddMissingIndicesEvent` / `AddMissingColumnsEvent` / `AddMissingPrimaryKeyEvent`

---

## §6: Authentication & Security

### Overview

Nextcloud provides multiple authentication mechanisms: session-based login, Login Flow v2 for desktop/mobile clients, app passwords for device-specific credentials, OAuth2, and OIDC. The security model includes CSRF protection, rate limiting, brute force protection, and Content Security Policy.

### Login Flow v2 Protocol

Four-step protocol for external clients:

**Step 1: Initiate**
```bash
curl -X POST https://cloud.example.com/index.php/login/v2
```

**Response**:
```json
{
    "poll": {
        "token": "mQUYQdffOSAMJYtm8pVpkOsVqXt5hglnuSpO5EMbgJ...",
        "endpoint": "https://cloud.example.com/login/v2/poll"
    },
    "login": "https://cloud.example.com/login/v2/flow/[flow-identifier]"
}
```

**Step 2: Open browser** — Open the `login` URL in the user's default browser. The user authenticates through the web interface (handles passwords, 2FA, SSO, etc.).

**Step 3: Poll for credentials**
```bash
curl -X POST https://cloud.example.com/login/v2/poll \
  -d "token=mQUYQdffOSAMJYtm8pVpkOsVqXt5hglnuSpO5EMbgJ..."
```
Returns `404` until authentication completes. Token valid for 20 minutes. Result returned ONCE per token.

**Step 4: Receive credentials**
```json
{
    "server": "https://cloud.example.com",
    "loginName": "username",
    "appPassword": "yKTVA4zgxjfivy52WqD8kW3M2pKGQr6srmUXMipRdun..."
}
```

### App Passwords

- **Purpose**: Device-specific credentials that replace user passwords in client applications
- **Creation**: Automatic via Login Flow v2, or manual in Settings > Security > Devices & sessions
- **Scoping**: Automatically named based on `USER_AGENT` header sent during authentication
- **Usage**: Standard basic auth with `loginName` as username and `appPassword` as password
- **Storage**: Clients MUST store credentials securely; the app password is shown only once

### CSRF Protection

**Default behavior**: ALL controller methods require CSRF token validation. CSRF tokens are validated via:
1. The `requesttoken` form field or header
2. The `OCS-APIRequest: true` header (alternative for API clients)

**Disabling CSRF** (for API endpoints):
```php
#[NoCSRFRequired]
public function apiEndpoint(): JSONResponse {
    return new JSONResponse(['data' => 'value']);
}
```

**IMPORTANT**: When using `#[NoCSRFRequired]`, ensure the endpoint is safe from CSRF attacks through other means (e.g., requiring API authentication headers, being read-only).

### Rate Limiting

Per-method rate limits using attributes:
```php
#[UserRateLimit(limit: 5, period: 100)]   // 5 calls per 100 seconds for logged-in users
#[AnonRateLimit(limit: 1, period: 100)]   // 1 call per 100 seconds for anonymous
public function sensitiveAction(): Response { }
```

### Brute Force Protection

Throttle repeated failed attempts:
```php
#[BruteForceProtection(action: 'login')]
public function login(string $username, string $password): Response {
    $response = new JSONResponse();
    if (!$this->authenticate($username, $password)) {
        $response->throttle(['action' => 'login']);
    }
    return $response;
}
```

Multiple actions can be protected independently on the same method. The `throttle()` call on the response triggers the delay.

### Controller Security Defaults

Without any attributes, controller methods enforce:
1. Admin-only access (non-admins get 403)
2. Authenticated users only (anonymous get redirect to login)
3. Two-factor authentication completed
4. CSRF token validation (or `OCS-APIRequest: true` header)

To make a public API endpoint:
```php
#[PublicPage]        // No login required
#[NoCSRFRequired]    // No CSRF token (API clients)
public function publicApi(): JSONResponse {
    return new JSONResponse(['status' => 'ok']);
}
```

### Events System (Security-Relevant)

Nextcloud provides extensive security-related events for monitoring and extending authentication:

| Event | Since | Purpose |
|-------|-------|---------|
| `BeforeUserLoggedInEvent` | v18 | Pre-login hook |
| `PostLoginEvent` | v18 | Post-login hook |
| `LoginFailedEvent` | v19 | Failed login attempt |
| `AnyLoginFailedEvent` | v26 | Any login failure (broader) |
| `UserFirstTimeLoggedInEvent` | v28 | First-ever login |
| `TokenInvalidatedEvent` | v32 | Auth token revoked |
| `TwoFactorProviderChallengeFailed` | v28 | 2FA failure |
| `TwoFactorProviderChallengePassed` | v28 | 2FA success |

### Content Security Policy

Modify CSP on a per-response basis:
```php
$csp = new ContentSecurityPolicy();
$csp->addAllowedImageDomain('https://images.example.com');
$csp->addAllowedConnectDomain('https://api.example.com');
$csp->allowInlineScript(false);  // Default: false
$csp->useStrictDynamic(true);    // Default: true
$response->setContentSecurityPolicy($csp);
```

Or globally via event listener for `AddContentSecurityPolicyEvent`.

### Anti-Patterns

- **NEVER** store user passwords in client applications — always use Login Flow v2 to obtain app passwords.
- **NEVER** use `#[PublicPage]` + `#[NoCSRFRequired]` on state-changing endpoints without additional authentication.
- **NEVER** ignore the 20-minute token expiry in Login Flow v2 — implement timeout handling.
- **NEVER** poll the Login Flow v2 endpoint without backoff — implement reasonable intervals (1-2 seconds).
- **NEVER** disable brute force protection on authentication endpoints.
- **NEVER** call `$response->throttle()` on success — only on failure conditions.

### Version Notes

- NC 28+: `UserFirstTimeLoggedInEvent`, `BeforeShareCreatedEvent`
- NC 27+: PHP 8 security attributes replace annotations
- NC 26+: `AnyLoginFailedEvent`, global middleware
- Login Flow v2: Available since NC 16, current standard for all clients

---

## Appendix: Events Catalog (Partial — Security & Core)

The Nextcloud event system provides 150+ typed events. Key categories:

- **File events**: `BeforeNodeCreatedEvent`, `NodeCreatedEvent`, `NodeDeletedEvent`, `NodeRenamedEvent`, `NodeWrittenEvent`, etc. (all since v20)
- **User lifecycle**: `UserCreatedEvent`, `UserDeletedEvent`, `UserChangedEvent`, `PasswordUpdatedEvent`
- **Group events**: `GroupCreatedEvent`, `UserAddedEvent`, `UserRemovedEvent`
- **Share events**: `BeforeShareCreatedEvent`, `ShareCreatedEvent`, `ShareDeletedEvent`
- **DAV events**: `CalendarCreatedEvent`, `CalendarObjectCreatedEvent`, `CardCreatedEvent`, etc.
- **App events**: `AppEnableEvent`, `AppDisableEvent`, `AppUpdateEvent`
- **AI/Processing**: `TaskFailedEvent`, `TaskSuccessfulEvent` (TaskProcessing, v30+)

All events follow the naming pattern `{Subject}Event` or `Before{Subject}Event`. Register listeners via `IRegistrationContext::registerEventListener()` in the Application class.
