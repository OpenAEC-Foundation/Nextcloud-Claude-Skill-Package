# WebDAV Methods Reference

## DAV Operations

### PROPFIND -- Query Properties

Retrieves properties for a resource or collection. Returns `207 Multi-Status`.

**Request format**:
```http
PROPFIND /remote.php/dav/files/{username}/{path} HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
Depth: 1
Content-Type: application/xml; charset=utf-8

<?xml version="1.0" encoding="UTF-8"?>
<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:prop>
    <d:getlastmodified/>
    <d:getetag/>
    <d:getcontenttype/>
    <d:resourcetype/>
    <d:getcontentlength/>
    <oc:fileid/>
    <oc:permissions/>
    <oc:favorite/>
    <nc:has-preview/>
  </d:prop>
</d:propfind>
```

**Response format** (207 Multi-Status):
```xml
<?xml version="1.0"?>
<d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns" xmlns:s="http://sabredav.org/ns">
  <d:response>
    <d:href>/remote.php/dav/files/username/Documents/</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype><d:collection/></d:resourcetype>
        <d:getlastmodified>Wed, 15 Nov 2023 10:30:00 GMT</d:getlastmodified>
        <d:getetag>"6554c6b8e4b01"</d:getetag>
        <oc:fileid>12345</oc:fileid>
        <oc:permissions>RGDNVCK</oc:permissions>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
  <d:response>
    <d:href>/remote.php/dav/files/username/Documents/report.pdf</d:href>
    <d:propstat>
      <d:prop>
        <d:resourcetype/>
        <d:getlastmodified>Mon, 13 Nov 2023 08:15:00 GMT</d:getlastmodified>
        <d:getcontentlength>524288</d:getcontentlength>
        <d:getcontenttype>application/pdf</d:getcontenttype>
        <d:getetag>"6551a7c4d2f01"</d:getetag>
        <oc:fileid>12346</oc:fileid>
        <oc:permissions>RGDNVW</oc:permissions>
      </d:prop>
      <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>
```

**Depth header**:
- `0` -- Target resource only (use for checking existence or single file properties)
- `1` -- Target + immediate children (standard directory listing)
- `infinity` -- Full recursive tree (AVOID on large directories; may be disabled server-side)

**Request all properties**:
```xml
<d:propfind xmlns:d="DAV:">
  <d:allprop/>
</d:propfind>
```

---

### GET -- Download File

Downloads the file content. Returns `200 OK` with the file body.

```http
GET /remote.php/dav/files/{username}/{path} HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
```

**Range requests** (partial download):
```http
GET /remote.php/dav/files/{username}/{path} HTTP/1.1
Range: bytes=0-1023
```

**Folder download as ZIP** (Nextcloud extension):
```http
GET /remote.php/dav/files/{username}/{folder}/ HTTP/1.1
Accept: application/zip
```

---

### PUT -- Upload/Overwrite File

Creates or replaces a file. Returns `201 Created` (new) or `204 No Content` (overwrite).

```http
PUT /remote.php/dav/files/{username}/{path} HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
Content-Type: application/octet-stream
X-OC-MTime: 1700000000
OC-Checksum: SHA256:e3b0c44298fc1c149afbf4c8996fb924...
X-NC-WebDAV-AutoMkcol: 1

[file content]
```

**Response headers** on success:
- `OC-Etag` -- Entity tag of the created/updated file
- `OC-FileId` -- Nextcloud file identifier
- `X-Hash-SHA256` -- Computed hash (if `X-Hash: sha256` was sent)

---

### MKCOL -- Create Directory

Creates a new collection (directory). Returns `201 Created`.

```http
MKCOL /remote.php/dav/files/{username}/{path}/ HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
```

Returns `405 Method Not Allowed` if the directory already exists. Returns `409 Conflict` if a parent directory does not exist.

---

### MOVE -- Rename or Move

Moves or renames a resource. Returns `201 Created` (new location) or `204 No Content` (overwritten).

```http
MOVE /remote.php/dav/files/{username}/{source-path} HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
Destination: https://cloud.example.com/remote.php/dav/files/{username}/{dest-path}
Overwrite: F
```

