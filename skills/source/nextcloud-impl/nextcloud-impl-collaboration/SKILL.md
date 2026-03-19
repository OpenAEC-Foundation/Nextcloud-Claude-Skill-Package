---
name: nextcloud-impl-collaboration
description: >
  Use when implementing file sharing, creating notifications, publishing activity events, or building collaboration features.
  Prevents incorrect share permission bitmasks, unregistered notifiers, and missing activity providers.
  Covers OCS Share API with share types and permissions, notification system with INotificationManager and INotifier, activity stream with IActivityManager, and push notifications.
  Keywords: Share API, INotificationManager, INotifier, IActivityManager, permissions, share type, push notifications, activity.
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-impl-collaboration

## Quick Reference

### Share Types

| Type | Value | `shareWith` Parameter |
|------|-------|-----------------------|
| User | 0 | User ID |
| Group | 1 | Group ID |
| Public link | 3 | (omit entirely) |
| Email | 4 | Email address |
| Federated | 6 | `user@remote.server` |
| Circle | 7 | Circle ID |
| Talk conversation | 10 | Conversation token |

### Permission Bitmask

| Permission | Value | Combine with `\|` |
|-----------|-------|-------------------|
| Read | 1 | Always included |
| Update | 2 | Edit file content |
| Create | 4 | Upload to folder |
| Delete | 8 | Remove files |
| Share | 16 | Re-share |
| All | 31 | `1\|2\|4\|8\|16` |

### Share API Base URL

```
/ocs/v2.php/apps/files_sharing/api/v1/shares
```

**ALWAYS** include the `OCS-APIRequest: true` header on every OCS request.

**ALWAYS** use API v2 (`/ocs/v2.php/`) -- v1 returns 100 for success instead of standard HTTP codes.

### Notification Interfaces

| Interface | Purpose |
|-----------|---------|
| `OCP\Notification\IManager` | Create and dispatch notifications |
| `OCP\Notification\INotifier` | Prepare notifications for display (translation/rendering) |
| `OCP\Notification\INotification` | Single notification object |
| `OCP\Notification\UnknownNotificationException` | Thrown when notifier cannot handle a notification |

### Activity Interfaces

| Interface | Purpose |
|-----------|---------|
| `OCP\Activity\IManager` | Generate and publish activity events |
| `OCP\Activity\IEvent` | Single activity event object |
| `OCP\Activity\IProvider` | Render activity events for display |

---

## Decision Trees

### Which Share Type to Use?

```
Sharing with a specific Nextcloud user?
  YES --> shareType=0, shareWith=userId
  NO --> Sharing with a group?
    YES --> shareType=1, shareWith=groupId
    NO --> Creating a public link?
      YES --> shareType=3, do NOT set shareWith
      NO --> Sharing via email?
        YES --> shareType=4, shareWith=email
        NO --> Federated (remote server)?
          YES --> shareType=6, shareWith=user@server
          NO --> Talk conversation?
            YES --> shareType=10, shareWith=conversationToken
```

### Notification vs Activity?

```
Is this a real-time alert requiring user action?
  YES --> Use INotificationManager (appears in notification bell)
  NO --> Is this a historical record of something that happened?
    YES --> Use IActivityManager (appears in activity stream)
    NO --> Both? Use BOTH -- they are independent systems
```

---

## Essential Patterns

### Pattern 1: Create a User Share via OCS

```php
use OCP\Http\Client\IClientService;

$client = $clientService->newClient();
$response = $client->post(
    $baseUrl . '/ocs/v2.php/apps/files_sharing/api/v1/shares',
    [
        'headers' => [
            'OCS-APIRequest' => 'true',
            'Content-Type' => 'application/x-www-form-urlencoded',
        ],
        'auth' => [$username, $password],
        'body' => [
            'path' => '/Documents/report.pdf',
            'shareType' => 0,
            'shareWith' => 'targetuser',
            'permissions' => 1 | 2,  // Read + Update
        ],
    ]
);
```

### Pattern 2: Create a Public Link with Expiry

```php
$response = $client->post(
    $baseUrl . '/ocs/v2.php/apps/files_sharing/api/v1/shares',
    [
        'headers' => ['OCS-APIRequest' => 'true'],
        'auth' => [$username, $password],
        'body' => [
            'path' => '/Documents/report.pdf',
            'shareType' => 3,
            'password' => 'SecurePass123!',
            'expireDate' => '2025-12-31',
            'permissions' => 1,  // Read-only
        ],
    ]
);
// The response contains the share token in ocs.data.token
```

### Pattern 3: Share Attributes (Disable Download)

```php
$body = [
    'path' => '/Documents/report.pdf',
    'shareType' => 3,
    'permissions' => 1,
    'attributes' => json_encode([
        ['scope' => 'permissions', 'key' => 'download', 'value' => false],
    ]),
];
```

### Pattern 4: Create and Dispatch a Notification

```php
use OCP\Notification\IManager as INotificationManager;

class MyService {
    public function __construct(
        private INotificationManager $notificationManager,
    ) {}

    public function notifyUser(string $userId, string $itemId, string $itemName): void {
        $notification = $this->notificationManager->createNotification();
        $notification->setApp('myapp')
            ->setUser($userId)
            ->setDateTime(new \DateTime())
            ->setObject('item', $itemId)
            ->setSubject('new_item', ['itemName' => $itemName]);

        $this->notificationManager->notify($notification);
    }
}
```

