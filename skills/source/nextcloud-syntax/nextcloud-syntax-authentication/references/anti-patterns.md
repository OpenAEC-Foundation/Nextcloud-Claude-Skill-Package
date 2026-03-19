# Authentication Anti-Patterns

## AP-1: Storing User Passwords in Client Applications

**NEVER** store the user's actual password in a client application.

```php
// WRONG -- storing user password
$config->setAppValue('myapp', 'password', $userPassword);
```

```php
// CORRECT -- use Login Flow v2 to obtain an app password
// Then store only the app password
$config->setAppValue('myapp', 'app_password', $appPassword);
```

**Why**: User passwords grant full account access and cannot be scoped or revoked independently. App passwords can be revoked per-device without affecting the user's main credentials.

---

## AP-2: Unprotected State-Changing Public Endpoints

**NEVER** combine `#[PublicPage]` + `#[NoCSRFRequired]` on endpoints that modify data without additional authentication.

```php
// WRONG -- completely unprotected state change
#[PublicPage]
#[NoCSRFRequired]
public function deleteItem(int $id): JSONResponse {
    $this->service->delete($id);
    return new JSONResponse(['status' => 'deleted']);
}
```

```php
// CORRECT -- require authentication or add brute force protection
#[NoAdminRequired]
public function deleteItem(int $id): JSONResponse {
    $this->service->delete($id, $this->userId);
    return new JSONResponse(['status' => 'deleted']);
}

// OR for public endpoints that MUST exist: add rate limiting + token validation
#[PublicPage]
#[NoCSRFRequired]
#[BruteForceProtection(action: 'api_token')]
#[AnonRateLimit(limit: 5, period: 60)]
public function publicAction(string $apiToken): JSONResponse {
    if (!$this->tokenService->validate($apiToken)) {
        $response = new JSONResponse([], Http::STATUS_UNAUTHORIZED);
        $response->throttle(['action' => 'api_token']);
        return $response;
    }
    // ... perform action
}
```

**Why**: Without any protection, attackers can trigger state changes via CSRF attacks or direct requests.

---

## AP-3: Calling throttle() on Success

**NEVER** call `$response->throttle()` on successful authentication.

```php
// WRONG -- throttling on success penalizes legitimate users
#[BruteForceProtection(action: 'login')]
public function login(string $user, string $pass): JSONResponse {
    $response = new JSONResponse();
    if ($this->auth->check($user, $pass)) {
        $response->setData(['status' => 'ok']);
        $response->throttle(['action' => 'login']); // BUG: throttles success
    } else {
        $response->setStatus(Http::STATUS_UNAUTHORIZED);
        $response->throttle(['action' => 'login']);
    }
    return $response;
}
```

```php
// CORRECT -- throttle only on failure
#[BruteForceProtection(action: 'login')]
public function login(string $user, string $pass): JSONResponse {
    $response = new JSONResponse();
    if ($this->auth->check($user, $pass)) {
        $response->setData(['status' => 'ok']);
        // No throttle on success
    } else {
        $response->setStatus(Http::STATUS_UNAUTHORIZED);
        $response->throttle(['action' => 'login']);
    }
    return $response;
}
```

**Why**: Throttling on success causes exponential delays for legitimate users, effectively creating a denial-of-service.

---

## AP-4: Missing Action Key in throttle()

**NEVER** call `throttle()` without matching the `action` parameter to the `#[BruteForceProtection]` attribute.

```php
// WRONG -- action mismatch, throttling will not work
#[BruteForceProtection(action: 'token_check')]
public function check(string $token): JSONResponse {
    $response = new JSONResponse();
    if (!$this->validate($token)) {
        $response->throttle(); // Missing action key
        return $response;
    }
    return $response;
}
```

```php
// CORRECT -- action key matches attribute
#[BruteForceProtection(action: 'token_check')]
public function check(string $token): JSONResponse {
    $response = new JSONResponse();
    if (!$this->validate($token)) {
        $response->throttle(['action' => 'token_check']);
        return $response;
    }
    return $response;
}
```

**Why**: Without the matching action key, the brute force protection middleware cannot associate the throttle with the correct protection scope.

---

## AP-5: Aggressive Login Flow v2 Polling

**NEVER** poll the Login Flow v2 endpoint without delay or with sub-second intervals.

```php
// WRONG -- polling as fast as possible
while (true) {
    $result = $client->post($endpoint, ['body' => ['token' => $token]]);
    if ($result->getStatusCode() === 200) break;
    // No delay -- hammers the server
}
```

