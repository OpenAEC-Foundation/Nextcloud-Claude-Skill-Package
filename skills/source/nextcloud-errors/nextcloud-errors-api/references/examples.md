# API Error Scenarios with Complete Fixes

## Scenario 1: OCS Request Rejected with CSRF Error

### Symptom
```
HTTP/1.1 200 OK
{"ocs":{"meta":{"status":"failure","statuscode":997,"message":"Current user is not logged in"},"data":[]}}
```
Or on v2:
```
HTTP/1.1 500 Internal Server Error
```

### Root Cause
The `OCS-APIRequest: true` header is missing from the request.

### Fix

```bash
# Before (broken)
curl -u admin:app-password \
  'https://cloud.example.com/ocs/v2.php/cloud/users?format=json'

# After (working)
curl -u admin:app-password \
  -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v2.php/cloud/users?format=json'
```

```typescript
// Before (broken) -- raw axios without Nextcloud wrapper
import axios from 'axios';
const resp = await axios.get('/ocs/v2.php/cloud/capabilities');

// After (working) -- @nextcloud/axios adds the header automatically
import axios from '@nextcloud/axios';
const resp = await axios.get('/ocs/v2.php/cloud/capabilities?format=json');

// After (working) -- manual header if not using @nextcloud/axios
import axios from 'axios';
const resp = await axios.get('/ocs/v2.php/cloud/capabilities?format=json', {
    headers: { 'OCS-APIRequest': 'true' },
});
```

---

## Scenario 2: v1 Endpoint Masks Errors Behind HTTP 200

### Symptom
```bash
curl -s -o /dev/null -w "%{http_code}" -u admin:pass \
  -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v1.php/cloud/users/nonexistent'
# Returns: 200
```
HTTP status says 200, but the user does not exist.

### Root Cause
OCS v1 ALWAYS returns HTTP 200. The actual error is in `ocs.meta.statuscode`.

### Fix

**Option A (preferred): Switch to v2.**
```bash
curl -s -w "\nHTTP: %{http_code}" -u admin:pass \
  -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v2.php/cloud/users/nonexistent?format=json'
# Returns HTTP 404 with statuscode 404 in body
```

**Option B: Parse the envelope in v1.**
```php
$response = $client->get($url, [
    'headers' => ['OCS-APIRequest' => 'true'],
    'auth' => [$user, $pass],
]);

$body = json_decode($response->getBody(), true);
$ocsStatus = $body['ocs']['meta']['statuscode'];

if ($ocsStatus !== 100) {  // v1 success = 100, NOT 200
    throw new \RuntimeException(
        'OCS error ' . $ocsStatus . ': ' . $body['ocs']['meta']['message']
    );
}
```

---

## Scenario 3: WebDAV PROPFIND Returns 404

### Symptom
```bash
curl -u admin:pass -X PROPFIND \
  'https://cloud.example.com/remote.php/dav/files/Documents/'
# HTTP 404
```

### Root Cause
The username is missing from the DAV path. Nextcloud DAV requires `/remote.php/dav/files/{username}/path`.

### Fix
```bash
# Before (broken) -- missing username
curl -u admin:pass -X PROPFIND \
  'https://cloud.example.com/remote.php/dav/files/Documents/'

# After (working) -- username in path
curl -u admin:pass -X PROPFIND \
  -H 'Depth: 1' \
  'https://cloud.example.com/remote.php/dav/files/admin/Documents/'
```

---

## Scenario 4: MKCOL Fails with 409 Conflict

### Symptom
```bash
curl -u admin:pass -X MKCOL \
  'https://cloud.example.com/remote.php/dav/files/admin/a/b/c'
# HTTP 409 Conflict
```

### Root Cause
WebDAV MKCOL requires all parent directories to exist. Unlike `mkdir -p`, it does not create intermediate directories.

### Fix

**Option A: Create directories one level at a time.**
```bash
curl -u admin:pass -X MKCOL \
  'https://cloud.example.com/remote.php/dav/files/admin/a'
curl -u admin:pass -X MKCOL \
  'https://cloud.example.com/remote.php/dav/files/admin/a/b'
curl -u admin:pass -X MKCOL \
  'https://cloud.example.com/remote.php/dav/files/admin/a/b/c'
```

**Option B: Use PUT with auto-create header (for file uploads only).**
```bash
curl -u admin:pass -X PUT \
  -H 'X-NC-WebDAV-AutoMkcol: 1' \
  --upload-file localfile.txt \
  'https://cloud.example.com/remote.php/dav/files/admin/a/b/c/file.txt'
```
This auto-creates missing parent directories `/a/b/c/` before uploading the file.

---

## Scenario 5: Controller Returns 403 for Non-Admin Users

