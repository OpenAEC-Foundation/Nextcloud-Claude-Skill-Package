---
name: nextcloud-syntax-file-api
description: >
  Use when reading/writing files programmatically, listening to file events, or working with Nextcloud's filesystem abstraction.
  Prevents using deprecated Filesystem class, accessing files without proper user folder context, and missing NotFoundException handling.
  Covers Node API with IRootFolder and IUserFolder, File and Folder interfaces, file CRUD operations, file events (BeforeNodeCreated, NodeWritten, etc.), storage wrappers, versioning, and trash API.
  Keywords: IRootFolder, IUserFolder, Node, File, Folder, getContent, putContent, NodeWritten, storage wrapper, read file content, write file, file metadata, file events, file CRUD, storage..
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-syntax-file-api

## Quick Reference

### Entry Points

| Interface | Namespace | How to Get |
|-----------|-----------|------------|
| `IRootFolder` | `OCP\Files\IRootFolder` | Constructor injection (DI) |
| `IUserFolder` | `OCP\Files\Folder` | `$rootFolder->getUserFolder($userId)` |

**ALWAYS** inject `IRootFolder` via constructor -- NEVER instantiate it directly.

**ALWAYS** use `getUserFolder($userId)` to access a user's files -- NEVER construct paths manually to `/userid/files/`.

### Node Hierarchy

| Interface | Namespace | Represents |
|-----------|-----------|------------|
| `Node` | `OCP\Files\Node` | Base: any filesystem entry |
| `File` | `OCP\Files\File` | A file (extends Node) |
| `Folder` | `OCP\Files\Folder` | A folder (extends Node) |
| `FileInfo` | `OCP\Files\FileInfo` | Metadata-only interface |

### Key Folder Methods

| Method | Return | Description |
|--------|--------|-------------|
| `get(string $path)` | `Node` | Get node by relative path |
| `getById(int $id)` | `Node[]` | Get nodes by file ID (returns ARRAY) |
| `newFile(string $path, ?string $content = null)` | `File` | Create new file |
| `newFolder(string $path)` | `Folder` | Create new folder |
| `nodeExists(string $path)` | `bool` | Check if path exists |
| `getDirectoryListing()` | `Node[]` | List immediate children |
| `search(ISearchQuery $query)` | `Node[]` | Search within folder |
| `getById(int $id)` | `Node[]` | Lookup by filecache ID |

### Key File Methods

| Method | Return | Description |
|--------|--------|-------------|
| `getContent()` | `string` | Read entire file content |
| `putContent(string $data)` | `void` | Write/overwrite file content |
| `fopen(string $mode)` | `resource\|false` | Open file as stream |
| `getMimeType()` | `string` | Get MIME type |
| `getSize()` | `int\|float` | Get file size in bytes |

### Common Node Methods (File and Folder)

| Method | Return | Description |
|--------|--------|-------------|
| `getName()` | `string` | Filename or folder name |
| `getPath()` | `string` | Full internal path |
| `getInternalPath()` | `string` | Path relative to storage |
| `getId()` | `int` | Filecache ID |
| `getEtag()` | `string` | ETag for caching |
| `getMTime()` | `int` | Last modified timestamp |
| `getStorage()` | `IStorage` | Underlying storage backend |
| `getParent()` | `Folder` | Parent folder |
| `delete()` | `void` | Delete this node |
| `move(string $targetPath)` | `Node` | Move/rename node |
| `copy(string $targetPath)` | `Node` | Copy node |
| `lock(int $type)` | `void` | Acquire lock |
| `unlock(int $type)` | `void` | Release lock |

### File Events (`OCP\Files\Events\Node\`)

| Event | Trigger | Available Data |
|-------|---------|----------------|
| `BeforeNodeCreatedEvent` | Before file/folder creation | `getNode()` |
| `NodeCreatedEvent` | After file/folder creation | `getNode()` |
| `BeforeNodeWrittenEvent` | Before content write | `getNode()` |
| `NodeWrittenEvent` | After content write | `getNode()` |
| `BeforeNodeDeletedEvent` | Before deletion | `getNode()` |
| `NodeDeletedEvent` | After deletion | `getNode()` |
| `BeforeNodeRenamedEvent` | Before rename/move | `getSource()`, `getTarget()` |
| `NodeRenamedEvent` | After rename/move | `getSource()`, `getTarget()` |
| `BeforeNodeCopiedEvent` | Before copy | `getSource()`, `getTarget()` |
| `NodeCopiedEvent` | After copy | `getSource()`, `getTarget()` |
| `BeforeNodeTouchedEvent` | Before mtime update | `getNode()` |
| `NodeTouchedEvent` | After mtime update | `getNode()` |

### Critical Warnings

**NEVER** assume `getById()` returns a single node -- it returns an `array` because a file can appear in multiple mount points (external storage, group folders). ALWAYS access `$nodes[0]` after checking the array is not empty.

**NEVER** access files without wrapping in `try/catch` for `NotFoundException` -- the file may have been deleted between check and access.

**NEVER** use hardcoded absolute paths like `/admin/files/Documents/file.txt` -- ALWAYS use `getUserFolder()` which returns the user's files root.

