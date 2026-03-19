# Controller Examples Reference

## Controller Patterns

### Full Page Controller with Service Layer

```php
<?php
namespace OCA\MyApp\Controller;

use OCA\MyApp\Service\NoteService;
use OCA\MyApp\Service\NotFoundException;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\IRequest;

class NoteController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private NoteService $service,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        return new TemplateResponse($this->appName, 'main');
    }

    #[NoAdminRequired]
    public function list(): JSONResponse {
        return new JSONResponse($this->service->findAll($this->userId));
    }

    #[NoAdminRequired]
    public function show(int $id): JSONResponse {
        try {
            return new JSONResponse($this->service->find($id, $this->userId));
        } catch (NotFoundException $e) {
            return new JSONResponse([], Http::STATUS_NOT_FOUND);
        }
    }

    #[NoAdminRequired]
    public function create(string $title, string $content = ''): JSONResponse {
        return new JSONResponse(
            $this->service->create($title, $content, $this->userId),
            Http::STATUS_CREATED,
        );
    }

    #[NoAdminRequired]
    public function update(int $id, string $title, string $content): JSONResponse {
        try {
            return new JSONResponse(
                $this->service->update($id, $title, $content, $this->userId)
            );
        } catch (NotFoundException $e) {
            return new JSONResponse([], Http::STATUS_NOT_FOUND);
        }
    }

    #[NoAdminRequired]
    public function destroy(int $id): JSONResponse {
        try {
            $this->service->delete($id, $this->userId);
            return new JSONResponse([], Http::STATUS_NO_CONTENT);
        } catch (NotFoundException $e) {
            return new JSONResponse([], Http::STATUS_NOT_FOUND);
        }
    }
}
```

### OCS API Controller with Rate Limiting

```php
<?php
namespace OCA\MyApp\Controller;

use OCA\MyApp\Service\ShareService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;

class ShareApiController extends OCSController {
    public function __construct(
        string $appName,
        IRequest $request,
        private ShareService $service,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function getShares(): DataResponse {
        return new DataResponse($this->service->findAllForUser($this->userId));
    }

    #[NoAdminRequired]
    #[UserRateLimit(limit: 10, period: 60)]
    public function createShare(string $path, int $shareType, string $shareWith = ''): DataResponse {
        $share = $this->service->create($path, $shareType, $shareWith, $this->userId);
        return new DataResponse($share, Http::STATUS_CREATED);
    }

    #[NoAdminRequired]
    public function deleteShare(int $id): DataResponse {
        $this->service->delete($id, $this->userId);
        return new DataResponse([], Http::STATUS_NO_CONTENT);
    }
}
```

### Public Controller with Brute Force Protection

```php
<?php
namespace OCA\MyApp\Controller;

use OCA\MyApp\Service\TokenService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\IRequest;

class PublicController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private TokenService $tokenService,
    ) {
        parent::__construct($appName, $request);
    }

    #[PublicPage]
    #[NoCSRFRequired]
    #[BruteForceProtection(action: 'access_token')]
    public function access(string $token): TemplateResponse {
        $response = new TemplateResponse($this->appName, 'public', [], TemplateResponse::RENDER_AS_PUBLIC);

        if (!$this->tokenService->isValid($token)) {
            $response->setStatus(Http::STATUS_NOT_FOUND);
            $response->throttle(['action' => 'access_token']);
        }

        return $response;
    }

    #[PublicPage]
    #[NoCSRFRequired]
    #[BruteForceProtection(action: 'access_password')]
    public function verify(string $token, string $password): JSONResponse {
        $response = new JSONResponse();

        if (!$this->tokenService->verifyPassword($token, $password)) {
            $response->setStatus(Http::STATUS_FORBIDDEN);
            $response->throttle(['action' => 'access_password']);
            return $response;
        }

        $response->setData(['status' => 'ok']);
        return $response;
    }
}
```

### CORS-Enabled External API Controller

