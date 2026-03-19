# File Operations Implementation Examples

## Complete CRUD Service

### Full-Featured File Service

This is a production-ready service covering all standard file operations.

```php
namespace OCA\MyApp\Service;

use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\Files\NotFoundException;
use OCP\Files\NotPermittedException;
use OCP\Files\Search\ISearchComparison;
use OCP\Files\Search\SearchComparison;
use OCP\Files\Search\SearchQuery;
use Psr\Log\LoggerInterface;

class FileOperationService {
    private const APP_FOLDER = 'MyApp';

    public function __construct(
        private IRootFolder $rootFolder,
        private LoggerInterface $logger,
    ) {}

    /**
     * Get or create the app's dedicated folder in user space.
     * ALWAYS use a dedicated app folder -- NEVER scatter files in the user root.
     */
    public function getAppFolder(string $userId): Folder {
        $userFolder = $this->rootFolder->getUserFolder($userId);

        if ($userFolder->nodeExists(self::APP_FOLDER)) {
            $node = $userFolder->get(self::APP_FOLDER);
            if (!($node instanceof Folder)) {
                throw new \RuntimeException('App folder path is occupied by a file');
            }
            return $node;
        }

        return $userFolder->newFolder(self::APP_FOLDER);
    }

    /**
     * Upsert: create or update a file.
     * ALWAYS prefer this over separate create/update to handle race conditions.
     */
    public function saveFile(string $userId, string $relativePath, string $content): array {
        $appFolder = $this->getAppFolder($userId);

        // Ensure parent directories exist
        $parentPath = dirname($relativePath);
        if ($parentPath !== '.' && $parentPath !== '/') {
            $this->ensureSubFolderExists($appFolder, $parentPath);
        }

        try {
            $node = $appFolder->get($relativePath);
            if (!($node instanceof File)) {
                throw new \RuntimeException('Path is not a file: ' . $relativePath);
            }
            $node->putContent($content);
            $file = $node;
        } catch (NotFoundException) {
            $file = $appFolder->newFile($relativePath, $content);
        }

        return [
            'id' => $file->getId(),
            'name' => $file->getName(),
            'size' => $file->getSize(),
            'mtime' => $file->getMTime(),
        ];
    }

    /**
     * Read file content with type safety.
     */
    public function readFile(string $userId, string $relativePath): string {
        $appFolder = $this->getAppFolder($userId);

        try {
            $node = $appFolder->get($relativePath);
        } catch (NotFoundException) {
            throw new NotFoundException('File not found: ' . $relativePath);
        }

        if (!($node instanceof File)) {
            throw new \RuntimeException('Path is not a file');
        }

        return $node->getContent();
    }

    /**
     * Delete file idempotently.
     * ALWAYS handle NotFoundException gracefully -- the file may already be gone.
     */
    public function deleteFile(string $userId, string $relativePath): void {
        $appFolder = $this->getAppFolder($userId);

        try {
            $node = $appFolder->get($relativePath);
            $node->delete();
        } catch (NotFoundException) {
            $this->logger->debug('Delete skipped, already gone: ' . $relativePath);
        }
    }

    /**
     * List all files in a subfolder with metadata.
     */
    public function listFiles(string $userId, string $folderPath = '/'): array {
        $appFolder = $this->getAppFolder($userId);

        try {
            $folder = ($folderPath === '/') ? $appFolder : $appFolder->get($folderPath);
        } catch (NotFoundException) {
            throw new NotFoundException('Folder not found: ' . $folderPath);
        }

        if (!($folder instanceof Folder)) {
            throw new \RuntimeException('Path is not a folder');
        }

        $items = [];
        foreach ($folder->getDirectoryListing() as $node) {
            $items[] = [
                'id' => $node->getId(),
                'name' => $node->getName(),
                'type' => $node instanceof File ? 'file' : 'folder',
                'size' => $node->getSize(),
                'mtime' => $node->getMTime(),
                'mimetype' => $node instanceof File ? $node->getMimeType() : 'httpd/unix-directory',
            ];
        }
        return $items;
    }

    /**
     * Move or rename a file.
     * ALWAYS use full internal paths for move().
     */
    public function moveFile(string $userId, string $sourcePath, string $targetPath): array {
        $appFolder = $this->getAppFolder($userId);

        try {
            $node = $appFolder->get($sourcePath);
        } catch (NotFoundException) {
            throw new NotFoundException('Source file not found: ' . $sourcePath);
        }

        // Ensure target parent exists
        $targetParent = dirname($targetPath);
        if ($targetParent !== '.' && $targetParent !== '/') {
            $this->ensureSubFolderExists($appFolder, $targetParent);
        }

        $targetFullPath = $appFolder->getPath() . '/' . $targetPath;
        $moved = $node->move($targetFullPath);

        return [
            'id' => $moved->getId(),
            'name' => $moved->getName(),
            'path' => $targetPath,
        ];
    }

    /**
     * Copy a file with unique name generation.
     */
    public function copyFile(string $userId, string $sourcePath, string $targetFolder): array {
        $appFolder = $this->getAppFolder($userId);
        $node = $appFolder->get($sourcePath);

        $folder = $appFolder->get($targetFolder);
        if (!($folder instanceof Folder)) {
            throw new \RuntimeException('Target is not a folder');
        }

        // Generate unique name to avoid collisions
        $safeName = $folder->getNonExistingName($node->getName());
        $targetFullPath = $folder->getPath() . '/' . $safeName;
        $copy = $node->copy($targetFullPath);

        return [
            'id' => $copy->getId(),
            'name' => $copy->getName(),
        ];
    }

    private function ensureSubFolderExists(Folder $parent, string $path): Folder {
        $parts = explode('/', trim($path, '/'));
        $current = $parent;

        foreach ($parts as $part) {
            if ($current->nodeExists($part)) {
                $node = $current->get($part);
                if (!($node instanceof Folder)) {
                    throw new \RuntimeException('Path component is a file: ' . $part);
                }
                $current = $node;
            } else {
                $current = $current->newFolder($part);
            }
        }

        return $current;
    }
}
```

