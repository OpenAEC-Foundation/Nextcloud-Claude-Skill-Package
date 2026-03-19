# Security Examples

## Controller Security Patterns

### Admin-Only Endpoint (Default)

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class AdminController extends Controller {
    public function __construct(string $appName, IRequest $request) {
        parent::__construct($appName, $request);
    }

    // No attributes needed -- default is admin-only, authenticated, CSRF-validated, 2FA-required
    public function resetSystem(): JSONResponse {
        return new JSONResponse(['status' => 'reset']);
    }
}
```

### Regular User Endpoint

```php
use OCP\AppFramework\Http\Attribute\NoAdminRequired;

class NoteController extends Controller {
    #[NoAdminRequired]
    public function listNotes(): JSONResponse {
        // Accessible to any authenticated user (not just admins)
        return new JSONResponse($this->noteService->findAll());
    }
}
```

### Public API Endpoint

```php
use OCP\AppFramework\Http\Attribute\PublicPage;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;

class PublicApiController extends Controller {
    #[PublicPage]
    #[NoCSRFRequired]
    public function getStatus(): JSONResponse {
        // No login required, no CSRF token needed
        // Suitable for external API clients using basic auth or bearer tokens
        return new JSONResponse(['status' => 'online', 'version' => '1.0']);
    }
}
```

### Rate-Limited Endpoint

```php
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\UserRateLimit;
use OCP\AppFramework\Http\Attribute\AnonRateLimit;
use OCP\AppFramework\Http\Attribute\PublicPage;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;

class ExportController extends Controller {
    #[NoAdminRequired]
    #[UserRateLimit(limit: 5, period: 100)]
    public function exportData(): JSONResponse {
        // Authenticated users: max 5 calls per 100 seconds
        return new JSONResponse($this->exportService->generate());
    }

    #[PublicPage]
    #[NoCSRFRequired]
    #[AnonRateLimit(limit: 1, period: 100)]
    #[UserRateLimit(limit: 10, period: 100)]
    public function publicExport(): JSONResponse {
        // Anonymous: 1 call per 100s, Authenticated: 10 calls per 100s
        return new JSONResponse($this->exportService->generatePublic());
    }
}
```

### Brute Force Protected Authentication

```php
use OCP\AppFramework\Http\Attribute\PublicPage;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\Attribute\BruteForceProtection;

class TokenController extends Controller {
    #[PublicPage]
    #[NoCSRFRequired]
    #[BruteForceProtection(action: 'token')]
    #[BruteForceProtection(action: 'password')]
    public function validateShare(string $token, string $password): JSONResponse {
        $response = new JSONResponse();

        $share = $this->shareManager->getByToken($token);
        if ($share === null) {
            // Token invalid -- throttle the 'token' action
            $response->setStatus(404);
            $response->throttle(['action' => 'token']);
            return $response;
        }

        if (!$share->verifyPassword($password)) {
            // Password wrong -- throttle the 'password' action
            $response->setStatus(403);
            $response->throttle(['action' => 'password']);
            return $response;
        }

        // Success -- NEVER call throttle() here
        $response->setData(['share' => $share->getData()]);
        return $response;
    }
}
```

---

## Custom Middleware Implementation

### Security Logging Middleware

```php
namespace OCA\MyApp\Middleware;

use OCP\AppFramework\Middleware;
use OCP\AppFramework\Http\Response;
use Psr\Log\LoggerInterface;

class SecurityAuditMiddleware extends Middleware {
    public function __construct(
        private LoggerInterface $logger,
        private string $userId,
    ) {}

    public function beforeController($controller, $methodName): void {
        $this->logger->info('Access attempt', [
            'controller' => get_class($controller),
            'method' => $methodName,
            'user' => $this->userId,
        ]);
    }

    public function afterException($controller, $methodName, \Exception $exception): Response {
        $this->logger->error('Security exception in controller', [
            'controller' => get_class($controller),
            'method' => $methodName,
            'exception' => $exception->getMessage(),
        ]);
        throw $exception; // Re-throw to let other middleware handle it
    }

    public function afterController($controller, $methodName, Response $response): Response {
        // ALWAYS return the response -- forgetting this silently drops the response
        return $response;
    }
}
```

### Annotation-Aware Middleware

```php
namespace OCA\MyApp\Middleware;

use OCP\AppFramework\Middleware;
use OCP\AppFramework\Http\Response;
use OCP\AppFramework\Utility\IControllerMethodReflector;