**NEVER** put translated strings in `setSubject()` -- use a language key. Translation happens in the `INotifier::prepare()` method.

### Pattern 5: INotifier Implementation

```php
namespace OCA\MyApp\Notification;

use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\L10N\IFactory;
use OCP\Notification\INotification;
use OCP\Notification\INotifier;
use OCP\Notification\UnknownNotificationException;

class Notifier implements INotifier {
    public function __construct(
        private IFactory $l10nFactory,
        private IURLGenerator $urlGenerator,
    ) {}

    public function getID(): string {
        return 'myapp';
    }

    public function getName(): string {
        return $this->l10nFactory->get('myapp')->t('My App');
    }

    public function prepare(
        INotification $notification,
        string $languageCode,
    ): INotification {
        if ($notification->getApp() !== 'myapp') {
            throw new UnknownNotificationException();
        }

        $l = $this->l10nFactory->get('myapp', $languageCode);
        $params = $notification->getSubjectParameters();

        switch ($notification->getSubject()) {
            case 'new_item':
                $notification->setRichSubject(
                    $l->t('New item created: {item}'),
                    [
                        'item' => [
                            'type' => 'highlight',
                            'id' => $notification->getObjectId(),
                            'name' => $params['itemName'],
                        ],
                    ]
                );
                break;
            default:
                throw new UnknownNotificationException();
        }

        $notification->setIcon(
            $this->urlGenerator->imagePath('myapp', 'app-dark.svg')
        );

        return $notification;
    }
}
```

**ALWAYS** throw `UnknownNotificationException` when `getApp()` does not match or `getSubject()` is unrecognized -- this lets the next notifier in the chain handle it.

### Pattern 6: Register the Notifier

```php
// lib/AppInfo/Application.php
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        $context->registerNotifierService(Notifier::class);
    }

    public function boot(IBootContext $context): void {}
}
```

### Pattern 7: Notification with Actions

```php
// In prepare() method, add actions to the notification:
$acceptAction = $notification->createAction();
$acceptAction->setLabel('accept')
    ->setLink(
        $this->urlGenerator->linkToOCSRoute(
            'myapp.api.acceptItem',
            ['id' => $notification->getObjectId()]
        ),
        'POST'
    );
$notification->addAction($acceptAction);
```

### Pattern 8: Mark Notification as Processed

```php
// When the user acts on the item, remove the notification:
$notification = $this->notificationManager->createNotification();
$notification->setApp('myapp')
    ->setUser($userId)
    ->setObject('item', $itemId);
$this->notificationManager->markProcessed($notification);
```

### Pattern 9: Publish an Activity Event

```php
use OCP\Activity\IManager as IActivityManager;

class MyService {
    public function __construct(
        private IActivityManager $activityManager,
    ) {}

    public function logItemCreated(string $userId, string $filename): void {
        $event = $this->activityManager->generateEvent();
        $event->setApp('myapp')
            ->setType('myapp_updates')
            ->setAffectedUser($userId)
            ->setAuthor($userId)
            ->setTimestamp(time())
            ->setSubject('item_created', ['filename' => $filename])
            ->setObject('file', 42, $filename);

        $this->activityManager->publish($event);
    }
}
```

### Pattern 10: Push Notification Defer/Flush

```php
// When sending multiple notifications in a batch:
$this->notificationManager->defer();

foreach ($users as $userId) {
    $notification = $this->notificationManager->createNotification();
    $notification->setApp('myapp')
        ->setUser($userId)
        ->setDateTime(new \DateTime())
        ->setObject('batch', $batchId)
        ->setSubject('batch_ready', ['batchName' => $name]);
    $this->notificationManager->notify($notification);
}

$this->notificationManager->flush();
```

**ALWAYS** use `defer()`/`flush()` when sending notifications to multiple users in a loop -- this batches push notifications into a single request instead of one per user.

**NEVER** send individual push notifications inside a loop without `defer()`/`flush()` -- this causes N separate push requests and severe performance degradation.

---

## Critical Rules

- **ALWAYS** use OCS API v2 (`/ocs/v2.php/`) for the Share API -- v1 uses non-standard status codes.
- **ALWAYS** include the `OCS-APIRequest: true` header on Share API requests.
- **NEVER** set `shareWith` for public link shares (type 3) -- it is ignored and causes confusion.
- **NEVER** put translated user-facing strings in `setSubject()` -- use language keys and translate in `prepare()`.
- **ALWAYS** throw `UnknownNotificationException` in `prepare()` for unrecognized apps or subjects.
- **ALWAYS** register your `INotifier` via `$context->registerNotifierService()` in `Application::register()`.
- **ALWAYS** use `defer()`/`flush()` when notifying multiple users in a batch.
- **NEVER** forget to call `markProcessed()` when a user acts on a notification -- stale notifications degrade UX.
- **ALWAYS** set both `setAffectedUser()` and `setAuthor()` on activity events -- affected user sees it in their stream, author is who performed the action.

---

## Reference Links

- [references/methods.md](references/methods.md) -- Share API endpoints, Notification interfaces, Activity interfaces
- [references/examples.md](references/examples.md) -- Share CRUD operations, notification lifecycle, activity events
- [references/anti-patterns.md](references/anti-patterns.md) -- Collaboration mistakes and corrections

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/notifications.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/activities.html
- https://docs.nextcloud.com/server/latest/developer_manual/client_apis/OCS/ocs-share-api.html
- https://github.com/nextcloud/notifications/blob/master/docs/admin-notifications.md
