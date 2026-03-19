# Controller Methods Reference

## Controller Base Classes

### OCP\AppFramework\Controller

The base controller for all Nextcloud app controllers. Handles page rendering and internal API endpoints.

**Constructor signature:**
```php
public function __construct(string $appName, IRequest $request)
```

**Inherited properties:**
| Property | Type | Description |
|----------|------|-------------|
| `$this->appName` | `string` | App ID from constructor |
| `$this->request` | `IRequest` | Current HTTP request object |

**Key methods:**
| Method | Return | Description |
|--------|--------|-------------|
| `registerResponder(string $format, Closure $responder)` | `void` | Register custom format responder |
| `buildResponse(Response $response, string $format)` | `Response` | Build response using registered responder |

### OCP\AppFramework\OCSController

Extends `Controller` for OCS API endpoints. Automatically handles the OCS response envelope (meta + data wrapping) and format negotiation between JSON and XML.

**Constructor signature:**
```php
public function __construct(
    string $appName,
    IRequest $request,
    string $corsMethods = 'PUT, POST, GET, DELETE, PATCH',
    string $corsAllowedHeaders = 'Authorization, Content-Type, Accept',
    int $corsMaxAge = 1728000
)
```

**Additional methods:**
| Method | Return | Description |
|--------|--------|-------------|
| `getResponderByHTTPHeader(string $acceptHeader)` | `string` | Determine format from Accept header |

### OCP\AppFramework\ApiController

Extends `Controller` with CORS support for external REST API access. Use when building non-OCS REST APIs that need cross-origin access.

**Constructor signature:**
```php
public function __construct(
    string $appName,
    IRequest $request,
    string $corsMethods = 'PUT, POST, GET, DELETE, PATCH',
    string $corsAllowedHeaders = 'Authorization, Content-Type, Accept',
    int $corsMaxAge = 1728000
)
```

---

## Route Definition Syntax

### routes Array

Standard routes accessible via `/index.php/apps/{appid}/{url}`.

```php
[
    'name' => 'controller#method',   // REQUIRED: controller_name#method_name
    'url' => '/path/{param}',        // REQUIRED: URL pattern with {placeholders}
    'verb' => 'GET',                 // REQUIRED: HTTP method (GET, POST, PUT, DELETE, PATCH)
    'requirements' => [],            // OPTIONAL: regex constraints per param
    'defaults' => [],                // OPTIONAL: default values per param
    'postfix' => '',                 // OPTIONAL: suffix for route ID uniqueness
]
```

### ocs Array

OCS routes accessible via `/ocs/v2.php/apps/{appid}/{url}`. Same syntax as `routes`.

### resources Array

Auto-generates five CRUD routes for a resource controller.

```php
'resources' => [
    'controller_name' => ['url' => '/base-path'],
]
```

Generated routes:

| Route Name | Verb | URL | Method |
|------------|------|-----|--------|
| `{name}#index` | GET | `{url}` | `index()` |
| `{name}#show` | GET | `{url}/{id}` | `show(int $id)` |
| `{name}#create` | POST | `{url}` | `create()` |
| `{name}#update` | PUT | `{url}/{id}` | `update(int $id)` |
| `{name}#destroy` | DELETE | `{url}/{id}` | `destroy(int $id)` |

### Route Name Resolution Rules

1. Split on `#`: left = controller name, right = method name
2. Controller name: `snake_case` to `PascalCase` + `Controller` suffix
3. Method name: `snake_case` to `camelCase`

| Route Name | Class | Method |
|------------|-------|--------|
| `page#index` | `PageController` | `index()` |
| `author_api#get_data` | `AuthorApiController` | `getData()` |
| `my_settings#update_value` | `MySettingsController` | `updateValue()` |

### Route Options

**requirements** -- Regex constraints for URL parameters:
```php
['name' => 'file#get', 'url' => '/files/{path}', 'verb' => 'GET',
 'requirements' => ['path' => '.+']]  // Allow slashes in path
```

**defaults** -- Default parameter values:
```php
['name' => 'page#list', 'url' => '/list/{page}', 'verb' => 'GET',
 'defaults' => ['page' => 1]]
```

