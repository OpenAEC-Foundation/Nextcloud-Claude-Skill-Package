# File API Anti-Patterns Reference

## AP-01: Assuming getById() Returns a Single Node

**WRONG** -- Treating `getById()` result as a single node:
```php
$file = $userFolder->getById($fileId);
$content = $file->getContent(); // FATAL: calling method on array
```

**RIGHT** -- ALWAYS treat `getById()` as returning an array:
```php
$nodes = $userFolder->getById($fileId);
if (empty($nodes)) {
    throw new NotFoundException('File not found');
}
$file = $nodes[0];
if (!($file instanceof File)) {
    throw new \RuntimeException('Not a file');
}
$content = $file->getContent();
```

**Why**: A single file ID can appear in multiple mount points (group folders, external storage). `getById()` returns ALL matching nodes as an array.

---

## AP-02: Missing NotFoundException Handling

**WRONG** -- Accessing files without exception handling:
```php
$file = $userFolder->get('Documents/report.pdf');
$content = $file->getContent();
```

**RIGHT** -- ALWAYS wrap file access in try/catch:
```php
try {
    $file = $userFolder->get('Documents/report.pdf');
    if (!($file instanceof File)) {
        throw new \RuntimeException('Not a file');
    }
    $content = $file->getContent();
} catch (NotFoundException $e) {
    // Handle missing file gracefully
    throw new NotFoundException('File does not exist');
}
```

**Why**: Files can be deleted or moved between the time you check and the time you access. Race conditions are common in multi-user environments.

---

## AP-03: Hardcoded Absolute Paths

**WRONG** -- Using internal filesystem paths directly:
```php
$file = $rootFolder->get('/admin/files/Documents/report.pdf');
```

**RIGHT** -- ALWAYS use getUserFolder() for user file access:
```php
$userFolder = $rootFolder->getUserFolder('admin');
$file = $userFolder->get('Documents/report.pdf');
```

**Why**: Internal path structure (`/{userId}/files/`) is an implementation detail. `getUserFolder()` abstracts this and handles mount points, encryption, and storage backends correctly.

---

## AP-04: Not Checking Node Type After get()

**WRONG** -- Assuming `get()` returns a File:
```php
$node = $userFolder->get('Documents/report.pdf');
$content = $node->getContent(); // May fail if $node is a Folder
```

**RIGHT** -- ALWAYS check instanceof before using type-specific methods:
```php
$node = $userFolder->get('Documents/report.pdf');
if (!($node instanceof \OCP\Files\File)) {
    throw new \RuntimeException('Expected a file, got a folder');
}
$content = $node->getContent();
```

**Why**: `Folder::get()` returns `Node`, which could be either `File` or `Folder`. Calling `getContent()` on a `Folder` throws an error.

---

## AP-05: Loading Large Files into Memory

**WRONG** -- Reading a large file entirely into memory:
```php
$content = $file->getContent(); // 2GB file = 2GB memory usage
$this->processContent($content);
```

**RIGHT** -- Use streaming for large files:
```php
$handle = $file->fopen('r');
if ($handle === false) {
    throw new \RuntimeException('Cannot open file');
}
try {
    while (!feof($handle)) {
        $chunk = fread($handle, 8192);
        $this->processChunk($chunk);
    }
} finally {
    fclose($handle);
}
```

**Why**: `getContent()` loads the entire file into PHP memory. For files larger than a few MB, this can exhaust the memory limit and crash the request.

---

## AP-06: Injecting IUserFolder Directly

**WRONG** -- Attempting to inject IUserFolder via DI:
```php
class MyService {
    public function __construct(private IUserFolder $userFolder) {} // Will fail
}
```

**RIGHT** -- ALWAYS inject IRootFolder and call getUserFolder():
```php
use OCP\Files\IRootFolder;

class MyService {
    public function __construct(private IRootFolder $rootFolder) {}

    public function doWork(string $userId): void {
        $userFolder = $this->rootFolder->getUserFolder($userId);
        // ...
    }
}
```

**Why**: `IUserFolder` is not a registered DI service. The root folder is the injection point; user folders are obtained at runtime when the user context is known.

---

## AP-07: Using move() with Relative Paths

**WRONG** -- Passing a relative path to move():
```php
$file = $userFolder->get('old-name.txt');
$file->move('new-name.txt'); // Fails: move() expects full internal path
```

**RIGHT** -- ALWAYS use the full internal path for move() and copy():
```php
$file = $userFolder->get('old-name.txt');
$targetPath = $userFolder->getPath() . '/new-name.txt';
$file->move($targetPath);
```

**Why**: `move()` and `copy()` operate on the full internal filesystem path (e.g., `/admin/files/new-name.txt`), not paths relative to the user folder.

---

## AP-08: Forgetting to Check nodeExists() Before newFile()

**WRONG** -- Creating a file without checking existence:
```php
$userFolder->newFile('config.json', $defaultContent);
// Throws NotPermittedException if file already exists
```

**RIGHT** -- Check existence first or use upsert pattern:
```php
if ($userFolder->nodeExists('config.json')) {
    $file = $userFolder->get('config.json');
    if ($file instanceof File) {
        $file->putContent($newContent);
    }
} else {
    $userFolder->newFile('config.json', $newContent);
}
```

**Why**: `newFile()` throws `NotPermittedException` if the file already exists. ALWAYS check with `nodeExists()` or wrap in try/catch.

---

## AP-09: Registering Event Listeners in boot() Instead of register()

**WRONG** -- Registering listeners in the boot phase:
```php
class Application extends App implements IBootstrap {
    public function boot(IBootContext $context): void {
        // WRONG: event listeners should be in register()
        $dispatcher = $context->getServerContainer()->get(IEventDispatcher::class);
        $dispatcher->addListener(NodeCreatedEvent::class, function ($event) {
            // ...
        });
    }
}
```

**RIGHT** -- ALWAYS register event listeners in register():
```php
class Application extends App implements IBootstrap {
    public function register(IRegistrationContext $context): void {
        $context->registerEventListener(
            NodeCreatedEvent::class,
            FileCreatedListener::class
        );
    }

    public function boot(IBootContext $context): void {}
}
```

**Why**: The `register()` method is called during app loading and is the correct place for declarative registrations. The `boot()` method runs later and using it for listeners can cause missed events during early server operations.

---

## AP-10: Accessing Storage Layer Unnecessarily

**WRONG** -- Bypassing the Node API for simple file operations:
```php
$storage = $file->getStorage();
$content = $storage->file_get_contents($file->getInternalPath());
$storage->file_put_contents($file->getInternalPath(), $newContent);
```

**RIGHT** -- Use the Node API for standard operations:
```php
$content = $file->getContent();
$file->putContent($newContent);
```

**Why**: The Node API handles event dispatching, cache invalidation, encryption, versioning, and access control. Direct storage access bypasses ALL of these, leading to stale caches, missing version history, and security gaps.

---

## AP-11: Not Closing File Handles

**WRONG** -- Opening a stream without ensuring cleanup:
```php
$handle = $file->fopen('r');
$content = stream_get_contents($handle);
// If an exception occurs above, handle is never closed
```

**RIGHT** -- ALWAYS use try/finally to close file handles:
```php
$handle = $file->fopen('r');
if ($handle === false) {
    throw new \RuntimeException('Cannot open file');
}
try {
    $content = stream_get_contents($handle);
} finally {
    fclose($handle);
}
```

**Why**: Unclosed file handles leak resources and can cause locking issues, especially on external storage backends.
