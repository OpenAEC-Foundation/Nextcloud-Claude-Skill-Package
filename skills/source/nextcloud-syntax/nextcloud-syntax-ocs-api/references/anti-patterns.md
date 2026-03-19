# OCS API — Anti-Patterns

## AP-001: Missing OCS-APIRequest Header

**Wrong**:
```bash
curl -u admin:password "https://cloud.example.com/ocs/v2.php/cloud/capabilities"
```

**Result**: Server returns an HTML login page instead of API data. The request is treated as a browser request.

**Correct**:
```bash
curl -u admin:password \
  -H "OCS-APIRequest: true" \
  "https://cloud.example.com/ocs/v2.php/cloud/capabilities"
```

**Rule**: ALWAYS include `OCS-APIRequest: true` on every OCS request. This header is mandatory and also serves as CSRF protection for API clients.

---

## AP-002: Trusting HTTP Status Codes with v1 Endpoints

**Wrong**:
```python
response = requests.get(f"{url}/ocs/v1.php/cloud/users/nonexistent",
                        auth=(user, password),
                        headers={"OCS-APIRequest": "true"})
if response.status_code == 200:
    print("User found!")  # WRONG — v1 always returns HTTP 200
```

**Result**: Code treats every v1 response as successful because v1 always returns HTTP 200, even for errors.

**Correct**:
```python
response = requests.get(f"{url}/ocs/v1.php/cloud/users/nonexistent",
                        auth=(user, password),
                        headers={"OCS-APIRequest": "true"},
                        params={"format": "json"})
data = response.json()
if data["ocs"]["meta"]["statuscode"] == 100:
    print("User found!")
else:
    print(f"Error: {data['ocs']['meta']['message']}")
```

**Better**: Use v2 endpoints where HTTP status codes match OCS status codes:
```python
response = requests.get(f"{url}/ocs/v2.php/cloud/users/nonexistent",
                        auth=(user, password),
                        headers={"OCS-APIRequest": "true"})
if response.status_code == 200:
    print("User found!")  # Now correct — v2 returns HTTP 404 for not found
```

**Rule**: NEVER rely on HTTP status codes with v1 endpoints. ALWAYS check `ocs.meta.statuscode`. Prefer v2 endpoints for new code.

---

## AP-003: Parsing XML When JSON Is Available

**Wrong**:
```python
import xml.etree.ElementTree as ET

response = requests.get(f"{url}/ocs/v2.php/cloud/capabilities",
                        auth=(user, password),
                        headers={"OCS-APIRequest": "true"})
root = ET.fromstring(response.text)
status = root.find(".//meta/statuscode").text  # Fragile XML parsing
```

**Result**: Verbose, error-prone code. XML namespace handling adds complexity. Empty arrays vs objects can be ambiguous in XML.

**Correct**:
```python
response = requests.get(f"{url}/ocs/v2.php/cloud/capabilities",
                        auth=(user, password),
                        headers={"OCS-APIRequest": "true"},
                        params={"format": "json"})
data = response.json()
status = data["ocs"]["meta"]["statuscode"]
```

**Rule**: ALWAYS request JSON format using `?format=json` or `Accept: application/json`. XML is the default but JSON is simpler to parse.

---

## AP-004: Hardcoding Capabilities

**Wrong**:
```python
# Assuming file sharing is always available
shares = requests.get(f"{url}/ocs/v2.php/apps/files_sharing/api/v1/shares",
                      auth=(user, password),
                      headers={"OCS-APIRequest": "true"})
```

**Result**: Fails silently or with cryptic errors when the files_sharing app is disabled or the admin has restricted sharing.

**Correct**:
```python
# First check capabilities
caps = requests.get(f"{url}/ocs/v1.php/cloud/capabilities",
                    auth=(user, password),
                    headers={"OCS-APIRequest": "true"},
                    params={"format": "json"}).json()

sharing_enabled = caps["ocs"]["data"]["capabilities"].get("files_sharing", {}).get("api_enabled", False)

if sharing_enabled:
    shares = requests.get(f"{url}/ocs/v2.php/apps/files_sharing/api/v1/shares",
                          auth=(user, password),
                          headers={"OCS-APIRequest": "true"},
                          params={"format": "json"})
else:
    print("File sharing is not available on this server")
```

**Rule**: ALWAYS check `/cloud/capabilities` before using optional APIs. Features can be disabled by the admin.

---

## AP-005: Using Real Passwords Instead of App Passwords

**Wrong**:
```bash
# Storing the user's actual password in a config file
curl -u admin:MyRealPassword123 \
  -H "OCS-APIRequest: true" \
  "https://cloud.example.com/ocs/v2.php/cloud/capabilities"
```

**Result**: Security risk. If the stored password is compromised, the attacker has full account access. Real passwords may also fail if 2FA is enabled.

**Correct**:
```bash
# Use an app password obtained via Login Flow v2
curl -u admin:xxxxx-xxxxx-xxxxx-xxxxx-xxxxx \
  -H "OCS-APIRequest: true" \
  "https://cloud.example.com/ocs/v2.php/cloud/capabilities"
```

**Rule**: ALWAYS use app passwords for API clients. Obtain them via Login Flow v2. App passwords can be individually revoked and work with 2FA.

---

## AP-006: Creating Shares with Missing Required Parameters