**postfix** -- Disambiguate same URL with different methods:
```php
['name' => 'item#get', 'url' => '/items/{id}', 'verb' => 'GET', 'postfix' => '.get'],
['name' => 'item#update', 'url' => '/items/{id}', 'verb' => 'PUT', 'postfix' => '.update'],
```

---

## Attribute-Based Routing (NC 29+)

### FrontpageRoute

Replaces entries in the `routes` array. Applied directly to controller methods.

```php
use OCP\AppFramework\Http\Attribute\FrontpageRoute;

#[FrontpageRoute(verb: 'GET', url: '/')]
#[FrontpageRoute(verb: 'GET', url: '/path/{id}', requirements: ['id' => '\d+'])]
#[FrontpageRoute(verb: 'GET', url: '/list', defaults: ['page' => 1])]
```

### ApiRoute

Replaces entries in the `ocs` array. Applied directly to OCSController methods.

```php
use OCP\AppFramework\Http\Attribute\ApiRoute;

#[ApiRoute(verb: 'GET', url: '/api/v1/items')]
#[ApiRoute(verb: 'POST', url: '/api/v1/items')]
#[ApiRoute(verb: 'GET', url: '/api/v1/items/{id}', requirements: ['id' => '\d+'])]
```

---

## Parameter Extraction

### Extraction Priority

Parameters are extracted in this order (first match wins):
1. URL path parameters (`/items/{id}`)
2. Request body (JSON or form data)
3. Query string parameters (`?key=value`)

### Type Casting

Type casting uses PHP type hints or `@param` PHPDoc annotations:

| Annotation / Hint | Input | Result |
|-------------------|-------|--------|
| `int $id` | `"42"` | `42` |
| `float $price` | `"19.99"` | `19.99` |
| `bool $active` | `"true"`, `"1"`, `"on"` | `true` |
| `bool $active` | `"false"`, `"0"`, `""` | `false` |
| `array $items` | JSON array | PHP array |

### Direct Request Access

```php
// Headers
$contentType = $this->request->getHeader('Content-Type');

// Cookies
$session = $this->request->getCookie('nc_session');

// File uploads
$file = $this->request->getUploadedFile('attachment');
// Returns: ['name' => ..., 'type' => ..., 'tmp_name' => ..., 'size' => ..., 'error' => ...]

// HTTP method
$method = $this->request->getMethod();

// Raw parameters
$param = $this->request->getParam('key', 'default');
$params = $this->request->getParams();
```

---

## Response Types

### TemplateResponse

Renders a PHP template from `templates/` directory.

```php
use OCP\AppFramework\Http\TemplateResponse;

// Render templates/main.php
new TemplateResponse('myapp', 'main');

// With parameters
new TemplateResponse('myapp', 'main', ['key' => 'value']);

// Blank layout (no Nextcloud chrome)
new TemplateResponse('myapp', 'main', [], TemplateResponse::RENDER_AS_BLANK);
```

Render modes: `RENDER_AS_USER` (default), `RENDER_AS_GUEST`, `RENDER_AS_BLANK`, `RENDER_AS_BASE`, `RENDER_AS_PUBLIC`.

### PublicTemplateResponse

For public-facing pages with optional header actions.

```php
use OCP\AppFramework\Http\PublicTemplateResponse;

$response = new PublicTemplateResponse('myapp', 'public', ['data' => $data]);
$response->setHeaderTitle('Shared Document');
```

### JSONResponse

Direct JSON output with HTTP status code.

```php
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;

new JSONResponse(['items' => $items]);                         // 200 OK
new JSONResponse(['items' => $items], Http::STATUS_OK);        // Explicit 200
new JSONResponse([], Http::STATUS_NOT_FOUND);                  // 404
new JSONResponse(['error' => 'msg'], Http::STATUS_BAD_REQUEST); // 400
```

### DataResponse

Generic data container -- format determined by the responder system. ALWAYS use with OCSController.

```php
use OCP\AppFramework\Http\DataResponse;

new DataResponse(['shares' => $shares]);
new DataResponse([], Http::STATUS_NO_CONTENT);
```

