# File Operations Implementation Anti-Patterns

## AP-01: File Logic in Controllers

**WRONG** -- Putting file operations directly in the controller:
```php
class FileController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private IRootFolder $rootFolder,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function save(string $path, string $content): JSONResponse {
        $userFolder = $this->rootFolder->getUserFolder($this->userId);
        try {
            $file = $userFolder->get($path);
            $file->putContent($content);
        } catch (NotFoundException) {
            $userFolder->newFile($path, $content);
        }
        return new JSONResponse(['status' => 'ok']);
    }
}
```

**RIGHT** -- Delegate to a service class:
```php
class FileController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private FileOperationService $fileService,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function save(string $path, string $content): JSONResponse {
        $result = $this->fileService->upsertFile($this->userId, $path, $content);
        return new JSONResponse($result);
    }
}
```

**Why**: Controllers should only handle HTTP request/response. File operation logic in controllers cannot be reused by background jobs, OCC commands, or other services. ALWAYS use a dedicated service.

---

## AP-02: Caching User Folder as Class Property

**WRONG** -- Storing the user folder as a persistent property:
```php
class FileService {
    private Folder $userFolder;

    public function __construct(private IRootFolder $rootFolder) {
        // WRONG: userId may not be available at construction time
        $this->userFolder = $rootFolder->getUserFolder('admin');
    }
}
```

**RIGHT** -- Resolve user folder per method call:
```php
class FileService {
    public function __construct(private IRootFolder $rootFolder) {}

    public function readFile(string $userId, string $path): string {
        $userFolder = $this->rootFolder->getUserFolder($userId);
        // ... use $userFolder
    }
}
```

**Why**: Services are shared singletons in Nextcloud's DI container. Caching a user folder binds the service to one user, causing data leaks between requests. ALWAYS resolve `getUserFolder()` per method call with an explicit `$userId` parameter.

---

## AP-03: Missing Parent Directory Creation

**WRONG** -- Creating a file without ensuring its parent directory exists:
```php
public function saveReport(string $userId, string $content): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    // Throws NotFoundException if "Reports/2024" does not exist
    $userFolder->newFile('Reports/2024/Q4.pdf', $content);
}
```

**RIGHT** -- ALWAYS ensure parent directories exist before creating files:
```php
public function saveReport(string $userId, string $content): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    // Ensure full directory path exists
    $this->ensureFolderExists($userFolder, 'Reports/2024');
    $userFolder->newFile('Reports/2024/Q4.pdf', $content);
}
```

**Why**: `newFile()` does NOT create intermediate directories. If the parent path does not exist, the operation fails. ALWAYS use a recursive folder-creation helper.

---

## AP-04: Heavy Processing in Event Listeners

**WRONG** -- Doing expensive work directly in a listener:
```php
class FileCreatedListener implements IEventListener {
    public function handle(Event $event): void {
        $node = $event->getNode();
        if ($node instanceof File) {
            // WRONG: Blocks the file creation request
            $content = $node->getContent();
            $this->ocrService->processDocument($content); // Takes 30 seconds
            $this->indexService->indexFile($node);         // Takes 10 seconds
        }
    }
}
```

**RIGHT** -- Defer heavy work to background jobs:
```php
class FileCreatedListener implements IEventListener {
    public function __construct(private IJobList $jobList) {}

    public function handle(Event $event): void {
        $node = $event->getNode();
        if ($node instanceof File && $node->getMimeType() === 'application/pdf') {
            $this->jobList->add(ProcessDocumentJob::class, [
                'fileId' => $node->getId(),
                'userId' => $node->getOwner()->getUID(),
            ]);
        }
    }
}
```

**Why**: Event listeners run synchronously during the original operation. Slow listeners block file uploads and make the UI unresponsive. ALWAYS queue heavy work as background jobs.

---

## AP-05: Not Filtering Events Early

**WRONG** -- Doing work before checking if the event is relevant:
```php
class FileWrittenListener implements IEventListener {
    public function handle(Event $event): void {
        // WRONG: expensive service initialization before checking relevance
        $config = $this->configService->loadProcessingRules();
        $plugins = $this->pluginManager->getActivePlugins();

        if (!($event instanceof NodeWrittenEvent)) {
            return;
        }

        $node = $event->getNode();
        if ($node->getMimeType() !== 'application/json') {
            return;
        }
    }
}
```

**RIGHT** -- ALWAYS filter first, then do work:
```php
class FileWrittenListener implements IEventListener {
    public function handle(Event $event): void {
        if (!($event instanceof NodeWrittenEvent)) {
            return;
        }

        $node = $event->getNode();
        if (!($node instanceof File)) {
            return;
        }

        if ($node->getMimeType() !== 'application/json') {
            return;
        }

        // NOW do expensive work -- we know the event is relevant
        $config = $this->configService->loadProcessingRules();
        $this->process($node, $config);
    }
}
```

