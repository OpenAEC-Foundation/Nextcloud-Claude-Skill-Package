# OCS API — Methods Reference

## Endpoint Structure

All OCS endpoints follow the pattern:

```
/ocs/{version}/[cloud|apps/{appname}]/api/v{api_version}/{resource}
```

Where `{version}` is `v1.php` or `v2.php`.

---

## Response Envelope

### XML (Default)

```xml
<?xml version="1.0"?>
<ocs>
  <meta>
    <status>ok</status>
    <statuscode>200</statuscode>
    <message>OK</message>
    <totalitems>100</totalitems>
    <itemsperpage>25</itemsperpage>
  </meta>
  <data>
    <!-- response payload -->
  </data>
</ocs>
```

### JSON

Request with `?format=json` query parameter or `Accept: application/json` header.

```json
{
  "ocs": {
    "meta": {
      "status": "ok",
      "statuscode": 200,
      "message": "OK",
      "totalitems": "100",
      "itemsperpage": "25"
    },
    "data": {}
  }
}
```

### Meta Fields

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"ok"` or `"failure"` |
| `statuscode` | int | OCS status code (authoritative in v1) |
| `message` | string | Human-readable message |
| `totalitems` | string | Total count for paginated responses |
| `itemsperpage` | string | Items per page for paginated responses |

---

## Core Cloud Endpoints

### Capabilities Discovery

```
GET /ocs/v1.php/cloud/capabilities
```

**Response data structure** (key sections):

```json
{
  "version": {
    "major": 28,
    "minor": 0,
    "micro": 0,
    "string": "28.0.0",
    "edition": "",
    "extendedSupport": false
  },
  "capabilities": {
    "core": {
      "webdav-root": "remote.php/webdav",
      "reference-api": true,
      "reference-regex": "..."
    },
    "files_sharing": {
      "api_enabled": true,
      "public": {
        "enabled": true,
        "password": { "enforced": false },
        "expire_date": { "enabled": true, "days": 7, "enforced": false },
        "upload": true,
        "upload_files_drop": true
      },
      "user": { "send_mail": false, "expire_date": { "enabled": true } },
      "group_sharing": true,
      "resharing": true,
      "federation": { "outgoing": true, "incoming": true }
    },
    "user_status": { "enabled": true, "supports_emoji": true },
    "theming": {
      "name": "Nextcloud",
      "url": "https://nextcloud.com",
      "slogan": "a safe home for all your data",
      "color": "#0082c9"
    }
  }
}
```

### User Provisioning

```
GET /ocs/v1.php/cloud/users                    # List all users (admin)
GET /ocs/v1.php/cloud/users?search=query       # Search users
GET /ocs/v1.php/cloud/users/{USERID}           # Get user details
POST /ocs/v1.php/cloud/users                   # Create user
PUT /ocs/v1.php/cloud/users/{USERID}           # Edit user
DELETE /ocs/v1.php/cloud/users/{USERID}        # Delete user
GET /ocs/v1.php/cloud/users/{USERID}/groups    # Get user's groups
POST /ocs/v1.php/cloud/users/{USERID}/groups   # Add user to group
DELETE /ocs/v1.php/cloud/users/{USERID}/groups # Remove user from group
```

**Create user parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `userid` | string | Yes | Unique user ID |
| `password` | string | Yes | User password |
| `displayName` | string | No | Display name |
| `email` | string | No | Email address |
| `groups` | array | No | Groups to add user to |
| `quota` | string | No | Quota (e.g., `"5 GB"`, `"none"`) |
| `language` | string | No | Preferred language code |

### Group Management

```
GET /ocs/v1.php/cloud/groups                   # List groups
GET /ocs/v1.php/cloud/groups?search=query      # Search groups
POST /ocs/v1.php/cloud/groups                  # Create group
DELETE /ocs/v1.php/cloud/groups/{GROUPID}      # Delete group
GET /ocs/v1.php/cloud/groups/{GROUPID}/users   # List group members
```

---

## Share API (files_sharing)

Base: `/ocs/v2.php/apps/files_sharing/api/v1`

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/shares` | List all shares by the current user |
| GET | `/shares?path={path}` | List shares for a specific file/folder |
| GET | `/shares?path={path}&reshares=true` | Include reshares |
| GET | `/shares?path={path}&subfiles=true` | Shares in subfolder (folder only) |
| GET | `/shares?shared_with_me=true` | Shares received by current user |
| GET | `/shares/{id}` | Get single share details |
| POST | `/shares` | Create a new share |
| PUT | `/shares/{id}` | Update an existing share |
| DELETE | `/shares/{id}` | Delete a share |

### Share Object Fields (Response)

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Share ID |
| `share_type` | int | Share type (0=user, 1=group, 3=link, etc.) |
| `uid_owner` | string | Share owner user ID |
| `displayname_owner` | string | Share owner display name |
| `permissions` | int | Permission bitmask |
| `stime` | int | Share creation timestamp (Unix) |
| `parent` | int | Parent share ID (null if root) |
| `expiration` | string | Expiration date (YYYY-MM-DD HH:MM:SS) or null |
| `token` | string | Share token (public links only) |
| `uid_file_owner` | string | File owner user ID |
| `path` | string | File/folder path |
| `item_type` | string | `"file"` or `"folder"` |
| `mimetype` | string | MIME type |
| `share_with` | string | Share recipient |
| `share_with_displayname` | string | Recipient display name |
| `password` | string | Password hash (public links with password) |
| `url` | string | Public share URL (public links only) |
| `note` | string | Note for recipient |
| `label` | string | Share label |
| `attributes` | string | JSON-encoded share attributes |

