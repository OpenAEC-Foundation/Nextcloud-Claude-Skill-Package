# Security Anti-Patterns

## Controller Security

### AP-SEC-001: Assuming Default Is Public

**WRONG** -- Forgetting attributes and assuming the endpoint works for all users:
```php
class NoteController extends Controller {
    // No attributes -- developer thinks this is a regular endpoint
    public function listNotes(): JSONResponse {
        return new JSONResponse($this->service->findAll());
    }
}
```

**WHY IT FAILS**: The default security posture is admin-only, authenticated, 2FA-required, CSRF-validated. Non-admin users get HTTP 403. This is the most common security-related bug in Nextcloud app development.

**CORRECT**:
```php
#[NoAdminRequired]
public function listNotes(): JSONResponse {
    return new JSONResponse($this->service->findAll());
}
```

---

### AP-SEC-002: PublicPage + NoCSRFRequired on State-Changing Endpoints

**WRONG** -- Creating a writable public endpoint without authentication:
```php
#[PublicPage]
#[NoCSRFRequired]
public function deleteItem(int $id): JSONResponse {
    $this->service->delete($id);
    return new JSONResponse(['status' => 'deleted']);
}
```

**WHY IT FAILS**: Any website can trigger this request via a hidden form or JavaScript fetch. Without CSRF protection AND without authentication, there is no way to verify the request is intentional. This is a textbook CSRF vulnerability.

**CORRECT** -- Require authentication OR keep CSRF protection:
```php
// Option A: Public but CSRF-protected (for browser forms)
#[PublicPage]
public function deleteItem(int $id): JSONResponse {
    $this->service->delete($id);
    return new JSONResponse(['status' => 'deleted']);
}

// Option B: No CSRF but authenticated (for API clients)
#[NoAdminRequired]
#[NoCSRFRequired]
public function deleteItem(int $id): JSONResponse {
    $this->service->delete($id);
    return new JSONResponse(['status' => 'deleted']);
}
```

---

### AP-SEC-003: Throttling Successful Attempts

**WRONG** -- Calling throttle() on every response:
```php
#[BruteForceProtection(action: 'login')]
public function login(string $user, string $pass): JSONResponse {
    $response = new JSONResponse();
    $result = $this->auth->check($user, $pass);
    $response->setData($result);
    $response->throttle(['action' => 'login']); // Always throttles
    return $response;
}
```

**WHY IT FAILS**: Throttling increases response delay exponentially. Calling it on success penalizes legitimate users with growing delays after every successful login.

**CORRECT**:
```php
#[BruteForceProtection(action: 'login')]
public function login(string $user, string $pass): JSONResponse {
    $response = new JSONResponse();
    if (!$this->auth->check($user, $pass)) {
        $response->setStatus(401);
        $response->throttle(['action' => 'login']); // Only on failure
        return $response;
    }
    $response->setData(['status' => 'ok']);
    return $response;
}
```

---

## Middleware

### AP-SEC-004: Forgetting to Return Response in afterController

**WRONG** -- Not returning the response object:
```php
class MyMiddleware extends Middleware {
    public function afterController($controller, $methodName, Response $response): Response {
        // Add a header but forget to return
        $response->addHeader('X-Custom', 'value');
        // Missing: return $response;
    }
}
```

**WHY IT FAILS**: The middleware chain passes the response from one middleware to the next. If `afterController()` does not return the response, `null` propagates through the chain and the client receives an empty or broken response. PHP will emit a type error.

**CORRECT**:
```php
public function afterController($controller, $methodName, Response $response): Response {
    $response->addHeader('X-Custom', 'value');
    return $response; // ALWAYS return the response
}
```

---

### AP-SEC-005: Registering Middleware in boot() Instead of register()

**WRONG**:
```php
public function boot(IBootContext $context): void {
    // Too late -- controllers may already be executing
    $context->getAppContainer()->registerMiddleware(MyMiddleware::class);
}
```

