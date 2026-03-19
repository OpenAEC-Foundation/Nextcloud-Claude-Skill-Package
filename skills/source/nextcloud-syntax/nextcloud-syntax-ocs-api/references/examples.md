# OCS API — curl Examples

All examples use JSON format. Replace `cloud.example.com`, `admin`, and `app-password` with your values.

---

## Authentication & Headers

```bash
# Base variables for all examples
NC_URL="https://cloud.example.com"
NC_USER="admin"
NC_PASS="your-app-password"

# Standard OCS headers
OCS_HEADERS=(-H "OCS-APIRequest: true" -H "Accept: application/json")
```

---

## Capabilities Discovery

```bash
# Get server capabilities (feature negotiation)
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v1.php/cloud/capabilities?format=json" | jq '.ocs.data'

# Check specific capability (file sharing enabled?)
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v1.php/cloud/capabilities?format=json" \
  | jq '.ocs.data.capabilities.files_sharing.api_enabled'

# Get server version
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v1.php/cloud/capabilities?format=json" \
  | jq '.ocs.data.version'
```

---

## User Provisioning

```bash
# List all users
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v1.php/cloud/users?format=json" | jq '.ocs.data'

# Search users
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v1.php/cloud/users?search=john&format=json"

# Get user details
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v1.php/cloud/users/johndoe?format=json" | jq '.ocs.data'

# Create a new user
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "userid=newuser&password=SecurePass123&email=new@example.com&displayName=New User" \
  "$NC_URL/ocs/v1.php/cloud/users?format=json"

# Edit user (set quota)
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  -d "key=quota&value=5 GB" \
  "$NC_URL/ocs/v1.php/cloud/users/newuser?format=json"

# Delete user
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X DELETE \
  "$NC_URL/ocs/v1.php/cloud/users/newuser?format=json"

# Get user's groups
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v1.php/cloud/users/johndoe/groups?format=json"

# Add user to group
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "groupid=developers" \
  "$NC_URL/ocs/v1.php/cloud/users/johndoe/groups?format=json"
```

---

## Share API

### List Shares

```bash
# All shares by current user
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json" \
  | jq '.ocs.data'

# Shares for a specific file
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?path=/Documents/report.pdf&format=json"

# Shares for a folder including subfiles
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?path=/Documents&subfiles=true&format=json"

# Shares shared with me
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?shared_with_me=true&format=json"

# Get specific share
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares/42?format=json"
```

### Create Shares

```bash
# Share with a user (read + update permissions)
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "path=/Documents/report.pdf&shareType=0&shareWith=johndoe&permissions=3" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"

# Share with a group (all permissions)
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "path=/Projects&shareType=1&shareWith=developers&permissions=31" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"

# Create a public link (read-only)
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "path=/Documents/report.pdf&shareType=3&permissions=1" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json" \
  | jq '.ocs.data.url'

# Create a password-protected public link with expiration
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "path=/Documents/report.pdf&shareType=3&permissions=1&password=SecretPass&expireDate=2026-12-31" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"

# Create a file request (upload-only public link)
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "path=/Uploads&shareType=3&permissions=4" \
  --data-urlencode 'attributes=[{"scope":"fileRequest","key":"enabled","value":true}]' \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"

# Share via email
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "path=/Documents/report.pdf&shareType=4&shareWith=recipient@example.com&permissions=1" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"

# Share with a note
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "path=/Documents/report.pdf&shareType=0&shareWith=johndoe&permissions=3" \
  --data-urlencode "note=Please review by Friday" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares?format=json"
```

### Update Shares

```bash
# Change permissions to read-only
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  -d "permissions=1" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares/42?format=json"

# Set password on existing public link
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  -d "password=NewSecurePass" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares/42?format=json"

# Set expiration date
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  -d "expireDate=2026-06-30" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares/42?format=json"

# Remove expiration date
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  -d "expireDate=" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares/42?format=json"

# Disable download on public link
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  --data-urlencode 'attributes=[{"scope":"permissions","key":"download","value":false}]' \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares/42?format=json"
```

### Delete Shares

```bash
# Delete a share
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X DELETE \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares/42?format=json"
```

---

## User Status API

```bash
# Get current user's status
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/user_status/api/v1/user_status?format=json" \
  | jq '.ocs.data'

# Set status to "away"
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  -H "Content-Type: application/json" \
  -d '{"statusType": "away"}' \
  "$NC_URL/ocs/v2.php/apps/user_status/api/v1/user_status/status"

# Set status to "do not disturb"
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  -H "Content-Type: application/json" \
  -d '{"statusType": "dnd"}' \
  "$NC_URL/ocs/v2.php/apps/user_status/api/v1/user_status/status"

# Set custom status message with emoji
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  -H "Content-Type: application/json" \
  -d '{"statusIcon": "\u2615", "message": "Coffee break", "clearAt": null}' \
  "$NC_URL/ocs/v2.php/apps/user_status/api/v1/user_status/message/custom"

# Set custom message that auto-clears in 1 hour
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X PUT \
  -H "Content-Type: application/json" \
  -d "{\"statusIcon\": \"\ud83d\udcde\", \"message\": \"In a meeting\", \"clearAt\": $(($(date +%s) + 3600))}" \
  "$NC_URL/ocs/v2.php/apps/user_status/api/v1/user_status/message/custom"

# Clear status message
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X DELETE \
  "$NC_URL/ocs/v2.php/apps/user_status/api/v1/user_status/message"

# List all user statuses
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/user_status/api/v1/statuses?format=json"

# Get another user's status
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/user_status/api/v1/statuses/johndoe?format=json"
```

---

## Federated Shares

```bash
# List accepted remote shares
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/remote_shares?format=json"

# List pending remote shares
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending?format=json"

# Accept a pending remote share
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending/7?format=json"

# Decline a pending remote share
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X DELETE \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/remote_shares/pending/7?format=json"
```

---

## Autocomplete

```bash
# Search for users to share with
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/core/autocomplete/get?search=john&itemType=files&limit=5&format=json"

# Search with specific share types (users and groups)
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/core/autocomplete/get?search=dev&itemType=files&shareTypes[]=0&shareTypes[]=1&format=json"
```

---

## Direct Download

```bash
# Create a direct download link for a file
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "fileId=12345" \
  "$NC_URL/ocs/v2.php/apps/dav/api/v1/direct?format=json" \
  | jq '.ocs.data.url'
```

The returned URL is time-limited (8 hours) and single-use. No authentication required to access it.

---

## Group Management

```bash
# List all groups
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v1.php/cloud/groups?format=json"

# Create a group
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X POST \
  -d "groupid=developers" \
  "$NC_URL/ocs/v1.php/cloud/groups?format=json"

# List members of a group
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v1.php/cloud/groups/developers/users?format=json"

# Delete a group
curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  -X DELETE \
  "$NC_URL/ocs/v1.php/cloud/groups/developers?format=json"
```

---

## Error Handling Pattern

```bash
# Check for errors in the response
response=$(curl -s -u "$NC_USER:$NC_PASS" \
  "${OCS_HEADERS[@]}" \
  "$NC_URL/ocs/v2.php/apps/files_sharing/api/v1/shares/99999?format=json")

status=$(echo "$response" | jq -r '.ocs.meta.statuscode')
message=$(echo "$response" | jq -r '.ocs.meta.message')

if [ "$status" != "200" ]; then
  echo "Error $status: $message"
else
  echo "Success"
  echo "$response" | jq '.ocs.data'
fi
```