---

## File Search Workflows

### Search by Name Pattern

```php
public function searchByName(string $userId, string $pattern, int $limit = 50): array {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    $query = new SearchQuery(
        new SearchComparison(
            ISearchComparison::COMPARE_LIKE,
            'name',
            '%' . $pattern . '%'
        ),
        limit: $limit,
        offset: 0
    );

    return array_map(fn($node) => [
        'id' => $node->getId(),
        'name' => $node->getName(),
        'path' => $userFolder->getRelativePath($node->getPath()),
    ], $userFolder->search($query));
}
```

### Search by MIME Type with Size Filter

```php
use OCP\Files\Search\SearchBinaryOperator;

public function findLargeImages(string $userId, int $minSizeBytes = 5242880): array {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    $query = new SearchQuery(
        new SearchBinaryOperator(
            SearchBinaryOperator::OPERATOR_AND,
            [
                new SearchComparison(ISearchComparison::COMPARE_LIKE, 'mimetype', 'image/%'),
                new SearchComparison(ISearchComparison::COMPARE_GREATER_THAN, 'size', $minSizeBytes),
            ]
        ),
        limit: 100,
        offset: 0
    );

    return $userFolder->search($query);
}
```

### Paginated Search

```php
public function searchPaginated(
    string $userId,
    string $namePattern,
    int $page = 1,
    int $perPage = 25,
): array {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $offset = ($page - 1) * $perPage;

    $query = new SearchQuery(
        new SearchComparison(
            ISearchComparison::COMPARE_LIKE,
            'name',
            '%' . $namePattern . '%'
        ),
        limit: $perPage,
        offset: $offset
    );

    $results = $userFolder->search($query);

    return [
        'page' => $page,
        'per_page' => $perPage,
        'items' => array_map(fn($node) => [
            'id' => $node->getId(),
            'name' => $node->getName(),
            'path' => $userFolder->getRelativePath($node->getPath()),
            'size' => $node->getSize(),
        ], $results),
    ];
}
```

---

## Event-Driven Workflows

### Auto-Process Uploaded Files

A complete workflow that processes files when they are created.

```php
// lib/AppInfo/Application.php
namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Listener\AutoProcessListener;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\Files\Events\Node\NodeCreatedEvent;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        $context->registerEventListener(
            NodeCreatedEvent::class,
            AutoProcessListener::class
        );
    }

    public function boot(IBootContext $context): void {}
}
```

