---
name: nextcloud-syntax-authentication
description: "Guides Nextcloud authentication including Login Flow v2 protocol, app passwords, CSRF token handling, rate limiting with UserRateLimit and AnonRateLimit attributes, brute force protection with throttle(), and OAuth2. Activates when implementing authentication, handling CSRF tokens, configuring rate limiting, or integrating external clients via Login Flow v2."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-syntax-authentication

## Quick Reference

### Authentication Methods

| Method | Use Case | Credentials |
|--------|----------|-------------|
| Login Flow v2 | Desktop/mobile clients | App password (obtained via flow) |
| App passwords | API clients, device-specific access | Username + app password |
| Basic Auth | Simple API calls | Username + password (or app password) |
| Session cookies | Browser-based requests | CSRF token required |
| OAuth2 | Third-party integrations | Bearer token |
| OIDC | Enterprise SSO | `Authorization: Bearer ID_TOKEN` |

### Controller Security Defaults (No Attributes)

| Security Layer | Default State | Override Attribute |
|----------------|---------------|-------------------|
| Admin-only | Enforced | `#[NoAdminRequired]` |
| Authenticated | Required | `#[PublicPage]` |
| 2FA completed | Required | `#[NoTwoFactorRequired]` |
| CSRF validated | Required | `#[NoCSRFRequired]` |

### Security Attributes (NC 27+)

| Attribute | Effect |
|-----------|--------|
| `#[NoAdminRequired]` | Allow non-admin authenticated users |
| `#[PublicPage]` | No login required |
| `#[NoCSRFRequired]` | Skip CSRF token validation |
| `#[NoTwoFactorRequired]` | Bypass 2FA requirement |
| `#[UserRateLimit(limit: N, period: S)]` | N calls per S seconds for logged-in users |
| `#[AnonRateLimit(limit: N, period: S)]` | N calls per S seconds for anonymous users |
| `#[BruteForceProtection(action: 'name')]` | Enable brute force throttling |

### Security-Related Events

| Event | Since | Purpose |
|-------|-------|---------|
| `BeforeUserLoggedInEvent` | v18 | Pre-login hook |
| `PostLoginEvent` | v18 | Post-login hook |
| `LoginFailedEvent` | v19 | Failed login attempt |
| `AnyLoginFailedEvent` | v26 | Any login failure (broader scope) |
| `UserFirstTimeLoggedInEvent` | v28 | First-ever login |
| `TokenInvalidatedEvent` | v32 | Auth token revoked |
| `TwoFactorProviderChallengeFailed` | v28 | 2FA failure |
| `TwoFactorProviderChallengePassed` | v28 | 2FA success |

### Critical Warnings

**NEVER** store user passwords in client applications -- ALWAYS use Login Flow v2 to obtain app passwords.

**NEVER** use `#[PublicPage]` + `#[NoCSRFRequired]` on state-changing endpoints without additional authentication -- this leaves the endpoint completely unprotected.

**NEVER** disable brute force protection on authentication endpoints -- attackers will exploit unthrottled login.

**NEVER** call `$response->throttle()` on success -- ALWAYS call it only on failure conditions.

**NEVER** poll Login Flow v2 without backoff -- ALWAYS use 1-2 second intervals between polls.

**NEVER** ignore the 20-minute token expiry in Login Flow v2 -- ALWAYS implement timeout handling in the client.

**ALWAYS** require the `OCS-APIRequest: true` header on OCS endpoints as CSRF alternative.

**ALWAYS** use `#[BruteForceProtection]` on endpoints that accept credentials or tokens.

**ALWAYS** store app passwords securely on the client -- the password is shown only once.

---

## Decision Trees

### CSRF Protection Decision Tree

```
Is this a browser-based form submission?
├── YES → Use requesttoken field/header
│         (default CSRF protection handles this automatically)
│
└── NO → Is this an API endpoint?
         ├── YES → Is it an OCS endpoint?
         │         ├── YES → Require OCS-APIRequest: true header
         │         │         (OCSController handles this automatically)
         │         └── NO → Use #[NoCSRFRequired] + require
         │                  token-based auth (app password / OAuth2)
         │
         └── NO → Is it a public read-only endpoint?
                  ├── YES → #[PublicPage] + #[NoCSRFRequired] is acceptable
                  └── NO → Keep CSRF protection enabled (default)
```

### Authentication Attribute Decision Tree

```
Who needs access?
├── Admins only → No attributes needed (default)
├── Any logged-in user → #[NoAdminRequired]
├── Anonymous users → #[PublicPage]
│   └── Does it change state?
│       ├── YES → Add authentication via other means
│       │         (API key, app password, rate limiting)
│       └── NO → #[PublicPage] + #[NoCSRFRequired] is safe
└── External API clients → #[NoAdminRequired] + #[NoCSRFRequired]
    └── ALWAYS require Basic Auth with app password
```

### Rate Limiting Decision Tree

```
Is this a sensitive endpoint?
├── YES → Does it accept credentials?
│         ├── YES → #[BruteForceProtection(action: 'name')]
│         │         + throttle() on failure
│         └── NO → Is it resource-intensive?
│                  ├── YES → #[UserRateLimit] + #[AnonRateLimit]
│                  └── NO → No rate limiting needed
└── NO → Is it public?
         ├── YES → Consider #[AnonRateLimit] to prevent abuse
         └── NO → No rate limiting needed
```

---

## Essential Patterns

### Pattern 1: Login Flow v2 (4-Step Protocol)