**Why**: Event listeners fire for ALL file operations across ALL apps. Without early filtering, your listener wastes resources on irrelevant events.

---

## AP-06: Forgetting Unique Name Generation on Upload

**WRONG** -- Overwriting existing files on upload:
```php
public function handleUpload(string $userId, string $name, string $content): File {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    // WRONG: Overwrites existing "photo.jpg" silently
    if ($userFolder->nodeExists($name)) {
        $file = $userFolder->get($name);
        $file->putContent($content);
        return $file;
    }
    return $userFolder->newFile($name, $content);
}
```

**RIGHT** -- Use `getNonExistingName()` for user uploads:
```php
public function handleUpload(string $userId, string $name, string $content): File {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $safeName = $userFolder->getNonExistingName($name);
    return $userFolder->newFile($safeName, $content);
}
```

**Why**: Users expect uploads to create new files, not overwrite existing ones. `getNonExistingName()` generates `photo (2).jpg`, `photo (3).jpg`, etc., matching Nextcloud's built-in behavior.

---

## AP-07: Using getContent() for Large Files

**WRONG** -- Loading a multi-gigabyte file into memory:
```php
public function processVideo(string $userId, string $path): void {
    $file = $this->getFile($userId, $path);
    $content = $file->getContent(); // 2GB file = 2GB in PHP memory
    $this->analyzer->analyze($content);
}
```

**RIGHT** -- ALWAYS stream files larger than 5MB:
```php
public function processVideo(string $userId, string $path): void {
    $file = $this->getFile($userId, $path);

    if ($file->getSize() > 5 * 1024 * 1024) {
        $handle = $file->fopen('r');
        if ($handle === false) {
            throw new \RuntimeException('Cannot open file');
        }
        try {
            $this->analyzer->analyzeStream($handle);
        } finally {
            fclose($handle);
        }
    } else {
        $this->analyzer->analyze($file->getContent());
    }
}
```

**Why**: `getContent()` loads the entire file into PHP memory. This crashes requests when the file exceeds PHP's memory limit. ALWAYS check file size and stream when needed.

---

## AP-08: Ignoring NotPermittedException on Create

**WRONG** -- Not handling the case where a file already exists:
```php
public function initializeConfig(string $userId): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    // Throws NotPermittedException if config.json already exists
    $userFolder->newFile('config.json', '{"version": 1}');
}
```

**RIGHT** -- Check existence or catch the exception:
```php
public function initializeConfig(string $userId): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);

    if ($userFolder->nodeExists('config.json')) {
        return; // Already initialized
    }

    try {
        $userFolder->newFile('config.json', '{"version": 1}');
    } catch (NotPermittedException) {
        // Race condition: another request created it between check and create
        return;
    }
}
```

**Why**: `newFile()` throws `NotPermittedException` when a file already exists. In multi-user or concurrent environments, ALWAYS handle this exception even after a `nodeExists()` check.

---

## AP-09: Returning Internal Paths to Frontend

**WRONG** -- Exposing internal filesystem paths to API consumers:
```php
public function getFileInfo(string $userId, int $fileId): array {
    $file = $this->getFileById($userId, $fileId);
    return [
        'path' => $file->getPath(), // Returns "/admin/files/Documents/report.pdf"
    ];
}
```

**RIGHT** -- ALWAYS use `getRelativePath()` for user-facing paths:
```php
public function getFileInfo(string $userId, int $fileId): array {
    $userFolder = $this->rootFolder->getUserFolder($userId);
    $file = $this->getFileById($userId, $fileId);
    return [
        'path' => $userFolder->getRelativePath($file->getPath()), // Returns "Documents/report.pdf"
    ];
}
```

**Why**: Internal paths contain the user ID and internal directory structure (`/{userId}/files/`). Exposing them leaks implementation details and breaks if internal structure changes. ALWAYS convert to relative paths for API responses.

---

## AP-10: Direct Storage Access for Standard Operations

**WRONG** -- Bypassing the Node API for regular file operations:
```php
public function updateFile(File $file, string $content): void {
    $storage = $file->getStorage();
    $storage->file_put_contents($file->getInternalPath(), $content);
}
```

**RIGHT** -- Use the Node API:
```php
public function updateFile(File $file, string $content): void {
    $file->putContent($content);
}
```

**Why**: Direct storage access bypasses event dispatching, cache invalidation, encryption, versioning, and access control. The Node API handles all of these automatically. ONLY use direct storage access for custom storage backend implementations or batch migrations where Node API is provably insufficient.
