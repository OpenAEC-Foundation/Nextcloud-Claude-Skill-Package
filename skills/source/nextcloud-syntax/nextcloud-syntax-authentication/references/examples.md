# Authentication Examples

## Example 1: Complete Login Flow v2 Client Implementation

```php
namespace OCA\MyApp\Service;

use OCP\Http\Client\IClientService;
use Psr\Log\LoggerInterface;

class LoginFlowService {
    private const POLL_INTERVAL = 2; // seconds
    private const POLL_TIMEOUT = 1200; // 20 minutes in seconds

    public function __construct(
        private IClientService $clientService,
        private LoggerInterface $logger,
    ) {}

    /**
     * Step 1: Initiate Login Flow v2
     */
    public function initiateLogin(string $serverUrl): array {
        $client = $this->clientService->newClient();
        $response = $client->post($serverUrl . '/index.php/login/v2');
        return json_decode($response->getBody(), true);
    }

    /**
     * Steps 3-4: Poll for credentials with timeout
     */
    public function pollForCredentials(string $endpoint, string $token): ?array {
        $client = $this->clientService->newClient();
        $startTime = time();

        while ((time() - $startTime) < self::POLL_TIMEOUT) {
            try {
                $response = $client->post($endpoint, [
                    'body' => ['token' => $token],
                ]);
                // Success — credentials received (returned ONCE)
                return json_decode($response->getBody(), true);
            } catch (\Exception $e) {
                // 404 means user has not yet authenticated
                if ($e->getCode() === 404) {
                    sleep(self::POLL_INTERVAL);
                    continue;
                }
                $this->logger->error('Login Flow v2 poll failed: ' . $e->getMessage());
                return null;
            }
        }

        $this->logger->warning('Login Flow v2 token expired (20 minute timeout)');
        return null;
    }
}
```

## Example 2: CSRF-Protected Controller (Browser Form)

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\JSONResponse;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\IRequest;

class SettingsController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private SettingsService $service,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    /**
     * Render settings page -- CSRF not needed for GET (read-only).
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        return new TemplateResponse($this->appName, 'settings');
    }

    /**
     * Save settings -- CSRF validated automatically (default).
     * The template MUST include the requesttoken hidden field.
     */
    #[NoAdminRequired]
    public function save(string $key, string $value): JSONResponse {
        $this->service->setSetting($this->userId, $key, $value);
        return new JSONResponse(['status' => 'ok']);
    }
}
```

## Example 3: OCS API with App Password Authentication

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\Attribute\UserRateLimit;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;

class ExternalApiController extends OCSController {
    public function __construct(
        string $appName,
        IRequest $request,
        private DataService $service,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    /**
     * External clients call this with:
     *   curl -u "$USER:$APP_PASSWORD" \
     *     -H "OCS-APIRequest: true" \
     *     https://cloud.example.com/ocs/v2.php/apps/myapp/api/v1/data
     *
     * CSRF is handled by OCS-APIRequest header (required for all OCS calls).
     * #[NoCSRFRequired] is safe here because OCSController validates
     * the OCS-APIRequest header as CSRF alternative.
     */
    #[NoAdminRequired]
    #[NoCSRFRequired]
    #[UserRateLimit(limit: 30, period: 60)]
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll($this->userId));
    }
}
```

Client usage:
```bash
# Using app password obtained from Login Flow v2
curl -u "username:yKTVA4zgxjfivy52WqD8kW3M2pKGQr6srmUXMipRdun" \
  -H "OCS-APIRequest: true" \
  -H "Accept: application/json" \
  "https://cloud.example.com/ocs/v2.php/apps/myapp/api/v1/data"
```

