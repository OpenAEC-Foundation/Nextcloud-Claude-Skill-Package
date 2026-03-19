# Collaboration Examples Reference

## Share API CRUD Examples

### Create a User Share

```bash
curl -X POST "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares" \
  -H "OCS-APIRequest: true" \
  -u admin:password \
  -d "path=/Documents/report.pdf" \
  -d "shareType=0" \
  -d "shareWith=john" \
  -d "permissions=3"
```

Response (HTTP 200):
```json
{
  "ocs": {
    "meta": {"status": "ok", "statuscode": 200},
    "data": {
      "id": 42,
      "share_type": 0,
      "uid_owner": "admin",
      "share_with": "john",
      "path": "/Documents/report.pdf",
      "permissions": 3,
      "token": null
    }
  }
}
```

### Create a Public Link Share

```bash
curl -X POST "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares" \
  -H "OCS-APIRequest: true" \
  -u admin:password \
  -d "path=/Documents/report.pdf" \
  -d "shareType=3" \
  -d "password=SecurePass123!" \
  -d "expireDate=2025-12-31" \
  -d "permissions=1"
```

Response includes `token` and `url`:
```json
{
  "ocs": {
    "data": {
      "id": 43,
      "share_type": 3,
      "token": "abc123XYZ",
      "url": "https://cloud.example.com/s/abc123XYZ",
      "permissions": 1,
      "expiration": "2025-12-31 00:00:00"
    }
  }
}
```

### Create an Email Share

```bash
curl -X POST "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares" \
  -H "OCS-APIRequest: true" \
  -u admin:password \
  -d "path=/Documents/report.pdf" \
  -d "shareType=4" \
  -d "shareWith=external@example.com" \
  -d "permissions=1"
```

### List All Shares for a File

```bash
curl -X GET "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares?path=/Documents/report.pdf" \
  -H "OCS-APIRequest: true" \
  -u admin:password
```

### Update a Share (Change Permissions)

```bash
curl -X PUT "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares/42" \
  -H "OCS-APIRequest: true" \
  -u admin:password \
  -d "permissions=1"
```

### Delete a Share

```bash
curl -X DELETE "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares/42" \
  -H "OCS-APIRequest: true" \
  -u admin:password
```

### Share with Download Disabled

```bash
curl -X POST "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares" \
  -H "OCS-APIRequest: true" \
  -u admin:password \
  -d "path=/Documents/report.pdf" \
  -d "shareType=3" \
  -d "permissions=1" \
  -d 'attributes=[{"scope":"permissions","key":"download","value":false}]'
```

---

## Notification Examples

### Complete Notification Lifecycle

#### Step 1: Create and Dispatch

```php
use OCP\Notification\IManager as INotificationManager;

class ItemService {
    public function __construct(
        private INotificationManager $notificationManager,
        private IURLGenerator $urlGenerator,
    ) {}

    public function createItem(string $userId, string $title): Item {
        $item = $this->mapper->insert(new Item($title, $userId));

        // Notify collaborators
        $collaborators = $this->getCollaborators($item->getId());
        $this->notificationManager->defer();

        foreach ($collaborators as $collaboratorId) {
            $notification = $this->notificationManager->createNotification();
            $notification->setApp('myapp')
                ->setUser($collaboratorId)
                ->setDateTime(new \DateTime())
                ->setObject('item', (string)$item->getId())
                ->setSubject('item_created', [
                    'authorId' => $userId,
                    'itemTitle' => $title,
                ]);
            $this->notificationManager->notify($notification);
        }

        $this->notificationManager->flush();

        return $item;
    }
}
```

#### Step 2: Prepare for Display (Notifier)

```php
namespace OCA\MyApp\Notification;

use OCP\IL10N;
use OCP\IURLGenerator;
use OCP\IUserManager;
use OCP\L10N\IFactory;
use OCP\Notification\INotification;
use OCP\Notification\INotifier;
use OCP\Notification\UnknownNotificationException;

class Notifier implements INotifier {
    public function __construct(
        private IFactory $l10nFactory,
        private IURLGenerator $urlGenerator,
        private IUserManager $userManager,
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
            case 'item_created':
                $user = $this->userManager->get($params['authorId']);
                $displayName = $user ? $user->getDisplayName() : $params['authorId'];

                $notification->setRichSubject(
                    $l->t('{user} created item "{title}"'),
                    [
                        'user' => [
                            'type' => 'user',
                            'id' => $params['authorId'],
                            'name' => $displayName,
                        ],
                        'title' => [
                            'type' => 'highlight',
                            'id' => $notification->getObjectId(),
                            'name' => $params['itemTitle'],
                        ],
                    ]
                );

                // Add action buttons
                $viewAction = $notification->createAction();
                $viewAction->setLabel('view')
                    ->setParsedLabel($l->t('View'))
                    ->setLink(
                        $this->urlGenerator->linkToRouteAbsolute(
                            'myapp.page.index'
                        ) . '#/items/' . $notification->getObjectId(),
                        'GET'
                    )
                    ->setPrimary(true);
                $notification->addAction($viewAction);
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

#### Step 3: Mark as Processed

```php
// When user views or acts on the item:
public function markItemNotificationRead(string $userId, int $itemId): void {
    $notification = $this->notificationManager->createNotification();
    $notification->setApp('myapp')
        ->setUser($userId)
        ->setObject('item', (string)$itemId);
    $this->notificationManager->markProcessed($notification);
}
```

### Notification with Multiple Actions

```php
// In Notifier::prepare():
case 'approval_requested':
    $notification->setRichSubject(
        $l->t('{user} requests approval for "{document}"'),
        [
            'user' => [
                'type' => 'user',
                'id' => $params['authorId'],
                'name' => $displayName,
            ],
            'document' => [
                'type' => 'highlight',
                'id' => $notification->getObjectId(),
                'name' => $params['documentName'],
            ],
        ]
    );

    $approveAction = $notification->createAction();
    $approveAction->setLabel('approve')
        ->setParsedLabel($l->t('Approve'))
        ->setLink(
            $this->urlGenerator->linkToOCSRoute(
                'myapp.approval_api.approve',
                ['id' => $notification->getObjectId()]
            ),
            'POST'
        )
        ->setPrimary(true);
    $notification->addAction($approveAction);

    $rejectAction = $notification->createAction();
    $rejectAction->setLabel('reject')
        ->setParsedLabel($l->t('Reject'))
        ->setLink(
            $this->urlGenerator->linkToOCSRoute(
                'myapp.approval_api.reject',
                ['id' => $notification->getObjectId()]
            ),
            'DELETE'
        );
    $notification->addAction($rejectAction);
    break;
