# Vooronderzoek Nextcloud — Deep Research

> Research date: 2026-03-19
> Sources: Official Nextcloud Developer Manual, Admin Manual, GitHub repos, npm packages
> Scope: Complete Nextcloud NC 28+ platform coverage for skill package development
> Word count: ~10,000+ words across 19 sections

---

## Table of Contents

- §1: Platform Architecture
- §2: OCS API
- §3: WebDAV
- §4: App Framework — Controllers & Routing
- §5: Database Layer
- §6: Authentication & Security
- §7: Vue.js Frontend Development
- §8: Frontend Data Fetching
- §9: Event System
- §10: Services & Dependency Injection
- §11: App Structure & Bootstrap
- §12: File Handling API
- §13: Sharing API
- §14: Notifications API
- §15: Server Administration — OCC Commands
- §16: Configuration — config.php
- §17: Background Jobs
- §18: Testing
- §19: Anti-Patterns & Common Mistakes

---

## Part 1: Backend APIs

See: `docs/research/backend-apis-research.md`

Covers §1-§6: Platform Architecture, OCS API, WebDAV, Controllers & Routing, Database Layer, Authentication & Security.

## Part 2: Frontend & Events

See: `docs/research/frontend-events-research.md`

Covers §7-§11: Vue.js Frontend, Data Fetching, Event System, DI, App Structure & Bootstrap.

## Part 3: Administration, Files & Collaboration

Content below (from research agent output):

---

## §12: File Handling API

### Overview
Nextcloud provides an abstraction layer over file storage backends through its Node API. The primary entry point is `IRootFolder`, from which user-specific folders are accessed.

### Key Interfaces/APIs

**IRootFolder** — The root of the entire Nextcloud filesystem tree:
```php
use OCP\Files\IRootFolder;
use OCP\IUserSession;

class FileService {
    public function __construct(private IUserSession $userSession, private IRootFolder $rootFolder) {}
}
```

**IUserFolder** — A user's home folder:
```php
$userFolder = $this->rootFolder->getUserFolder($user->getUID());
```

**When to use which:**
- `IRootFolder`: ALWAYS use as the injection point
- `IUserFolder` (via `getUserFolder()`): ALWAYS use for accessing user files

**Key Folder methods:** `get(path)`, `getById(id)`, `newFile(path, content)`, `newFolder(path)`, `nodeExists(path)`
**Key File methods:** `getContent()`, `putContent(data)`, `getMimeType()`, `getSize()`

### Code Examples

```php
// Reading a file
try {
    $file = $userFolder->get('myfile.txt');
    if ($file instanceof \OCP\Files\File) {
        return $file->getContent();
    }
} catch (\OCP\Files\NotFoundException $e) {
    throw new StorageException('File not found');
}

// Writing a file
try {
    $file = $userFolder->get('myfile.txt');
    $file->putContent($content);
} catch (\OCP\Files\NotFoundException $e) {
    $userFolder->newFile('myfile.txt', $content);
}
```

### File Events

| Event | Trigger |
|-------|---------|
| `BeforeNodeCreatedEvent` / `NodeCreatedEvent` | File/folder creation |
| `BeforeNodeWrittenEvent` / `NodeWrittenEvent` | File content write |
| `BeforeNodeDeletedEvent` / `NodeDeletedEvent` | File/folder deletion |
| `BeforeNodeCopiedEvent` / `NodeCopiedEvent` | File/folder copy |
| `BeforeNodeRenamedEvent` / `NodeRenamedEvent` | File/folder rename |
| `NodeAddedToFavorite` / `NodeRemovedFromFavorite` | Favorite toggle (NC 28+) |

### Anti-Patterns
- **NEVER access storage directly** when the Node API suffices
- **NEVER assume `getById()` returns single result** — returns array
- **NEVER use hardcoded paths** — always use `getUserFolder()`
- **NEVER forget to handle `NotFoundException`**

---

## §13: Sharing API

### Overview
The OCS Share API provides REST interface for managing file/folder shares with multiple share types and permission bitmask.

**Base URL:** `/ocs/v2.php/apps/files_sharing/api/v1`
**Required header:** `OCS-APIRequest: true`

### Share Types

| Type | Value | shareWith |
|------|-------|-----------|
| User | 0 | User ID |
| Group | 1 | Group ID |
| Public link | 3 | (empty) |
| Email | 4 | Email address |
| Federated | 6 | user@server |
| Circle | 7 | Circle ID |
| Talk | 10 | Conversation token |

### Permission Bitmask

| Permission | Value |
|-----------|-------|
| Read | 1 |
| Update | 2 |
| Create | 4 |
| Delete | 8 |
| Share | 16 |
| All | 31 |

### Code Examples

```bash
# Create user share
POST /ocs/v2.php/apps/files_sharing/api/v1/shares
  path=/Documents/file.pdf&shareType=0&shareWith=targetuser&permissions=1

# Create public link with password
POST /ocs/v2.php/apps/files_sharing/api/v1/shares
  path=/Documents/file.pdf&shareType=3&password=secretpass&expireDate=2025-12-31

# Share attributes (disable download)
[{"scope": "permissions", "key": "download", "value": false}]
```

### Anti-Patterns
- **NEVER omit `OCS-APIRequest: true` header**
- **NEVER confuse v1/v2 status codes** — ALWAYS use v2
- **NEVER pass shareWith for public links (type 3)**

---

## §14: Notifications API

### Overview
Apps create notifications via `INotificationManager`, presented via `INotifier` implementations.

### Key Code

