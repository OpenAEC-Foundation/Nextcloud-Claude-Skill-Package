# WebDAV curl Examples

All examples use `--user username:app-password` for authentication. Replace `cloud.example.com`, `username`, and `app-password` with actual values.

---

## PROPFIND -- List Directory

### List immediate children with common properties

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents' \
  --user username:app-password \
  --request PROPFIND \
  --header 'Depth: 1' \
  --header 'Content-Type: application/xml; charset=utf-8' \
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
        <oc:favorite/>
        <nc:has-preview/>
      </d:prop>
    </d:propfind>'
```

### Check if a single file exists (Depth: 0)

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents/report.pdf' \
  --user username:app-password \
  --request PROPFIND \
  --header 'Depth: 0' \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:">
      <d:prop>
        <d:getetag/>
        <d:getcontentlength/>
      </d:prop>
    </d:propfind>'
```

### Get all available properties

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents' \
  --user username:app-password \
  --request PROPFIND \
  --header 'Depth: 0' \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:">
      <d:allprop/>
    </d:propfind>'
```

### List favorites

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/' \
  --user username:app-password \
  --request PROPFIND \
  --header 'Depth: 1' \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
      <d:prop>
        <d:resourcetype/>
        <d:getcontenttype/>
        <oc:favorite/>
      </d:prop>
    </d:propfind>'
```

---

## GET -- Download File

### Simple file download

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents/report.pdf' \
  --user username:app-password \
  --output report.pdf
```

### Download with ETag conditional (only if changed)

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents/report.pdf' \
  --user username:app-password \
  --header 'If-None-Match: "6554c6b8e4b01"' \
  --output report.pdf
```

Returns `304 Not Modified` if the file has not changed.

### Partial download (range request)

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/largefile.bin' \
  --user username:app-password \
  --header 'Range: bytes=0-1048575' \
  --output first-1mb.bin
```

### Download folder as ZIP

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/ProjectFolder' \
  --user username:app-password \
  --header 'Accept: application/zip' \
  --output project.zip
```

---

## PUT -- Upload File

### Simple upload

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents/newfile.txt' \
  --user username:app-password \
  --request PUT \
  --upload-file ./newfile.txt
```

### Upload with modification time and checksum

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents/important.pdf' \
  --user username:app-password \
  --request PUT \
  --upload-file ./important.pdf \
  --header 'X-OC-MTime: 1700000000' \
  --header 'OC-Checksum: SHA256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
```

### Upload with auto-create parent directories

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/new/deeply/nested/path/file.txt' \
  --user username:app-password \
  --request PUT \
  --upload-file ./file.txt \
  --header 'X-NC-WebDAV-AutoMkcol: 1'
```

### Upload and request server-computed hash

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents/data.bin' \
  --user username:app-password \
  --request PUT \
  --upload-file ./data.bin \
  --header 'X-Hash: sha256' \
  --verbose
```

The response includes `X-Hash-SHA256` header with the computed hash.

### Upload from stdin

```bash
echo "Hello, Nextcloud!" | curl 'https://cloud.example.com/remote.php/dav/files/username/hello.txt' \
  --user username:app-password \
  --request PUT \
  --data-binary @-
```

---

## MKCOL -- Create Directory

### Create a single directory

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/NewFolder' \
  --user username:app-password \
  --request MKCOL
```

### Create nested directories (one at a time)

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Level1' \
  --user username:app-password \
  --request MKCOL

curl 'https://cloud.example.com/remote.php/dav/files/username/Level1/Level2' \
  --user username:app-password \
  --request MKCOL
```

Parent directories MUST exist. Use `X-NC-WebDAV-AutoMkcol: 1` on PUT to auto-create parents for file uploads.

---

## MOVE -- Rename or Move

### Rename a file

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/oldname.txt' \
  --user username:app-password \
  --request MOVE \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/newname.txt'
```

### Move file to subdirectory

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/file.txt' \
  --user username:app-password \
  --request MOVE \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/archive/file.txt'
```

### Move without overwriting (fail-safe)

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/source.txt' \
  --user username:app-password \
  --request MOVE \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/target.txt' \
  --header 'Overwrite: F'
```

Returns `412 Precondition Failed` if `target.txt` already exists.

### Move entire directory

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/OldFolder' \
  --user username:app-password \
  --request MOVE \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/NewFolder'
```

---

## COPY -- Duplicate

### Copy a file

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/original.txt' \
  --user username:app-password \
  --request COPY \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/copy-of-original.txt'
```

### Copy without overwriting

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/source.pdf' \
  --user username:app-password \
  --request COPY \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/backup/source.pdf' \
  --header 'Overwrite: F'
```

### Copy entire directory

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Templates' \
  --user username:app-password \
  --request COPY \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/ProjectFromTemplate'
```

---

## DELETE -- Remove

### Delete a file

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/unwanted.txt' \
  --user username:app-password \
  --request DELETE
```

### Delete a directory (recursive)

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/OldProject' \
  --user username:app-password \
  --request DELETE
```

All contents are recursively moved to trashbin (if enabled).

---

## Chunked Upload v2 -- Complete Example

### Upload a 50MB file in 10MB chunks

```bash
# Variables
SERVER="https://cloud.example.com"
USER="username"
PASS="app-password"
UPLOAD_ID="myapp-$(uuidgen)"
DEST="$SERVER/remote.php/dav/files/$USER/uploads/largefile.bin"
TOTAL_SIZE=52428800

# Step 1: Create upload directory
curl -X MKCOL --user "$USER:$PASS" \
  "$SERVER/remote.php/dav/uploads/$USER/$UPLOAD_ID" \
  --header "Destination: $DEST"

