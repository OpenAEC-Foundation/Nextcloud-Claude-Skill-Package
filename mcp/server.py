"""
Nextcloud MCP Server
Comprehensive Nextcloud integration via FastMCP.
Covers: Files (WebDAV), Shares, Users, Groups, Apps, Notifications,
        Activity, Talk, Groupfolders, Trashbin, Server Info.

Part of @openaec/nextcloud-claude-skill-package
https://github.com/OpenAEC-Foundation/Nextcloud-Claude-Skill-Package
"""

import json
import sys
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

import requests
from fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------

CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"

def load_credentials() -> dict:
    if not CREDENTIALS_FILE.exists():
        print(
            f"ERROR: {CREDENTIALS_FILE} not found.\n"
            f"Copy credentials.example.json to credentials.json and fill in your values.\n"
            f"See README.md for setup instructions.",
            file=sys.stderr,
        )
        sys.exit(1)
    with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

CREDS = load_credentials()
BASE_URL = CREDS["nextcloud_url"].rstrip("/")
AUTH = (CREDS["username"], CREDS["app_password"])

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

OCS_HEADERS = {
    "OCS-APIRequest": "true",
    "Accept": "application/json",
}

def ocs_get(path: str, params: dict = None) -> dict:
    url = f"{BASE_URL}/{path.lstrip('/')}"
    if params is None:
        params = {}
    params["format"] = "json"
    r = requests.get(url, auth=AUTH, headers=OCS_HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def ocs_post(path: str, data: dict = None) -> dict:
    url = f"{BASE_URL}/{path.lstrip('/')}"
    params = {"format": "json"}
    r = requests.post(url, auth=AUTH, headers=OCS_HEADERS, params=params, data=data or {}, timeout=30)
    r.raise_for_status()
    return r.json()

def ocs_put(path: str, data: dict = None) -> dict:
    url = f"{BASE_URL}/{path.lstrip('/')}"
    params = {"format": "json"}
    r = requests.put(url, auth=AUTH, headers=OCS_HEADERS, params=params, data=data or {}, timeout=30)
    r.raise_for_status()
    return r.json()

def ocs_delete(path: str) -> dict:
    url = f"{BASE_URL}/{path.lstrip('/')}"
    params = {"format": "json"}
    r = requests.delete(url, auth=AUTH, headers=OCS_HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def webdav_url(path: str = "") -> str:
    user = CREDS["username"]
    return f"{BASE_URL}/remote.php/dav/files/{user}/{path.lstrip('/')}"

def webdav_request(method: str, path: str, headers: dict = None, data=None, timeout: int = 60) -> requests.Response:
    url = webdav_url(path)
    r = requests.request(method, url, auth=AUTH, headers=headers or {}, data=data, timeout=timeout)
    r.raise_for_status()
    return r

# WebDAV XML namespaces
NS = {
    "d": "DAV:",
    "oc": "http://owncloud.org/ns",
    "nc": "http://nextcloud.org/ns",
}

PROPFIND_BODY = """<?xml version="1.0" encoding="UTF-8"?>
<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:prop>
    <d:getlastmodified/>
    <d:getetag/>
    <d:getcontenttype/>
    <d:getcontentlength/>
    <d:resourcetype/>
    <oc:fileid/>
    <oc:size/>
    <oc:favorite/>
    <oc:permissions/>
    <oc:owner-id/>
    <nc:has-preview/>
  </d:prop>
</d:propfind>"""

def parse_propfind(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    items = []
    for response in root.findall("d:response", NS):
        href = response.findtext("d:href", "", NS)
        props = response.find(".//d:prop", NS)
        if props is None:
            continue
        is_dir = props.find("d:resourcetype/d:collection", NS) is not None
        item = {
            "href": href,
            "type": "directory" if is_dir else "file",
            "etag": (props.findtext("d:getetag", "", NS) or "").strip('"'),
            "last_modified": props.findtext("d:getlastmodified", "", NS),
            "content_type": props.findtext("d:getcontenttype", "", NS),
            "size": int(props.findtext("oc:size", "0", NS) or props.findtext("d:getcontentlength", "0", NS) or "0"),
            "fileid": props.findtext("oc:fileid", "", NS),
            "favorite": props.findtext("oc:favorite", "0", NS) == "1",
            "permissions": props.findtext("oc:permissions", "", NS),
            "owner": props.findtext("oc:owner-id", "", NS),
        }
        items.append(item)
    return items

def _json(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False, default=str)

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Nextcloud",
    instructions=(
        "Nextcloud MCP server for comprehensive Nextcloud instance management. "
        "Provides file management (WebDAV), sharing, user/group administration, "
        "app management, notifications, activity, Talk chat, groupfolders, "
        "trashbin, and server monitoring."
    ),
)

# ===== SERVER INFO & CAPABILITIES =====

@mcp.tool()
def nc_capabilities() -> str:
    """Get Nextcloud server capabilities, versions, and supported features."""
    return _json(ocs_get("ocs/v1.php/cloud/capabilities"))

@mcp.tool()
def nc_server_info() -> str:
    """Get server monitoring data: CPU, memory, storage, active users, shares."""
    return _json(ocs_get("ocs/v2.php/apps/serverinfo/api/v1/info", {"skipUpdate": "true"}))

# ===== FILES (WebDAV) =====

@mcp.tool()
def nc_files_list(path: str = "/", depth: int = 1) -> str:
    """List files and folders at a given path. Depth 0 = item only, 1 = children."""
    headers = {"Depth": str(depth), "Content-Type": "application/xml"}
    r = webdav_request("PROPFIND", path, headers=headers, data=PROPFIND_BODY)
    items = parse_propfind(r.text)
    if depth == 1 and len(items) > 1:
        items = items[1:]
    return _json(items)

@mcp.tool()
def nc_files_info(path: str) -> str:
    """Get metadata for a single file or folder."""
    headers = {"Depth": "0", "Content-Type": "application/xml"}
    r = webdav_request("PROPFIND", path, headers=headers, data=PROPFIND_BODY)
    items = parse_propfind(r.text)
    return _json(items[0] if items else {})

@mcp.tool()
def nc_files_read(path: str) -> str:
    """Download and return the content of a text file. For binary files, returns base64 info."""
    r = webdav_request("GET", path)
    content_type = r.headers.get("Content-Type", "")
    if "text" in content_type or "json" in content_type or "xml" in content_type or "javascript" in content_type:
        return r.text
    else:
        import base64
        return _json({
            "content_type": content_type,
            "size": len(r.content),
            "base64_preview": base64.b64encode(r.content[:4096]).decode("ascii"),
            "note": "Binary file. Only first 4KB shown as base64."
        })

@mcp.tool()
def nc_files_write(path: str, content: str, content_type: str = "text/plain") -> str:
    """Upload/create a file with the given text content."""
    headers = {"Content-Type": content_type}
    r = webdav_request("PUT", path, headers=headers, data=content.encode("utf-8"))
    return _json({"status": "created", "path": path, "status_code": r.status_code})

@mcp.tool()
def nc_files_mkdir(path: str) -> str:
    """Create a new directory (folder). Parent dirs must exist."""
    r = webdav_request("MKCOL", path)
    return _json({"status": "created", "path": path, "status_code": r.status_code})

@mcp.tool()
def nc_files_delete(path: str) -> str:
    """Delete a file or folder (recursively)."""
    r = webdav_request("DELETE", path)
    return _json({"status": "deleted", "path": path, "status_code": r.status_code})

@mcp.tool()
def nc_files_move(source: str, destination: str, overwrite: bool = False) -> str:
    """Move a file or folder to a new location."""
    headers = {
        "Destination": webdav_url(destination),
        "Overwrite": "T" if overwrite else "F",
    }
    r = webdav_request("MOVE", source, headers=headers)
    return _json({"status": "moved", "from": source, "to": destination, "status_code": r.status_code})

@mcp.tool()
def nc_files_copy(source: str, destination: str, overwrite: bool = False) -> str:
    """Copy a file or folder to a new location."""
    headers = {
        "Destination": webdav_url(destination),
        "Overwrite": "T" if overwrite else "F",
    }
    r = webdav_request("COPY", source, headers=headers)
    return _json({"status": "copied", "from": source, "to": destination, "status_code": r.status_code})

@mcp.tool()
def nc_files_search(query: str, path: str = "/", limit: int = 50) -> str:
    """Search for files by name. Uses WebDAV SEARCH with LIKE operator."""
    user = CREDS["username"]
    search_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<d:searchrequest xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:basicsearch>
    <d:select>
      <d:prop>
        <d:getlastmodified/><d:getetag/><d:getcontenttype/>
        <d:getcontentlength/><d:resourcetype/>
        <oc:fileid/><oc:size/><oc:favorite/>
      </d:prop>
    </d:select>
    <d:from>
      <d:scope><d:href>/files/{user}{path}</d:href><d:depth>infinity</d:depth></d:scope>
    </d:from>
    <d:where>
      <d:like>
        <d:prop><d:displayname/></d:prop>
        <d:literal>%{query}%</d:literal>
      </d:like>
    </d:where>
    <d:limit><d:nresults>{limit}</d:nresults></d:limit>
  </d:basicsearch>
</d:searchrequest>"""
    url = f"{BASE_URL}/remote.php/dav/"
    r = requests.request("SEARCH", url, auth=AUTH, headers={"Content-Type": "application/xml"}, data=search_xml, timeout=30)
    r.raise_for_status()
    return _json(parse_propfind(r.text))

@mcp.tool()
def nc_files_favorite(path: str, favorite: bool = True) -> str:
    """Set or unset a file/folder as favorite."""
    fav_val = "1" if favorite else "0"
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<d:propertyupdate xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns">
  <d:set><d:prop><oc:favorite>{fav_val}</oc:favorite></d:prop></d:set>
</d:propertyupdate>"""
    r = webdav_request("PROPPATCH", path, headers={"Content-Type": "application/xml"}, data=body)
    return _json({"status": "updated", "path": path, "favorite": favorite})

@mcp.tool()
def nc_files_favorites(path: str = "/") -> str:
    """List all favorite files and folders."""
    user = CREDS["username"]
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<oc:filter-files xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:prop>
    <d:getlastmodified/><d:getetag/><d:getcontenttype/>
    <d:getcontentlength/><d:resourcetype/>
    <oc:fileid/><oc:size/><oc:favorite/>
  </d:prop>
  <oc:filter-rules><oc:favorite>1</oc:favorite></oc:filter-rules>
</oc:filter-files>"""
    url = f"{BASE_URL}/remote.php/dav/files/{user}{path}"
    r = requests.request("REPORT", url, auth=AUTH, headers={"Content-Type": "application/xml", "Depth": "infinity"}, data=body, timeout=30)
    r.raise_for_status()
    return _json(parse_propfind(r.text))

# ===== TRASHBIN =====

@mcp.tool()
def nc_trash_list() -> str:
    """List items in the trashbin."""
    user = CREDS["username"]
    url = f"{BASE_URL}/remote.php/dav/trashbin/{user}/trash"
    trash_props = """<?xml version="1.0" encoding="UTF-8"?>
<d:propfind xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:nc="http://nextcloud.org/ns">
  <d:prop>
    <d:getlastmodified/><d:getcontentlength/><d:resourcetype/>
    <nc:trashbin-filename/><nc:trashbin-original-location/><nc:trashbin-deletion-time/>
  </d:prop>
</d:propfind>"""
    r = requests.request("PROPFIND", url, auth=AUTH, headers={"Depth": "1", "Content-Type": "application/xml"}, data=trash_props, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    items = []
    for resp in root.findall("d:response", NS)[1:]:
        props = resp.find(".//d:prop", NS)
        if props is None:
            continue
        items.append({
            "href": resp.findtext("d:href", "", NS),
            "filename": props.findtext("nc:trashbin-filename", "", NS),
            "original_location": props.findtext("nc:trashbin-original-location", "", NS),
            "deletion_time": props.findtext("nc:trashbin-deletion-time", "", NS),
            "size": int(props.findtext("d:getcontentlength", "0", NS) or "0"),
        })
    return _json(items)

@mcp.tool()
def nc_trash_restore(trash_item: str) -> str:
    """Restore an item from trashbin. Use href from nc_trash_list."""
    user = CREDS["username"]
    dest = f"{BASE_URL}/remote.php/dav/trashbin/{user}/restore/{Path(trash_item).name}"
    url = f"{BASE_URL}{trash_item}"
    r = requests.request("MOVE", url, auth=AUTH, headers={"Destination": dest}, timeout=30)
    r.raise_for_status()
    return _json({"status": "restored", "item": trash_item})

@mcp.tool()
def nc_trash_empty() -> str:
    """Empty the entire trashbin permanently."""
    user = CREDS["username"]
    url = f"{BASE_URL}/remote.php/dav/trashbin/{user}/trash"
    r = requests.delete(url, auth=AUTH, timeout=30)
    r.raise_for_status()
    return _json({"status": "trashbin emptied"})

# ===== SHARES =====

@mcp.tool()
def nc_shares_list(path: str = "", shared_with_me: bool = False) -> str:
    """List all shares, optionally filtered by path."""
    params = {}
    if path:
        params["path"] = path
    endpoint = "ocs/v2.php/apps/files_sharing/api/v1/shares"
    if shared_with_me:
        endpoint += "?shared_with_me=true"
    return _json(ocs_get(endpoint, params))

@mcp.tool()
def nc_share_get(share_id: int) -> str:
    """Get details of a specific share."""
    return _json(ocs_get(f"ocs/v2.php/apps/files_sharing/api/v1/shares/{share_id}"))

@mcp.tool()
def nc_share_create(
    path: str,
    share_type: int,
    share_with: str = "",
    permissions: int = 1,
    password: str = "",
    expire_date: str = "",
    note: str = "",
    label: str = "",
) -> str:
    """Create a share. share_type: 0=user, 1=group, 3=public link, 4=email, 6=federated.
    permissions: 1=read, 2=update, 4=create, 8=delete, 16=share, 31=all."""
    data = {"path": path, "shareType": share_type, "permissions": permissions}
    if share_with:
        data["shareWith"] = share_with
    if password:
        data["password"] = password
    if expire_date:
        data["expireDate"] = expire_date
    if note:
        data["note"] = note
    if label:
        data["label"] = label
    return _json(ocs_post("ocs/v2.php/apps/files_sharing/api/v1/shares", data))

@mcp.tool()
def nc_share_update(share_id: int, permissions: int = None, password: str = None, expire_date: str = None, note: str = None) -> str:
    """Update an existing share's permissions, password, expiry, or note."""
    data = {}
    if permissions is not None:
        data["permissions"] = permissions
    if password is not None:
        data["password"] = password
    if expire_date is not None:
        data["expireDate"] = expire_date
    if note is not None:
        data["note"] = note
    return _json(ocs_put(f"ocs/v2.php/apps/files_sharing/api/v1/shares/{share_id}", data))

@mcp.tool()
def nc_share_delete(share_id: int) -> str:
    """Delete (unshare) a share."""
    return _json(ocs_delete(f"ocs/v2.php/apps/files_sharing/api/v1/shares/{share_id}"))

# ===== USERS =====

@mcp.tool()
def nc_users_list(search: str = "", limit: int = 50, offset: int = 0) -> str:
    """List all users, optionally filtered by search term."""
    params = {"limit": limit, "offset": offset}
    if search:
        params["search"] = search
    return _json(ocs_get("ocs/v1.php/cloud/users", params))

@mcp.tool()
def nc_user_get(userid: str) -> str:
    """Get detailed info about a specific user."""
    return _json(ocs_get(f"ocs/v1.php/cloud/users/{userid}"))

@mcp.tool()
def nc_user_create(userid: str, password: str, display_name: str = "", email: str = "", groups: str = "", quota: str = "") -> str:
    """Create a new user. groups = comma-separated group IDs."""
    data = {"userid": userid, "password": password}
    if display_name:
        data["displayName"] = display_name
    if email:
        data["email"] = email
    if groups:
        for g in groups.split(","):
            data.setdefault("groups[]", [])
            if isinstance(data["groups[]"], list):
                data["groups[]"] = g.strip()
    if quota:
        data["quota"] = quota
    return _json(ocs_post("ocs/v1.php/cloud/users", data))

@mcp.tool()
def nc_user_update(userid: str, key: str, value: str) -> str:
    """Update a user field. key: email, quota, displayname, phone, address, website, twitter, password."""
    return _json(ocs_put(f"ocs/v1.php/cloud/users/{userid}", {"key": key, "value": value}))

@mcp.tool()
def nc_user_enable(userid: str) -> str:
    """Enable a disabled user."""
    return _json(ocs_put(f"ocs/v1.php/cloud/users/{userid}/enable"))

@mcp.tool()
def nc_user_disable(userid: str) -> str:
    """Disable a user (cannot login, data preserved)."""
    return _json(ocs_put(f"ocs/v1.php/cloud/users/{userid}/disable"))

@mcp.tool()
def nc_user_delete(userid: str) -> str:
    """Delete a user permanently. WARNING: this removes all their data."""
    return _json(ocs_delete(f"ocs/v1.php/cloud/users/{userid}"))

@mcp.tool()
def nc_user_groups(userid: str) -> str:
    """List groups a user belongs to."""
    return _json(ocs_get(f"ocs/v1.php/cloud/users/{userid}/groups"))

@mcp.tool()
def nc_user_add_to_group(userid: str, groupid: str) -> str:
    """Add a user to a group."""
    return _json(ocs_post(f"ocs/v1.php/cloud/users/{userid}/groups", {"groupid": groupid}))

@mcp.tool()
def nc_user_remove_from_group(userid: str, groupid: str) -> str:
    """Remove a user from a group."""
    return _json(ocs_delete(f"ocs/v1.php/cloud/users/{userid}/groups"))

# ===== GROUPS =====

@mcp.tool()
def nc_groups_list(search: str = "", limit: int = 50, offset: int = 0) -> str:
    """List all groups, optionally filtered by search term."""
    params = {"limit": limit, "offset": offset}
    if search:
        params["search"] = search
    return _json(ocs_get("ocs/v1.php/cloud/groups", params))

@mcp.tool()
def nc_group_create(groupid: str) -> str:
    """Create a new group."""
    return _json(ocs_post("ocs/v1.php/cloud/groups", {"groupid": groupid}))

@mcp.tool()
def nc_group_members(groupid: str) -> str:
    """List members of a group."""
    return _json(ocs_get(f"ocs/v1.php/cloud/groups/{groupid}"))

@mcp.tool()
def nc_group_delete(groupid: str) -> str:
    """Delete a group."""
    return _json(ocs_delete(f"ocs/v1.php/cloud/groups/{groupid}"))

# ===== APPS =====

@mcp.tool()
def nc_apps_list(filter: str = "") -> str:
    """List installed apps. filter: 'enabled' or 'disabled' (empty = all)."""
    params = {}
    if filter:
        params["filter"] = filter
    return _json(ocs_get("ocs/v1.php/cloud/apps", params))

@mcp.tool()
def nc_app_info(appid: str) -> str:
    """Get detailed info about an installed app."""
    return _json(ocs_get(f"ocs/v1.php/cloud/apps/{appid}"))

@mcp.tool()
def nc_app_enable(appid: str) -> str:
    """Enable an app."""
    return _json(ocs_post(f"ocs/v1.php/cloud/apps/{appid}"))

@mcp.tool()
def nc_app_disable(appid: str) -> str:
    """Disable an app."""
    return _json(ocs_delete(f"ocs/v1.php/cloud/apps/{appid}"))

# ===== NOTIFICATIONS =====

@mcp.tool()
def nc_notifications_list() -> str:
    """List all notifications for the current user."""
    return _json(ocs_get("ocs/v2.php/apps/notifications/api/v2/notifications"))

@mcp.tool()
def nc_notification_delete(notification_id: int) -> str:
    """Dismiss a specific notification."""
    return _json(ocs_delete(f"ocs/v2.php/apps/notifications/api/v2/notifications/{notification_id}"))

@mcp.tool()
def nc_notifications_delete_all() -> str:
    """Dismiss all notifications."""
    return _json(ocs_delete("ocs/v2.php/apps/notifications/api/v2/notifications"))

# ===== ACTIVITY =====

@mcp.tool()
def nc_activity_list(limit: int = 50, since: int = 0, sort: str = "desc", object_type: str = "", object_id: str = "") -> str:
    """List recent activity. object_type: 'files', 'calendar', etc. since: activity ID to start after."""
    params = {"limit": limit, "sort": sort}
    if since:
        params["since"] = since
    if object_type:
        params["object_type"] = object_type
    if object_id:
        params["object_id"] = object_id
    return _json(ocs_get("ocs/v2.php/apps/activity/api/v2/activity", params))

# ===== USER STATUS =====

@mcp.tool()
def nc_status_get() -> str:
    """Get current user's status (online/away/dnd/invisible/offline)."""
    return _json(ocs_get("ocs/v2.php/apps/user_status/api/v1/user_status"))

@mcp.tool()
def nc_status_set(status_type: str) -> str:
    """Set user status. status_type: online, away, dnd, invisible, offline."""
    return _json(ocs_put("ocs/v2.php/apps/user_status/api/v1/user_status/status", {"statusType": status_type}))

@mcp.tool()
def nc_status_message(message: str, icon: str = "") -> str:
    """Set a custom status message with optional emoji icon."""
    data = {"message": message}
    if icon:
        data["statusIcon"] = icon
    return _json(ocs_put("ocs/v2.php/apps/user_status/api/v1/user_status/message/custom", data))

@mcp.tool()
def nc_status_clear() -> str:
    """Clear the current status message."""
    return _json(ocs_delete("ocs/v2.php/apps/user_status/api/v1/user_status/message"))

# ===== TALK (Spreed) =====

@mcp.tool()
def nc_talk_conversations() -> str:
    """List all Talk conversations."""
    return _json(ocs_get("ocs/v2.php/apps/spreed/api/v4/room"))

@mcp.tool()
def nc_talk_conversation_get(token: str) -> str:
    """Get details of a specific Talk conversation by its token."""
    return _json(ocs_get(f"ocs/v2.php/apps/spreed/api/v4/room/{token}"))

@mcp.tool()
def nc_talk_create(room_type: int, room_name: str = "", invite: str = "") -> str:
    """Create a Talk conversation. room_type: 1=one-on-one, 2=group, 3=public."""
    data = {"roomType": room_type}
    if room_name:
        data["roomName"] = room_name
    if invite:
        data["invite"] = invite
    return _json(ocs_post("ocs/v2.php/apps/spreed/api/v4/room", data))

@mcp.tool()
def nc_talk_messages(token: str, limit: int = 100, look_into_future: int = 0, last_known_message_id: int = 0) -> str:
    """Get chat messages from a Talk conversation."""
    params = {"limit": limit, "lookIntoFuture": look_into_future}
    if last_known_message_id:
        params["lastKnownMessageId"] = last_known_message_id
    return _json(ocs_get(f"ocs/v2.php/apps/spreed/api/v4/chat/{token}", params))

@mcp.tool()
def nc_talk_send(token: str, message: str, reply_to: int = 0) -> str:
    """Send a chat message to a Talk conversation."""
    data = {"message": message}
    if reply_to:
        data["replyTo"] = reply_to
    return _json(ocs_post(f"ocs/v2.php/apps/spreed/api/v4/chat/{token}", data))

@mcp.tool()
def nc_talk_delete_message(token: str, message_id: int) -> str:
    """Delete a chat message."""
    return _json(ocs_delete(f"ocs/v2.php/apps/spreed/api/v4/chat/{token}/{message_id}"))

# ===== GROUPFOLDERS =====

@mcp.tool()
def nc_groupfolders_list() -> str:
    """List all group folders."""
    return _json(ocs_get("index.php/apps/groupfolders/folders"))

@mcp.tool()
def nc_groupfolder_get(folder_id: int) -> str:
    """Get details of a specific group folder."""
    return _json(ocs_get(f"index.php/apps/groupfolders/folders/{folder_id}"))

@mcp.tool()
def nc_groupfolder_create(mountpoint: str) -> str:
    """Create a new group folder with the given name."""
    return _json(ocs_post("index.php/apps/groupfolders/folders", {"mountpoint": mountpoint}))

@mcp.tool()
def nc_groupfolder_delete(folder_id: int) -> str:
    """Delete a group folder."""
    return _json(ocs_delete(f"index.php/apps/groupfolders/folders/{folder_id}"))

@mcp.tool()
def nc_groupfolder_add_group(folder_id: int, group: str) -> str:
    """Add a group to a group folder."""
    return _json(ocs_post(f"index.php/apps/groupfolders/folders/{folder_id}/groups", {"group": group}))

@mcp.tool()
def nc_groupfolder_remove_group(folder_id: int, group: str) -> str:
    """Remove a group from a group folder."""
    return _json(ocs_delete(f"index.php/apps/groupfolders/folders/{folder_id}/groups/{group}"))

@mcp.tool()
def nc_groupfolder_set_quota(folder_id: int, quota: int) -> str:
    """Set quota for a group folder in bytes. -3 = unlimited."""
    return _json(ocs_post(f"index.php/apps/groupfolders/folders/{folder_id}/quota", {"quota": quota}))

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