- `Destination` header is REQUIRED -- MUST be a full absolute URL
- `Overwrite: T` (default) -- replace existing resource at destination
- `Overwrite: F` -- fail with `412 Precondition Failed` if destination exists

---

### COPY -- Duplicate Resource

Copies a resource. Returns `201 Created` (new location) or `204 No Content` (overwritten).

```http
COPY /remote.php/dav/files/{username}/{source-path} HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
Destination: https://cloud.example.com/remote.php/dav/files/{username}/{dest-path}
Overwrite: F
```

Same `Destination` and `Overwrite` semantics as MOVE.

---

### DELETE -- Remove Resource

Deletes a file or recursively deletes a directory. Returns `204 No Content`.

```http
DELETE /remote.php/dav/files/{username}/{path} HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
```

Deleted items go to the trashbin (if enabled). To permanently delete, use the trashbin DAV endpoint.

---

## Property Namespace Reference

### DAV: (standard WebDAV properties)

| Property | Type | Description |
|----------|------|-------------|
| `d:getlastmodified` | HTTP-date | RFC 2822 formatted modification time |
| `d:getetag` | string | Entity tag for conditional requests |
| `d:getcontenttype` | string | MIME type of the resource |
| `d:getcontentlength` | integer | Size in bytes (files only) |
| `d:resourcetype` | element | Empty for files; `<d:collection/>` for directories |
| `d:creationdate` | datetime | Resource creation date |
| `d:displayname` | string | Human-readable name |
| `d:getcontentlanguage` | string | Content language tag |
| `d:lockdiscovery` | element | Active locks on the resource |
| `d:supportedlock` | element | Supported lock types |

### http://owncloud.org/ns (ownCloud legacy)

| Property | Type | Description |
|----------|------|-------------|
| `oc:fileid` | integer | Internal file ID (unique per instance) |
| `oc:permissions` | string | Permission flags: R, G, D, N, V, C, K, W |
| `oc:size` | integer | Total size (including children for directories) |
| `oc:favorite` | integer | 0 or 1 (favorite status) |
| `oc:comments-unread` | integer | Count of unread comments |
| `oc:comments-count` | integer | Total comment count |
| `oc:owner-display-name` | string | Display name of file owner |
| `oc:owner-id` | string | User ID of file owner |
| `oc:share-types` | element | Share types active on this resource |
| `oc:checksums` | element | Stored checksums for the file |
| `oc:data-fingerprint` | string | Data fingerprint for sync |

### http://nextcloud.org/ns (Nextcloud-specific)

| Property | Type | Description |
|----------|------|-------------|
| `nc:has-preview` | boolean | Whether preview generation is available |
| `nc:mount-type` | string | Storage mount type (local, shared, external) |
| `nc:is-encrypted` | integer | End-to-end encryption flag |
| `nc:lock` | integer | File lock status |
| `nc:lock-owner` | string | User who holds the lock |
| `nc:lock-owner-displayname` | string | Display name of lock owner |
| `nc:lock-time` | integer | Unix timestamp of lock acquisition |
| `nc:lock-timeout` | integer | Lock timeout in seconds |
| `nc:lock-owner-type` | integer | 0=user, 1=office, 2=token |
| `nc:lock-owner-editor` | string | Editor identifier holding the lock |
| `nc:share-attributes` | JSON | Share attribute metadata |
| `nc:note` | string | Note attached to the resource |
| `nc:rich-workspace` | string | Rich workspace content (MD) |
| `nc:creation_time` | integer | Creation timestamp (Unix) |
| `nc:upload_time` | integer | Upload timestamp (Unix) |
| `nc:hidden` | boolean | Whether file is hidden |

---

## Chunked Upload v2 Protocol

### Overview

Three-step protocol for reliable upload of large files (>5MB). Uses the `/remote.php/dav/uploads/{username}/` endpoint.

### Step 1: Create Upload Directory (MKCOL)

```http
MKCOL /remote.php/dav/uploads/{username}/{upload-id} HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
Destination: https://cloud.example.com/remote.php/dav/files/{username}/{dest-path}
```

