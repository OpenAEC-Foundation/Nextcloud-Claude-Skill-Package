---
name: nextcloud-syntax-controllers
description: "Guides Nextcloud controller development including Controller and OCSController types, routes.php definition, attribute-based routing, parameter extraction, security attributes, response types, and format negotiation. Activates when creating controllers, defining routes, handling requests, or implementing API endpoints."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-syntax-controllers

## Quick Reference

### Controller Types

| Class | Base Path | Use Case |
|-------|-----------|----------|
| `OCP\AppFramework\Controller` | `/index.php/apps/{appid}/` | Page rendering, internal endpoints |
| `OCP\AppFramework\OCSController` | `/ocs/v2.php/apps/{appid}/` | OCS API with JSON/XML envelope |
| `OCP\AppFramework\ApiController` | `/index.php/apps/{appid}/` | REST API (extends Controller, adds CORS) |

### Route Definition Arrays (`appinfo/routes.php`)

| Array | URL Prefix | Controller Base |
|-------|-----------|-----------------|
| `routes` | `/index.php/apps/{appid}/` | `Controller` or `ApiController` |
| `ocs` | `/ocs/v2.php/apps/{appid}/` | `OCSController` |
| `resources` | `/index.php/apps/{appid}/` | Auto-generates 5 CRUD routes |

### Route Name Resolution

| Route Name | Controller Class | Method |
|------------|-----------------|--------|
| `page#index` | `PageController` | `index()` |
| `author_api#some_method` | `AuthorApiController` | `someMethod()` |
| `api#getData` | `ApiController` | `getData()` |

### Parameter Extraction

| Source | Example | Extraction |
|--------|---------|------------|
| URL path | `/authors/{id}` | `$id` parameter |
| Query string | `?name=john` | `$name` parameter |
| JSON body | `{"title": "Test"}` | `$title` parameter |
| Form data | `name=john` | `$name` parameter |
| Default value | `$page = 1` | Falls back if not in request |

### Type Casting (via type hints or `@param`)

| Type | PHP Hint | Notes |
|------|----------|-------|
| `int` / `integer` | `int $id` | Numeric string to int |
| `float` | `float $value` | Numeric string to float |
| `bool` / `boolean` | `bool $flag` | `"true"`/`"1"` to true |
| `string` | `string $name` | Default, no conversion |
| `array` | `array $items` | From JSON body |

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

### Response Types

| Class | Use Case |
|-------|----------|
| `TemplateResponse` | Render server-side PHP template |
| `PublicTemplateResponse` | Public page with header actions |
| `JSONResponse` | JSON data with HTTP status |
| `DataResponse` | Generic data (format via responder) |
| `RedirectResponse` | HTTP redirect |
| `DownloadResponse` | File download |
| `StreamResponse` | Stream file contents |

### Critical Warnings

**NEVER** create controller methods without security attributes and assume they are public -- the default is admin-only. Explicitly add `#[NoAdminRequired]` for regular user access or `#[PublicPage]` for anonymous access.

**NEVER** use `#[NoCSRFRequired]` on state-changing endpoints without alternative protection -- either require the `OCS-APIRequest: true` header or use token-based authentication.

**NEVER** use `#[PublicPage]` + `#[NoCSRFRequired]` on state-changing endpoints without additional authentication -- this leaves the endpoint completely unprotected.

**NEVER** return a response without the correct HTTP status code -- use the `Http::STATUS_*` constants for clarity.

**ALWAYS** extend `OCSController` for OCS API endpoints -- using `Controller` with OCS routes will break the response envelope.

**ALWAYS** define routes in `appinfo/routes.php` -- controllers without routes are unreachable.

**ALWAYS** use constructor injection for dependencies -- Nextcloud auto-wires by type hint.

**ALWAYS** call `$response->throttle()` only on failure conditions when using `#[BruteForceProtection]` -- never on success.

---

## Essential Patterns

### Pattern 1: Page Controller with Template

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\IRequest;

class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private MyService $service,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        return new TemplateResponse($this->appName, 'main');
    }
}
```

```php
// appinfo/routes.php
return [
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
    ],
];
```

### Pattern 2: OCS API Controller

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;

class ItemApiController extends OCSController {
    public function __construct(
        string $appName,
        IRequest $request,
        private ItemService $service,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll($this->userId));
    }

    #[NoAdminRequired]
    public function show(int $id): DataResponse {
        return new DataResponse($this->service->find($id, $this->userId));
    }

    #[NoAdminRequired]
    public function create(string $title, string $content = ''): DataResponse {
        return new DataResponse(
            $this->service->create($title, $content, $this->userId)
        );
    }
}
```