**WHY IT FAILS**: The `boot()` method runs after all apps have registered. If a request targets your app's controller before `boot()` completes the middleware setup, the middleware will not be in the chain. ALWAYS use `register()` for middleware.

**CORRECT**:
```php
public function register(IRegistrationContext $context): void {
    $context->registerMiddleware(MyMiddleware::class);
}
```

---

## Content Security Policy

### AP-SEC-006: Using Wildcard CSP Domains

**WRONG** -- Opening CSP to all domains:
```php
$csp = new ContentSecurityPolicy();
$csp->addAllowedScriptDomain('*');
$csp->addAllowedConnectDomain('*');
$csp->allowInlineScript(true);
$csp->allowEvalScript(true);
```

**WHY IT FAILS**: This completely defeats the purpose of CSP. Any domain can inject scripts, any script can use `eval()`, and inline scripts are allowed. This provides zero XSS protection.

**CORRECT** -- Allow only what you need:
```php
$csp = new ContentSecurityPolicy();
$csp->addAllowedScriptDomain('https://specific-cdn.example.com');
$csp->addAllowedConnectDomain('https://api.example.com');
// Leave allowInlineScript and allowEvalScript at their defaults (false)
```

---

### AP-SEC-007: Enabling allowEvalScript Without Justification

**WRONG**:
```php
$csp = new ContentSecurityPolicy();
$csp->allowEvalScript(true); // "Just to make it work"
```

**WHY IT FAILS**: `eval()` is the primary vector for code injection attacks. Enabling it means any attacker-controlled string can become executable JavaScript. Modern frameworks (Vue.js, React) do NOT require `eval()` in production builds.

**CORRECT**: Fix the root cause. If a library requires `eval()`, consider replacing it or using a CSP nonce-based approach with `useStrictDynamic(true)`.

---

## Authentication

### AP-SEC-008: Storing User Passwords in Client Applications

**WRONG** -- Asking for and storing the user's password directly:
```
username: john
password: MySecretPass123!  <-- stored in config file
```

**WHY IT FAILS**: If the client is compromised, the attacker has the user's actual password, which may be reused across services. App passwords are scoped, revocable, and do not expose the master password.

**CORRECT**: ALWAYS use Login Flow v2 to obtain an app password. Store only the `loginName` and `appPassword` returned by the flow.

---

### AP-SEC-009: NoCSRFRequired on Browser Form Endpoints

**WRONG** -- Disabling CSRF on a form submission handler:
```php
#[NoAdminRequired]
#[NoCSRFRequired]  // Dangerous for browser forms
public function saveSettings(string $theme, string $language): JSONResponse {
    $this->settingsService->save($theme, $language);
    return new JSONResponse(['status' => 'saved']);
}
```

**WHY IT FAILS**: If the endpoint is called from a browser form or AJAX request with session cookies, any external website can forge the request. `#[NoCSRFRequired]` should ONLY be used on endpoints that authenticate via bearer tokens or basic auth (not session cookies).

**CORRECT**:
```php
#[NoAdminRequired]
// Keep CSRF protection for browser-based endpoints
public function saveSettings(string $theme, string $language): JSONResponse {
    $this->settingsService->save($theme, $language);
    return new JSONResponse(['status' => 'saved']);
}
```

---

### AP-SEC-010: Ignoring Login Flow v2 Token Expiry

**WRONG** -- Polling indefinitely without timeout:
```python
while True:
    response = requests.post(poll_endpoint, data={"token": token})
    if response.status_code == 200:
        break
    time.sleep(1)  # Polls forever
```

**WHY IT FAILS**: Login Flow v2 tokens expire after 20 minutes. Polling after expiry wastes resources and confuses users who may have abandoned the flow.

**CORRECT**:
```python
start = time.time()
while time.time() - start < 1200:  # 20-minute timeout
    response = requests.post(poll_endpoint, data={"token": token})
    if response.status_code == 200:
        break
    time.sleep(2)  # Reasonable interval with backoff
else:
    raise TimeoutError("Login flow expired")
```