**NEVER** call `getContent()` on large files -- use `fopen()` with streaming for files larger than a few MB.

**ALWAYS** check `instanceof File` or `instanceof Folder` after `get()` -- the return type is `Node` which could be either.

**ALWAYS** inject `IRootFolder` and call `getUserFolder()` -- NEVER try to inject `IUserFolder` directly (it is not a registered DI service).

**ALWAYS** register file event listeners in `lib/AppInfo/Application.php` `register()` method using `$context->registerEventListener()`.

---

## Decision Tree: File Access

```
Need to access files?
├── Which user's files? → getUserFolder($userId)
│   ├── Know the path? → $userFolder->get('path/to/file')
│   │   ├── Is it a File? → instanceof \OCP\Files\File → getContent() / putContent()
│   │   └── Is it a Folder? → instanceof \OCP\Files\Folder → getDirectoryListing()
│   ├── Know the file ID? → $userFolder->getById($id)
│   │   └── ALWAYS check: if (empty($nodes)) { throw ... }
│   │   └── Use $nodes[0] for first match
│   ├── Need to create? → Does it exist?
│   │   ├── nodeExists() returns true → get() then putContent()
│   │   └── nodeExists() returns false → newFile() or newFolder()
│   └── Need to search? → $userFolder->search(ISearchQuery)
└── System-level access? → Use IRootFolder directly (admin only)
```

---

## Essential Patterns

### Pattern 1: Service with File Access

```php
namespace OCA\MyApp\Service;

use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\IRootFolder;
use OCP\Files\NotFoundException;

class FileService {
    public function __construct(
        private IRootFolder $rootFolder,
    ) {}

    public function readFile(string $userId, string $path): string {
        $userFolder = $this->rootFolder->getUserFolder($userId);
        try {
            $node = $userFolder->get($path);
            if (!($node instanceof File)) {
                throw new \RuntimeException('Not a file');
            }
            return $node->getContent();
        } catch (NotFoundException $e) {
            throw new NotFoundException('File not found: ' . $path);
        }
    }

    public function writeFile(string $userId, string $path, string $content): void {
        $userFolder = $this->rootFolder->getUserFolder($userId);
        try {
            $file = $userFolder->get($path);
            if (!($file instanceof File)) {
                throw new \RuntimeException('Not a file');
            }
            $file->putContent($content);
        } catch (NotFoundException $e) {
            $userFolder->newFile($path, $content);
        }
    }
}
```

### Pattern 2: Safe getById() Usage

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

### Pattern 3: Folder Listing with Type Filtering

```php
public function listFiles(string $userId, string $folderPath): array {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    try {
        $folder = $userFolder->get($folderPath);
        if (!($folder instanceof Folder)) {
            throw new \RuntimeException('Not a folder');
        }

        $result = [];
        foreach ($folder->getDirectoryListing() as $node) {
            $result[] = [
                'name' => $node->getName(),
                'type' => $node instanceof File ? 'file' : 'folder',
                'size' => $node->getSize(),
                'mtime' => $node->getMTime(),
                'mimetype' => $node instanceof File ? $node->getMimeType() : 'httpd/unix-directory',
            ];
        }
        return $result;
    } catch (NotFoundException $e) {
        throw new NotFoundException('Folder not found: ' . $folderPath);
    }
}
```

### Pattern 4: File Event Listener Registration

```php
// lib/AppInfo/Application.php
namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Listener\FileCreatedListener;
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
            FileCreatedListener::class
        );
    }

    public function boot(IBootContext $context): void {}
}
```

```php
// lib/Listener/FileCreatedListener.php
namespace OCA\MyApp\Listener;

use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeCreatedEvent;
use OCP\Files\File;
use Psr\Log\LoggerInterface;

/** @template-implements IEventListener<NodeCreatedEvent> */
class FileCreatedListener implements IEventListener {
    public function __construct(
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

        $this->logger->info('File created: ' . $node->getPath());
    }
}
```

### Pattern 5: Streaming Large Files

```php
public function streamFile(string $userId, string $path): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $file = $userFolder->get($path);

    if (!($file instanceof File)) {
        throw new \RuntimeException('Not a file');
    }

    $handle = $file->fopen('r');
    if ($handle === false) {
        throw new \RuntimeException('Cannot open file');
    }

    try {
        while (!feof($handle)) {
            echo fread($handle, 8192);
            flush();
        }
    } finally {
        fclose($handle);
    }
}
```

### Pattern 6: Create or Update (Upsert)

```php
public function upsertFile(string $userId, string $path, string $content): File {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    if ($userFolder->nodeExists($path)) {
        $file = $userFolder->get($path);
        if (!($file instanceof File)) {
            throw new \RuntimeException('Path exists but is not a file');
        }
        $file->putContent($content);
        return $file;
    }

    return $userFolder->newFile($path, $content);
}
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- Complete IRootFolder, File, Folder, Node method tables
- [references/examples.md](references/examples.md) -- File CRUD, events, storage access examples
- [references/anti-patterns.md](references/anti-patterns.md) -- File handling mistakes and corrections

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/files.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/events.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/storage.html
