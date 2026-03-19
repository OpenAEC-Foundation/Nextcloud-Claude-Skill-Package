# WebDAV Anti-Patterns

## AP-001: Missing Destination Header on MOVE/COPY

**NEVER** send a MOVE or COPY request without the `Destination` header.

```bash
# WRONG -- missing Destination header
curl -X MOVE --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/file.txt'
# Result: 400 Bad Request

# CORRECT -- full absolute URL in Destination
curl -X MOVE --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/file.txt' \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/user/renamed.txt'
```

The `Destination` header MUST contain a full absolute URL including scheme, host, and path.

---

## AP-002: Relative Path in Destination Header

**NEVER** use a relative path in the `Destination` header.

```bash
# WRONG -- relative path
--header 'Destination: /remote.php/dav/files/user/newname.txt'

# WRONG -- path only, no host
--header 'Destination: remote.php/dav/files/user/newname.txt'

# CORRECT -- full absolute URL
--header 'Destination: https://cloud.example.com/remote.php/dav/files/user/newname.txt'
```

---

## AP-003: Using Depth: infinity on Large Directories

**NEVER** use `Depth: infinity` on directories with unknown or large file counts.

```bash
# WRONG -- may time out or be rejected on large directories
curl -X PROPFIND --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/' \
  --header 'Depth: infinity' \
  --data '<d:propfind xmlns:d="DAV:"><d:allprop/></d:propfind>'

# CORRECT -- use Depth: 1 and recurse programmatically
curl -X PROPFIND --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/Documents' \
  --header 'Depth: 1' \
  --data '<?xml version="1.0"?>
    <d:propfind xmlns:d="DAV:">
      <d:prop><d:resourcetype/></d:prop>
    </d:propfind>'
```

Many servers disable `Depth: infinity` for performance reasons. ALWAYS use `Depth: 1` and implement client-side recursion if needed.

---

## AP-004: Omitting XML Namespaces in PROPFIND

**NEVER** request properties without declaring their namespace.

```xml
<!-- WRONG -- oc:fileid without namespace declaration -->
<d:propfind xmlns:d="DAV:">
  <d:prop>
    <oc:fileid/>
  </d:prop>
</d:propfind>

<!-- CORRECT -- namespace declared -->
<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:prop>
    <oc:fileid/>
  </d:prop>
</d:propfind>
```

Missing namespace declarations cause properties to be silently ignored or return errors.

---

## AP-005: Skipping Checksum on Important Uploads

**NEVER** upload critical files without checksum verification.

```bash
# WRONG -- no integrity verification
curl -X PUT --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/database-backup.sql' \
  --upload-file ./database-backup.sql

# CORRECT -- checksum for integrity verification
curl -X PUT --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/database-backup.sql' \
  --upload-file ./database-backup.sql \
  --header 'OC-Checksum: SHA256:a1b2c3d4e5f6...'
```

The `OC-Checksum` format is `ALGORITHM:HASH`. Supported algorithms: MD5, SHA1, SHA256, SHA3-256, Adler32.

---

## AP-006: Assuming Chunk Assembly Order

**NEVER** assume chunks are assembled in upload order -- they are assembled in numeric filename order.

```bash
# If you upload in this order:
# 00003, 00001, 00002

# Assembly order is ALWAYS: 00001, 00002, 00003
# (sorted by filename, not upload sequence)
```

ALWAYS name chunks with zero-padded numbers to ensure correct sorting.

---

## AP-007: Missing Destination on Chunked Upload Requests

**NEVER** omit the `Destination` header on ANY step of the chunked upload protocol.

```bash
# WRONG -- Destination missing on MKCOL
curl -X MKCOL --user user:pass \
  'https://cloud.example.com/remote.php/dav/uploads/user/upload-123'

# WRONG -- Destination missing on chunk PUT
curl -X PUT --user user:pass \
  'https://cloud.example.com/remote.php/dav/uploads/user/upload-123/00001' \
  --data-binary @chunk1.bin

# CORRECT -- Destination on every request
DEST="https://cloud.example.com/remote.php/dav/files/user/target.zip"

curl -X MKCOL --user user:pass \
  'https://cloud.example.com/remote.php/dav/uploads/user/upload-123' \
  --header "Destination: $DEST"

curl -X PUT --user user:pass \
  'https://cloud.example.com/remote.php/dav/uploads/user/upload-123/00001' \
  --data-binary @chunk1.bin \
  --header "Destination: $DEST" \
  --header "OC-Total-Length: 52428800"
```

