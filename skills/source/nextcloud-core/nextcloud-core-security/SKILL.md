---
name: nextcloud-core-security
description: "Guides Nextcloud security model including controller security defaults, middleware chain architecture, Content Security Policy configuration, security attributes overview, and encryption interfaces. Activates when securing Nextcloud apps, configuring CSP, understanding the middleware chain, or implementing security patterns."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-core-security

## Quick Reference

### Controller Security Defaults

Every controller method enforces ALL of the following unless explicitly overridden with attributes:

| Default | Effect | Override Attribute |
|---------|--------|--------------------|
| Admin-only | Non-admin users receive HTTP 403 | `#[NoAdminRequired]` |
| Authenticated | Anonymous users redirected to login | `#[PublicPage]` |
| 2FA required | Users without completed 2FA are blocked | `#[NoTwoFactorRequired]` |
| CSRF validated | Request must include CSRF token or `OCS-APIRequest: true` header | `#[NoCSRFRequired]` |

**ALWAYS** start from the default secure posture and relax only what is needed. The default is the most restrictive configuration possible.

### Security Attributes (NC 27+)

| Attribute | Effect | Use Case |
|-----------|--------|----------|
| `#[NoAdminRequired]` | Allow non-admin authenticated users | Regular user-facing endpoints |
| `#[PublicPage]` | No login required | Public APIs, share pages |
| `#[NoCSRFRequired]` | Skip CSRF token validation | API endpoints using bearer/basic auth |
| `#[NoTwoFactorRequired]` | Bypass 2FA requirement | 2FA setup pages themselves |
| `#[UserRateLimit(limit: N, period: S)]` | Rate limit for logged-in users | Sensitive operations |
| `#[AnonRateLimit(limit: N, period: S)]` | Rate limit for anonymous users | Public endpoints |
| `#[BruteForceProtection(action: 'name')]` | Throttle repeated failures | Login, token validation |

**Legacy annotations** (pre-NC 27): `@NoAdminRequired`, `@NoCSRFRequired`, `@PublicPage`. ALWAYS use PHP 8 attributes for NC 28+ apps.

### Critical Warnings

**NEVER** assume a controller method without attributes is public -- the default is admin-only, authenticated, 2FA-required, CSRF-validated. Forgetting `#[NoAdminRequired]` means regular users get HTTP 403.

**NEVER** combine `#[PublicPage]` + `#[NoCSRFRequired]` on state-changing endpoints without additional authentication (bearer token, API key, or `OCS-APIRequest: true` header). This creates a CSRF vulnerability.

**NEVER** use `#[NoCSRFRequired]` on browser-facing form endpoints -- CSRF protection exists to prevent cross-site attacks on session-authenticated users.

**NEVER** call `$response->throttle()` on successful attempts -- only on failures. Throttling success slows legitimate users.

**NEVER** disable brute force protection on authentication endpoints.

**NEVER** forget to return the `$response` from `afterController()` middleware -- the response will be silently lost.

---

## Middleware Chain Architecture

Middleware provides cross-cutting security concerns. The chain follows Django's pattern with four hooks executed in a specific order:

### Hook Execution Order

```
Request arrives
    |
    v
[Middleware 1] beforeController()    (forward order: 1 -> 2 -> 3)
[Middleware 2] beforeController()
[Middleware 3] beforeController()
    |
    v
Controller method executes
    |
    v  (if exception thrown, skip to afterException)
[Middleware 3] afterController()     (reverse order: 3 -> 2 -> 1)
[Middleware 2] afterController()
[Middleware 1] afterController()
    |
    v
[Middleware 3] beforeOutput()        (reverse order: 3 -> 2 -> 1)
[Middleware 2] beforeOutput()
[Middleware 1] beforeOutput()
    |
    v
Response sent
```

### Exception Handling Flow

```
Exception thrown during controller execution
    |
    v
[Middleware 3] afterException()      (reverse order: 3 -> 2 -> 1)
    |-- if handled (returns Response): continue to afterController chain
    |-- if not handled: propagate to next middleware
[Middleware 2] afterException()
[Middleware 1] afterException()
```

### Hook Signatures

| Hook | Signature | Direction | Purpose |
|------|-----------|-----------|---------|
| `beforeController` | `($controller, $methodName)` | Forward | Pre-execution checks, auth |
| `afterException` | `($controller, $methodName, $exception): Response` | Reverse | Exception recovery |
| `afterController` | `($controller, $methodName, $response): Response` | Reverse | Response modification |
| `beforeOutput` | `($controller, $methodName, $output): string` | Reverse | Output manipulation |

### Middleware Registration

```php
// App-level middleware (runs only for your app's controllers)
public function register(IRegistrationContext $context): void {
    $context->registerMiddleware(MySecurityMiddleware::class);
}

// Global middleware (NC 26+, runs across ALL apps)
$context->registerMiddleware(MonitoringMiddleware::class, true);
```

