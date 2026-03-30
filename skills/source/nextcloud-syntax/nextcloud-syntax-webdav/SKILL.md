---
name: nextcloud-syntax-webdav
description: >
  Use when performing file operations via WebDAV, implementing chunked uploads, or querying file properties.
  Prevents incorrect DAV endpoint paths, missing Destination headers on MOVE/COPY, and broken chunked upload sequences.
  Covers DAV endpoint structure, file operations (PROPFIND/GET/PUT/MKCOL/MOVE/COPY/DELETE), property namespaces, special headers, chunked upload v2 protocol, and public share DAV access.
  Keywords: WebDAV, PROPFIND, MKCOL, chunked upload, /remote.php/dav, OC-Chunked, Destination header, WebDAV client, file sync, upload large file, PROPFIND, remote file access..
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-syntax-webdav

## Quick Reference

### DAV Endpoint Structure

| Endpoint | Purpose |
|----------|---------|
| `/remote.php/dav/files/{username}/` | File operations |
| `/remote.php/dav/calendars/{username}/` | Calendar access (CalDAV) |
| `/remote.php/dav/addressbooks/users/{username}/` | Contacts (CardDAV) |
| `/remote.php/dav/uploads/{username}/` | Chunked upload staging |
| `/remote.php/dav/trashbin/{username}/` | Trash operations |
| `/remote.php/dav/versions/{username}/` | File version history |
| `/public.php/dav/files/{share_token}/` | Public share access (NC 29+) |

### File Operations

| Method | Purpose | Required Headers |
|--------|---------|-----------------|
| PROPFIND | List directory / get properties | `Depth: 0\|1` + XML body |
| GET | Download file | None |
| PUT | Upload file | Optional: `X-OC-MTime`, `OC-Checksum` |
| MKCOL | Create directory | None |
| MOVE | Rename or move | `Destination` (full URL) |
| COPY | Duplicate file | `Destination` (full URL) |
| DELETE | Remove file or directory | None |

### Property Namespaces

| URI | Prefix | Origin |
|-----|--------|--------|
| `DAV:` | `d` | WebDAV standard (RFC 4918) |
| `http://owncloud.org/ns` | `oc` | ownCloud legacy properties |
| `http://nextcloud.org/ns` | `nc` | Nextcloud-specific properties |
| `http://open-collaboration-services.org/ns` | `ocs` | Open Collaboration Services |
| `http://open-cloud-mesh.org/ns` | `ocm` | Open Cloud Mesh |

### Common Properties

| Property | Namespace | Type | Description |
|----------|-----------|------|-------------|
| `getlastmodified` | `d` | datetime | Last modification time |
| `getetag` | `d` | string | Entity tag for caching |
| `getcontenttype` | `d` | string | MIME type |
| `getcontentlength` | `d` | integer | File size in bytes |
| `resourcetype` | `d` | element | `<d:collection/>` for directories |
| `fileid` | `oc` | integer | Nextcloud internal file ID |
| `permissions` | `oc` | string | Permission flags (RGDNVCK) |
| `favorite` | `oc` | integer | 0 or 1 |
| `comments-unread` | `oc` | integer | Unread comment count |
| `has-preview` | `nc` | boolean | Preview generation available |
| `mount-type` | `nc` | string | Storage mount type |
| `is-encrypted` | `nc` | integer | End-to-end encryption flag |
| `lock` | `nc` | integer | File lock status |
| `share-attributes` | `nc` | JSON | Share attribute metadata |

### Special Request Headers

| Header | Purpose | Direction |
|--------|---------|-----------|
| `X-OC-MTime` | Set modification timestamp (Unix epoch) | Request |
| `X-OC-CTime` | Set creation timestamp (Unix epoch) | Request |
| `OC-Checksum` | Store checksum (`MD5:xxx`, `SHA1:xxx`, `SHA256:xxx`) | Request |
| `X-Hash` | Request server to compute hash (`md5`, `sha1`, `sha256`) | Request |
| `X-Hash-MD5` / `X-Hash-SHA1` / `X-Hash-SHA256` | Computed hash values | Response |
| `OC-Etag` | File etag on create/move/copy | Response |
| `OC-FileId` | File identifier (padded-id + instance-id) | Response |
| `OC-Total-Length` | Total file size for quota checks | Request |
| `X-NC-WebDAV-AutoMkcol` | Auto-create parent directories (set to `1`) | Request |
| `Overwrite` | `T` (overwrite) or `F` (fail if exists) on MOVE/COPY | Request |

### Depth Header Values (PROPFIND)

| Value | Behavior |
|-------|----------|
| `0` | Target resource only |
| `1` | Target + immediate children |
| `infinity` | Recursive (may be disabled on server) |

### Critical Warnings

**NEVER** omit the `Destination` header on MOVE or COPY requests -- the server returns 400 Bad Request.

**NEVER** use `Depth: infinity` on large directories -- the server may time out or reject the request. ALWAYS use `Depth: 1` and paginate manually.

**NEVER** skip checksum verification on important uploads -- ALWAYS send the `OC-Checksum` header with format `ALGO:HASH` (e.g., `SHA256:abc123`).

**NEVER** assume chunk assembly order -- chunks are assembled in numeric filename order regardless of upload sequence.

**NEVER** use relative paths in the `Destination` header -- ALWAYS use the full absolute URL including scheme and host.

**ALWAYS** authenticate WebDAV requests with basic auth (username + app password) or bearer token.

**ALWAYS** include the XML namespace declarations in PROPFIND request bodies -- omitting them causes property resolution failures.