### RedirectResponse

```php
use OCP\AppFramework\Http\RedirectResponse;

new RedirectResponse($this->urlGenerator->linkToRoute('myapp.page.index'));
```

### DownloadResponse

```php
use OCP\AppFramework\Http\DownloadResponse;

new DownloadResponse('report.csv', 'text/csv');
```

### StreamResponse

```php
use OCP\AppFramework\Http\StreamResponse;

$response = new StreamResponse('/path/to/file.pdf');
$response->addHeader('Content-Type', 'application/pdf');
```

### Custom Response

Extend `Response` and implement `render()`:

```php
use OCP\AppFramework\Http\Response;

class CsvResponse extends Response {
    public function __construct(private array $rows) {
        $this->addHeader('Content-Type', 'text/csv');
    }

    public function render(): string {
        $output = fopen('php://temp', 'r+');
        foreach ($this->rows as $row) {
            fputcsv($output, $row);
        }
        rewind($output);
        return stream_get_contents($output);
    }
}
```

---

## Security Attributes

### Full Attribute Reference

| Attribute | Since | Default | Effect |
|-----------|-------|---------|--------|
| `#[NoAdminRequired]` | NC 27 | Admin-only | Allows any authenticated user |
| `#[PublicPage]` | NC 27 | Login required | Allows anonymous access |
| `#[NoCSRFRequired]` | NC 27 | CSRF enforced | Skips CSRF validation |
| `#[NoTwoFactorRequired]` | NC 27 | 2FA enforced | Bypasses 2FA check |
| `#[SubAdminRequired]` | NC 27 | Admin-only | Allows sub-admins |
| `#[UserRateLimit(limit: N, period: S)]` | NC 27 | No limit | N requests per S seconds (auth users) |
| `#[AnonRateLimit(limit: N, period: S)]` | NC 27 | No limit | N requests per S seconds (anonymous) |
| `#[BruteForceProtection(action: 'name')]` | NC 27 | No throttle | Throttle on `$response->throttle()` |
| `#[UseSession]` | NC 26 | Session read-only | Enable session writes |
| `#[CORS]` | NC 27 | No CORS | Add CORS headers |

### Legacy Annotations (pre-NC 27)

| Annotation | Equivalent Attribute |
|------------|---------------------|
| `@NoAdminRequired` | `#[NoAdminRequired]` |
| `@NoCSRFRequired` | `#[NoCSRFRequired]` |
| `@PublicPage` | `#[PublicPage]` |
| `@CORS` | `#[CORS]` |
| `@UseSession` | `#[UseSession]` |

### Common Security Combinations

| Use Case | Attributes |
|----------|-----------|
| Admin-only page | (none -- this is the default) |
| Authenticated user page | `#[NoAdminRequired]` |
| Public read-only page | `#[PublicPage]`, `#[NoCSRFRequired]` |
| Authenticated API | `#[NoAdminRequired]`, `#[NoCSRFRequired]` |
| Public API | `#[PublicPage]`, `#[NoCSRFRequired]` |
| CORS-enabled API | `#[NoAdminRequired]`, `#[NoCSRFRequired]`, `#[CORS]` |

---

## URL Generation

### IURLGenerator Methods

| Method | Returns | Example |
|--------|---------|---------|
| `linkToRoute(string $route, array $params)` | `string` | Internal route URL |
| `linkToOCSRoute(string $route, array $params)` | `string` | OCS route URL |
| `getAbsoluteURL(string $url)` | `string` | Full URL with domain |
| `imagePath(string $appName, string $image)` | `string` | Path to app image |
| `linkTo(string $appName, string $file)` | `string` | Path to app file |

### Route Name Format

Format: `{appid}.{controller_name}.{method_name}`

- Hashes (`#`) in route definitions become dots (`.`) in route names
- Underscores in controller names are preserved
- App ID is case-sensitive

```php
// Route: ['name' => 'author_api#do_something', ...]
// Route name: myapp.author_api.do_something
$url = $urlGenerator->linkToRoute('myapp.author_api.do_something', ['id' => 3]);
```