---

## AP-008: Not Cleaning Up Failed Chunked Uploads

**NEVER** leave upload directories after a failed chunked upload.

```bash
# After a failed upload, ALWAYS clean up:
curl -X DELETE --user user:pass \
  'https://cloud.example.com/remote.php/dav/uploads/user/upload-123'
```

Upload directories expire after 24 hours, but orphaned directories consume server resources. ALWAYS delete on failure.

---

## AP-009: Creating Nested Directories Without Parents

**NEVER** attempt to create nested directories when parents do not exist.

```bash
# WRONG -- parent "Level1" does not exist
curl -X MKCOL --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/Level1/Level2/Level3'
# Result: 409 Conflict

# CORRECT (option 1) -- create parents first
curl -X MKCOL --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/Level1'
curl -X MKCOL --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/Level1/Level2'
curl -X MKCOL --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/Level1/Level2/Level3'

# CORRECT (option 2) -- use AutoMkcol on PUT (files only, not directories)
curl -X PUT --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/Level1/Level2/Level3/file.txt' \
  --upload-file ./file.txt \
  --header 'X-NC-WebDAV-AutoMkcol: 1'
```

Note: `X-NC-WebDAV-AutoMkcol` only works with PUT (file uploads), not with MKCOL.

---

## AP-010: Ignoring 207 Multi-Status Errors

**NEVER** treat HTTP `207 Multi-Status` as unconditional success.

A PROPFIND returning `207` may contain individual `<d:status>` elements with error codes (e.g., `403 Forbidden`, `404 Not Found`) for specific properties or resources.

```xml
<!-- This 207 response contains an error -->
<d:multistatus xmlns:d="DAV:">
  <d:response>
    <d:href>/remote.php/dav/files/user/restricted/</d:href>
    <d:propstat>
      <d:prop><d:getcontentlength/></d:prop>
      <d:status>HTTP/1.1 403 Forbidden</d:status>
    </d:propstat>
  </d:response>
</d:multistatus>
```

ALWAYS parse individual `<d:status>` elements within each `<d:propstat>` block.

---

## AP-011: Sending PUT to Directory Path

**NEVER** send a PUT request to create a directory.

```bash
# WRONG -- PUT creates files, not directories
curl -X PUT --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/NewFolder/'

# CORRECT -- use MKCOL for directories
curl -X MKCOL --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/NewFolder'
```

---

## AP-012: Not URL-Encoding Special Characters in Paths

**NEVER** use unencoded special characters in WebDAV URLs.

```bash
# WRONG -- spaces and special characters unencoded
curl 'https://cloud.example.com/remote.php/dav/files/user/My Documents/file (copy).txt' \
  --user user:pass

# CORRECT -- URL-encoded path
curl 'https://cloud.example.com/remote.php/dav/files/user/My%20Documents/file%20(copy).txt' \
  --user user:pass
```

Encode spaces as `%20`, parentheses as `%28`/`%29`, and other special characters per RFC 3986.

---

## AP-013: Using Simple PUT for Large Files

**NEVER** use a simple PUT for files larger than 5MB in production environments.

```bash
# WRONG -- 500MB file via simple PUT (unreliable, no resume)
curl -X PUT --user user:pass \
  'https://cloud.example.com/remote.php/dav/files/user/huge.zip' \
  --upload-file ./huge.zip

# CORRECT -- use chunked upload v2 for large files
# (see chunked upload examples in examples.md)
```

Simple PUT has no resume capability. If the connection drops, the entire upload must restart. Chunked upload v2 allows resuming from the last successful chunk.

---

## AP-014: Hardcoding Username in Public Share URLs

**NEVER** use `/remote.php/dav/files/{username}/` for public share access.

```bash
# WRONG -- requires authentication as the sharing user
curl 'https://cloud.example.com/remote.php/dav/files/sharer/SharedFolder/file.txt' \
  --user sharer:password

# CORRECT -- use the public share endpoint (NC 29+)
curl 'https://cloud.example.com/public.php/dav/files/SHARE_TOKEN/file.txt'

# CORRECT -- with password-protected share
curl 'https://cloud.example.com/public.php/dav/files/SHARE_TOKEN/file.txt' \
  --user 'anonymous:share-password'
```

Public share access uses `anonymous` as the username with the share password.