class CustomHeaderMiddleware extends Middleware {
    public function __construct(
        private IControllerMethodReflector $reflector,
    ) {}

    public function afterController($controller, $methodName, Response $response): Response {
        // Check if the controller method has a custom annotation
        if ($this->reflector->hasAnnotation('AddSecurityHeaders')) {
            $response->addHeader('X-Content-Type-Options', 'nosniff');
            $response->addHeader('X-Frame-Options', 'DENY');
            $response->addHeader('Referrer-Policy', 'no-referrer');
        }
        return $response;
    }
}
```

### Middleware Registration

```php
namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Middleware\SecurityAuditMiddleware;
use OCA\MyApp\Middleware\CustomHeaderMiddleware;
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
        // App-level middleware (only this app's controllers)
        $context->registerMiddleware(SecurityAuditMiddleware::class);
        $context->registerMiddleware(CustomHeaderMiddleware::class);

        // Global middleware (NC 26+, ALL apps' controllers)
        // $context->registerMiddleware(GlobalMonitorMiddleware::class, true);
    }

    public function boot(IBootContext $context): void {
        // Nothing needed for middleware
    }
}
```

---

## Content Security Policy Configuration

### Per-Response CSP

```php
use OCP\AppFramework\Http\ContentSecurityPolicy;
use OCP\AppFramework\Http\TemplateResponse;

class PageController extends Controller {
    #[NoAdminRequired]
    public function index(): TemplateResponse {
        $response = new TemplateResponse('myapp', 'main');

        $csp = new ContentSecurityPolicy();
        // Allow loading images from an external CDN
        $csp->addAllowedImageDomain('https://cdn.example.com');
        // Allow XHR/fetch to your API
        $csp->addAllowedConnectDomain('https://api.example.com');
        // Allow embedding videos from a media server
        $csp->addAllowedMediaDomain('https://media.example.com');

        $response->setContentSecurityPolicy($csp);
        return $response;
    }
}
```

### Global CSP via Event Listener

```php
namespace OCA\MyApp\Listener;

use OCP\AppFramework\Http\ContentSecurityPolicy;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Security\CSP\AddContentSecurityPolicyEvent;

class CSPListener implements IEventListener {
    public function handle(Event $event): void {
        if (!$event instanceof AddContentSecurityPolicyEvent) {
            return;
        }

        $csp = new ContentSecurityPolicy();
        $csp->addAllowedConnectDomain('https://api.example.com');
        $csp->addAllowedImageDomain('https://images.example.com');
        $event->addPolicy($csp);
    }
}
```

Register in `Application::register()`:

```php
$context->registerEventListener(
    AddContentSecurityPolicyEvent::class,
    CSPListener::class
);
```

### Restrictive CSP for Sensitive Pages

```php
$csp = new ContentSecurityPolicy();
// Explicitly disable dangerous options (these are already false by default)
$csp->allowInlineScript(false);
$csp->allowEvalScript(false);
$csp->allowInlineStyle(false);
// Enable strict-dynamic for nonce-based script loading
$csp->useStrictDynamic(true);
$response->setContentSecurityPolicy($csp);
```

---

## Security Event Listeners

### Login Monitoring

```php
namespace OCA\MyApp\Listener;

use OCP\Authentication\Events\LoginFailedEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use Psr\Log\LoggerInterface;

class LoginFailedListener implements IEventListener {
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function handle(Event $event): void {
        if (!$event instanceof LoginFailedEvent) {
            return;
        }

        $this->logger->warning('Failed login attempt', [
            'loginName' => $event->getLoginName(),
        ]);
    }
}
```

### First-Time Login Onboarding (NC 28+)

```php
namespace OCA\MyApp\Listener;

use OCP\Authentication\Events\UserFirstTimeLoggedInEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;

class OnboardingListener implements IEventListener {
    public function handle(Event $event): void {
        if (!$event instanceof UserFirstTimeLoggedInEvent) {
            return;
        }

        $user = $event->getUser();
        // Set up default preferences, create welcome files, etc.
        $this->setupService->initializeUser($user->getUID());
    }
}
```

### Registration of Security Event Listeners

```php
public function register(IRegistrationContext $context): void {
    $context->registerEventListener(
        LoginFailedEvent::class,
        LoginFailedListener::class
    );
    $context->registerEventListener(
        UserFirstTimeLoggedInEvent::class,
        OnboardingListener::class
    );
}
```