```php
// lib/Listener/AutoProcessListener.php
namespace OCA\MyApp\Listener;

use OCA\MyApp\Service\ProcessingService;
use OCP\BackgroundJob\IJobList;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeCreatedEvent;
use OCP\Files\File;
use Psr\Log\LoggerInterface;

/** @template-implements IEventListener<NodeCreatedEvent> */
class AutoProcessListener implements IEventListener {
    private const SUPPORTED_MIMES = [
        'application/pdf',
        'text/csv',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ];

    public function __construct(
        private IJobList $jobList,
        private LoggerInterface $logger,
    ) {}

    public function handle(Event $event): void {
        if (!($event instanceof NodeCreatedEvent)) {
            return;
        }

        $node = $event->getNode();
        if (!($node instanceof File)) {
            return;
        }

        // ALWAYS filter early -- check MIME type before doing any work
        if (!in_array($node->getMimeType(), self::SUPPORTED_MIMES, true)) {
            return;
        }

        // ALWAYS defer heavy processing to background jobs
        // NEVER do expensive work in event listeners
        $this->jobList->add(ProcessFileJob::class, [
            'fileId' => $node->getId(),
            'userId' => $node->getOwner()->getUID(),
        ]);

        $this->logger->info('Queued processing for: ' . $node->getName());
    }
}
```

### Track File Renames

```php
// lib/Listener/FileRenameTracker.php
namespace OCA\MyApp\Listener;

use OCA\MyApp\Db\FileTrackingMapper;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeRenamedEvent;

/** @template-implements IEventListener<NodeRenamedEvent> */
class FileRenameTracker implements IEventListener {
    public function __construct(
        private FileTrackingMapper $mapper,
    ) {}

    public function handle(Event $event): void {
        if (!($event instanceof NodeRenamedEvent)) {
            return;
        }

        $source = $event->getSource();
        $target = $event->getTarget();

        // Update any app-internal references to this file
        $this->mapper->updatePath(
            $source->getId(),
            $target->getPath(),
            $target->getName()
        );
    }
}
```

### Favorite Event Handling (NC 28+)

```php
// lib/AppInfo/Application.php
use OCA\MyApp\Listener\FavoriteListener;
use OCP\Files\Events\Node\NodeAddedToFavorite;
use OCP\Files\Events\Node\NodeRemovedFromFavorite;

public function register(IRegistrationContext $context): void {
    $context->registerEventListener(
        NodeAddedToFavorite::class,
        FavoriteListener::class
    );
    $context->registerEventListener(
        NodeRemovedFromFavorite::class,
        FavoriteListener::class
    );
}
```

```php
// lib/Listener/FavoriteListener.php
namespace OCA\MyApp\Listener;

use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeAddedToFavorite;
use OCP\Files\Events\Node\NodeRemovedFromFavorite;

/** @template-implements IEventListener<NodeAddedToFavorite|NodeRemovedFromFavorite> */
class FavoriteListener implements IEventListener {
    public function handle(Event $event): void {
        if ($event instanceof NodeAddedToFavorite) {
            $node = $event->getNode();
            // Index favorited file for quick access
            $this->indexService->markFavorite($node->getId());
        } elseif ($event instanceof NodeRemovedFromFavorite) {
            $node = $event->getNode();
            $this->indexService->unmarkFavorite($node->getId());
        }
    }
}
```

---

## Streaming Workflows

### Process Large CSV File

```php
public function importCsv(string $userId, string $path): int {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $node = $userFolder->get($path);

    if (!($node instanceof File)) {
        throw new \RuntimeException('Not a file');
    }

    $handle = $node->fopen('r');
    if ($handle === false) {
        throw new \RuntimeException('Cannot open file');
    }

    $rowCount = 0;
    try {
        // Skip header
        fgetcsv($handle);

        while (($row = fgetcsv($handle)) !== false) {
            $this->processRow($row);
            $rowCount++;
        }
    } finally {
        fclose($handle);
    }

    return $rowCount;
}
```

### Write Large Output via Stream