**Wrong**:
```bash
# Missing shareType
curl -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Documents/file.pdf" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

**Result**: Returns a 400 error with an unclear message.

**Wrong**:
```bash
# User share without shareWith
curl -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Documents/file.pdf&shareType=0" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

**Result**: Returns error because user shares (type 0) require a `shareWith` parameter.

**Correct**:
```bash
# User share with all required parameters
curl -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Documents/file.pdf&shareType=0&shareWith=johndoe&permissions=1" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"

# Public link (shareWith not needed)
curl -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Documents/file.pdf&shareType=3&permissions=1" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

**Rule**: ALWAYS include `path` and `shareType`. Include `shareWith` for user (0), group (1), email (4), federated (6), circle (7), and Talk (10) share types.

---

## AP-007: Invalid Permission Combinations

**Wrong**:
```bash
# Giving write permissions on a public link to a file (not folder)
curl -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Documents/file.pdf&shareType=3&permissions=15" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

**Result**: May fail or silently downgrade permissions. Public upload only works on folders.

**Correct**:
```bash
# Read-only public link for files
curl -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Documents/file.pdf&shareType=3&permissions=1" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"

# Public link with upload for folders
curl -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Uploads&shareType=3&permissions=5" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

**Rule**: NEVER grant create/update/delete permissions on public file links. Public upload (create permission = 4) is only valid for folders.

---

## AP-008: Not URL-Encoding Share Attributes

**Wrong**:
```bash
curl -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d 'path=/Uploads&shareType=3&permissions=4&attributes=[{"scope":"fileRequest","key":"enabled","value":true}]' \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

**Result**: The JSON brackets and quotes in the attributes parameter break the form encoding, leading to malformed requests.

**Correct**:
```bash
curl -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/Uploads&shareType=3&permissions=4" \
  --data-urlencode 'attributes=[{"scope":"fileRequest","key":"enabled","value":true}]' \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

**Rule**: ALWAYS use `--data-urlencode` for the `attributes` parameter because it contains JSON with special characters.

---

## AP-009: Missing Security Attributes on OCSController Methods

**Wrong**:
```php
class ApiController extends OCSController {
    // No security attributes — defaults to admin-only
    public function getPublicData(): DataResponse {
        return new DataResponse(['status' => 'ok']);
    }
}
```

**Result**: Only admin users can access this endpoint. Regular authenticated users get HTTP 403.

**Correct**:
```php
use OCP\AppFramework\Http\Attribute\NoAdminRequired;

class ApiController extends OCSController {
    #[NoAdminRequired]
    public function getPublicData(): DataResponse {
        return new DataResponse(['status' => 'ok']);
    }
}
```

**Rule**: ALWAYS add `#[NoAdminRequired]` to OCSController methods that should be accessible to regular users. The default security posture is admin-only.

---

## AP-010: Using v1 Success Code 200 Instead of 100

**Wrong**:
```python
response = requests.get(f"{url}/ocs/v1.php/cloud/capabilities",
                        auth=(user, password),
                        headers={"OCS-APIRequest": "true"},
                        params={"format": "json"})
data = response.json()
if data["ocs"]["meta"]["statuscode"] == 200:
    print("Success")  # WRONG — v1 success code is 100, not 200
```

**Correct**:
```python
# v1: success code is 100
if data["ocs"]["meta"]["statuscode"] == 100:
    print("Success")

# v2: success code is 200
response_v2 = requests.get(f"{url}/ocs/v2.php/cloud/capabilities", ...)
data_v2 = response_v2.json()
if data_v2["ocs"]["meta"]["statuscode"] == 200:
    print("Success")
```

**Rule**: NEVER assume v1 and v2 use the same success status codes. v1 uses 100 for success; v2 uses 200.

---

## AP-011: Forgetting DataResponse in OCSController

**Wrong**:
```php
class ApiController extends OCSController {
    public function getData(): JSONResponse {
        return new JSONResponse(['items' => []]);
    }
}
```

**Result**: The response bypasses the OCS envelope entirely. Clients expecting `ocs.meta` + `ocs.data` structure will break.

**Correct**:
```php
class ApiController extends OCSController {
    public function getData(): DataResponse {
        return new DataResponse(['items' => []]);
    }
}
```

**Rule**: ALWAYS return `DataResponse` from OCSController methods. Use `JSONResponse` only in regular Controllers, not OCSControllers.

---

## AP-012: Polling Without Proper Error Handling

**Wrong**:
```bash
# Fire-and-forget without checking response
curl -s -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/file.pdf&shareType=0&shareWith=johndoe" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
# Assume share was created successfully
```

**Correct**:
```bash
response=$(curl -s -u admin:app-password \
  -H "OCS-APIRequest: true" \
  -X POST \
  -d "path=/file.pdf&shareType=0&shareWith=johndoe&permissions=1" \
  "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json")

statuscode=$(echo "$response" | jq -r '.ocs.meta.statuscode')
if [ "$statuscode" = "200" ]; then
  share_id=$(echo "$response" | jq -r '.ocs.data.id')
  echo "Share created: $share_id"
else
  message=$(echo "$response" | jq -r '.ocs.meta.message')
  echo "Failed: $message"
fi
```

**Rule**: ALWAYS check `ocs.meta.statuscode` after every OCS API call. Handle errors explicitly.