```

---

## Activity Examples

### Publish an Activity Event

```php
use OCP\Activity\IManager as IActivityManager;

class ItemService {
    public function __construct(
        private IActivityManager $activityManager,
    ) {}

    public function updateItem(string $userId, int $itemId, string $newTitle): void {
        // ... perform the update ...

        $event = $this->activityManager->generateEvent();
        $event->setApp('myapp')
            ->setType('myapp_item_changes')
            ->setAffectedUser($userId)
            ->setAuthor($userId)
            ->setTimestamp(time())
            ->setSubject('item_updated', [
                'itemId' => $itemId,
                'newTitle' => $newTitle,
            ])
            ->setObject('item', $itemId, $newTitle);

        $this->activityManager->publish($event);
    }
}
```

### Activity Event for Multiple Affected Users

```php
public function shareItem(string $authorId, int $itemId, array $targetUsers): void {
    // ... perform the share ...

    foreach ($targetUsers as $targetUser) {
        $event = $this->activityManager->generateEvent();
        $event->setApp('myapp')
            ->setType('myapp_shares')
            ->setAffectedUser($targetUser)
            ->setAuthor($authorId)
            ->setTimestamp(time())
            ->setSubject('item_shared', [
                'authorId' => $authorId,
                'itemTitle' => $itemTitle,
            ])
            ->setObject('item', $itemId, $itemTitle);

        $this->activityManager->publish($event);
    }
}
```

### Activity Provider (IProvider)

```php
namespace OCA\MyApp\Activity;

use OCP\Activity\IEvent;
use OCP\Activity\IProvider;
use OCP\IURLGenerator;
use OCP\IUserManager;
use OCP\L10N\IFactory;

class Provider implements IProvider {
    public function __construct(
        private IFactory $l10nFactory,
        private IURLGenerator $urlGenerator,
        private IUserManager $userManager,
    ) {}

    public function parse(string $language, IEvent $event, ?IEvent $previousEvent = null): IEvent {
        if ($event->getApp() !== 'myapp') {
            throw new \InvalidArgumentException('Unknown app');
        }

        $l = $this->l10nFactory->get('myapp', $language);
        $params = $event->getSubjectParameters();

        switch ($event->getSubject()) {
            case 'item_updated':
                $event->setRichSubject(
                    $l->t('You updated item "{item}"'),
                    [
                        'item' => [
                            'type' => 'highlight',
                            'id' => (string)$params['itemId'],
                            'name' => $params['newTitle'],
                        ],
                    ]
                );
                break;

            case 'item_shared':
                $author = $this->userManager->get($params['authorId']);
                $event->setRichSubject(
                    $l->t('{user} shared "{item}" with you'),
                    [
                        'user' => [
                            'type' => 'user',
                            'id' => $params['authorId'],
                            'name' => $author ? $author->getDisplayName() : $params['authorId'],
                        ],
                        'item' => [
                            'type' => 'highlight',
                            'id' => (string)$event->getObjectId(),
                            'name' => $params['itemTitle'],
                        ],
                    ]
                );
                break;
        }

        $event->setIcon($this->urlGenerator->imagePath('myapp', 'app-dark.svg'));
        return $event;
    }
}
```

### Activity Setting (User-Configurable Filter)

```php
namespace OCA\MyApp\Activity;

use OCP\Activity\ActivitySettings;

class Setting extends ActivitySettings {
    public function getIdentifier(): string {
        return 'myapp_item_changes';
    }

    public function getName(): string {
        return $this->l->t('Item changes');
    }

    public function getGroupIdentifier(): string {
        return 'myapp';
    }

    public function getGroupName(): string {
        return $this->l->t('My App');
    }

    public function getPriority(): int {
        return 50;
    }

    public function canChangeMail(): bool {
        return true;
    }

    public function isDefaultEnabledMail(): bool {
        return false;
    }

    public function canChangeNotification(): bool {
        return true;
    }

    public function isDefaultEnabledNotification(): bool {
        return true;
    }
}
```