```php
// CORRECT -- poll with reasonable interval and timeout
$startTime = time();
$maxWait = 1200; // 20 minutes
while ((time() - $startTime) < $maxWait) {
    try {
        $result = $client->post($endpoint, ['body' => ['token' => $token]]);
        return json_decode($result->getBody(), true);
    } catch (\Exception $e) {
        if ($e->getCode() === 404) {
            sleep(2); // 2-second interval
            continue;
        }
        throw $e;
    }
}
throw new \RuntimeException('Login Flow v2 timeout');
```

**Why**: Aggressive polling wastes server resources and may trigger rate limiting, causing the flow to fail.

---

## AP-6: Ignoring Login Flow v2 Token Expiry

**NEVER** assume the Login Flow v2 token lives forever.

```php
// WRONG -- no timeout handling
public function waitForLogin(string $endpoint, string $token): array {
    while (true) { // Infinite loop
        $result = $this->poll($endpoint, $token);
        if ($result !== null) return $result;
        sleep(2);
    }
}
```

```php
// CORRECT -- enforce 20-minute timeout
public function waitForLogin(string $endpoint, string $token): ?array {
    $deadline = time() + 1200; // 20 minutes
    while (time() < $deadline) {
        $result = $this->poll($endpoint, $token);
        if ($result !== null) return $result;
        sleep(2);
    }
    return null; // Token expired
}
```

**Why**: Tokens expire after 20 minutes. Polling beyond that wastes resources and confuses users.

---

## AP-7: Removing CSRF on Browser-Facing Endpoints

**NEVER** add `#[NoCSRFRequired]` to endpoints called by browser forms or AJAX from the Nextcloud frontend.

```php
// WRONG -- browser form endpoint without CSRF
#[NoAdminRequired]
#[NoCSRFRequired] // Dangerous for browser-based calls
public function updateProfile(string $name, string $email): JSONResponse {
    $this->service->updateProfile($this->userId, $name, $email);
    return new JSONResponse(['status' => 'ok']);
}
```

```php
// CORRECT -- let default CSRF protection handle browser requests
#[NoAdminRequired]
public function updateProfile(string $name, string $email): JSONResponse {
    $this->service->updateProfile($this->userId, $name, $email);
    return new JSONResponse(['status' => 'ok']);
}
```

**Why**: Browser requests are vulnerable to CSRF attacks. The `requesttoken` mechanism protects against this automatically.

---

## AP-8: Missing Rate Limiting on Public Endpoints

**NEVER** expose public endpoints without rate limiting.

```php
// WRONG -- public endpoint with no rate limiting
#[PublicPage]
#[NoCSRFRequired]
public function search(string $query): JSONResponse {
    return new JSONResponse($this->service->search($query));
}
```

```php
// CORRECT -- add rate limiting
#[PublicPage]
#[NoCSRFRequired]
#[AnonRateLimit(limit: 10, period: 60)]
public function search(string $query): JSONResponse {
    return new JSONResponse($this->service->search($query));
}
```

**Why**: Public endpoints without rate limiting are trivially abused for denial-of-service or data scraping.

---

## AP-9: Assuming Default Security is Public

**NEVER** create controller methods without security attributes and assume they are accessible to regular users.

```php
// WRONG -- developer assumes this is accessible to all users
public function getData(): JSONResponse {
    return new JSONResponse($this->service->getData());
}
// Result: Only admins can access (default security posture)
```

```php
// CORRECT -- explicitly declare access level
#[NoAdminRequired]
public function getData(): JSONResponse {
    return new JSONResponse($this->service->getData());
}
```

**Why**: Nextcloud's default security posture is admin-only, authenticated, 2FA required, CSRF validated. Without attributes, regular users receive HTTP 403.

---

## AP-10: Omitting OCS-APIRequest Header

**NEVER** call OCS endpoints without the `OCS-APIRequest: true` header.

```bash
# WRONG -- missing required header
curl -u user:apppassword \
  "https://cloud.example.com/ocs/v2.php/apps/myapp/api/v1/data"
# Result: Request rejected
```

```bash
# CORRECT -- include required header
curl -u user:apppassword \
  -H "OCS-APIRequest: true" \
  "https://cloud.example.com/ocs/v2.php/apps/myapp/api/v1/data"
```

**Why**: The `OCS-APIRequest` header serves as CSRF protection for OCS endpoints. Without it, Nextcloud rejects the request to prevent cross-site request forgery.
