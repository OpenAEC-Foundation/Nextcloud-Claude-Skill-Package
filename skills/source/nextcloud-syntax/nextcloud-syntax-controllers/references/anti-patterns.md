# Controller Anti-Patterns Reference

## Routing Anti-Patterns

### AP-01: Missing routes.php Entry

**WRONG** -- Controller method exists but has no route:
```php
class NoteController extends Controller {
    public function archive(int $id): JSONResponse {
        return new JSONResponse($this->service->archive($id));
    }
}
// appinfo/routes.php: NO entry for archive
```

**RIGHT** -- ALWAYS define a route for every controller method:
```php
// appinfo/routes.php
'routes' => [
    ['name' => 'note#archive', 'url' => '/notes/{id}/archive', 'verb' => 'POST'],
]
```

### AP-02: Using Controller for OCS Routes

**WRONG** -- Standard Controller in the `ocs` routes array:
```php
class ApiController extends Controller {  // Wrong base class
    public function getData(): DataResponse {
        return new DataResponse(['items' => []]);
    }
}
```
```php
'ocs' => [
    ['name' => 'api#getData', 'url' => '/api/v1/data', 'verb' => 'GET'],
]
```
Result: The OCS response envelope (meta + data wrapping) will NOT be applied.

**RIGHT** -- ALWAYS use OCSController for `ocs` routes:
```php
class ApiController extends OCSController {  // Correct base class
    public function getData(): DataResponse {
        return new DataResponse(['items' => []]);
    }
}
```

### AP-03: Wrong Route Name Format

**WRONG** -- Using dots or PascalCase in route names:
```php
'routes' => [
    ['name' => 'PageController#index', 'url' => '/', 'verb' => 'GET'],     // Wrong: PascalCase
    ['name' => 'page.index', 'url' => '/', 'verb' => 'GET'],               // Wrong: dot separator
]
```

**RIGHT** -- ALWAYS use `snake_case#camelCase` format:
```php
'routes' => [
    ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
    ['name' => 'author_api#getData', 'url' => '/api/data', 'verb' => 'GET'],
]
```

### AP-04: Missing Path Regex for Slash-Containing Parameters

**WRONG** -- File path parameter without regex:
```php
['name' => 'file#get', 'url' => '/files/{path}', 'verb' => 'GET']
// Request: GET /files/documents/report.pdf
// Result: 404 — {path} only matches "documents", not "documents/report.pdf"
```

**RIGHT** -- ALWAYS add `requirements` for path parameters that may contain slashes:
```php
['name' => 'file#get', 'url' => '/files/{path}', 'verb' => 'GET',
 'requirements' => ['path' => '.+']]
```

---

## Security Anti-Patterns

### AP-05: Assuming Default is Public

**WRONG** -- No security attributes, expecting public access:
```php
// Developer thinks this is accessible by all users
public function index(): JSONResponse {
    return new JSONResponse($this->service->findAll());
}
// Result: Only admins can access this endpoint
```

**RIGHT** -- ALWAYS explicitly set security attributes:
```php
#[NoAdminRequired]  // For authenticated non-admin users
public function index(): JSONResponse {
    return new JSONResponse($this->service->findAll());
}
```

### AP-06: Public State-Changing Endpoint Without Protection

**WRONG** -- Public write endpoint with no authentication:
```php
#[PublicPage]
#[NoCSRFRequired]
public function createItem(string $title): JSONResponse {
    // Anyone can create items — no authentication, no CSRF, no rate limiting
    return new JSONResponse($this->service->create($title));
}
```

**RIGHT** -- ALWAYS add rate limiting and/or authentication on public write endpoints:
```php
#[PublicPage]
#[NoCSRFRequired]
#[AnonRateLimit(limit: 5, period: 60)]
#[BruteForceProtection(action: 'create_item')]
public function createItem(string $title, string $token): JSONResponse {
    if (!$this->tokenService->isValid($token)) {
        $response = new JSONResponse([], Http::STATUS_FORBIDDEN);
        $response->throttle(['action' => 'create_item']);
        return $response;
    }
    return new JSONResponse($this->service->create($title));
}
```