```php
// appinfo/routes.php
return [
    'ocs' => [
        ['name' => 'item_api#index', 'url' => '/api/v1/items', 'verb' => 'GET'],
        ['name' => 'item_api#show', 'url' => '/api/v1/items/{id}', 'verb' => 'GET'],
        ['name' => 'item_api#create', 'url' => '/api/v1/items', 'verb' => 'POST'],
    ],
];
```

### Pattern 3: Resource Routes (Auto-CRUD)

```php
// appinfo/routes.php
return [
    'resources' => [
        'author' => ['url' => '/authors'],
    ],
];
```

This auto-generates five routes mapping to `AuthorController`:

| Verb | URL | Method |
|------|-----|--------|
| GET | `/authors` | `index()` |
| GET | `/authors/{id}` | `show(int $id)` |
| POST | `/authors` | `create()` |
| PUT | `/authors/{id}` | `update(int $id)` |
| DELETE | `/authors/{id}` | `destroy(int $id)` |

### Pattern 4: Attribute-Based Routing (NC 29+)

```php
use OCP\AppFramework\Http\Attribute\FrontpageRoute;
use OCP\AppFramework\Http\Attribute\ApiRoute;

class PageController extends Controller {

    #[NoAdminRequired]
    #[FrontpageRoute(verb: 'GET', url: '/')]
    public function index(): TemplateResponse {
        return new TemplateResponse($this->appName, 'main');
    }
}

class ItemApiController extends OCSController {

    #[NoAdminRequired]
    #[ApiRoute(verb: 'GET', url: '/api/v1/items')]
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll());
    }
}
```

### Pattern 5: Error Handling with Status Codes

```php
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;

#[NoAdminRequired]
public function show(int $id): JSONResponse {
    try {
        return new JSONResponse($this->service->find($id, $this->userId));
    } catch (NotFoundException $e) {
        return new JSONResponse([], Http::STATUS_NOT_FOUND);
    } catch (ForbiddenException $e) {
        return new JSONResponse(['message' => $e->getMessage()], Http::STATUS_FORBIDDEN);
    }
}
```

### Pattern 6: Complete routes.php with All Three Arrays

```php
<?php
return [
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
        ['name' => 'page#settings', 'url' => '/settings', 'verb' => 'GET'],
        [
            'name' => 'file#download',
            'url' => '/files/{path}',
            'verb' => 'GET',
            'requirements' => ['path' => '.+'],  // match slashes in path
        ],
        [
            'name' => 'page#list',
            'url' => '/list',
            'verb' => 'GET',
            'defaults' => ['page' => 1, 'limit' => 20],
        ],
    ],
    'ocs' => [
        ['name' => 'api#getData', 'url' => '/api/v1/data', 'verb' => 'GET'],
        ['name' => 'api#updateData', 'url' => '/api/v1/data/{id}', 'verb' => 'PUT'],
    ],
    'resources' => [
        'author' => ['url' => '/authors'],
    ],
];
```

---

## Responder System (Format Negotiation)

Priority order for response format:
1. `?format=xml` or `?format=json` query parameter (highest)
2. `Accept` HTTP header
3. Default: `json`

OCSController handles this automatically -- `DataResponse` is rendered as JSON or XML based on negotiation.

For custom formats, register a responder:

```php
class MyController extends Controller {
    public function __construct(string $appName, IRequest $request) {
        parent::__construct($appName, $request);
        $this->registerResponder('xml', function ($data) {
            return new XMLResponse($data);
        });
    }
}
```

---

## URL Generation

```php
use OCP\IURLGenerator;

// Route URL: /index.php/apps/myapp/authors/3
$url = $urlGenerator->linkToRoute('myapp.author.show', ['id' => 3]);

// OCS route URL: /ocs/v2.php/apps/myapp/api/v1/data
$url = $urlGenerator->linkToOCSRoute('myapp.api.getData');
```

Route name format: `{appid}.{controller}.{method}` where hashes become dots and underscores are preserved.

---

## Reference Links

- [references/methods.md](references/methods.md) -- Controller types, route syntax, response types, parameter extraction
- [references/examples.md](references/examples.md) -- Controller patterns, routing patterns
- [references/anti-patterns.md](references/anti-patterns.md) -- Controller mistakes

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/controllers.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/routing.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/middleware.html
