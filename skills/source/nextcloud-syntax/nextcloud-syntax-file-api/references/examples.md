# File API Examples Reference

## File CRUD Operations

### Create a File

```php
use OCP\Files\IRootFolder;

class DocumentService {
    public function __construct(private IRootFolder $rootFolder) {}

    public function createDocument(string $userId, string $name, string $content): int {
        $userFolder = $this->rootFolder->getUserFolder($userId);

        // Ensure parent directory exists
        if (!$userFolder->nodeExists('Documents')) {
            $userFolder->newFolder('Documents');
        }

        $file = $userFolder->newFile('Documents/' . $name, $content);
        return $file->getId();
    }
}
```

### Read a File

```php
use OCP\Files\File;
use OCP\Files\NotFoundException;

public function readDocument(string $userId, string $path): string {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    try {
        $node = $userFolder->get($path);
    } catch (NotFoundException $e) {
        throw new NotFoundException('File does not exist: ' . $path);
    }

    if (!($node instanceof File)) {
        throw new \RuntimeException('Path is a folder, not a file');
    }

    return $node->getContent();
}
```

### Update a File

```php
use OCP\Files\File;
use OCP\Files\NotFoundException;

public function updateDocument(string $userId, string $path, string $content): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    try {
        $file = $userFolder->get($path);
    } catch (NotFoundException $e) {
        throw new NotFoundException('Cannot update non-existent file: ' . $path);
    }

    if (!($file instanceof File)) {
        throw new \RuntimeException('Path is not a file');
    }

    $file->putContent($content);
}
```

### Delete a File

```php
use OCP\Files\NotFoundException;

public function deleteDocument(string $userId, string $path): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    try {
        $node = $userFolder->get($path);
        $node->delete();
    } catch (NotFoundException $e) {
        // Already deleted -- no action needed
    }
}
```

### Move / Rename a File

```php
public function moveFile(string $userId, string $sourcePath, string $targetPath): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $node = $userFolder->get($sourcePath);

    // move() expects the FULL internal path, not relative
    $targetFullPath = $userFolder->getPath() . '/' . $targetPath;
    $node->move($targetFullPath);
}
```

### Copy a File

```php
public function copyFile(string $userId, string $sourcePath, string $targetPath): int {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $node = $userFolder->get($sourcePath);

    $targetFullPath = $userFolder->getPath() . '/' . $targetPath;
    $copy = $node->copy($targetFullPath);
    return $copy->getId();
}
```

---

## File Lookup by ID

### Safe getById() Pattern

```php
use OCP\Files\File;
use OCP\Files\NotFoundException;

public function getFileById(string $userId, int $fileId): File {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $nodes = $userFolder->getById($fileId);

    // CRITICAL: getById() returns an ARRAY -- a file can appear in
    // multiple mount points (group folders, external storage).
    if (empty($nodes)) {
        throw new NotFoundException('No file found for ID: ' . $fileId);
    }

    $node = $nodes[0];
    if (!($node instanceof File)) {
        throw new \RuntimeException('Node is not a file');
    }

    return $node;
}
```

### Get File Metadata by ID

```php
public function getFileInfo(string $userId, int $fileId): array {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $nodes = $userFolder->getById($fileId);

    if (empty($nodes)) {
        throw new NotFoundException('File not found');
    }

    $node = $nodes[0];
    return [
        'id' => $node->getId(),
        'name' => $node->getName(),
        'path' => $userFolder->getRelativePath($node->getPath()),
        'size' => $node->getSize(),
        'mtime' => $node->getMTime(),
        'mimetype' => $node instanceof File ? $node->getMimeType() : 'httpd/unix-directory',
        'etag' => $node->getEtag(),
        'permissions' => $node->getPermissions(),
    ];
}
```

---

## Directory Operations

### List Folder Contents

```php
use OCP\Files\File;
use OCP\Files\Folder;
use OCP\Files\NotFoundException;

public function listFolder(string $userId, string $path = '/'): array {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    try {
        $folder = $userFolder->get($path);
    } catch (NotFoundException $e) {
        throw new NotFoundException('Folder not found: ' . $path);
    }

    if (!($folder instanceof Folder)) {
        throw new \RuntimeException('Path is not a folder');
    }

    $items = [];
    foreach ($folder->getDirectoryListing() as $node) {
        $items[] = [
            'name' => $node->getName(),
            'type' => $node instanceof File ? 'file' : 'folder',
            'size' => $node->getSize(),
            'mtime' => $node->getMTime(),
        ];
    }
    return $items;
}
```

### Recursive Folder Creation

```php
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
```

### Generate Unique Filename