```php
<?php
namespace OCA\MyApp\Controller;

use OCA\MyApp\Service\DataService;
use OCP\AppFramework\ApiController;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class ExternalApiController extends ApiController {
    public function __construct(
        string $appName,
        IRequest $request,
        private DataService $service,
        private ?string $userId,
    ) {
        parent::__construct(
            $appName,
            $request,
            'GET, POST, PUT, DELETE',       // Allowed methods
            'Authorization, Content-Type',   // Allowed headers
            86400,                           // Max age (seconds)
        );
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    #[CORS]
    public function getData(): JSONResponse {
        return new JSONResponse($this->service->findAll($this->userId));
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    #[CORS]
    public function updateData(int $id, string $value): JSONResponse {
        return new JSONResponse($this->service->update($id, $value, $this->userId));
    }
}
```

---

## Routing Patterns

### Complete routes.php with All Features

```php
<?php
return [
    'routes' => [
        // Basic page routes
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
        ['name' => 'page#settings', 'url' => '/settings', 'verb' => 'GET'],

        // CRUD via Controller (non-OCS)
        ['name' => 'note#list', 'url' => '/notes', 'verb' => 'GET'],
        ['name' => 'note#show', 'url' => '/notes/{id}', 'verb' => 'GET'],
        ['name' => 'note#create', 'url' => '/notes', 'verb' => 'POST'],
        ['name' => 'note#update', 'url' => '/notes/{id}', 'verb' => 'PUT'],
        ['name' => 'note#destroy', 'url' => '/notes/{id}', 'verb' => 'DELETE'],

        // Path parameter with regex (match slashes)
        [
            'name' => 'file#download',
            'url' => '/download/{path}',
            'verb' => 'GET',
            'requirements' => ['path' => '.+'],
        ],

        // Default parameter values
        [
            'name' => 'search#query',
            'url' => '/search',
            'verb' => 'GET',
            'defaults' => ['page' => 1, 'limit' => 25],
        ],

        // Public access route
        ['name' => 'public#access', 'url' => '/s/{token}', 'verb' => 'GET'],
    ],

    'ocs' => [
        // OCS API v1 routes
        ['name' => 'share_api#getShares', 'url' => '/api/v1/shares', 'verb' => 'GET'],
        ['name' => 'share_api#createShare', 'url' => '/api/v1/shares', 'verb' => 'POST'],
        ['name' => 'share_api#deleteShare', 'url' => '/api/v1/shares/{id}', 'verb' => 'DELETE'],

        // External CORS-enabled API
        ['name' => 'external_api#getData', 'url' => '/api/v1/external/data', 'verb' => 'GET'],
    ],

    'resources' => [
        // Auto-generates: index, show, create, update, destroy
        'author' => ['url' => '/authors'],
        'category' => ['url' => '/categories'],
    ],
];
```

### Attribute-Based Routing (NC 29+) -- Full Example

```php
<?php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\Attribute\FrontpageRoute;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\IRequest;

class PageController extends Controller {
    public function __construct(string $appName, IRequest $request) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    #[FrontpageRoute(verb: 'GET', url: '/')]
    public function index(): TemplateResponse {
        return new TemplateResponse($this->appName, 'main');
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    #[FrontpageRoute(verb: 'GET', url: '/settings')]
    public function settings(): TemplateResponse {
        return new TemplateResponse($this->appName, 'settings');
    }
}
```

```php
<?php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Http\Attribute\ApiRoute;
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
    #[ApiRoute(verb: 'GET', url: '/api/v1/items')]
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll($this->userId));
    }

    #[NoAdminRequired]
    #[ApiRoute(verb: 'GET', url: '/api/v1/items/{id}', requirements: ['id' => '\d+'])]
    public function show(int $id): DataResponse {
        return new DataResponse($this->service->find($id, $this->userId));
    }

    #[NoAdminRequired]
    #[ApiRoute(verb: 'POST', url: '/api/v1/items')]
    public function create(string $title, string $content = ''): DataResponse {
        return new DataResponse($this->service->create($title, $content, $this->userId));
    }

    #[NoAdminRequired]
    #[ApiRoute(verb: 'PUT', url: '/api/v1/items/{id}')]
    public function update(int $id, string $title, string $content): DataResponse {
        return new DataResponse($this->service->update($id, $title, $content, $this->userId));
    }

    #[NoAdminRequired]
    #[ApiRoute(verb: 'DELETE', url: '/api/v1/items/{id}')]
    public function destroy(int $id): DataResponse {
        $this->service->delete($id, $this->userId);
        return new DataResponse([], Http::STATUS_NO_CONTENT);
    }
}
```