### Symptom
Regular (non-admin) user calls an API endpoint and receives HTTP 403 Forbidden.

### Root Cause
Controller methods default to admin-only access. Without `#[NoAdminRequired]`, only admin users can call the method.

### Fix

```php
// Before (broken) -- admin-only by default
class ItemController extends OCSController {
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll());
    }
}

// After (working) -- explicitly allow non-admin users
class ItemController extends OCSController {
    #[NoAdminRequired]
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll());
    }
}
```

---

## Scenario 6: CORS Preflight Fails for External JavaScript Client

### Symptom
Browser console:
```
Access to XMLHttpRequest at 'https://cloud.example.com/...' from origin 'https://myapp.example.com'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present.
```

### Root Cause
Using `Controller` or `OCSController` instead of `ApiController`. Only `ApiController` sets CORS headers.

### Fix

```php
// Before (broken) -- no CORS support
class DataController extends Controller {
    public function getData(): JSONResponse {
        return new JSONResponse($this->service->findAll());
    }
}

// After (working) -- ApiController with CORS configuration
class DataController extends ApiController {
    public function __construct(
        string $appName,
        IRequest $request,
        private DataService $service,
    ) {
        parent::__construct(
            $appName,
            $request,
            'GET, POST',           // allowed HTTP methods
            'Authorization, Content-Type, Accept',  // allowed headers
            86400                   // preflight cache max-age (seconds)
        );
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]  // Required -- browsers cannot send CSRF tokens cross-origin
    public function getData(): JSONResponse {
        return new JSONResponse($this->service->findAll());
    }
}
```

---

## Scenario 7: Login Flow v2 Poll Times Out

### Symptom
Poll endpoint keeps returning 404 even after the user has logged in.

### Root Cause
Either: (A) the 20-minute token expired, (B) the user opened a different login URL, or (C) the poll endpoint was called with wrong token.

### Fix

```php
// Implement proper Login Flow v2 with timeout handling
$initResponse = $client->post($server . '/index.php/login/v2');
$flow = json_decode($initResponse->getBody(), true);

$pollUrl = $flow['poll']['endpoint'];
$token = $flow['poll']['token'];
$loginUrl = $flow['login'];

// Open $loginUrl in browser for user authentication

$maxAttempts = 120;  // 20 minutes at 10-second intervals
$attempt = 0;

while ($attempt < $maxAttempts) {
    $attempt++;
    sleep(10);  // Poll every 10 seconds -- NEVER flood the endpoint

    try {
        $pollResponse = $client->post($pollUrl, [
            'body' => ['token' => $token],
        ]);

        $credentials = json_decode($pollResponse->getBody(), true);
        // Success: $credentials['server'], $credentials['loginName'], $credentials['appPassword']
        break;
    } catch (\Exception $e) {
        if ($e->getCode() === 404) {
            continue;  // User has not authenticated yet
        }
        throw $e;  // Unexpected error
    }
}

if ($attempt >= $maxAttempts) {
    throw new \RuntimeException('Login Flow v2 timed out after 20 minutes');
}
```

---

## Scenario 8: Chunked Upload Fails with 507

### Symptom
MOVE operation to assemble chunks returns HTTP 507 Insufficient Storage.

### Root Cause
The user's quota is exceeded. The `OC-Total-Length` header triggers a quota check during chunk assembly.

### Fix

```bash
# Check quota before starting upload
curl -u admin:pass -X PROPFIND \
  -H 'Depth: 0' \
  'https://cloud.example.com/remote.php/dav/files/admin/' \
  -d '<?xml version="1.0"?>
    <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
      <d:prop>
        <oc:quota-available-bytes/>
        <oc:quota-used-bytes/>
      </d:prop>
    </d:propfind>'
```

If `quota-available-bytes` is less than the file size, the upload will fail. Either free space or request a quota increase before uploading.

---

## Scenario 9: DataResponse in OCSController Returns Wrong Format

### Symptom
OCS endpoint returns raw JSON without the `ocs` envelope wrapper.

### Root Cause
Using `JSONResponse` instead of `DataResponse` in an `OCSController`. `JSONResponse` bypasses the OCS responder.

### Fix

```php
// Before (broken) -- JSONResponse bypasses OCS envelope
class MyOcsController extends OCSController {
    public function getData(): JSONResponse {
        return new JSONResponse(['items' => $this->service->findAll()]);
    }
}
// Returns: {"items": [...]}  -- missing ocs envelope

// After (working) -- DataResponse goes through OCS responder
class MyOcsController extends OCSController {
    #[NoAdminRequired]
    public function getData(): DataResponse {
        return new DataResponse(['items' => $this->service->findAll()]);
    }
}
// Returns: {"ocs": {"meta": {...}, "data": {"items": [...]}}}
```
