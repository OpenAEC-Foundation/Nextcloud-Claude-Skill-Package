# Collaboration Anti-Patterns Reference

## Share API Anti-Patterns

### AP-01: Missing OCS-APIRequest Header

**WRONG** -- OCS request without required header:
```bash
curl -X POST "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares" \
  -u admin:password \
  -d "path=/file.pdf&shareType=0&shareWith=john"
```
Result: Returns HTML login page instead of JSON/XML response.

**RIGHT** -- ALWAYS include the `OCS-APIRequest: true` header:
```bash
curl -X POST "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares" \
  -H "OCS-APIRequest: true" \
  -u admin:password \
  -d "path=/file.pdf&shareType=0&shareWith=john"
```

### AP-02: Using API v1 Instead of v2

**WRONG** -- Using OCS v1 endpoint:
```bash
curl "https://cloud.example.com/ocs/v1.php/apps/files_sharing/api/v1/shares" \
  -H "OCS-APIRequest: true" \
  -u admin:password
```
Result: Returns status code 100 for success instead of 200. Client libraries expecting standard HTTP codes break.

**RIGHT** -- ALWAYS use `/ocs/v2.php/` which returns standard HTTP status codes:
```bash
curl "https://cloud.example.com/ocs/v2.php/apps/files_sharing/api/v1/shares" \
  -H "OCS-APIRequest: true" \
  -u admin:password
```

### AP-03: Setting shareWith on Public Links

**WRONG** -- Providing shareWith for share type 3:
```bash
curl -X POST ".../shares" \
  -H "OCS-APIRequest: true" \
  -d "path=/file.pdf&shareType=3&shareWith=nobody"
```
Result: The `shareWith` parameter is ignored for public links but creates confusion in the codebase.

**RIGHT** -- NEVER set `shareWith` for public link shares (type 3):
```bash
curl -X POST ".../shares" \
  -H "OCS-APIRequest: true" \
  -d "path=/file.pdf&shareType=3&permissions=1"
```

### AP-04: Hardcoding Permission Values

**WRONG** -- Magic numbers without explanation:
```php
$body = ['path' => '/file.pdf', 'shareType' => 0, 'shareWith' => 'john', 'permissions' => 19];
```

**RIGHT** -- ALWAYS use named constants or comments for permission bitmask:
```php
$permissions = 1 | 2 | 16;  // Read | Update | Share
$body = ['path' => '/file.pdf', 'shareType' => 0, 'shareWith' => 'john', 'permissions' => $permissions];
```

### AP-05: Not Checking Share Existence Before Update

**WRONG** -- Blindly updating a share that may not exist:
```php
$client->put($baseUrl . '/shares/' . $shareId, [
    'body' => ['permissions' => 1],
]);
// May get 404 -- no error handling
```

**RIGHT** -- ALWAYS handle the case where the share no longer exists:
```php
try {
    $response = $client->put($baseUrl . '/shares/' . $shareId, [
        'headers' => ['OCS-APIRequest' => 'true'],
        'body' => ['permissions' => 1],
    ]);
} catch (ClientException $e) {
    if ($e->getResponse()->getStatusCode() === 404) {
        // Share was already deleted
        $this->logger->info('Share {id} no longer exists', ['id' => $shareId]);
        return;
    }
    throw $e;
}
```

---

## Notification Anti-Patterns

### AP-06: Translated Strings in setSubject()

**WRONG** -- Putting user-facing text in setSubject():
```php
$notification->setSubject('John created a new item "Report Q4"');
```
Result: The notification cannot be translated to other languages. The subject is stored in the database as-is.

**RIGHT** -- ALWAYS use a language key in `setSubject()` and translate in `prepare()`:
```php
// When creating:
$notification->setSubject('new_item', ['authorId' => 'john', 'itemName' => 'Report Q4']);

// In Notifier::prepare():
$l = $this->l10nFactory->get('myapp', $languageCode);
$notification->setRichSubject($l->t('{user} created item "{item}"'), [...]);
```

### AP-07: Missing UnknownNotificationException

**WRONG** -- Notifier does not throw for unknown apps/subjects:
```php
public function prepare(INotification $notification, string $languageCode): INotification {
    // No check for app or subject
    $notification->setRichSubject('Something happened');
    return $notification;
}
```
Result: This notifier intercepts notifications from ALL apps, breaking the notifier chain.

**RIGHT** -- ALWAYS throw `UnknownNotificationException` for unrecognized apps AND subjects:
```php
public function prepare(INotification $notification, string $languageCode): INotification {
    if ($notification->getApp() !== 'myapp') {
        throw new UnknownNotificationException();
    }

    switch ($notification->getSubject()) {
        case 'new_item':
            // Handle known subject
            break;
        default:
            throw new UnknownNotificationException();
    }

    return $notification;
}
```

### AP-08: Forgetting to Register the Notifier

**WRONG** -- Notifier class exists but is never registered:
```php
// Notifier class is in lib/Notification/Notifier.php
// BUT Application::register() does not register it
class Application extends App implements IBootstrap {
    public function register(IRegistrationContext $context): void {
        // Missing: $context->registerNotifierService(Notifier::class);
    }
}
```
Result: Notifications are created and stored, but never prepared for display. Users see raw subject keys instead of translated text.

