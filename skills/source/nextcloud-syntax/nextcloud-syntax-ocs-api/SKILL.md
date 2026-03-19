---
name: nextcloud-syntax-ocs-api
description: "Guides Nextcloud OCS REST API including endpoint structure, v1 vs v2 versioning, authentication methods, response envelope format, capabilities discovery, user provisioning, share API endpoints, and user status API. Activates when calling OCS endpoints, creating OCS controllers, handling OCS responses, or implementing share operations."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-syntax-ocs-api

## Quick Reference

### Endpoint Versioning

| Version | Base Path | OCS Status Code (Success) | HTTP Status Code | Notes |
|---------|-----------|--------------------------|------------------|-------|
| v1 | `/ocs/v1.php/` | 100 | Always 200 | Legacy — check `statuscode` field |
| v2 | `/ocs/v2.php/` | 200 | Mirrors OCS status | Preferred for all new code |

App-specific OCS endpoints: `/ocs/v2.php/apps/{APPNAME}/api/v1/{endpoint}`

### Required Header

**ALWAYS** send this header with every OCS request:

```
OCS-APIRequest: true
```

Without this header, the server rejects the request. This header also serves as CSRF protection for API clients.

### Authentication Methods

| Method | Header/Syntax | Use Case |
|--------|---------------|----------|
| Basic Auth | `-u username:password` | Server-side scripts, CLI tools |
| App Password | `-u username:app-password` | Desktop/mobile clients (Login Flow v2) |
| OIDC Bearer | `Authorization: Bearer ID_TOKEN` | SSO/OIDC environments |
| Session Cookie | Browser cookies + CSRF token | Browser-based requests |

### Response Format (JSON)

Request JSON with `?format=json` or `Accept: application/json` header.

```json
{
  "ocs": {
    "meta": {
      "status": "ok",
      "statuscode": 200,
      "message": "OK"
    },
    "data": { }
  }
}
```

**ALWAYS** check `ocs.meta.statuscode` for the authoritative status — especially in v1 where HTTP status is always 200.

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ocs/v1.php/cloud/capabilities` | GET | Server capabilities and feature negotiation |
| `/ocs/v1.php/cloud/users` | GET | List all users (admin only) |
| `/ocs/v1.php/cloud/users/{USERID}` | GET | Get user details |
| `/ocs/v2.php/apps/files_sharing/api/v1/shares` | GET/POST | List or create shares |
| `/ocs/v2.php/apps/files_sharing/api/v1/shares/{id}` | GET/PUT/DELETE | Get, update, or delete share |
| `/ocs/v2.php/apps/user_status/api/v1/user_status` | GET/PUT | Current user status |
| `/ocs/v2.php/core/autocomplete/get` | GET | Autocomplete search |
| `/ocs/v2.php/apps/dav/api/v1/direct` | POST | Create direct download link |

### Share Types

| Value | Type | `shareWith` Required |
|-------|------|---------------------|
| 0 | User | Yes (user ID) |
| 1 | Group | Yes (group ID) |
| 3 | Public link | No |
| 4 | Email | Yes (email address) |
| 6 | Federated (remote) | Yes (user@server) |
| 7 | Circle | Yes (circle ID) |
| 10 | Talk conversation | Yes (conversation token) |

### Permissions Bitmask

| Value | Permission | Binary |
|-------|-----------|--------|
| 1 | Read | 00001 |
| 2 | Update | 00010 |
| 4 | Create | 00100 |
| 8 | Delete | 01000 |
| 16 | Share | 10000 |
| 31 | All | 11111 |

Combine with bitwise OR: Read + Create = `1 | 4` = `5`.

### User Status Types

| Status | Description |
|--------|-------------|
| `online` | User is actively using Nextcloud |
| `away` | User is idle |
| `dnd` | Do not disturb — suppress notifications |
| `invisible` | Appear offline to others |
| `offline` | User is not connected |

### Critical Warnings

**NEVER** omit the `OCS-APIRequest: true` header — requests will be rejected with a login page redirect.

**NEVER** assume HTTP status codes reflect success in v1 — v1 ALWAYS returns HTTP 200. Check `ocs.meta.statuscode` instead.

**NEVER** parse XML when JSON is available — use `?format=json` for simpler and less error-prone parsing.

**NEVER** hardcode server capabilities — ALWAYS check `/cloud/capabilities` for feature detection before using optional APIs.

**NEVER** create shares without validating `shareType` and `permissions` — invalid combinations produce cryptic errors.

**ALWAYS** use v2 endpoints for new code — they map OCS status codes to HTTP status codes for standard HTTP error handling.

**ALWAYS** use app passwords instead of real user passwords for API clients — obtain them via Login Flow v2.

**ALWAYS** include `path` and `shareType` when creating shares — they are required parameters.

---

## Essential Patterns

### Pattern 1: Basic OCS Request (JSON)

```bash
curl -u "$USER:$APP_PASSWORD" \
  -H "OCS-APIRequest: true" \
  -H "Accept: application/json" \
  "https://cloud.example.com/ocs/v2.php/cloud/capabilities"