### AP-07: Throttling on Success

**WRONG** -- Calling throttle() regardless of outcome:
```php
#[BruteForceProtection(action: 'login')]
public function login(string $user, string $pass): JSONResponse {
    $response = new JSONResponse();
    $response->throttle();  // WRONG: Always throttles, even on success
    if ($this->auth->verify($user, $pass)) {
        $response->setData(['status' => 'ok']);
    }
    return $response;
}
```

**RIGHT** -- ALWAYS call throttle() only on failure:
```php
#[BruteForceProtection(action: 'login')]
public function login(string $user, string $pass): JSONResponse {
    $response = new JSONResponse();
    if (!$this->auth->verify($user, $pass)) {
        $response->setStatus(Http::STATUS_FORBIDDEN);
        $response->throttle(['action' => 'login']);  // Only on failure
        return $response;
    }
    $response->setData(['status' => 'ok']);
    return $response;
}
```

### AP-08: NoCSRFRequired on Browser Form Endpoints

**WRONG** -- Disabling CSRF on a form submission endpoint:
```php
#[NoAdminRequired]
#[NoCSRFRequired]  // WRONG: form submissions need CSRF protection
public function saveSettings(string $key, string $value): JSONResponse {
    $this->config->setUserValue($this->userId, $this->appName, $key, $value);
    return new JSONResponse(['status' => 'ok']);
}
```

**RIGHT** -- ALWAYS keep CSRF protection for browser form endpoints:
```php
#[NoAdminRequired]
// No #[NoCSRFRequired] — CSRF token is validated from the form
public function saveSettings(string $key, string $value): JSONResponse {
    $this->config->setUserValue($this->userId, $this->appName, $key, $value);
    return new JSONResponse(['status' => 'ok']);
}
```

Only use `#[NoCSRFRequired]` for API endpoints accessed by external clients that send the `OCS-APIRequest: true` header.

---

## Response Anti-Patterns

### AP-09: Using JSONResponse in OCSController

**WRONG** -- JSONResponse in an OCS controller:
```php
class ItemApiController extends OCSController {
    public function index(): JSONResponse {  // Wrong response type
        return new JSONResponse($this->service->findAll());
    }
}
```
Result: The OCS envelope is NOT applied. Clients expecting `ocs.data` will break.

**RIGHT** -- ALWAYS use DataResponse with OCSController:
```php
class ItemApiController extends OCSController {
    public function index(): DataResponse {  // Correct for OCS
        return new DataResponse($this->service->findAll());
    }
}
```

### AP-10: Missing Error Status Codes

**WRONG** -- Returning errors with 200 status:
```php
public function show(int $id): JSONResponse {
    $item = $this->service->find($id);
    if ($item === null) {
        return new JSONResponse(['error' => 'Not found']);  // Still returns 200
    }
    return new JSONResponse($item);
}
```

**RIGHT** -- ALWAYS set appropriate HTTP status codes:
```php
public function show(int $id): JSONResponse {
    $item = $this->service->find($id);
    if ($item === null) {
        return new JSONResponse(['error' => 'Not found'], Http::STATUS_NOT_FOUND);
    }
    return new JSONResponse($item);
}
```

### AP-11: Swallowing Exceptions Silently

**WRONG** -- Catching all exceptions without proper response:
```php
public function create(string $title): JSONResponse {
    try {
        $item = $this->service->create($title);
        return new JSONResponse($item);
    } catch (\Exception $e) {
        return new JSONResponse([]);  // Client has no idea what went wrong
    }
}
```

**RIGHT** -- ALWAYS return meaningful error responses:
```php
public function create(string $title): JSONResponse {
    try {
        $item = $this->service->create($title);
        return new JSONResponse($item, Http::STATUS_CREATED);
    } catch (ValidationException $e) {
        return new JSONResponse(
            ['message' => $e->getMessage()],
            Http::STATUS_BAD_REQUEST,
        );
    } catch (NotFoundException $e) {
        return new JSONResponse(
            ['message' => $e->getMessage()],
            Http::STATUS_NOT_FOUND,
        );
    }
}
```

