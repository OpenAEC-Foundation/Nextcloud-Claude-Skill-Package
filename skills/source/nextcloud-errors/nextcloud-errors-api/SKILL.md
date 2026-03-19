---
name: nextcloud-errors-api
description: >
  Use when encountering OCS or WebDAV API errors, debugging response codes, or troubleshooting authentication.
  Prevents misinterpreting OCS v1 status 100 as error, forgetting OCS-APIRequest header, and ignoring DAV XML error bodies.
  Covers OCS status code confusion (v1 vs v2), missing OCS-APIRequest header, DAV error responses, HTTP status mapping, authentication failures, and CORS issues.
  Keywords: OCS error, 997, 998, 999, OCS-APIRequest, DAV error, CORS, 401, 403, HTTP status.
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-errors-api

## Diagnostic Quick Reference

### OCS API Errors

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| HTTP 200 but unexpected `statuscode` | Using v1 endpoint | Switch to `/ocs/v2.php/` |
| HTTP 997 / CSRF validation failed | Missing `OCS-APIRequest` header | Add `OCS-APIRequest: true` header |
| HTTP 401 Unauthorized | Bad credentials or expired token | Verify credentials, use Login Flow v2 for app passwords |
| HTTP 403 Forbidden | Missing security attribute on controller | Add `#[NoAdminRequired]` or `#[PublicPage]` |
| HTTP 404 on OCS endpoint | Wrong URL path or missing route | Verify `/ocs/v2.php/apps/{appid}/...` structure |
| HTTP 429 Too Many Requests | Rate limiting triggered | Respect `Retry-After` header, reduce request frequency |
| Empty `<data>` in response | Endpoint returns no data for query | Check parameters, verify resource exists |

### WebDAV Errors

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| HTTP 401 on DAV endpoint | Invalid basic auth credentials | Use `username:app-password` (not user password) |
| HTTP 404 on PROPFIND | Wrong path or missing username in URL | Use `/remote.php/dav/files/{username}/path` |
| HTTP 405 Method Not Allowed | Wrong HTTP verb for endpoint | Check DAV method (PROPFIND, MKCOL, etc.) |
| HTTP 409 Conflict on MKCOL | Parent directory missing | Create parent directories first or use `X-NC-WebDAV-AutoMkcol: 1` |
| HTTP 412 Precondition Failed | ETag mismatch (concurrent edit) | Re-fetch resource, retry with updated ETag |
| HTTP 423 Locked | File locked by another process | Wait for lock release or check lock owner |
| HTTP 507 Insufficient Storage | Quota exceeded | Check user quota, free space |
| XML parse error in response | Malformed PROPFIND request body | Validate XML namespaces and property names |

### Authentication Errors

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Login Flow v2 poll returns 404 indefinitely | User has not completed browser login | Verify login URL opened, check 20-minute timeout |
| App password rejected | Password revoked or account disabled | Generate new app password via Login Flow v2 |
| 2FA blocks API access | Session requires 2FA completion | Use app passwords (bypass 2FA) or add `#[NoTwoFactorRequired]` |
| OIDC Bearer token rejected | Token expired or wrong audience | Refresh token, verify OIDC provider configuration |

---

## Error 1: OCS v1 vs v2 Status Code Confusion

### What You See
- HTTP response is always 200, but the `ocs.meta.statuscode` field contains an error code (e.g., 404, 403)
- Client code checks HTTP status and assumes success, but the operation actually failed

### Why It Happens
OCS v1 (`/ocs/v1.php/`) ALWAYS returns HTTP 200 regardless of the actual result. The real status is buried in the XML/JSON envelope under `ocs.meta.statuscode`. Success in v1 is `statuscode: 100`, not `200`.

OCS v2 (`/ocs/v2.php/`) maps the OCS status code directly to the HTTP status code. Success is `statuscode: 200` and HTTP 200. Errors return the actual HTTP error code.

### How to Fix

**ALWAYS use v2 endpoints.** Replace `/ocs/v1.php/` with `/ocs/v2.php/` in all API URLs.

```php
// WRONG: v1 endpoint -- HTTP status is ALWAYS 200
$url = 'https://cloud.example.com/ocs/v1.php/cloud/users';

// CORRECT: v2 endpoint -- HTTP status reflects actual result
$url = 'https://cloud.example.com/ocs/v2.php/cloud/users';
```

**If you MUST use v1**, ALWAYS check the envelope status code:

```php
$response = json_decode($body, true);
$statusCode = $response['ocs']['meta']['statuscode'];
if ($statusCode !== 100) {
    // v1 error -- 100 means success in v1
    throw new \RuntimeException('OCS error: ' . $response['ocs']['meta']['message']);
}
```

| Version | Success Code | Error Codes | HTTP Status |
|---------|-------------|-------------|-------------|
| v1 | 100 | 400, 403, 404, 997, 998 | ALWAYS 200 |
| v2 | 200 | 400, 403, 404, 500 | Mirrors OCS code |

