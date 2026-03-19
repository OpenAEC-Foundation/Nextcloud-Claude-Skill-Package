# Authentication Methods Reference

## Login Flow v2 Endpoints

### POST /index.php/login/v2 -- Initiate Flow

**Request**: No body required. No authentication required.

**Response** (HTTP 200):
```json
{
    "poll": {
        "token": "mQUYQdffOSAMJYtm8pVpkOsVqXt5hglnuSpO5EMbgJ...",
        "endpoint": "https://cloud.example.com/login/v2/poll"
    },
    "login": "https://cloud.example.com/login/v2/flow/[flow-identifier]"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `poll.token` | string | Token to use when polling for credentials |
| `poll.endpoint` | string | URL to poll against |
| `login` | string | URL to open in user's browser |

### POST /login/v2/poll -- Poll for Credentials

**Request**: `token` parameter (form data or query string).

**Response when pending** (HTTP 404): Empty body. Continue polling.

**Response when complete** (HTTP 200):
```json
{
    "server": "https://cloud.example.com",
    "loginName": "username",
    "appPassword": "yKTVA4zgxjfivy52WqD8kW3M2pKGQr6srmUXMipRdun..."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `server` | string | Server URL (use for all subsequent API calls) |
| `loginName` | string | Username to use for authentication |
| `appPassword` | string | App-specific password (shown ONCE) |

**Constraints**:
- Token expires after 20 minutes
- Credentials returned exactly ONCE per token
- ALWAYS poll with 1-2 second intervals
- ALWAYS implement timeout handling (20 minutes max)

---

## Security Attributes

### #[NoAdminRequired]

**Namespace**: `OCP\AppFramework\Http\Attribute\NoAdminRequired`

**Effect**: Allows any authenticated user (not just admins) to access the endpoint.

**When to use**: ALWAYS add to endpoints intended for regular users.

```php
use OCP\AppFramework\Http\Attribute\NoAdminRequired;

#[NoAdminRequired]
public function getUserData(): JSONResponse { }
```

### #[PublicPage]

**Namespace**: `OCP\AppFramework\Http\Attribute\PublicPage`

**Effect**: Disables authentication requirement entirely. Anonymous access allowed.

**When to use**: Public APIs, shared resource access, status endpoints.

```php
use OCP\AppFramework\Http\Attribute\PublicPage;

#[PublicPage]
public function getPublicInfo(): JSONResponse { }
```

### #[NoCSRFRequired]

**Namespace**: `OCP\AppFramework\Http\Attribute\NoCSRFRequired`

**Effect**: Disables CSRF token validation for the endpoint.

**When to use**: API endpoints accessed by external clients using token-based auth.

**NEVER use on**: State-changing browser-based endpoints without alternative CSRF protection.

```php
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;

#[NoCSRFRequired]
public function apiEndpoint(): JSONResponse { }
```

### #[NoTwoFactorRequired]

**Namespace**: `OCP\AppFramework\Http\Attribute\NoTwoFactorRequired`

**Effect**: Bypasses the requirement that 2FA must be completed.

**When to use**: Endpoints needed during the 2FA setup/challenge process itself.

```php
use OCP\AppFramework\Http\Attribute\NoTwoFactorRequired;

#[NoTwoFactorRequired]
public function twoFactorSetup(): JSONResponse { }
```

### #[UserRateLimit(limit: N, period: S)]

**Namespace**: `OCP\AppFramework\Http\Attribute\UserRateLimit`

**Effect**: Limits authenticated users to `N` requests per `S` seconds.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Maximum number of requests |
| `period` | int | Time window in seconds |

**Exceeded**: Returns HTTP 429 (Too Many Requests).

```php
use OCP\AppFramework\Http\Attribute\UserRateLimit;

#[UserRateLimit(limit: 5, period: 100)]
public function search(): JSONResponse { }
```

### #[AnonRateLimit(limit: N, period: S)]

**Namespace**: `OCP\AppFramework\Http\Attribute\AnonRateLimit`

**Effect**: Limits anonymous (unauthenticated) users to `N` requests per `S` seconds.

**Parameters**: Same as `#[UserRateLimit]`.

```php
use OCP\AppFramework\Http\Attribute\AnonRateLimit;

#[AnonRateLimit(limit: 1, period: 100)]
public function publicEndpoint(): JSONResponse { }
```

### #[BruteForceProtection(action: 'name')]

**Namespace**: `OCP\AppFramework\Http\Attribute\BruteForceProtection`

**Effect**: Enables exponential delay throttling for the named action when `$response->throttle()` is called.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `action` | string | Identifier for the protected action |

**Key rules**:
- Multiple attributes allowed on the same method (different actions)
- ALWAYS call `$response->throttle(['action' => 'name'])` on failure only
- NEVER call `$response->throttle()` on success paths
- Delay increases exponentially per IP for repeated failures

```php
use OCP\AppFramework\Http\Attribute\BruteForceProtection;

#[BruteForceProtection(action: 'login')]
public function login(): JSONResponse { }
```

---

## CSRF Protection Mechanisms

### requesttoken (Browser Forms)

CSRF token included automatically in Nextcloud templates. Available via:

| Method | Usage |
|--------|-------|
| Hidden form field | `<input type="hidden" name="requesttoken" value="...">` |
| Request header | `requesttoken: <token_value>` |
| PHP template | `<?php p($_['requesttoken']); ?>` |
| JavaScript | `OC.requestToken` (available globally in Nextcloud frontend) |

### OCS-APIRequest Header (API Clients)

Alternative CSRF protection for OCS API calls. Required on ALL OCS requests regardless of CSRF attribute.

```
OCS-APIRequest: true
```

This header confirms the request originates from an intentional API call, not a CSRF-exploited browser request.

---

## App Password Properties

| Property | Value |
|----------|-------|
| Length | 72 characters (random) |
| Scoping | Named based on `USER_AGENT` header during creation |
| Revocation | User can revoke in Settings > Security > Devices & sessions |
| Storage | Hashed server-side; plaintext shown to client ONCE |
| Usage | Standard Basic Auth: `username:appPassword` |
| Creation | Login Flow v2 (automatic) or Settings UI (manual) |

---

## Authentication Events

### LoginFailedEvent (v19+)

**Class**: `OCP\Authentication\Events\LoginFailedEvent`

**Available methods**:
| Method | Return | Description |
|--------|--------|-------------|
| `getUid()` | string | Username that was attempted |

### AnyLoginFailedEvent (v26+)

**Class**: `OCP\Authentication\Events\AnyLoginFailedEvent`

**Available methods**:
| Method | Return | Description |
|--------|--------|-------------|
| `getLoginName()` | string | Login name attempted |

Broader than `LoginFailedEvent` -- fires for any authentication failure regardless of mechanism.

### UserFirstTimeLoggedInEvent (v28+)

**Class**: `OCP\User\Events\UserFirstTimeLoggedInEvent`

**Available methods**:
| Method | Return | Description |
|--------|--------|-------------|
| `getUser()` | IUser | The user who logged in for the first time |

### PostLoginEvent (v18+)

**Class**: `OCP\User\Events\PostLoginEvent`

**Available methods**:
| Method | Return | Description |
|--------|--------|-------------|
| `getUser()` | IUser | The user who logged in |
| `isTokenLogin()` | bool | Whether login used an app token |

### BeforeUserLoggedInEvent (v18+)

**Class**: `OCP\User\Events\BeforeUserLoggedInEvent`

**Available methods**:
| Method | Return | Description |
|--------|--------|-------------|
| `getUsername()` | string | Username being attempted |
