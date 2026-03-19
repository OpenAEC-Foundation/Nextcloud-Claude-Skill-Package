# API Error Anti-Patterns

## OCS API Anti-Patterns

### AP-1: Using v1 Endpoints Without Checking the Envelope

**NEVER** use OCS v1 endpoints and rely on the HTTP status code for success/failure detection.

```php
// WRONG: HTTP status is ALWAYS 200 on v1
$response = $client->get('/ocs/v1.php/cloud/users/john');
if ($response->getStatusCode() === 200) {
    // This ALWAYS executes, even if user "john" does not exist
    $user = json_decode($response->getBody(), true)['ocs']['data'];
}

// CORRECT: Use v2 where HTTP status reflects the actual result
$response = $client->get('/ocs/v2.php/cloud/users/john');
if ($response->getStatusCode() === 200) {
    $user = json_decode($response->getBody(), true)['ocs']['data'];
}
```

### AP-2: Omitting the OCS-APIRequest Header

**NEVER** make OCS requests without the `OCS-APIRequest: true` header. The request will be rejected with a CSRF error (status 997) regardless of valid authentication.

```bash
# WRONG
curl -u "$USER:$APP_PASSWORD" 'https://cloud.example.com/ocs/v2.php/cloud/capabilities'

# CORRECT
curl -u "$USER:$APP_PASSWORD" -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v2.php/cloud/capabilities'
```

### AP-3: Hardcoding Server Capabilities

**NEVER** assume which features or apps are available on a Nextcloud instance. Different installations have different apps enabled.

```php
// WRONG: Assuming files_sharing is available
$response = $client->get('/ocs/v2.php/apps/files_sharing/api/v1/shares');

// CORRECT: Check capabilities first
$caps = $client->get('/ocs/v2.php/cloud/capabilities?format=json');
$data = json_decode($caps->getBody(), true)['ocs']['data'];
if (isset($data['capabilities']['files_sharing'])) {
    $response = $client->get('/ocs/v2.php/apps/files_sharing/api/v1/shares');
}
```

### AP-4: Parsing XML When JSON Is Available

**NEVER** parse OCS XML responses when JSON format is available. XML parsing adds complexity and error surface.

```bash
# WRONG: Default XML response requires XML parser
curl -u "$USER:$APP_PASSWORD" -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v2.php/cloud/capabilities'

# CORRECT: Request JSON format
curl -u "$USER:$APP_PASSWORD" -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v2.php/cloud/capabilities?format=json'

# ALSO CORRECT: Use Accept header
curl -u "$USER:$APP_PASSWORD" \
  -H 'OCS-APIRequest: true' \
  -H 'Accept: application/json' \
  'https://cloud.example.com/ocs/v2.php/cloud/capabilities'
```

---

## WebDAV Anti-Patterns

### AP-5: Missing Username in DAV Path

**NEVER** omit the username from WebDAV file paths. Nextcloud DAV endpoints require the username as part of the URL structure.

```bash
# WRONG: No username
curl -u "$USER:$APP_PASSWORD" -X PROPFIND \
  'https://cloud.example.com/remote.php/dav/files/Documents/'

# CORRECT: Username in path
curl -u "$USER:$APP_PASSWORD" -X PROPFIND \
  'https://cloud.example.com/remote.php/dav/files/admin/Documents/'
```

### AP-6: Missing Destination Header on MOVE/COPY

**NEVER** send MOVE or COPY requests without the `Destination` header. The request will fail with 400 Bad Request.

```bash
# WRONG: No Destination header
curl -u "$USER:$APP_PASSWORD" -X MOVE \
  'https://cloud.example.com/remote.php/dav/files/admin/old.txt'

# CORRECT: Full absolute URL in Destination
curl -u "$USER:$APP_PASSWORD" -X MOVE \
  -H 'Destination: https://cloud.example.com/remote.php/dav/files/admin/new.txt' \
  'https://cloud.example.com/remote.php/dav/files/admin/old.txt'
```

### AP-7: Using Depth: infinity on Large Directories

**NEVER** use `Depth: infinity` in PROPFIND requests on directories with many files. This can cause server timeouts, memory exhaustion, or be rejected by the server entirely.

```bash
# WRONG: May timeout or be rejected
curl -u "$USER:$APP_PASSWORD" -X PROPFIND \
  -H 'Depth: infinity' \
  'https://cloud.example.com/remote.php/dav/files/admin/'

# CORRECT: Use Depth: 1 and paginate or recurse manually
curl -u "$USER:$APP_PASSWORD" -X PROPFIND \
  -H 'Depth: 1' \
  'https://cloud.example.com/remote.php/dav/files/admin/'
```

### AP-8: Assuming MKCOL Creates Parent Directories

**NEVER** assume MKCOL will create intermediate directories. WebDAV requires parent directories to exist before creating a child.

```bash
# WRONG: Fails with 409 if /a/ or /a/b/ do not exist
curl -u "$USER:$APP_PASSWORD" -X MKCOL \
  'https://cloud.example.com/remote.php/dav/files/admin/a/b/c'

# CORRECT: Create parents first
curl -u "$USER:$APP_PASSWORD" -X MKCOL '.../admin/a'
curl -u "$USER:$APP_PASSWORD" -X MKCOL '.../admin/a/b'
curl -u "$USER:$APP_PASSWORD" -X MKCOL '.../admin/a/b/c'
```

### AP-9: Ignoring ETag for Concurrent Edits

**NEVER** update files without checking the ETag when concurrent access is possible. This leads to silent data loss.