```php
public function exportData(string $userId, string $path, iterable $records): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    // Create empty file first, then write via stream
    if (!$userFolder->nodeExists($path)) {
        $userFolder->newFile($path, '');
    }

    $file = $userFolder->get($path);
    if (!($file instanceof File)) {
        throw new \RuntimeException('Not a file');
    }

    $handle = $file->fopen('w');
    if ($handle === false) {
        throw new \RuntimeException('Cannot open for writing');
    }

    try {
        // Write CSV header
        fputcsv($handle, ['id', 'name', 'value']);

        foreach ($records as $record) {
            fputcsv($handle, [$record->id, $record->name, $record->value]);
        }
    } finally {
        fclose($handle);
    }
}
```

---

## Trash and Versioning Workflows

### Pattern 7: Working with Trash (ITrashManager)

```php
use OCA\Files_Trashbin\Trash\ITrashManager;

class TrashService {
    public function __construct(
        private ITrashManager $trashManager,
        private IRootFolder $rootFolder,
    ) {}

    /**
     * List trashed items for a user.
     */
    public function listTrash(string $userId): array {
        $user = \OCP\Server::get(\OCP\IUserManager::class)->get($userId);
        $items = $this->trashManager->listTrashRoot($user);

        return array_map(fn($item) => [
            'name' => $item->getName(),
            'original_location' => $item->getOriginalLocation(),
            'deleted_time' => $item->getDeletedTime(),
            'size' => $item->getSize(),
        ], $items);
    }

    /**
     * Restore a specific trashed item.
     */
    public function restoreItem(string $userId, string $trashItemName): void {
        $user = \OCP\Server::get(\OCP\IUserManager::class)->get($userId);
        $items = $this->trashManager->listTrashRoot($user);

        foreach ($items as $item) {
            if ($item->getName() === $trashItemName) {
                $this->trashManager->restoreItem($item);
                return;
            }
        }

        throw new NotFoundException('Trash item not found: ' . $trashItemName);
    }
}
```

### Pattern 8: Working with Versions (IVersionManager)

```php
use OCA\Files_Versions\Versions\IVersionManager;

class VersionService {
    public function __construct(
        private IVersionManager $versionManager,
        private IRootFolder $rootFolder,
    ) {}

    /**
     * List available versions of a file.
     */
    public function listVersions(string $userId, string $path): array {
        $userFolder = $this->rootFolder->getUserFolder($userId);
        $node = $userFolder->get($path);

        if (!($node instanceof File)) {
            throw new \RuntimeException('Not a file');
        }

        $user = \OCP\Server::get(\OCP\IUserManager::class)->get($userId);
        $versions = $this->versionManager->getVersionsForFile($user, $node);

        return array_map(fn($version) => [
            'revision_id' => $version->getRevisionId(),
            'timestamp' => $version->getTimestamp(),
            'size' => $version->getSize(),
        ], $versions);
    }

    /**
     * Restore a specific version.
     */
    public function restoreVersion(string $userId, string $path, string $revisionId): void {
        $userFolder = $this->rootFolder->getUserFolder($userId);
        $node = $userFolder->get($path);

        if (!($node instanceof File)) {
            throw new \RuntimeException('Not a file');
        }

        $user = \OCP\Server::get(\OCP\IUserManager::class)->get($userId);
        $versions = $this->versionManager->getVersionsForFile($user, $node);

        foreach ($versions as $version) {
            if ($version->getRevisionId() === $revisionId) {
                $this->versionManager->rollback($version);
                return;
            }
        }

        throw new NotFoundException('Version not found: ' . $revisionId);
    }
}
```

---

## Advanced Storage Access

### Pattern 9: Direct Storage Access (Use Sparingly)

**ONLY** use direct storage access when the Node API cannot accomplish the task.

```php
/**
 * Get storage-level metadata not available via Node API.
 * NEVER use this for standard CRUD -- use File/Folder methods instead.
 */
public function getStorageStats(string $userId, string $path): array {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $node = $userFolder->get($path);

    $storage = $node->getStorage();

    return [
        'storage_id' => $storage->getId(),
        'is_local' => $storage->isLocal(),
        'free_space' => $storage->free_space($node->getInternalPath()),
        'available' => $storage->isAvailable(),
    ];
}
```
