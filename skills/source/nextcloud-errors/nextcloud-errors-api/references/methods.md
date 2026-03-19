# API Error Reference: Codes, Formats, and Mappings

## OCS Status Codes

### v1 vs v2 Code Mapping

| OCS v1 statuscode | OCS v2 statuscode | HTTP Status (v2) | Meaning |
|-------------------|-------------------|-------------------|---------|
| 100 | 200 | 200 | Success |
| 400 | 400 | 400 | Bad request / invalid parameters |
| 401 | 401 | 401 | Unauthorized / not authenticated |
| 403 | 403 | 403 | Forbidden / insufficient permissions |
| 404 | 404 | 404 | Resource not found |
| 997 | 997 | 500 | CSRF check failed (missing OCS-APIRequest header) |
| 998 | 998 | 500 | Server error / not allowed |
| 999 | 999 | 500 | Internal server error |

**Key difference**: v1 ALWAYS returns HTTP 200 regardless of the OCS status code. v2 maps the OCS status code to the corresponding HTTP status code.

### OCS Response Envelope Structure

**JSON format** (request with `?format=json` or `Accept: application/json`):

```json
{
  "ocs": {
    "meta": {
      "status": "ok",
      "statuscode": 200,
      "message": "OK",
      "totalitems": "",
      "itemsperpage": ""
    },
    "data": {}
  }
}
```

**XML format** (default):

```xml
<?xml version="1.0"?>
<ocs>
  <meta>
    <status>ok</status>
    <statuscode>200</statuscode>
    <message>OK</message>
    <totalitems></totalitems>
    <itemsperpage></itemsperpage>
  </meta>
  <data>
    <!-- response payload -->
  </data>
</ocs>
```

**Error envelope**:

```json
{
  "ocs": {
    "meta": {
      "status": "failure",
      "statuscode": 404,
      "message": "User does not exist"
    },
    "data": []
  }
}
```

### OCS Meta Status Values

| `meta.status` | Meaning |
|---------------|---------|
| `"ok"` | Request succeeded |
| `"failure"` | Request failed |

---

## WebDAV Error Format

### DAV Error XML Structure

WebDAV errors follow the Sabre\DAV format with two namespaces:

```xml
<?xml version="1.0" encoding="utf-8"?>
<d:error xmlns:d="DAV:" xmlns:s="http://sabredav.org/ns">
  <s:exception>Sabre\DAV\Exception\NotFound</s:exception>
  <s:message>File with name /path/to/file could not be located</s:message>
</d:error>
```

### DAV Exception to HTTP Status Mapping

| Sabre Exception Class | HTTP Status | Description |
|-----------------------|-------------|-------------|
| `Sabre\DAV\Exception\BadRequest` | 400 | Malformed request (invalid XML, missing params) |
| `Sabre\DAV\Exception\NotAuthenticated` | 401 | Missing or invalid credentials |
| `Sabre\DAV\Exception\Forbidden` | 403 | Authenticated but not authorized |
| `Sabre\DAV\Exception\NotFound` | 404 | Resource does not exist |
| `Sabre\DAV\Exception\MethodNotAllowed` | 405 | HTTP method not supported on resource |
| `Sabre\DAV\Exception\Conflict` | 409 | Conflict (parent missing on MKCOL, name clash) |
| `Sabre\DAV\Exception\PreconditionFailed` | 412 | If-Match/If-None-Match header mismatch |
| `Sabre\DAV\Exception\UnsupportedMediaType` | 415 | Content-Type not accepted |
| `Sabre\DAV\Exception\Locked` | 423 | Resource is locked |
| `Sabre\DAV\Exception\TooManyRequests` | 429 | Rate limit exceeded |
| `Sabre\DAV\Exception\InsufficientStorage` | 507 | Quota exceeded |

### PROPFIND Multi-Status Response (207)

Successful PROPFIND returns HTTP 207 (Multi-Status) with per-resource status:

```xml
<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/admin/Documents/</d:href>
    <d:propstat>
      <d:prop>
        <d:getlastmodified>Thu, 14 Mar 2024 12:00:00 GMT</d:getlastmodified>
        <d:resourcetype><d:collection/></d:resourcetype>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/admin/Documents/report.pdf</d:href>
    <d:propstat>
      <d:prop>
        <d:getlastmodified>Wed, 13 Mar 2024 09:30:00 GMT</d:getlastmodified>
        <d:getcontentlength>245678</d:getcontentlength>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
    <d:propstat>
      <d:prop>
        <nc:nonexistent-prop/>
      </d:prop>
      <d:status>HTTP/1.1 404 Not Found</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>
```

**Key insight**: A single PROPFIND response can contain MULTIPLE `<d:propstat>` blocks per resource -- one for found properties (status 200) and one for missing properties (status 404). ALWAYS check the `<d:status>` inside each `<d:propstat>`.

---

## HTTP Status Codes Reference for Nextcloud APIs

### Successful Responses

| Code | OCS Usage | DAV Usage |
|------|-----------|-----------|
| 200 OK | Success (v2) | GET file content |
| 201 Created | Resource created | PUT new file, MKCOL folder |
| 204 No Content | Delete success | DELETE file |
| 207 Multi-Status | -- | PROPFIND results |

### Client Errors

| Code | OCS Usage | DAV Usage |
|------|-----------|-----------|
| 400 Bad Request | Invalid parameters | Malformed XML |
| 401 Unauthorized | Auth required | Auth required |
| 403 Forbidden | Admin-only endpoint | No permission |
| 404 Not Found | Endpoint/resource missing | File not found |
| 405 Method Not Allowed | Wrong HTTP verb | Wrong DAV method |
| 409 Conflict | -- | Parent missing on MKCOL |
| 412 Precondition Failed | -- | ETag mismatch |
| 423 Locked | -- | File locked |
| 429 Too Many Requests | Rate limited | Rate limited |

### Server Errors

| Code | OCS Usage | DAV Usage |
|------|-----------|-----------|
| 500 Internal Server Error | Server bug, CSRF failure | Server bug |
| 507 Insufficient Storage | -- | Quota exceeded |

---

## App Framework Response Types and Status Codes

### DataResponse (for OCSController)

```php
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\DataResponse;

// Available status constants
Http::STATUS_OK                    // 200
Http::STATUS_CREATED               // 201
Http::STATUS_NO_CONTENT            // 204
Http::STATUS_BAD_REQUEST           // 400
Http::STATUS_UNAUTHORIZED          // 401
Http::STATUS_FORBIDDEN             // 403
Http::STATUS_NOT_FOUND             // 404
Http::STATUS_CONFLICT              // 409
Http::STATUS_INTERNAL_SERVER_ERROR // 500
```

### JSONResponse (for Controller/ApiController)

```php
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\JSONResponse;

return new JSONResponse(['error' => 'Not found'], Http::STATUS_NOT_FOUND);
```

**NEVER** use `JSONResponse` in an `OCSController` -- it bypasses the OCS envelope. ALWAYS use `DataResponse` for OCS endpoints.