```php
public function createUniqueFile(string $userId, string $folder, string $name, string $content): File {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $targetFolder = $userFolder->get($folder);

    if (!($targetFolder instanceof Folder)) {
        throw new \RuntimeException('Not a folder');
    }

    // getNonExistingName generates "file (2).txt", "file (3).txt", etc.
    $uniqueName = $targetFolder->getNonExistingName($name);
    return $targetFolder->newFile($uniqueName, $content);
}
```

---

## File Event Listeners

### Listen for File Writes

```php
// lib/AppInfo/Application.php
use OCA\MyApp\Listener\FileWrittenListener;
use OCP\Files\Events\Node\NodeWrittenEvent;

public function register(IRegistrationContext $context): void {
    $context->registerEventListener(
        NodeWrittenEvent::class,
        FileWrittenListener::class
    );
}
```

```php
// lib/Listener/FileWrittenListener.php
namespace OCA\MyApp\Listener;

use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeWrittenEvent;
use OCP\Files\File;

/** @template-implements IEventListener<NodeWrittenEvent> */
class FileWrittenListener implements IEventListener {
    public function handle(Event $event): void {
        if (!($event instanceof NodeWrittenEvent)) {
            return;
        }

        $node = $event->getNode();
        if (!($node instanceof File)) {
            return; // Ignore folder events
        }

        // Filter by MIME type
        if ($node->getMimeType() !== 'application/pdf') {
            return;
        }

        // Process the PDF...
    }
}
```

### Listen for Rename/Move Events

```php
// lib/Listener/FileRenamedListener.php
namespace OCA\MyApp\Listener;

use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeRenamedEvent;

/** @template-implements IEventListener<NodeRenamedEvent> */
class FileRenamedListener implements IEventListener {
    public function handle(Event $event): void {
        if (!($event instanceof NodeRenamedEvent)) {
            return;
        }

        $source = $event->getSource();
        $target = $event->getTarget();

        // $source->getPath() = old path
        // $target->getPath() = new path
    }
}
```

### Prevent Deletion (Before Event)

```php
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\BeforeNodeDeletedEvent;

/** @template-implements IEventListener<BeforeNodeDeletedEvent> */
class PreventDeleteListener implements IEventListener {
    public function handle(Event $event): void {
        if (!($event instanceof BeforeNodeDeletedEvent)) {
            return;
        }

        $node = $event->getNode();

        // Block deletion of protected files
        if (str_starts_with($node->getName(), '.protected-')) {
            throw new \OCP\Files\ForbiddenException('This file cannot be deleted', false);
        }
    }
}
```

---

## Storage Access (Advanced)

### Access Underlying Storage

```php
use OCP\Files\File;

public function getStorageInfo(File $file): array {
    $storage = $file->getStorage();

    return [
        'storage_id' => $storage->getId(),
        'is_local' => $storage->isLocal(),
        'free_space' => $storage->free_space('/'),
        'internal_path' => $file->getInternalPath(),
    ];
}
```

### Stream-Based File Processing

```php
public function processLargeFile(string $userId, string $path): int {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $file = $userFolder->get($path);

    if (!($file instanceof File)) {
        throw new \RuntimeException('Not a file');
    }

    $handle = $file->fopen('r');
    if ($handle === false) {
        throw new \RuntimeException('Cannot open file for reading');
    }

    $lineCount = 0;
    try {
        while (($line = fgets($handle)) !== false) {
            $lineCount++;
            // Process each line...
        }
    } finally {
        fclose($handle);
    }

    return $lineCount;
}
```

### Write via Stream

```php
public function writeFromStream(string $userId, string $path, $sourceStream): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    if ($userFolder->nodeExists($path)) {
        $file = $userFolder->get($path);
    } else {
        $file = $userFolder->newFile($path);
    }

    if (!($file instanceof File)) {
        throw new \RuntimeException('Not a file');
    }

    $handle = $file->fopen('w');
    if ($handle === false) {
        throw new \RuntimeException('Cannot open file for writing');
    }

    try {
        stream_copy_to_stream($sourceStream, $handle);
    } finally {
        fclose($handle);
    }
}
```

---

## Controller Integration

### File Download Endpoint

```php
namespace OCA\MyApp\Controller;

use OCA\MyApp\Service\FileService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\StreamResponse;
use OCP\AppFramework\Http\DownloadResponse;
use OCP\AppFramework\Http\JSONResponse;
use OCP\AppFramework\Http;
use OCP\Files\NotFoundException;
use OCP\IRequest;

class FileController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private FileService $fileService,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function download(int $fileId): DownloadResponse|JSONResponse {
        try {
            $file = $this->fileService->getFileById($this->userId, $fileId);
            $response = new DownloadResponse(
                $file->getContent(),
                $file->getName(),
                $file->getMimeType()
            );
            return $response;
        } catch (NotFoundException $e) {
            return new JSONResponse(
                ['message' => 'File not found'],
                Http::STATUS_NOT_FOUND
            );
        }
    }
}
```