---

## Error 2: Missing OCS-APIRequest Header (CSRF Rejection)

### What You See
- HTTP 997 or "CSRF check failed" error
- OCS endpoint rejects request even with valid credentials
- Works in browser but fails from external client

### Why It Happens
Nextcloud requires the `OCS-APIRequest: true` header on ALL OCS requests. This header serves as an alternative CSRF protection mechanism for API clients that cannot provide a CSRF token. Without it, Nextcloud treats the request as a potential CSRF attack.

### How to Fix

**ALWAYS include the `OCS-APIRequest: true` header on every OCS request.**

```bash
# WRONG: Missing required header
curl -u "$USER:$APP_PASSWORD" \
  'https://cloud.example.com/ocs/v2.php/cloud/capabilities'

# CORRECT: Header included
curl -u "$USER:$APP_PASSWORD" \
  -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v2.php/cloud/capabilities'
```

```php
// PHP client example
$client = \OCP\Server::get(\OCP\Http\Client\IClientService::class)->newClient();
$response = $client->get($url, [
    'headers' => [
        'OCS-APIRequest' => 'true',
    ],
    'auth' => [$username, $password],
]);
```

```typescript
// TypeScript frontend using @nextcloud/axios
import axios from '@nextcloud/axios';
// @nextcloud/axios adds OCS-APIRequest automatically
const response = await axios.get('/ocs/v2.php/cloud/capabilities');
```

**NEVER** omit this header. There is no scenario where an OCS request succeeds without it (except browser requests with a valid CSRF token in the session).

---

## Error 3: DAV XML Error Responses

### What You See
- WebDAV request returns an XML body with `<d:error>` instead of the expected response
- HTTP 4xx/5xx with XML error details

### Why It Happens
WebDAV uses structured XML error responses as defined in RFC 4918. Unlike OCS (which uses an envelope), DAV errors are returned as standard HTTP error codes with an XML body describing the problem.

### How to Fix

**Parse the XML error body to get the actual error message:**

```xml
<!-- Typical DAV error response -->
<?xml version="1.0" encoding="utf-8"?>
<d:error xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns">
  <s:exception>Sabre\DAV\Exception\NotFound</s:exception>
  <s:message>File with name /nonexistent.txt could not be located</s:message>
</d:error>
```

**Common DAV exceptions and their HTTP codes:**

| Exception | HTTP Code | Meaning |
|-----------|-----------|---------|
| `Sabre\DAV\Exception\NotFound` | 404 | File or folder does not exist |
| `Sabre\DAV\Exception\Forbidden` | 403 | No permission for operation |
| `Sabre\DAV\Exception\Conflict` | 409 | Parent folder missing (MKCOL) or name conflict |
| `Sabre\DAV\Exception\Locked` | 423 | File is locked |
| `Sabre\DAV\Exception\InsufficientStorage` | 507 | Quota exceeded |
| `Sabre\DAV\Exception\MethodNotAllowed` | 405 | HTTP method not supported on resource |
| `Sabre\DAV\Exception\PreconditionFailed` | 412 | ETag or If-Match header mismatch |

**ALWAYS check the `s:exception` and `s:message` elements** for the specific cause. The HTTP status code alone is insufficient for debugging.

---

## Error 4: Authentication Failures

### What You See
- HTTP 401 on any API endpoint
- "Current user is not logged in" message
- Login Flow v2 poll stuck returning 404

### Why It Happens

**Cause A: Wrong credential type.** Using the user's login password instead of an app password. Nextcloud may reject direct passwords when 2FA is enabled.

**Cause B: Expired or revoked app password.** App passwords can be revoked by the user or admin from Settings > Security > Devices & sessions.

**Cause C: Login Flow v2 timeout.** The poll token expires after 20 minutes. The login URL must be opened in a browser within this window.

### How to Fix

**For external clients, ALWAYS use Login Flow v2 to obtain app passwords:**

```bash
# Step 1: Initiate login flow
curl -X POST https://cloud.example.com/index.php/login/v2

# Step 2: Open the "login" URL from response in browser
# Step 3: Poll for credentials (with backoff, max 20 minutes)
curl -X POST https://cloud.example.com/login/v2/poll \
  -d "token=<poll-token>"

# Step 4: Use returned appPassword for all subsequent requests
curl -u "$USER:$APP_PASSWORD" \
  -H 'OCS-APIRequest: true' \
  'https://cloud.example.com/ocs/v2.php/cloud/capabilities'
```

**NEVER** store or transmit the user's actual password. **ALWAYS** use app passwords for API access.

**NEVER** poll the Login Flow v2 endpoint without backoff -- use 1-2 second intervals.

---

## Error 5: CORS Issues with API Controllers