---

## Parameter Extraction Examples

### URL Path + Query + Defaults

```php
// Route: ['name' => 'search#find', 'url' => '/search/{category}', 'verb' => 'GET',
//         'defaults' => ['page' => 1]]
// Request: GET /search/books?q=nextcloud&limit=10

#[NoAdminRequired]
public function find(string $category, string $q, int $limit = 25, int $page = 1): JSONResponse {
    // $category = "books" (from URL path)
    // $q = "nextcloud" (from query string)
    // $limit = 10 (from query string, overrides default)
    // $page = 1 (from route default, not in query)
    return new JSONResponse($this->service->search($category, $q, $limit, $page));
}
```

### JSON Body Parameters

```php
// Route: ['name' => 'item#create', 'url' => '/items', 'verb' => 'POST']
// Request: POST /items
// Content-Type: application/json
// Body: {"title": "My Item", "tags": ["php", "nextcloud"], "metadata": {"priority": 1}}

#[NoAdminRequired]
public function create(string $title, array $tags, array $metadata): JSONResponse {
    // $title = "My Item"
    // $tags = ["php", "nextcloud"]
    // $metadata = ["priority" => 1]
    return new JSONResponse($this->service->create($title, $tags, $metadata));
}
```

### File Upload Handling

```php
// Route: ['name' => 'upload#handle', 'url' => '/upload', 'verb' => 'POST']

#[NoAdminRequired]
public function handle(): JSONResponse {
    $file = $this->request->getUploadedFile('document');

    if ($file === null || $file['error'] !== UPLOAD_ERR_OK) {
        return new JSONResponse(['error' => 'Upload failed'], Http::STATUS_BAD_REQUEST);
    }

    $result = $this->service->processUpload(
        $file['tmp_name'],
        $file['name'],
        $file['type'],
        $file['size'],
    );

    return new JSONResponse($result, Http::STATUS_CREATED);
}
```

---

## Response Pattern Examples

### Content Security Policy Customization

```php
use OCP\AppFramework\Http\ContentSecurityPolicy;
use OCP\AppFramework\Http\TemplateResponse;

#[NoAdminRequired]
#[NoCSRFRequired]
public function index(): TemplateResponse {
    $response = new TemplateResponse($this->appName, 'main');

    $csp = new ContentSecurityPolicy();
    $csp->addAllowedImageDomain('https://images.example.com');
    $csp->addAllowedConnectDomain('https://api.example.com');
    $csp->addAllowedMediaDomain('*');
    $response->setContentSecurityPolicy($csp);

    return $response;
}
```

### Streaming File Download

```php
use OCP\AppFramework\Http\StreamResponse;

#[NoAdminRequired]
#[NoCSRFRequired]
public function download(string $path): StreamResponse {
    $file = $this->storage->getFile($path);

    $response = new StreamResponse($file->getLocalPath());
    $response->addHeader('Content-Type', $file->getMimeType());
    $response->addHeader('Content-Disposition', 'attachment; filename="' . $file->getName() . '"');

    return $response;
}
```

### Redirect After Action

```php
use OCP\AppFramework\Http\RedirectResponse;
use OCP\IURLGenerator;

#[NoAdminRequired]
public function processForm(string $name, string $email): RedirectResponse {
    $this->service->saveContact($name, $email);

    $url = $this->urlGenerator->linkToRoute('myapp.page.index');
    return new RedirectResponse($url);
}
```