### Update Share Parameters (PUT)

| Parameter | Type | Description |
|-----------|------|-------------|
| `permissions` | int | New permission bitmask |
| `password` | string | Set/change password (public links) |
| `expireDate` | string | New expiry date (`YYYY-MM-DD`) or empty to remove |
| `note` | string | Note for recipient |
| `label` | string | Label for public link |
| `attributes` | JSON | Share attributes |

### Share Attributes

Advanced configuration passed as JSON array:

```json
[
  {"scope": "permissions", "key": "download", "value": false},
  {"scope": "fileRequest", "key": "enabled", "value": true}
]
```

| Scope | Key | Value | Effect |
|-------|-----|-------|--------|
| `permissions` | `download` | `false` | Disable download on public link |
| `fileRequest` | `enabled` | `true` | Enable file request (upload-only) |

---

## Federated Shares

Base: `/ocs/v2.php/apps/files_sharing/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/remote_shares` | List accepted remote shares |
| GET | `/remote_shares/pending` | List pending remote shares |
| POST | `/remote_shares/pending/{id}` | Accept a pending share |
| DELETE | `/remote_shares/pending/{id}` | Decline a pending share |
| DELETE | `/remote_shares/{id}` | Remove an accepted share |
| GET | `/remote_shares/{id}` | Get remote share details |

---

## User Status API

Base: `/ocs/v2.php/apps/user_status/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/user_status` | Get current user's status |
| PUT | `/user_status/status` | Set status type |
| GET | `/user_status/message/custom` | Get custom message |
| PUT | `/user_status/message/custom` | Set custom status message |
| PUT | `/user_status/message/predefined` | Set predefined message |
| DELETE | `/user_status/message` | Clear status message |
| GET | `/statuses` | List all user statuses |
| GET | `/statuses/{userId}` | Get specific user's status |

### Set Status Type (PUT /user_status/status)

| Parameter | Type | Values |
|-----------|------|--------|
| `statusType` | string | `online`, `away`, `dnd`, `invisible`, `offline` |

### Set Custom Message (PUT /user_status/message/custom)

| Parameter | Type | Description |
|-----------|------|-------------|
| `statusIcon` | string | Single emoji character |
| `message` | string | Custom message text (max 80 chars) |
| `clearAt` | int/null | Unix timestamp to auto-clear, or `null` for permanent |

### Set Predefined Message (PUT /user_status/message/predefined)

| Parameter | Type | Description |
|-----------|------|-------------|
| `messageId` | string | Predefined message ID |
| `clearAt` | int/null | Unix timestamp to auto-clear |

---

## Autocomplete API

```
GET /ocs/v2.php/core/autocomplete/get
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search query |
| `itemType` | string | Context type (e.g., `"files"`, `"call"`) |
| `itemId` | string | Context item ID |
| `shareTypes[]` | int[] | Filter by share types |
| `limit` | int | Max results (default: 10) |

---

## Direct Download API

```
POST /ocs/v2.php/apps/dav/api/v1/direct
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `fileId` | int | File ID to create direct link for |

Returns a time-limited direct download URL (valid for 8 hours, single use).

---

## OCSController (PHP Server-Side)

For creating custom OCS endpoints in Nextcloud apps:

```php
use OCP\AppFramework\OCSController;
use OCP\AppFramework\Http\DataResponse;
```

**DataResponse** is the standard return type for OCS controllers. The response is automatically wrapped in the OCS envelope and formatted as XML or JSON based on the client's request.

### OCS Route Registration

In `appinfo/routes.php`, use the `ocs` key:

```php
return [
    'ocs' => [
        ['name' => 'api#list',   'url' => '/api/v1/items',      'verb' => 'GET'],
        ['name' => 'api#create', 'url' => '/api/v1/items',      'verb' => 'POST'],
        ['name' => 'api#get',    'url' => '/api/v1/items/{id}',  'verb' => 'GET'],
        ['name' => 'api#update', 'url' => '/api/v1/items/{id}',  'verb' => 'PUT'],
        ['name' => 'api#delete', 'url' => '/api/v1/items/{id}',  'verb' => 'DELETE'],
    ],
];
```

These routes become accessible at `/ocs/v2.php/apps/{appname}/api/v1/items`.

### Attribute-Based OCS Routing (NC 29+)

```php
use OCP\AppFramework\Http\Attribute\ApiRoute;

#[ApiRoute(verb: 'GET', url: '/api/v1/items/{id}')]
public function get(int $id): DataResponse {
    return new DataResponse($this->service->find($id));
}
```

---

## Utility Parameters

| Parameter | Scope | Description |
|-----------|-------|-------------|
| `format=json` | All OCS | Return JSON instead of XML |
| `forceLanguage=en` | All OCS | Override response locale |