## Example 4: Brute Force Protection on Login Endpoint

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\Attribute\BruteForceProtection;
use OCP\AppFramework\Http\Attribute\PublicPage;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\Attribute\AnonRateLimit;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class TokenController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private TokenService $tokenService,
    ) {
        parent::__construct($appName, $request);
    }

    /**
     * Validate an access token. Protected against brute force attacks.
     *
     * Key rules:
     * - throttle() is called ONLY on failure
     * - The 'action' key in throttle() MUST match the BruteForceProtection action
     * - AnonRateLimit provides additional protection layer
     */
    #[PublicPage]
    #[NoCSRFRequired]
    #[BruteForceProtection(action: 'validate_token')]
    #[AnonRateLimit(limit: 5, period: 60)]
    public function validate(string $token): JSONResponse {
        $result = $this->tokenService->validate($token);

        if ($result === null) {
            $response = new JSONResponse(
                ['error' => 'Invalid token'],
                Http::STATUS_UNAUTHORIZED
            );
            // CRITICAL: throttle() on failure ONLY
            $response->throttle(['action' => 'validate_token']);
            return $response;
        }

        // Success path -- NEVER call throttle() here
        return new JSONResponse(['data' => $result]);
    }
}
```

## Example 5: Combined Rate Limiting (User + Anonymous)

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Http\Attribute\AnonRateLimit;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\Attribute\PublicPage;
use OCP\AppFramework\Http\Attribute\UserRateLimit;
use OCP\AppFramework\Http\JSONResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;

class SearchController extends OCSController {
    public function __construct(
        string $appName,
        IRequest $request,
        private SearchService $searchService,
    ) {
        parent::__construct($appName, $request);
    }

    /**
     * Search endpoint with different rate limits for authenticated
     * and anonymous users.
     *
     * Authenticated users: 20 requests per 60 seconds
     * Anonymous users: 5 requests per 60 seconds
     */
    #[PublicPage]
    #[NoCSRFRequired]
    #[UserRateLimit(limit: 20, period: 60)]
    #[AnonRateLimit(limit: 5, period: 60)]
    public function search(string $query, int $limit = 20): DataResponse {
        return new DataResponse($this->searchService->search($query, $limit));
    }
}
```

## Example 6: Security Event Listener Registration

```php
namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Listener\LoginFailedListener;
use OCA\MyApp\Listener\FirstLoginListener;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\Authentication\Events\LoginFailedEvent;
use OCP\User\Events\UserFirstTimeLoggedInEvent;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct(array $urlParams = []) {
        parent::__construct(self::APP_ID, $urlParams);
    }

    public function register(IRegistrationContext $context): void {
        $context->registerEventListener(
            LoginFailedEvent::class,
            LoginFailedListener::class
        );
        $context->registerEventListener(
            UserFirstTimeLoggedInEvent::class,
            FirstLoginListener::class
        );
    }

    public function boot(IBootContext $context): void {}
}
```

```php
namespace OCA\MyApp\Listener;

use OCP\User\Events\UserFirstTimeLoggedInEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;

class FirstLoginListener implements IEventListener {
    public function __construct(
        private OnboardingService $onboarding,
    ) {}

    public function handle(Event $event): void {
        if (!$event instanceof UserFirstTimeLoggedInEvent) {
            return;
        }
        $user = $event->getUser();
        $this->onboarding->setupDefaults($user->getUID());
    }
}
```

## Example 7: Multiple Brute Force Actions on One Endpoint

```php
use OCP\AppFramework\Http\Attribute\BruteForceProtection;
use OCP\AppFramework\Http\Attribute\PublicPage;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;

/**
 * Access a password-protected shared resource.
 * Two independent brute force actions:
 * - 'share_token': throttles invalid token attempts
 * - 'share_password': throttles wrong password attempts
 */
#[PublicPage]
#[NoCSRFRequired]
#[BruteForceProtection(action: 'share_token')]
#[BruteForceProtection(action: 'share_password')]
public function accessShare(string $token, string $password): JSONResponse {
    $response = new JSONResponse();

    // Check token validity
    $share = $this->shareManager->getByToken($token);
    if ($share === null) {
        $response->setStatus(Http::STATUS_NOT_FOUND);
        $response->throttle(['action' => 'share_token']);
        return $response;
    }

    // Check password
    if (!$share->verifyPassword($password)) {
        $response->setStatus(Http::STATUS_FORBIDDEN);
        $response->throttle(['action' => 'share_password']);
        return $response;
    }

    // Success -- no throttle
    $response->setData(['name' => $share->getName(), 'path' => $share->getTarget()]);
    return $response;
}
```