**ALWAYS** register middleware in `Application::register()`, not in `boot()`. Middleware must be available before any controller executes.

---

## Content Security Policy

### Per-Response CSP

```php
use OCP\AppFramework\Http\ContentSecurityPolicy;

$response = new TemplateResponse('myapp', 'main');
$csp = new ContentSecurityPolicy();
$csp->addAllowedImageDomain('https://images.example.com');
$csp->addAllowedConnectDomain('https://api.example.com');
$response->setContentSecurityPolicy($csp);
```

### Global CSP via Event Listener

Register a listener for `AddContentSecurityPolicyEvent` to modify CSP across all responses from your app.

### CSP Method Overview

| Method | Directive | Default |
|--------|-----------|---------|
| `allowInlineScript(bool)` | script-src 'unsafe-inline' | false |
| `allowInlineStyle(bool)` | style-src 'unsafe-inline' | false |
| `allowEvalScript(bool)` | script-src 'unsafe-eval' | false |
| `useStrictDynamic(bool)` | script-src 'strict-dynamic' | true |
| `addAllowedScriptDomain(string)` | script-src | -- |
| `addAllowedStyleDomain(string)` | style-src | -- |
| `addAllowedFontDomain(string)` | font-src | -- |
| `addAllowedImageDomain(string)` | img-src | -- |
| `addAllowedConnectDomain(string)` | connect-src | -- |
| `addAllowedMediaDomain(string)` | media-src | -- |
| `addAllowedObjectDomain(string)` | object-src | -- |
| `addAllowedFrameDomain(string)` | frame-src | -- |
| `addAllowedChildSrcDomain(string)` | child-src | -- |

**ALWAYS** use the most restrictive CSP possible. Only add domains that your app actually needs.

**NEVER** use `allowInlineScript(true)` or `allowEvalScript(true)` unless absolutely required -- these weaken XSS protection significantly.

---

## Security Events Catalog

| Event | Since | Purpose |
|-------|-------|---------|
| `BeforeUserLoggedInEvent` | NC 18 | Pre-login hook for custom validation |
| `PostLoginEvent` | NC 18 | Post-login hook for auditing |
| `LoginFailedEvent` | NC 19 | Failed login (known user) |
| `AnyLoginFailedEvent` | NC 26 | Any login failure (broader scope) |
| `UserFirstTimeLoggedInEvent` | NC 28 | First-ever login for onboarding |
| `TokenInvalidatedEvent` | NC 32 | Auth token revoked |
| `TwoFactorProviderChallengeFailed` | NC 28 | 2FA challenge failed |
| `TwoFactorProviderChallengePassed` | NC 28 | 2FA challenge succeeded |

Register listeners via `IRegistrationContext::registerEventListener()` in `Application::register()`.

---

## Authentication Mechanisms

| Method | Use Case | Details |
|--------|----------|---------|
| Session + CSRF | Browser-based access | Default for web UI |
| Basic Auth (app password) | Desktop/mobile clients | Via Login Flow v2 |
| OIDC Bearer Token | SSO integration | `Authorization: Bearer ID_TOKEN` |
| `OCS-APIRequest: true` header | API clients | Alternative to CSRF token |

**ALWAYS** use Login Flow v2 to obtain app passwords for external clients. NEVER store user passwords directly.

---

## Decision Trees

### Choosing Security Attributes

```
Is this endpoint admin-only?
  YES -> Use no attributes (default is admin-only)
  NO  -> Add #[NoAdminRequired]
         |
         Does it need to work without login?
           YES -> Add #[PublicPage]
           NO  -> Stop here
         |
         Is it called by an API client (not browser)?
           YES -> Add #[NoCSRFRequired]
           NO  -> Keep CSRF protection
         |
         Is it a 2FA setup page?
           YES -> Add #[NoTwoFactorRequired]
           NO  -> Keep 2FA requirement
```

### Choosing Rate Limiting

```
Is the endpoint sensitive (auth, data modification)?
  NO  -> No rate limiting needed
  YES -> Is it accessible to anonymous users?
           YES -> Add #[AnonRateLimit(limit: N, period: S)]
           NO  -> (skip)
         Is it accessible to authenticated users?
           YES -> Add #[UserRateLimit(limit: N, period: S)]
           NO  -> (skip)
         Does it involve credentials/tokens?
           YES -> Add #[BruteForceProtection(action: 'name')]
                  Call $response->throttle() on FAILURE only
           NO  -> Rate limiting is sufficient
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- Security attributes, middleware methods, CSP methods
- [references/examples.md](references/examples.md) -- Security patterns, CSP configuration, middleware implementation
- [references/anti-patterns.md](references/anti-patterns.md) -- Security mistakes and how to avoid them

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/middleware.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/controllers.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/security.html
