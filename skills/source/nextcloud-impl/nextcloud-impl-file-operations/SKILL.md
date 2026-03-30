---
name: nextcloud-impl-file-operations
description: >
  Use when implementing file manipulation features, building file-aware apps, or handling file lifecycle events.
  Prevents direct storage access bypassing the Node API, missing lock handling, and unhandled NotFoundException.
  Covers reading, writing, creating, deleting files and folders using the Node API, file search patterns, listening to file events, working with favorites, trash and versioning, and advanced storage access patterns.
  Keywords: Node API, IRootFolder, getUserFolder, file search, favorites, trash, versioning, NotFoundException, lock, read file, write file, create folder, file events, file search, trash, versioning..
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-impl-file-operations

> Implementation workflows for Nextcloud file operations. For API signatures and method tables, see [nextcloud-syntax-file-api](../../nextcloud-syntax/nextcloud-syntax-file-api/SKILL.md).

## Quick Reference

### Workflow Map

| Workflow | When to Use | Key Pattern |
|----------|-------------|-------------|
| File CRUD Service | App needs to read/write user files | Service class with IRootFolder injection |
| Folder Tree Management | App organizes files in directories | Recursive ensure-folder + upsert |
| File Search | App finds files by criteria | ISearchQuery with SearchComparison |
| Event-Driven Processing | React to file changes | Event listeners in `register()` |
| Batch File Operations | Process many files at once | Stream-based + chunked iteration |
| Trash & Versioning | Integrate with file history | ITrashManager / IVersionManager |

### Service Architecture

```
Controller → FileService → IRootFolder → getUserFolder($userId)
                ↓                              ↓
           Business logic              Node API (File/Folder)
                ↓                              ↓
           Return DTO                  Events dispatched automatically
```

**ALWAYS** build a dedicated service class for file operations -- NEVER put file logic directly in controllers.

**ALWAYS** pass `$userId` as a parameter to service methods -- NEVER rely on session state inside services.

---

## Decision Tree: Choosing a File Workflow

```
What does your app need?
├── CRUD on individual files?
│   ├── Simple read/write → Upsert Pattern (Pattern 1)
│   ├── Large files (>5MB) → Stream Pattern (Pattern 4)
│   └── Files by ID → Safe getById Pattern (Pattern 2)
├── Organize files in folders?
│   ├── Single level → nodeExists() + newFolder()
│   └── Deep nesting → Recursive Ensure Pattern (Pattern 3)
├── Find files matching criteria?
│   ├── By name/mime → SearchQuery Pattern (Pattern 5)
│   └── By tag → searchByTag()
├── React to file changes?
│   ├── After change → NodeCreatedEvent / NodeWrittenEvent
│   ├── Before change (block) → BeforeNodeDeletedEvent + throw
│   └── Favorites → NodeAddedToFavorite / NodeRemovedFromFavorite
├── Integrate with trash/versions?
│   ├── Restore from trash → ITrashManager (Pattern 7)
│   └── Access file versions → IVersionManager (Pattern 8)
└── Direct storage access?
    └── ONLY when Node API is insufficient → Pattern 9
```

---

## Essential Patterns

### Pattern 1: File CRUD Service with Upsert

**ALWAYS** use this pattern as the foundation for any file-manipulating app.

```php
namespace OCA\MyApp\Service;

use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\Files\NotFoundException;
use OCP\Files\NotPermittedException;
use Psr\Log\LoggerInterface;

class FileOperationService {
    public function __construct(
        private IRootFolder $rootFolder,
        private LoggerInterface $logger,
    ) {}

    /**
     * Create or update a file. ALWAYS use this instead of
     * separate create/update methods to avoid race conditions.
     */
    public function upsertFile(string $userId, string $path, string $content): File {
        $userFolder = $this->rootFolder->getUserFolder($userId);

        try {
            $node = $userFolder->get($path);
            if (!($node instanceof File)) {
                throw new \RuntimeException('Path exists but is not a file: ' . $path);
            }
            $node->putContent($content);
            return $node;
        } catch (NotFoundException) {
            // Ensure parent directory exists
            $parentPath = dirname($path);
            if ($parentPath !== '.' && $parentPath !== '/') {
                $this->ensureFolderExists($userId, $parentPath);
            }
            return $userFolder->newFile($path, $content);
        }
    }

    public function readFile(string $userId, string $path): string {
        $userFolder = $this->rootFolder->getUserFolder($userId);

        try {
            $node = $userFolder->get($path);
        } catch (NotFoundException) {
            throw new NotFoundException('File not found: ' . $path);
        }

        if (!($node instanceof File)) {
            throw new \RuntimeException('Path is not a file: ' . $path);
        }

        return $node->getContent();
    }

    public function deleteFile(string $userId, string $path): void {
        $userFolder = $this->rootFolder->getUserFolder($userId);

        try {
            $node = $userFolder->get($path);
            $node->delete();
        } catch (NotFoundException) {
            $this->logger->debug('Delete skipped, file already gone: ' . $path);
        }
    }

    public function ensureFolderExists(string $userId, string $path): Folder {
        $userFolder = $this->rootFolder->getUserFolder($userId);
        $parts = explode('/', trim($path, '/'));
        $current = $userFolder;

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

### Pattern 2: Safe File Lookup by ID

**ALWAYS** use this pattern when resolving file IDs from frontend or API requests.

```php
public function getFileById(string $userId, int $fileId): File {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $nodes = $userFolder->getById($fileId);

    if (empty($nodes)) {
        throw new NotFoundException('File not found for ID: ' . $fileId);
    }

    $node = $nodes[0];
    if (!($node instanceof File)) {
        throw new \RuntimeException('Node is not a file');
    }

    return $node;
}
```

**NEVER** assume `getById()` returns a single node -- it returns an array because files can exist in multiple mount points.

### Pattern 3: Controller Integration

**ALWAYS** delegate to a service -- controllers handle HTTP concerns only.

```php
namespace OCA\MyApp\Controller;