```bash
# Step 1: Get current ETag
curl -u "$USER:$APP_PASSWORD" -X PROPFIND -H 'Depth: 0' \
  'https://cloud.example.com/remote.php/dav/files/admin/document.txt' \
  -d '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:getetag/></d:prop></d:propfind>'

# Step 2: Upload with If-Match to prevent overwriting concurrent changes
curl -u "$USER:$APP_PASSWORD" -X PUT \
  -H 'If-Match: "etag-value-from-step-1"' \
  --upload-file updated.txt \
  'https://cloud.example.com/remote.php/dav/files/admin/document.txt'
# Returns 412 Precondition Failed if file was modified since step 1
```

---

## Authentication Anti-Patterns

### AP-10: Using User Passwords Instead of App Passwords

**NEVER** use the user's actual login password for API authentication in client applications. App passwords are purpose-built for API access, survive password changes, and can be individually revoked.

```bash
# WRONG: User's login password -- breaks with 2FA, not revocable individually
curl -u "$USER:MyLoginPassword123" -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v2.php/cloud/capabilities'

# CORRECT: App password from Login Flow v2
curl -u "$USER:$APP_PASSWORD" \
  -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v2.php/cloud/capabilities'
```

### AP-11: Flooding the Login Flow v2 Poll Endpoint

**NEVER** poll the Login Flow v2 endpoint without rate limiting. Aggressive polling wastes server resources and may trigger brute force protection.

```php
// WRONG: Polling every 100ms
while (true) {
    usleep(100000);
    $response = $client->post($pollUrl, ['body' => ['token' => $token]]);
}

// CORRECT: Poll every 5-10 seconds with a 20-minute timeout
$maxWait = 1200;  // 20 minutes in seconds
$elapsed = 0;
$interval = 10;

while ($elapsed < $maxWait) {
    sleep($interval);
    $elapsed += $interval;

    try {
        $response = $client->post($pollUrl, ['body' => ['token' => $token]]);
        if ($response->getStatusCode() === 200) {
            return json_decode($response->getBody(), true);
        }
    } catch (\Exception $e) {
        if ($e->getCode() !== 404) throw $e;
    }
}
throw new \RuntimeException('Login Flow v2 timed out');
```

### AP-12: Storing App Passwords Insecurely

**NEVER** store app passwords in plaintext configuration files, environment variables visible in process listings, or version-controlled files.

**ALWAYS** use the operating system's credential storage (keychain, credential manager) or encrypted configuration.

---

## Controller Anti-Patterns

### AP-13: Returning JSONResponse from OCSController

**NEVER** return `JSONResponse` from an `OCSController` method. This bypasses the OCS response envelope, breaking clients that expect the standard `{"ocs": {"meta": {...}, "data": {...}}}` format.

```php
// WRONG: Bypasses OCS envelope
class MyApiController extends OCSController {
    public function getData(): JSONResponse {
        return new JSONResponse($data);
    }
}

// CORRECT: DataResponse goes through OCS responder
class MyApiController extends OCSController {
    public function getData(): DataResponse {
        return new DataResponse($data);
    }
}
```

### AP-14: Missing Security Attributes on Controller Methods

**NEVER** assume controller methods are accessible to regular users. The default security posture is admin-only, authenticated, 2FA required, CSRF validated.

```php
// WRONG: Only admin users can call this (no attributes = admin-only)
public function listItems(): DataResponse {
    return new DataResponse($this->service->findAll());
}

// CORRECT: Explicitly allow non-admin authenticated users
#[NoAdminRequired]
public function listItems(): DataResponse {
    return new DataResponse($this->service->findAll());
}
```

### AP-15: Using Controller for Cross-Origin API Endpoints

**NEVER** use `Controller` or `OCSController` for endpoints that must serve cross-origin JavaScript clients. Only `ApiController` provides CORS headers.

```php
// WRONG: No CORS headers
class ExternalApi extends Controller { }

// CORRECT: CORS-enabled
class ExternalApi extends ApiController {
    public function __construct(string $appName, IRequest $request) {
        parent::__construct($appName, $request, 'GET, POST', 'Authorization, Content-Type', 86400);
    }
}
```

### AP-16: Combining PublicPage + NoCSRFRequired on State-Changing Endpoints

**NEVER** apply both `#[PublicPage]` and `#[NoCSRFRequired]` to endpoints that modify data. This creates a completely unprotected endpoint vulnerable to CSRF attacks.

```php
// WRONG: Unprotected state-changing endpoint
#[PublicPage]
#[NoCSRFRequired]
public function deleteItem(int $id): DataResponse {
    $this->service->delete($id);
    return new DataResponse([]);
}

// CORRECT: Require authentication for state-changing operations
#[NoAdminRequired]
public function deleteItem(int $id): DataResponse {
    $this->service->delete($id);
    return new DataResponse([]);
}
```

### AP-17: Calling throttle() on Success

**NEVER** call `$response->throttle()` when the operation succeeds. Brute force protection must only trigger on failures.

```php
// WRONG: Throttles all requests including successful ones
#[BruteForceProtection(action: 'verify')]
public function verify(string $token): DataResponse {
    $result = $this->service->verify($token);
    $response = new DataResponse($result);
    $response->throttle();  // WRONG -- throttles success too
    return $response;
}

// CORRECT: Only throttle on failure
#[BruteForceProtection(action: 'verify')]
public function verify(string $token): DataResponse {
    $result = $this->service->verify($token);
    $response = new DataResponse($result);
    if (!$result['valid']) {
        $response->throttle(['action' => 'verify']);
    }
    return $response;
}
```
