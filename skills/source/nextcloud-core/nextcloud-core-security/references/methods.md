# Security Methods Reference

## Security Attributes

### Controller Security Attributes (NC 27+)

| Attribute | Class | Parameters | Effect |
|-----------|-------|------------|--------|
| `#[NoAdminRequired]` | `OCP\AppFramework\Http\Attribute\NoAdminRequired` | none | Allows non-admin authenticated users |
| `#[PublicPage]` | `OCP\AppFramework\Http\Attribute\PublicPage` | none | Removes authentication requirement |
| `#[NoCSRFRequired]` | `OCP\AppFramework\Http\Attribute\NoCSRFRequired` | none | Skips CSRF token validation |
| `#[NoTwoFactorRequired]` | `OCP\AppFramework\Http\Attribute\NoTwoFactorRequired` | none | Bypasses 2FA completion requirement |

### Rate Limiting Attributes (NC 27+)

| Attribute | Class | Parameters | Effect |
|-----------|-------|------------|--------|
| `#[UserRateLimit(limit: N, period: S)]` | `OCP\AppFramework\Http\Attribute\UserRateLimit` | `limit` (int), `period` (int, seconds) | Limits calls per period for authenticated users |
| `#[AnonRateLimit(limit: N, period: S)]` | `OCP\AppFramework\Http\Attribute\AnonRateLimit` | `limit` (int), `period` (int, seconds) | Limits calls per period for anonymous users |

### Brute Force Protection Attribute (NC 27+)

| Attribute | Class | Parameters | Effect |
|-----------|-------|------------|--------|
| `#[BruteForceProtection(action: 'name')]` | `OCP\AppFramework\Http\Attribute\BruteForceProtection` | `action` (string) | Enables throttling for the named action |

Multiple `#[BruteForceProtection]` attributes can be stacked on the same method with different action names.

### Legacy Annotations (Pre-NC 27)

| Annotation | Equivalent Attribute |
|------------|---------------------|
| `@NoAdminRequired` | `#[NoAdminRequired]` |
| `@NoCSRFRequired` | `#[NoCSRFRequired]` |
| `@PublicPage` | `#[PublicPage]` |
| `@CORS` | (use CORS middleware) |

---

## Middleware Methods

### `OCP\AppFramework\Middleware` (Abstract Base Class)

| Method | Signature | Execution Order | Purpose |
|--------|-----------|-----------------|---------|
| `beforeController` | `(Controller $controller, string $methodName): void` | Forward (1 -> 2 -> 3) | Pre-execution logic, security checks, request validation |
| `afterException` | `(Controller $controller, string $methodName, \Exception $exception): Response` | Reverse (3 -> 2 -> 1) | Exception handling, error response generation |
| `afterController` | `(Controller $controller, string $methodName, Response $response): Response` | Reverse (3 -> 2 -> 1) | Response modification, header injection |
| `beforeOutput` | `(Controller $controller, string $methodName, string $output): string` | Reverse (3 -> 2 -> 1) | Output transformation, content filtering |

### `OCP\AppFramework\Utility\IControllerMethodReflector`

Used in middleware to inspect controller method attributes/annotations:

| Method | Signature | Purpose |
|--------|-----------|---------|
| `hasAnnotation` | `(string $name): bool` | Check if method has a specific annotation |
| `getAnnotationParameter` | `(string $name, string $param): string` | Get annotation parameter value |
| `reflect` | `(object $object, string $method): void` | Parse annotations for given method |

### Middleware Registration Methods

| Context | Method | Signature | Scope |
|---------|--------|-----------|-------|
| `IRegistrationContext` | `registerMiddleware` | `(string $class, bool $global = false): void` | App-level (default) or global |

---

## Content Security Policy Methods

### `OCP\AppFramework\Http\ContentSecurityPolicy`

#### Domain Allow Methods

| Method | CSP Directive | Parameter |
|--------|---------------|-----------|
| `addAllowedScriptDomain(string $domain)` | `script-src` | Full domain or `*` |
| `addAllowedStyleDomain(string $domain)` | `style-src` | Full domain or `*` |
| `addAllowedFontDomain(string $domain)` | `font-src` | Full domain or `*` |
| `addAllowedImageDomain(string $domain)` | `img-src` | Full domain or `*` |
| `addAllowedConnectDomain(string $domain)` | `connect-src` | Full domain or `*` |
| `addAllowedMediaDomain(string $domain)` | `media-src` | Full domain or `*` |
| `addAllowedObjectDomain(string $domain)` | `object-src` | Full domain or `*` |
| `addAllowedFrameDomain(string $domain)` | `frame-src` | Full domain or `*` |
| `addAllowedChildSrcDomain(string $domain)` | `child-src` | Full domain or `*` |

#### Inline/Eval Control Methods

| Method | CSP Directive | Default | Security Impact |
|--------|---------------|---------|-----------------|
| `allowInlineScript(bool $state)` | `script-src 'unsafe-inline'` | `false` | HIGH -- enables XSS vectors |
| `allowInlineStyle(bool $state)` | `style-src 'unsafe-inline'` | `false` | MEDIUM -- enables CSS injection |
| `allowEvalScript(bool $state)` | `script-src 'unsafe-eval'` | `false` | HIGH -- enables code injection |
| `useStrictDynamic(bool $state)` | `script-src 'strict-dynamic'` | `true` | Positive -- restricts to trusted scripts |

#### Response Integration

| Method | Class | Purpose |
|--------|-------|---------|
| `setContentSecurityPolicy(ContentSecurityPolicy $csp)` | `Response` | Apply CSP to a specific response |

---

## Response Security Methods

### `OCP\AppFramework\Http\Response`

| Method | Purpose |
|--------|---------|
| `throttle(array $data = [])` | Trigger brute force throttling on this response |
| `setContentSecurityPolicy(ContentSecurityPolicy $csp)` | Set CSP for this response |
| `addHeader(string $name, string $value)` | Add custom security headers |
| `cacheFor(int $cacheSeconds, bool $isPublic = false)` | Set cache headers (security-relevant for sensitive data) |

### Throttle Data Parameter

The `throttle()` method accepts an associative array. ALWAYS include the `action` key matching the `#[BruteForceProtection(action: '...')]` attribute:

```php
$response->throttle(['action' => 'login']);
```

---

## Security Event Classes

| Event Class | Namespace | Key Properties |
|-------------|-----------|----------------|
| `BeforeUserLoggedInEvent` | `OCP\Authentication\Events` | `getUsername(): string` |
| `PostLoginEvent` | `OCP\Authentication\Events` | `getUser(): IUser`, `isTokenLogin(): bool` |
| `LoginFailedEvent` | `OCP\Authentication\Events` | `getLoginName(): string` |
| `AnyLoginFailedEvent` | `OCP\Authentication\Events` | `getLoginName(): string` |
| `UserFirstTimeLoggedInEvent` | `OCP\Authentication\Events` | `getUser(): IUser` |
| `TokenInvalidatedEvent` | `OCP\Authentication\Token\Events` | `getToken(): IToken` |
| `AddContentSecurityPolicyEvent` | `OCP\Security\CSP` | `addPolicy(ContentSecurityPolicy $csp)` |
