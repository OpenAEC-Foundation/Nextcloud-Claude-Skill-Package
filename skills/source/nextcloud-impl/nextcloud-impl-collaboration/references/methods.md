# Collaboration Methods Reference

## Share API (OCS Endpoints)

Base URL: `/ocs/v2.php/apps/files_sharing/api/v1`

### Share CRUD Endpoints

| Verb | Endpoint | Description |
|------|----------|-------------|
| GET | `/shares` | List all shares by the current user |
| GET | `/shares/{shareId}` | Get a specific share by ID |
| GET | `/shares?path={path}` | Get shares for a specific file/folder |
| GET | `/shares?shared_with_me=true` | List shares received by the current user |
| POST | `/shares` | Create a new share |
| PUT | `/shares/{shareId}` | Update an existing share |
| DELETE | `/shares/{shareId}` | Delete a share |

### Create Share Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | YES | File/folder path relative to user root |
| `shareType` | int | YES | Share type (0, 1, 3, 4, 6, 7, 10) |
| `shareWith` | string | Depends | Target (user ID, group ID, email, etc.) |
| `permissions` | int | NO | Permission bitmask (default: 31 for folders, 19 for files) |
| `password` | string | NO | Password protection (public links) |
| `expireDate` | string | NO | Expiration date in `YYYY-MM-DD` format |
| `publicUpload` | bool | NO | Allow uploads on public link folders |
| `note` | string | NO | Note to share recipient |
| `label` | string | NO | Label for the share (public links) |
| `attributes` | string | NO | JSON-encoded share attributes array |

### Update Share Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `permissions` | int | New permission bitmask |
| `password` | string | New password (empty string to remove) |
| `expireDate` | string | New expiration date |
| `note` | string | Updated note |
| `label` | string | Updated label |

### Share Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Share ID |
| `share_type` | int | Share type |
| `uid_owner` | string | Owner user ID |
| `uid_file_owner` | string | File owner user ID |
| `share_with` | string | Share recipient |
| `path` | string | File path |
| `permissions` | int | Permission bitmask |
| `token` | string | Public link token (type 3 only) |
| `url` | string | Full public link URL (type 3 only) |
| `expiration` | string | Expiration date or null |

### Share Type Reference

| Constant | Value | `shareWith` Value |
|----------|-------|-------------------|
| `SHARE_TYPE_USER` | 0 | Nextcloud user ID |
| `SHARE_TYPE_GROUP` | 1 | Nextcloud group ID |
| `SHARE_TYPE_LINK` | 3 | Not used -- omit |
| `SHARE_TYPE_EMAIL` | 4 | Email address |
| `SHARE_TYPE_REMOTE` | 6 | `user@remote.nextcloud.com` |
| `SHARE_TYPE_CIRCLE` | 7 | Circle ID |
| `SHARE_TYPE_ROOM` | 10 | Talk conversation token |

### Permission Bitmask Reference

| Constant | Value | Meaning |
|----------|-------|---------|
| `PERMISSION_READ` | 1 | View the file |
| `PERMISSION_UPDATE` | 2 | Edit the file |
| `PERMISSION_CREATE` | 4 | Create files in folder |
| `PERMISSION_DELETE` | 8 | Delete files |
| `PERMISSION_SHARE` | 16 | Re-share the item |
| `PERMISSION_ALL` | 31 | All permissions combined |

Common combinations:
- Read-only: `1`
- Read + Edit: `1 | 2` = `3`
- Read + Upload (folder): `1 | 4` = `5`
- Full access: `31`

---

## Notification API (INotificationManager)

### OCP\Notification\IManager

| Method | Return | Description |
|--------|--------|-------------|
| `createNotification()` | `INotification` | Create a new notification object |
| `notify(INotification $notification)` | `void` | Dispatch the notification |
| `markProcessed(INotification $notification)` | `void` | Remove matching notifications |
| `getCount(INotification $notification)` | `int` | Count matching notifications |
| `defer()` | `void` | Start batching push notifications |
| `flush()` | `void` | Send all deferred push notifications |