**ALWAYS** use `Depth: 1` as the default for directory listings -- it is the most common and safest option.

---

## Essential Patterns

### Pattern 1: List Directory Contents (PROPFIND)

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents' \
  --user "$USER:$APP_PASSWORD" \
  --request PROPFIND \
  --header 'Depth: 1' \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
      <d:prop>
        <d:getlastmodified/>
        <d:getcontentlength/>
        <d:getcontenttype/>
        <d:resourcetype/>
        <d:getetag/>
        <oc:fileid/>
        <oc:permissions/>
      </d:prop>
    </d:propfind>'
```

Response is a `207 Multi-Status` XML with one `<d:response>` per item. The first response is the directory itself.

### Pattern 2: Upload File with Metadata

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/report.pdf' \
  --user "$USER:$APP_PASSWORD" \
  --request PUT \
  --upload-file ./report.pdf \
  --header 'X-OC-MTime: 1700000000' \
  --header 'OC-Checksum: SHA256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855' \
  --header 'X-NC-WebDAV-AutoMkcol: 1'
```

The `X-NC-WebDAV-AutoMkcol: 1` header auto-creates any missing parent directories.

### Pattern 3: Move/Rename a File

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/old-name.txt' \
  --user "$USER:$APP_PASSWORD" \
  --request MOVE \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/subfolder/new-name.txt' \
  --header 'Overwrite: F'
```

`Overwrite: F` prevents overwriting an existing file at the destination. Use `Overwrite: T` (default) to allow it.

### Pattern 4: Chunked Upload v2 (Large Files)

Three-step protocol for reliable large file uploads:

**Step 1: Create upload directory**
```bash
curl -X MKCOL --user "$USER:$APP_PASSWORD" \
  'https://cloud.example.com/remote.php/dav/uploads/username/myapp-unique-upload-id' \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/dest/largefile.zip'
```

**Step 2: Upload chunks (5MB-5GB each)**
```bash
# Chunk 1
curl -X PUT --user "$USER:$APP_PASSWORD" \
  'https://cloud.example.com/remote.php/dav/uploads/username/myapp-unique-upload-id/00001' \
  --data-binary @chunk1.bin \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/dest/largefile.zip' \
  --header 'OC-Total-Length: 52428800'

# Chunk 2
curl -X PUT --user "$USER:$APP_PASSWORD" \
  'https://cloud.example.com/remote.php/dav/uploads/username/myapp-unique-upload-id/00002' \
  --data-binary @chunk2.bin \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/dest/largefile.zip' \
  --header 'OC-Total-Length: 52428800'
```

**Step 3: Assemble file (MOVE .file)**
```bash
curl -X MOVE --user "$USER:$APP_PASSWORD" \
  'https://cloud.example.com/remote.php/dav/uploads/username/myapp-unique-upload-id/.file' \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/dest/largefile.zip' \
  --header 'OC-Total-Length: 52428800' \
  --header 'X-OC-MTime: 1700000000'
```

**Constraints**: Chunk names must be numbers 1-10000. Final chunk can be smaller than 5MB. Upload directory expires after 24 hours of inactivity. `OC-Total-Length` triggers quota validation (returns `507 Insufficient Storage` if exceeded). To abort: `DELETE` the upload directory.

### Pattern 5: Public Share Access (NC 29+)

```bash
# Public share without password
curl 'https://cloud.example.com/public.php/dav/files/SHARE_TOKEN/' \
  --request PROPFIND \
  --header 'Depth: 1' \
  --data '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/></d:prop></d:propfind>'

# Public share with password
curl 'https://cloud.example.com/public.php/dav/files/SHARE_TOKEN/' \
  --user 'anonymous:' \
  --request PROPFIND \
  --header 'Depth: 1' \
  --data '<?xml version="1.0"?><d:propfind xmlns:d="DAV:"><d:prop><d:resourcetype/></d:prop></d:propfind>'
```

Password-protected shares use basic auth with username `anonymous` and the share password as the password.

### Pattern 6: Download Folder as ZIP

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/ProjectFolder' \
  --user "$USER:$APP_PASSWORD" \
  --header 'Accept: application/zip' \
  --output project.zip
```

Optionally filter which files to include using the `X-NC-Files` header or `files` query parameter (JSON array of filenames).

---

## Chunked Upload Decision Tree

```
File size > 5MB?
├── YES → Use chunked upload v2
│   ├── Generate unique upload ID (UUID recommended)
│   ├── MKCOL → create upload directory
│   ├── Split file into 5MB-5GB chunks
│   ├── PUT each chunk (numbered 00001-10000)
│   ├── MOVE .file → assemble at destination
│   └── On failure → DELETE upload directory to clean up
└── NO → Use simple PUT
    ├── Include OC-Checksum for integrity
    └── Include X-OC-MTime to preserve timestamp
```

---

## Permission Flags (oc:permissions)

| Flag | Meaning |
|------|---------|
| `R` | Read (Shareable) |
| `G` | Read (not shareable) |
| `D` | Delete |
| `N` | Rename/Move (NV = move into) |
| `V` | Move from |
| `C` | Create (new files/folders) |
| `K` | Create (new files only, not folders) |
| `W` | Write (update content) |

---

## Reference Links

- [references/methods.md](references/methods.md) -- DAV operations, property details, namespace reference, chunked upload protocol
- [references/examples.md](references/examples.md) -- Complete curl examples for all DAV operations
- [references/anti-patterns.md](references/anti-patterns.md) -- Common WebDAV mistakes and how to avoid them

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/index.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/basic.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/chunked_file_upload_v2.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/trashbin.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/WebDAV/versions.html