```

### Pattern 2: Create a Public Link Share

```bash
curl -u "$USER:$APP_PASSWORD" \
  -H "OCS-APIRequest: true" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -X POST \
  -d "path=/Documents/report.pdf&shareType=3&permissions=1" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

### Pattern 3: OCSController for App Endpoints

```php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;

class ApiController extends OCSController {
    public function __construct(
        string $appName,
        IRequest $request,
        private MyService $service,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function getData(int $id): DataResponse {
        $item = $this->service->find($id);
        return new DataResponse(['item' => $item]);
    }
}
```

Register the OCS route in `appinfo/routes.php`:

```php
return [
    'ocs' => [
        ['name' => 'api#getData', 'url' => '/api/v1/data/{id}', 'verb' => 'GET'],
    ],
];
```

Accessible at: `/ocs/v2.php/apps/myapp/api/v1/data/42`

### Pattern 4: Capabilities Check Before Feature Use

```bash
# Check if the server supports file sharing
CAPS=$(curl -s -u "$USER:$APP_PASSWORD" \
  -H "OCS-APIRequest: true" \
  "https://cloud.example.com/ocs/v1.php/cloud/capabilities?format=json")

# Parse capabilities (using jq)
echo "$CAPS" | jq '.ocs.data.capabilities.files_sharing'
```

**ALWAYS** check capabilities before calling optional APIs — apps may be disabled or features restricted by admin.

### Pattern 5: Set User Status with Custom Message

```bash
curl -u "$USER:$APP_PASSWORD" \
  -H "OCS-APIRequest: true" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{"statusType": "away"}' \
  "https://cloud.example.com/ocs/v2.php/apps/user_status/api/v1/user_status/status"

curl -u "$USER:$APP_PASSWORD" \
  -H "OCS-APIRequest: true" \
  -H "Content-Type: application/json" \
  -X PUT \
  -d '{"statusIcon": "☕", "message": "On a break", "clearAt": null}' \
  "https://cloud.example.com/ocs/v2.php/apps/user_status/api/v1/user_status/message/custom"
```

### Pattern 6: Share with Advanced Attributes

```bash
# Create a file request (upload-only public share)
curl -u "$USER:$APP_PASSWORD" \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Uploads&shareType=3&permissions=4" \
  --data-urlencode 'attributes=[{"scope":"fileRequest","key":"enabled","value":true}]' \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"

# Create a share with download disabled
curl -u "$USER:$APP_PASSWORD" \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Documents/secret.pdf&shareType=3&permissions=1" \
  --data-urlencode 'attributes=[{"scope":"permissions","key":"download","value":false}]' \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

---

## v1 vs v2 Status Code Mapping

| Scenario | v1 `statuscode` | v1 HTTP | v2 `statuscode` | v2 HTTP |
|----------|-----------------|---------|-----------------|---------|
| Success | 100 | 200 | 200 | 200 |
| Bad request | 400 | 200 | 400 | 400 |
| Unauthorized | 401 | 200 | 401 | 401 |
| Forbidden | 403 | 200 | 403 | 403 |
| Not found | 404 | 200 | 404 | 404 |

**ALWAYS** prefer v2 for new integrations — standard HTTP error handling works out of the box.

---

## Create Share Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | Yes | File/folder path relative to user root |
| `shareType` | int | Yes | Share type (see Share Types table) |
| `shareWith` | string | Conditional | Required for user, group, email, federated, circle, Talk |
| `permissions` | int | No | Bitmask (default: 31 for user/group, 1 for public link) |
| `password` | string | No | Password protection (public links) |
| `expireDate` | string | No | Expiry date in `YYYY-MM-DD` format |
| `publicUpload` | bool | No | Allow public upload (deprecated — use permissions) |
| `note` | string | No | Note for share recipient |
| `label` | string | No | Label for public link |
| `attributes` | JSON | No | Advanced share attributes (download control, file request) |

---

## Reference Links

- [references/methods.md](references/methods.md) -- All OCS endpoints, response format details, share API reference
- [references/examples.md](references/examples.md) -- curl examples for all major endpoints
- [references/anti-patterns.md](references/anti-patterns.md) -- Common OCS API mistakes and corrections

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/OCS/index.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/OCS/ocs-share-api.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/OCS/ocs-status-api.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/rest_apis.html