**RIGHT** -- ALWAYS register the notifier in `Application::register()`:
```php
public function register(IRegistrationContext $context): void {
    $context->registerNotifierService(Notifier::class);
}
```

### AP-09: Not Calling markProcessed()

**WRONG** -- Notifications persist after user acts on them:
```php
public function acceptInvitation(int $itemId): JSONResponse {
    $this->service->accept($itemId, $this->userId);
    // Notification still shows in the bell icon
    return new JSONResponse(['status' => 'ok']);
}
```
Result: Stale notifications accumulate, degrading user experience and cluttering the notification panel.

**RIGHT** -- ALWAYS call `markProcessed()` when the user acts on the notification:
```php
public function acceptInvitation(int $itemId): JSONResponse {
    $this->service->accept($itemId, $this->userId);

    $notification = $this->notificationManager->createNotification();
    $notification->setApp('myapp')
        ->setUser($this->userId)
        ->setObject('invitation', (string)$itemId);
    $this->notificationManager->markProcessed($notification);

    return new JSONResponse(['status' => 'ok']);
}
```

### AP-10: Individual Push Notifications in Loop

**WRONG** -- Sending push notifications one by one:
```php
foreach ($users as $userId) {
    $notification = $this->notificationManager->createNotification();
    $notification->setApp('myapp')
        ->setUser($userId)
        ->setDateTime(new \DateTime())
        ->setObject('batch', $batchId)
        ->setSubject('batch_ready', ['name' => $batchName]);
    $this->notificationManager->notify($notification);
    // Each notify() triggers a separate push request
}
```
Result: If notifying 100 users, this sends 100 separate HTTP requests to the push server, causing massive latency.

**RIGHT** -- ALWAYS use `defer()`/`flush()` for batch notifications:
```php
$this->notificationManager->defer();

foreach ($users as $userId) {
    $notification = $this->notificationManager->createNotification();
    $notification->setApp('myapp')
        ->setUser($userId)
        ->setDateTime(new \DateTime())
        ->setObject('batch', $batchId)
        ->setSubject('batch_ready', ['name' => $batchName]);
    $this->notificationManager->notify($notification);
}

$this->notificationManager->flush();
// All push notifications sent in a single batched request
```

---

## Activity Anti-Patterns

### AP-11: Missing setAffectedUser()

**WRONG** -- Activity event without affected user:
```php
$event = $this->activityManager->generateEvent();
$event->setApp('myapp')
    ->setType('myapp_updates')
    ->setAuthor($userId)
    ->setSubject('item_created', ['title' => $title]);
$this->activityManager->publish($event);
```
Result: The event is published but appears in nobody's activity stream.

**RIGHT** -- ALWAYS set both `setAffectedUser()` and `setAuthor()`:
```php
$event = $this->activityManager->generateEvent();
$event->setApp('myapp')
    ->setType('myapp_updates')
    ->setAffectedUser($targetUserId)
    ->setAuthor($authorUserId)
    ->setTimestamp(time())
    ->setSubject('item_created', ['title' => $title]);
$this->activityManager->publish($event);
```

### AP-12: Translated Strings in Activity setSubject()

**WRONG** -- Same as notifications, putting translated text in setSubject():
```php
$event->setSubject('John updated the report');
```

**RIGHT** -- ALWAYS use language keys in `setSubject()` and translate in `IProvider::parse()`:
```php
$event->setSubject('item_updated', ['authorId' => 'john', 'itemName' => 'report']);

// In Provider::parse():
$event->setRichSubject($l->t('{user} updated "{item}"'), [...]);
```

### AP-13: Not Registering Activity Provider in info.xml

**WRONG** -- Activity provider class exists but is not registered:
```php
// lib/Activity/Provider.php exists
// BUT appinfo/info.xml has no <activity> section
```
Result: Activity events are stored in the database but displayed as raw subject keys.

**RIGHT** -- ALWAYS register providers and settings in `appinfo/info.xml`:
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

---

## Summary Table

| ID | Anti-Pattern | Rule |
|----|-------------|------|
| AP-01 | Missing OCS-APIRequest header | ALWAYS include `OCS-APIRequest: true` |
| AP-02 | Using OCS API v1 | ALWAYS use `/ocs/v2.php/` for standard HTTP codes |
| AP-03 | shareWith on public links | NEVER set shareWith for share type 3 |
| AP-04 | Hardcoded permission values | ALWAYS use named constants or comments |
| AP-05 | No existence check on update | ALWAYS handle 404 on share update/delete |
| AP-06 | Translated strings in setSubject() | ALWAYS use language keys, translate in prepare() |
| AP-07 | Missing UnknownNotificationException | ALWAYS throw for unrecognized apps/subjects |
| AP-08 | Unregistered notifier | ALWAYS register in Application::register() |
| AP-09 | Not calling markProcessed() | ALWAYS mark notifications as processed after user action |
| AP-10 | Individual push in loop | ALWAYS use defer()/flush() for batch notifications |
| AP-11 | Missing setAffectedUser() | ALWAYS set both affectedUser and author on events |
| AP-12 | Translated strings in activity subject | ALWAYS use language keys, translate in parse() |
| AP-13 | Unregistered activity provider | ALWAYS register in info.xml |