```php
// Creating notification
$manager = \OCP\Server::get(\OCP\Notification\IManager::class);
$notification = $manager->createNotification();
$notification->setApp('myapp')
    ->setUser('targetuser')
    ->setDateTime(new \DateTime())
    ->setObject('item', '42')
    ->setSubject('new_item', ['itemName' => 'Report Q4']);
$manager->notify($notification);

// INotifier implementation
class Notifier implements INotifier {
    public function prepare(INotification $notification, string $languageCode): INotification {
        if ($notification->getApp() !== 'myapp') throw new UnknownNotificationException();
        $notification->setRichSubject('New item: {item}', [...]);
        return $notification;
    }
}
```

### Activity API
```php
$event = $activityManager->generateEvent();
$event->setApp('myapp')->setType('file_changed')->setAffectedUser('targetuser')
    ->setSubject('file_updated', ['filename' => 'report.pdf']);
$activityManager->publish($event);
```

### Anti-Patterns
- **NEVER put translated strings in setSubject()** — use language keys
- **NEVER forget to throw UnknownNotificationException** in prepare()
- **NEVER send individual push notifications in loop** — use defer()/flush()

---

## §15: Server Administration — OCC Commands

### Key Commands
```bash
occ maintenance:mode --on/--off
occ user:add --display-name="John" --group="admin" john
occ app:enable/disable calendar
occ config:system:set trusted_domains 1 --value=cloud.example.com
occ config:system:set debug --value=true --type=boolean
occ files:scan --all | --path="/john/files/Documents"
occ background:cron
```

### Custom Command
```php
class ProcessItems extends Command {
    protected function configure(): void {
        $this->setName('myapp:process-items')
            ->addArgument('user', InputArgument::OPTIONAL)
            ->addOption('force', 'f', InputOption::VALUE_NONE);
    }
    protected function execute(InputInterface $input, OutputInterface $output): int {
        return Command::SUCCESS;
    }
}
```

Register in info.xml: `<commands><command>OCA\MyApp\Command\ProcessItems</command></commands>`

### Anti-Patterns
- **NEVER run occ as root** — use `sudo -u www-data`
- **NEVER use `files:scan --all` on large installations** without targeting specific paths

---

## §16: Configuration — config.php

### Key Settings

| Parameter | Purpose |
|-----------|---------|
| `trusted_domains` | Allowed login domains |
| `datadirectory` | User files location |
| `dbtype/dbhost/dbname` | Database config |
| `overwrite.cli.url` | CLI URL generation |
| `overwriteprotocol` | Reverse proxy HTTPS |
| `memcache.local` | APCu cache |
| `memcache.distributed` | Redis cache |
| `log_type/loglevel` | Logging config |
| `maintenance_window_start` | Heavy job scheduling (NC 28+) |

### Programmatic Access (IConfig)
```php
$this->config->getSystemValue('maintenance', false);
$this->config->getAppValue('myapp', 'api_key', '');
$this->config->setAppValue('myapp', 'api_key', 'new_value');
$this->config->getUserValue('john', 'myapp', 'preference', 'default');
```

### Anti-Patterns
- **NEVER store config.php in version control**
- **NEVER forget trusted_domains** — most common post-install issue
- **NEVER set loglevel 0 in production**

---

## §17: Background Jobs

### Job Types
```php
// TimedJob (recurring)
class CleanupTask extends TimedJob {
    public function __construct(ITimeFactory $time, MyService $service) {
        parent::__construct($time);
        $this->setInterval(3600); // minimum seconds between runs
    }
    protected function run($arguments): void { $this->service->cleanup(); }
}

// QueuedJob (one-time)
class ProcessUpload extends QueuedJob {
    protected function run($arguments): void {
        $this->processor->process($arguments['fileId']);
    }
}
```

Register: `<background-jobs><job>OCA\MyApp\Cron\CleanupTask</job></background-jobs>`

Programmatic: `$jobList->add(ProcessUpload::class, ['fileId' => 42]);`
Scheduled: `$jobList->scheduleAfter(RevokeShare::class, ['id' => $id], $timestamp);`
Performance: `$this->setTimeSensitivity(IJob::TIME_INSENSITIVE);` and `$this->setAllowParallelRuns(false);`

### Anti-Patterns
- **NEVER use AJAX mode in production**
- **NEVER assume exact timing for setInterval()**
- **NEVER forget ITimeFactory in constructor**

---

## §18: Testing

### PHPUnit Setup
All tests extend `\Test\TestCase`. Bootstrap: `../../tests/bootstrap.php`.

```php
class ItemServiceTest extends TestCase {
    protected function setUp(): void {
        parent::setUp(); // ALWAYS call
        $this->service = new ItemService($this->createMock(IDBConnection::class));
    }
}
```

### Anti-Patterns
- **NEVER forget parent::setUp()/tearDown()** — causes test pollution
- **NEVER bootstrap without tests/bootstrap.php**

---

## §19: Anti-Patterns & Common Mistakes

### OCS API
- ALWAYS use v2 endpoints, ALWAYS include `OCS-APIRequest: true`

### CSRF
- NEVER combine `#[NoCSRFRequired]` + `#[PublicPage]` on state-changing endpoints

### File Paths
- NEVER use hardcoded paths — use Node API
- ALWAYS handle NotFoundException
- ALWAYS check `getById()` returns array

### Database
- NEVER modify existing migrations
- NEVER use raw SQL — use query builder
- NEVER create tables without primary keys

### Frontend
- NEVER use `OC.generateUrl()` — use `@nextcloud/router`
- NEVER use deprecated `OCP\ILogger` — use `Psr\Log\LoggerInterface`
- NEVER use `\OCP\Server::get()` — use constructor injection
- NEVER use deprecated hooks — use typed events

### Performance
- ALWAYS configure system cron for production
- NEVER set loglevel 0 in production