use OCA\MyApp\Service\FileOperationService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\JSONResponse;
use OCP\AppFramework\Http;
use OCP\Files\NotFoundException;
use OCP\IRequest;

class FileController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private FileOperationService $fileService,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[\OCP\AppFramework\Http\Attribute\NoAdminRequired]
    public function read(string $path): JSONResponse {
        try {
            $content = $this->fileService->readFile($this->userId, $path);
            return new JSONResponse(['content' => $content]);
        } catch (NotFoundException) {
            return new JSONResponse(
                ['error' => 'File not found'],
                Http::STATUS_NOT_FOUND
            );
        }
    }

    #[\OCP\AppFramework\Http\Attribute\NoAdminRequired]
    public function save(string $path, string $content): JSONResponse {
        $file = $this->fileService->upsertFile($this->userId, $path, $content);
        return new JSONResponse(['id' => $file->getId()]);
    }
}
```

### Pattern 4: Event-Driven File Processing

**ALWAYS** register event listeners in `register()`, NEVER in `boot()`.

```php
// lib/AppInfo/Application.php
public function register(IRegistrationContext $context): void {
    $context->registerEventListener(
        NodeWrittenEvent::class,
        FileChangedListener::class
    );
    $context->registerEventListener(
        BeforeNodeDeletedEvent::class,
        ProtectFileListener::class
    );
}
```

```php
// lib/Listener/FileChangedListener.php
namespace OCA\MyApp\Listener;

use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeWrittenEvent;
use OCP\Files\File;

/** @template-implements IEventListener<NodeWrittenEvent> */
class FileChangedListener implements IEventListener {
    public function __construct(
        private MyProcessingService $processor,
    ) {}

    public function handle(Event $event): void {
        if (!($event instanceof NodeWrittenEvent)) {
            return;
        }

        $node = $event->getNode();
        if (!($node instanceof File)) {
            return;
        }

        // ALWAYS filter early to avoid unnecessary processing
        if ($node->getMimeType() !== 'application/json') {
            return;
        }

        $this->processor->processJsonFile($node);
    }
}
```

### Pattern 5: Blocking Deletion with Before Events

```php
/** @template-implements IEventListener<BeforeNodeDeletedEvent> */
class ProtectFileListener implements IEventListener {
    public function handle(Event $event): void {
        if (!($event instanceof BeforeNodeDeletedEvent)) {
            return;
        }

        $node = $event->getNode();

        if ($this->isProtected($node)) {
            throw new \OCP\Files\ForbiddenException(
                'Protected files cannot be deleted',
                false
            );
        }
    }
}
```

**ALWAYS** throw `ForbiddenException` from Before-events to block the operation. NEVER throw generic exceptions.

### Pattern 6: File Search Workflow

```php
use OCP\Files\Search\ISearchComparison;
use OCP\Files\Search\SearchComparison;
use OCP\Files\Search\SearchQuery;

public function findFiles(string $userId, string $namePattern, int $limit = 50): array {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    $query = new SearchQuery(
        new SearchComparison(
            ISearchComparison::COMPARE_LIKE,
            'name',
            '%' . $namePattern . '%'
        ),
        limit: $limit,
        offset: 0
    );

    $results = $userFolder->search($query);

    return array_map(fn($node) => [
        'id' => $node->getId(),
        'name' => $node->getName(),
        'path' => $userFolder->getRelativePath($node->getPath()),
        'size' => $node->getSize(),
        'mtime' => $node->getMTime(),
    ], $results);
}
```

**ALWAYS** set a `limit` on search queries -- unbounded searches on large installations cause timeouts.

---

## Critical Rules

1. **ALWAYS** inject `IRootFolder` via constructor DI -- NEVER instantiate or inject `IUserFolder` directly.
2. **ALWAYS** wrap file access in `try/catch` for `NotFoundException` -- files can vanish between check and access.
3. **ALWAYS** check `instanceof File` or `instanceof Folder` after `get()` -- the return type is `Node`.
4. **ALWAYS** use `fopen()` for files larger than 5MB -- `getContent()` loads entire file into memory.
5. **ALWAYS** use full internal paths for `move()` and `copy()`: `$userFolder->getPath() . '/' . $target`.
6. **NEVER** put file operation logic directly in controllers -- delegate to a service class.
7. **NEVER** use direct storage access (`$file->getStorage()`) for standard CRUD -- the Node API handles events, caching, encryption, and versioning automatically.
8. **NEVER** register file event listeners in `boot()` -- ALWAYS use `register()` to avoid missed events.
9. **NEVER** create files without checking existence first -- `newFile()` throws `NotPermittedException` on duplicates.
10. **NEVER** forget to close file handles from `fopen()` -- ALWAYS use `try/finally`.

---

## Reference Links

- [references/methods.md](references/methods.md) -- Complete File, Folder, IRootFolder method reference for implementation
- [references/examples.md](references/examples.md) -- CRUD workflows, search, event handling, trash, versioning
- [references/anti-patterns.md](references/anti-patterns.md) -- File operation implementation mistakes

### Related Skills

- [nextcloud-syntax-file-api](../../nextcloud-syntax/nextcloud-syntax-file-api/SKILL.md) -- API signatures and method tables

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/files.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/events.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/storage.html