# Step 2: Upload chunks
curl -X PUT --user "$USER:$PASS" \
  "$SERVER/remote.php/dav/uploads/$USER/$UPLOAD_ID/00001" \
  --data-binary @chunk_00001.bin \
  --header "Destination: $DEST" \
  --header "OC-Total-Length: $TOTAL_SIZE"

curl -X PUT --user "$USER:$PASS" \
  "$SERVER/remote.php/dav/uploads/$USER/$UPLOAD_ID/00002" \
  --data-binary @chunk_00002.bin \
  --header "Destination: $DEST" \
  --header "OC-Total-Length: $TOTAL_SIZE"

curl -X PUT --user "$USER:$PASS" \
  "$SERVER/remote.php/dav/uploads/$USER/$UPLOAD_ID/00003" \
  --data-binary @chunk_00003.bin \
  --header "Destination: $DEST" \
  --header "OC-Total-Length: $TOTAL_SIZE"

curl -X PUT --user "$USER:$PASS" \
  "$SERVER/remote.php/dav/uploads/$USER/$UPLOAD_ID/00004" \
  --data-binary @chunk_00004.bin \
  --header "Destination: $DEST" \
  --header "OC-Total-Length: $TOTAL_SIZE"

curl -X PUT --user "$USER:$PASS" \
  "$SERVER/remote.php/dav/uploads/$USER/$UPLOAD_ID/00005" \
  --data-binary @chunk_00005.bin \
  --header "Destination: $DEST" \
  --header "OC-Total-Length: $TOTAL_SIZE"

# Step 3: Assemble
curl -X MOVE --user "$USER:$PASS" \
  "$SERVER/remote.php/dav/uploads/$USER/$UPLOAD_ID/.file" \
  --header "Destination: $DEST" \
  --header "OC-Total-Length: $TOTAL_SIZE" \
  --header "X-OC-MTime: $(date +%s)" \
  --header "OC-Checksum: SHA256:$(sha256sum largefile.bin | cut -d' ' -f1)"
```

### Abort chunked upload

```bash
curl -X DELETE --user "$USER:$PASS" \
  "$SERVER/remote.php/dav/uploads/$USER/$UPLOAD_ID"
```

---

## Public Share Access (NC 29+)

### List public share contents

```bash
curl 'https://cloud.example.com/public.php/dav/files/AbCdEfGh/' \
  --request PROPFIND \
  --header 'Depth: 1' \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:">
      <d:prop>
        <d:resourcetype/>
        <d:getcontentlength/>
        <d:getlastmodified/>
      </d:prop>
    </d:propfind>'
```

### Download from password-protected share

```bash
curl 'https://cloud.example.com/public.php/dav/files/AbCdEfGh/shared-doc.pdf' \
  --user 'anonymous:share-password' \
  --output shared-doc.pdf
```

### Upload to public share (if permitted)

```bash
curl 'https://cloud.example.com/public.php/dav/files/AbCdEfGh/uploaded.txt' \
  --user 'anonymous:share-password' \
  --request PUT \
  --upload-file ./uploaded.txt
```

---

## Trashbin Operations

### List trashed items

```bash
curl 'https://cloud.example.com/remote.php/dav/trashbin/username/trash/' \
  --user username:app-password \
  --request PROPFIND \
  --header 'Depth: 1' \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:">
      <d:prop>
        <d:getlastmodified/>
        <d:getcontentlength/>
        <d:resourcetype/>
      </d:prop>
    </d:propfind>'
```

### Restore from trash

```bash
curl 'https://cloud.example.com/remote.php/dav/trashbin/username/trash/report.pdf.d1700000000' \
  --user username:app-password \
  --request MOVE \
  --header 'Destination: https://cloud.example.com/remote.php/dav/trashbin/username/restore/report.pdf'
```

### Permanently delete from trash

```bash
curl 'https://cloud.example.com/remote.php/dav/trashbin/username/trash/report.pdf.d1700000000' \
  --user username:app-password \
  --request DELETE
```

---

## Version Operations

### List file versions

```bash
curl 'https://cloud.example.com/remote.php/dav/versions/username/versions/12345/' \
  --user username:app-password \
  --request PROPFIND \
  --header 'Depth: 1' \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propfind xmlns:d="DAV:">
      <d:prop>
        <d:getlastmodified/>
        <d:getcontentlength/>
      </d:prop>
    </d:propfind>'
```

Replace `12345` with the `oc:fileid` from a PROPFIND on the file.

### Restore a specific version

```bash
curl 'https://cloud.example.com/remote.php/dav/versions/username/versions/12345/1700000000' \
  --user username:app-password \
  --request COPY \
  --header 'Destination: https://cloud.example.com/remote.php/dav/files/username/Documents/report.pdf'
```

---

## Set/Update Properties (PROPPATCH)

### Set file as favorite

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents/important.pdf' \
  --user username:app-password \
  --request PROPPATCH \
  --header 'Content-Type: application/xml; charset=utf-8' \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propertyupdate xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
      <d:set>
        <d:prop>
          <oc:favorite>1</oc:favorite>
        </d:prop>
      </d:set>
    </d:propertyupdate>'
```

### Remove favorite

```bash
curl 'https://cloud.example.com/remote.php/dav/files/username/Documents/important.pdf' \
  --user username:app-password \
  --request PROPPATCH \
  --data '<?xml version="1.0" encoding="UTF-8"?>
    <d:propertyupdate xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
      <d:set>
        <d:prop>
          <oc:favorite>0</oc:favorite>
        </d:prop>
      </d:set>
    </d:propertyupdate>'
```