---

## Dependency Injection Anti-Patterns

### AP-12: Static Service Access

**WRONG** -- Using static container access:
```php
class NoteController extends Controller {
    public function index(): JSONResponse {
        $service = \OCP\Server::get(NoteService::class);  // WRONG: breaks testability
        return new JSONResponse($service->findAll());
    }
}
```

**RIGHT** -- ALWAYS use constructor injection:
```php
class NoteController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private NoteService $service,
    ) {
        parent::__construct($appName, $request);
    }

    public function index(): JSONResponse {
        return new JSONResponse($this->service->findAll());
    }
}
```

### AP-13: Missing Namespace in info.xml

**WRONG** -- No namespace element in `appinfo/info.xml`:
```xml
<info>
    <id>myapp</id>
    <!-- Missing: <namespace>MyApp</namespace> -->
</info>
```
Result: Auto-wiring silently fails. Controllers cannot be resolved from routes.

**RIGHT** -- ALWAYS include the namespace:
```xml
<info>
    <id>myapp</id>
    <namespace>MyApp</namespace>
</info>
```

---

## Attribute-Based Routing Anti-Patterns

### AP-14: Mixing Route Definitions

**WRONG** -- Same route defined in both routes.php and as attribute:
```php
// appinfo/routes.php
'routes' => [
    ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
]

// Controller
#[FrontpageRoute(verb: 'GET', url: '/')]
public function index() { }
```
Result: Duplicate route registration, unpredictable behavior.

**RIGHT** -- Use ONE method consistently. Either routes.php OR attributes, not both:
```php
// Option A: routes.php only (works on NC 28+)
// Option B: Attributes only (requires NC 29+)

// If supporting NC 28, use routes.php
// If NC 29+ only, prefer attributes for co-location
```

### AP-15: FrontpageRoute on OCSController

**WRONG** -- Using FrontpageRoute with OCSController:
```php
class ApiController extends OCSController {
    #[FrontpageRoute(verb: 'GET', url: '/api/data')]  // Wrong attribute
    public function getData(): DataResponse { }
}
```

**RIGHT** -- ALWAYS use ApiRoute with OCSController:
```php
class ApiController extends OCSController {
    #[ApiRoute(verb: 'GET', url: '/api/v1/data')]  // Correct attribute
    public function getData(): DataResponse { }
}
```

---

## Summary Table

| ID | Anti-Pattern | Rule |
|----|-------------|------|
| AP-01 | Missing route entry | ALWAYS define routes for all controller methods |
| AP-02 | Controller for OCS routes | ALWAYS use OCSController for `ocs` array |
| AP-03 | Wrong route name format | ALWAYS use `snake_case#camelCase` |
| AP-04 | No regex for path params | ALWAYS add `requirements` for slash-containing params |
| AP-05 | Assuming default is public | ALWAYS set explicit security attributes |
| AP-06 | Unprotected public writes | ALWAYS add rate limiting on public write endpoints |
| AP-07 | Throttling on success | NEVER call throttle() on success |
| AP-08 | NoCSRFRequired on forms | NEVER disable CSRF for browser form endpoints |
| AP-09 | JSONResponse in OCSController | ALWAYS use DataResponse with OCSController |
| AP-10 | Missing error status codes | ALWAYS set HTTP status codes on errors |
| AP-11 | Swallowing exceptions | ALWAYS return meaningful error responses |
| AP-12 | Static service access | ALWAYS use constructor injection |
| AP-13 | Missing namespace in info.xml | ALWAYS include `<namespace>` element |
| AP-14 | Mixing route definitions | NEVER mix routes.php and attribute routing |
| AP-15 | FrontpageRoute on OCSController | ALWAYS use ApiRoute with OCSController |