```
Client                          Nextcloud Server              Browser
  │                                    │                         │
  │ POST /index.php/login/v2           │                         │
  │ ──────────────────────────────────>│                         │
  │                                    │                         │
  │ {poll.token, poll.endpoint, login} │                         │
  │ <──────────────────────────────────│                         │
  │                                    │                         │
  │ Open login URL ───────────────────────────────────────────> │
  │                                    │     User authenticates  │
  │                                    │ <─────────────────────  │
  │                                    │     Grant access         │
  │                                    │ <─────────────────────  │
  │                                    │                         │
  │ POST /login/v2/poll (token=...)    │                         │
  │ ──────────────────────────────────>│                         │
  │                                    │                         │
  │ {server, loginName, appPassword}   │                         │
  │ <──────────────────────────────────│                         │
```

**Step 1: Initiate the flow**
```bash
curl -X POST https://cloud.example.com/index.php/login/v2
```

Response:
```json
{
    "poll": {
        "token": "mQUYQdffOSAMJYtm8pVpkOsVqXt5hglnuSpO5EMbgJ...",
        "endpoint": "https://cloud.example.com/login/v2/poll"
    },
    "login": "https://cloud.example.com/login/v2/flow/[flow-identifier]"
}
```

**Step 2: Open browser** -- Direct the user to the `login` URL. The server handles passwords, 2FA, SSO transparently.

**Step 3: Poll for credentials** (1-2 second intervals, max 20 minutes)
```bash
curl -X POST https://cloud.example.com/login/v2/poll \
  -d "token=mQUYQdffOSAMJYtm8pVpkOsVqXt5hglnuSpO5EMbgJ..."
```

Returns `404` until authentication completes. Credentials returned ONCE per token.

**Step 4: Receive and store credentials**
```json
{
    "server": "https://cloud.example.com",
    "loginName": "username",
    "appPassword": "yKTVA4zgxjfivy52WqD8kW3M2pKGQr6srmUXMipRdun..."
}
```

ALWAYS store `appPassword` securely. ALWAYS use `loginName` + `appPassword` for all subsequent requests.

### Pattern 2: CSRF Token Handling

**Browser-based requests** (default -- no attributes needed):
```php
// CSRF is validated automatically by the SecurityMiddleware
#[NoAdminRequired]
public function updateItem(int $id, string $title): JSONResponse {
    return new JSONResponse($this->service->update($id, $title));
}
```

```html
<!-- Template includes requesttoken automatically -->
<form method="POST" action="...">
    <input type="hidden" name="requesttoken" value="<?php p($_['requesttoken']); ?>">
    ...
</form>
```

**API clients** use the `OCS-APIRequest: true` header as CSRF alternative:
```bash
curl -X PUT https://cloud.example.com/ocs/v2.php/apps/myapp/api/v1/items/5 \
  -u username:app-password \
  -H "OCS-APIRequest: true" \
  -H "Content-Type: application/json" \
  -d '{"title": "Updated"}'
```

### Pattern 3: Rate Limiting

```php
use OCP\AppFramework\Http\Attribute\UserRateLimit;
use OCP\AppFramework\Http\Attribute\AnonRateLimit;

#[NoAdminRequired]
#[UserRateLimit(limit: 5, period: 100)]
#[AnonRateLimit(limit: 1, period: 100)]
public function search(string $query): JSONResponse {
    return new JSONResponse($this->service->search($query));
}
```

- `limit`: Maximum number of requests allowed
- `period`: Time window in seconds
- Exceeding the limit returns HTTP 429 (Too Many Requests)

### Pattern 4: Brute Force Protection

```php
use OCP\AppFramework\Http\Attribute\BruteForceProtection;

#[PublicPage]
#[NoCSRFRequired]
#[BruteForceProtection(action: 'token')]
#[BruteForceProtection(action: 'password')]
public function accessShare(string $token, string $password): JSONResponse {
    $response = new JSONResponse();

    $share = $this->shareManager->getByToken($token);
    if ($share === null) {
        $response->throttle(['action' => 'token']);
        return $response;
    }

    if (!$share->verifyPassword($password)) {
        $response->throttle(['action' => 'password']);
        return $response;
    }

    $response->setData($share->getData());
    return $response;
}
```

Key rules:
- ALWAYS call `$response->throttle()` only on **failure** paths
- ALWAYS pass the `action` key matching the attribute's action name
- Multiple `#[BruteForceProtection]` attributes can protect different actions independently
- Throttling increases delay exponentially with repeated failures from the same IP

### Pattern 5: Public API Endpoint (Fully Open)

```php
#[PublicPage]
#[NoCSRFRequired]
#[AnonRateLimit(limit: 10, period: 60)]
public function getStatus(): JSONResponse {
    return new JSONResponse(['status' => 'online', 'version' => '1.0']);
}
```

ALWAYS add `#[AnonRateLimit]` to public endpoints to prevent abuse.

### Pattern 6: Listening for Authentication Events

```php
namespace OCA\MyApp\Listener;

use OCP\Authentication\Events\LoginFailedEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use Psr\Log\LoggerInterface;

class LoginFailedListener implements IEventListener {
    public function __construct(private LoggerInterface $logger) {}

    public function handle(Event $event): void {
        if (!$event instanceof LoginFailedEvent) {
            return;
        }
        $this->logger->warning('Login failed for user: ' . $event->getUid());
    }
}
```

Register in `Application::register()`:
```php
$context->registerEventListener(LoginFailedEvent::class, LoginFailedListener::class);
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- Login Flow v2 endpoints, security attributes, rate limiting
- [references/examples.md](references/examples.md) -- Login Flow v2, CSRF handling, brute force protection
- [references/anti-patterns.md](references/anti-patterns.md) -- Authentication mistakes

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/controllers.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/LoginFlow/index.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/OCS/ocs-api-overview.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/events.html