### What You See
- Browser console shows "CORS policy" or "No 'Access-Control-Allow-Origin' header"
- API works from curl/Postman but fails from JavaScript in a different domain
- Preflight OPTIONS request fails

### Why It Happens
Standard `Controller` and `OCSController` do not set CORS headers. Cross-origin requests from browser JavaScript are blocked by default. Only `ApiController` includes built-in CORS handling.

### How to Fix

**For cross-origin API access, extend `ApiController` instead of `Controller`:**

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\ApiController;
use OCP\AppFramework\Http\JSONResponse;
use OCP\IRequest;

class ExternalApiController extends ApiController {
    public function __construct(
        string $appName,
        IRequest $request,
        private MyService $service,
    ) {
        parent::__construct(
            $appName,
            $request,
            'GET, POST, PUT, DELETE',  // allowed methods
            'Authorization, Content-Type, Accept',  // allowed headers
            86400  // max age for preflight cache (seconds)
        );
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function getData(): JSONResponse {
        return new JSONResponse($this->service->findAll());
    }
}
```

**ALWAYS** add `#[NoCSRFRequired]` to CORS-enabled endpoints -- browsers send preflight OPTIONS requests without CSRF tokens.

**ALWAYS** use `ApiController` for endpoints consumed by external JavaScript clients. Using `Controller` with manual CORS headers is fragile and error-prone.

**NEVER** add wildcard `Access-Control-Allow-Origin: *` headers manually -- use `ApiController` which handles origin whitelisting properly.

---

## Error 6: HTTP Status Code Mismatches in OCS Controllers

### What You See
- OCSController returns wrong HTTP status codes
- `DataResponse` with error status still returns HTTP 200
- Client cannot distinguish success from failure by HTTP status alone

### Why It Happens
When using `OCSController`, the `DataResponse` status code is mapped through the OCS envelope. If you create a `DataResponse` with a non-standard status code or forget to set it, the OCS layer may not translate it correctly.

### How to Fix

**ALWAYS pass the correct HTTP status constant to `DataResponse`:**

```php
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;

// Success
return new DataResponse($data);  // defaults to Http::STATUS_OK (200)

// Not found
return new DataResponse(
    ['message' => 'Item not found'],
    Http::STATUS_NOT_FOUND  // 404
);

// Validation error
return new DataResponse(
    ['message' => 'Invalid input', 'errors' => $errors],
    Http::STATUS_BAD_REQUEST  // 400
);

// Server error
return new DataResponse(
    ['message' => 'Internal error'],
    Http::STATUS_INTERNAL_SERVER_ERROR  // 500
);
```

**NEVER** return `JSONResponse` from an `OCSController` -- it bypasses the OCS envelope formatting. **ALWAYS** use `DataResponse` with OCS controllers.

---

## Decision Tree: Diagnosing API Errors

```
API request fails
|
+-- Is it an OCS endpoint (/ocs/...)?
|   |
|   +-- HTTP 200 but wrong data?
|   |   --> Check if using v1 endpoint. Switch to v2.
|   |   --> Check ocs.meta.statuscode in response body.
|   |
|   +-- HTTP 997 or "CSRF check failed"?
|   |   --> Add OCS-APIRequest: true header.
|   |
|   +-- HTTP 401?
|   |   --> Verify credentials. Use app passwords, not user passwords.
|   |   --> Check if 2FA is blocking. Use app passwords to bypass.
|   |
|   +-- HTTP 403?
|   |   --> Check controller security attributes.
|   |   --> Add #[NoAdminRequired] for non-admin users.
|   |
|   +-- HTTP 404?
|       --> Verify URL structure: /ocs/v2.php/apps/{appid}/...
|       --> Check routes.php has matching 'ocs' route.
|
+-- Is it a WebDAV endpoint (/remote.php/dav/...)?
|   |
|   +-- HTTP 401?
|   |   --> Use basic auth with app password.
|   |
|   +-- HTTP 404?
|   |   --> Verify path includes username: /dav/files/{username}/...
|   |
|   +-- HTTP 409 on MKCOL?
|   |   --> Create parent directories first.
|   |   --> Or add X-NC-WebDAV-AutoMkcol: 1 header on PUT.
|   |
|   +-- HTTP 412?
|   |   --> ETag mismatch. Re-fetch resource, retry.
|   |
|   +-- HTTP 507?
|       --> User quota exceeded. Check storage limits.
|
+-- Is it a CORS error (browser only)?
    |
    +-- Extend ApiController instead of Controller.
    +-- Add #[NoCSRFRequired] to the endpoint.
    +-- Set allowed methods, headers, and max-age in constructor.
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- OCS error codes, DAV error format, status code mapping
- [references/examples.md](references/examples.md) -- Error scenarios with complete fix examples
- [references/anti-patterns.md](references/anti-patterns.md) -- Common API error causes and how to avoid them

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/OCS/ocs-api-overview.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/index.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/LoginFlow/index.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/controllers.html