### OCP\Notification\INotification

| Method | Parameter | Description |
|--------|-----------|-------------|
| `setApp(string $app)` | App ID | Identifies which app created it |
| `setUser(string $user)` | User ID | Target user |
| `setDateTime(\DateTime $dt)` | DateTime | When the event occurred |
| `setObject(string $type, string $id)` | Type + ID | Object reference (e.g., `'item'`, `'42'`) |
| `setSubject(string $subject, array $params)` | Key + params | Subject identifier (NOT translated text) |
| `setMessage(string $message, array $params)` | Key + params | Optional longer message |
| `setLink(string $link)` | URL | Link to the relevant item |
| `setIcon(string $icon)` | URL | Notification icon URL |
| `setRichSubject(string $subject, array $params)` | Translated + rich params | Set translated rich subject in `prepare()` |
| `setRichMessage(string $message, array $params)` | Translated + rich params | Set translated rich message in `prepare()` |
| `createAction()` | -- | Returns `IAction` for notification buttons |
| `addAction(IAction $action)` | IAction | Add an action button |
| `getApp()` | -- | Returns app ID |
| `getSubject()` | -- | Returns subject key |
| `getSubjectParameters()` | -- | Returns subject parameters array |
| `getObjectType()` | -- | Returns object type |
| `getObjectId()` | -- | Returns object ID |

### OCP\Notification\IAction

| Method | Parameter | Description |
|--------|-----------|-------------|
| `setLabel(string $label)` | Label key | Action button label (translated in notifier) |
| `setLink(string $link, string $verb)` | URL + HTTP verb | Endpoint to call when clicked |
| `setPrimary(bool $primary)` | bool | Make this the primary action |
| `setParsedLabel(string $label)` | Translated label | Set translated label in `prepare()` |

### OCP\Notification\INotifier

| Method | Return | Description |
|--------|--------|-------------|
| `getID()` | `string` | Unique notifier identifier |
| `getName()` | `string` | Human-readable notifier name |
| `prepare(INotification $notification, string $languageCode)` | `INotification` | Prepare notification for display |

Registration: `$context->registerNotifierService(MyNotifier::class)` in `Application::register()`.

---

## Activity API (IActivityManager)

### OCP\Activity\IManager

| Method | Return | Description |
|--------|--------|-------------|
| `generateEvent()` | `IEvent` | Create a new activity event |
| `publish(IEvent $event)` | `void` | Publish the event to activity stream |

### OCP\Activity\IEvent

| Method | Parameter | Description |
|--------|-----------|-------------|
| `setApp(string $app)` | App ID | Which app generated the event |
| `setType(string $type)` | Activity type | Category for filtering (e.g., `'myapp_updates'`) |
| `setAffectedUser(string $user)` | User ID | Who sees this in their activity stream |
| `setAuthor(string $author)` | User ID | Who performed the action |
| `setTimestamp(int $timestamp)` | Unix timestamp | When the action occurred |
| `setSubject(string $subject, array $params)` | Key + params | Subject identifier (NOT translated) |
| `setMessage(string $message, array $params)` | Key + params | Optional longer message |
| `setObject(string $type, int $id, string $name)` | Type + ID + name | Related object |
| `setLink(string $link)` | URL | Link to the related item |

### OCP\Activity\IProvider

| Method | Return | Description |
|--------|--------|-------------|
| `parse(string $language, IEvent $event)` | `IEvent` | Prepare event for display (translation/rich objects) |

### Activity Registration (info.xml)

```xml
<activity>
    <settings>
        <setting>OCA\MyApp\Activity\Setting</setting>
    </settings>
    <providers>
        <provider>OCA\MyApp\Activity\Provider</provider>
    </providers>
</activity>
```