- `{upload-id}` -- Client-generated unique identifier (UUID recommended)
- `Destination` header is REQUIRED on EVERY request in the chunked upload flow

### Step 2: Upload Chunks (PUT)

```http
PUT /remote.php/dav/uploads/{username}/{upload-id}/{chunk-number} HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
Content-Type: application/octet-stream
Destination: https://cloud.example.com/remote.php/dav/files/{username}/{dest-path}
OC-Total-Length: {total-file-size-bytes}

[chunk data]
```

- Chunk numbers: `1` to `10000` (zero-padded recommended: `00001`)
- Chunk size: 5MB minimum, 5GB maximum (final chunk may be smaller)
- Chunks can be uploaded in any order and in parallel
- `OC-Total-Length` triggers server-side quota validation (returns `507` if insufficient)

### Step 3: Assemble File (MOVE .file)

```http
MOVE /remote.php/dav/uploads/{username}/{upload-id}/.file HTTP/1.1
Host: cloud.example.com
Authorization: Basic {base64(username:app-password)}
Destination: https://cloud.example.com/remote.php/dav/files/{username}/{dest-path}
OC-Total-Length: {total-file-size-bytes}
X-OC-MTime: {unix-timestamp}
OC-Checksum: SHA256:{hash}
```

- The `.file` pseudo-resource triggers server-side assembly
- Chunks are assembled in numeric filename order
- Optional `X-OC-MTime` sets the final file modification time
- Optional `OC-Checksum` validates the assembled file integrity

### Abort/Cleanup

```http
DELETE /remote.php/dav/uploads/{username}/{upload-id} HTTP/1.1
```

Upload directories auto-expire after 24 hours of inactivity.

### Constraints Summary

| Constraint | Value |
|-----------|-------|
| Chunk numbers | 1-10000 |
| Minimum chunk size | 5 MB |
| Maximum chunk size | 5 GB |
| Upload directory expiry | 24 hours (inactivity) |
| `Destination` header | REQUIRED on every request |
| Assembly order | Numeric filename order |
| Maximum chunks | 10,000 |

---

## Trashbin DAV Operations

**Endpoint**: `/remote.php/dav/trashbin/{username}/trash/`

**List trashed items**:
```http
PROPFIND /remote.php/dav/trashbin/{username}/trash/ HTTP/1.1
Depth: 1
```

**Restore item**:
```http
MOVE /remote.php/dav/trashbin/{username}/trash/{item-id} HTTP/1.1
Destination: https://cloud.example.com/remote.php/dav/trashbin/{username}/restore/{original-filename}
```

**Permanently delete**:
```http
DELETE /remote.php/dav/trashbin/{username}/trash/{item-id} HTTP/1.1
```

---

## Versions DAV Operations

**Endpoint**: `/remote.php/dav/versions/{username}/versions/{fileid}/`

**List versions**:
```http
PROPFIND /remote.php/dav/versions/{username}/versions/{fileid}/ HTTP/1.1
Depth: 1
```

**Restore version** (copies version to current):
```http
COPY /remote.php/dav/versions/{username}/versions/{fileid}/{version-id} HTTP/1.1
Destination: https://cloud.example.com/remote.php/dav/files/{username}/{path}
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200 OK` | GET success, property found |
| `201 Created` | PUT/MKCOL/MOVE/COPY created new resource |
| `204 No Content` | DELETE success, MOVE/COPY overwrite success |
| `207 Multi-Status` | PROPFIND response with multiple resource statuses |
| `400 Bad Request` | Malformed request or missing required header |
| `401 Unauthorized` | Authentication required or invalid credentials |
| `403 Forbidden` | Insufficient permissions |
| `404 Not Found` | Resource does not exist |
| `405 Method Not Allowed` | MKCOL on existing directory |
| `409 Conflict` | Parent directory does not exist |
| `412 Precondition Failed` | `Overwrite: F` and destination exists |
| `423 Locked` | Resource is locked by another user/process |
| `507 Insufficient Storage` | Quota exceeded |
