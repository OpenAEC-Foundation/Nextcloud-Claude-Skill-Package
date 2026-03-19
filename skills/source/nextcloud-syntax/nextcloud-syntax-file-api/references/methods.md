# File API Methods Reference

## IRootFolder (`OCP\Files\IRootFolder`)

The root of Nextcloud's virtual filesystem. ALWAYS inject via constructor dependency injection.

**Injection:**
```php
use OCP\Files\IRootFolder;

class MyService {
    public function __construct(private IRootFolder $rootFolder) {}
}
```

**Key methods:**

| Method | Return | Description |
|--------|--------|-------------|
| `getUserFolder(string $userId)` | `Folder` | Get user's home files folder |
| `get(string $path)` | `Node` | Get node by absolute internal path |
| `getById(int $id)` | `Node[]` | Get nodes by filecache ID |
| `nodeExists(string $path)` | `bool` | Check path existence |

**ALWAYS** use `getUserFolder()` to access user files. The returned `Folder` represents `/userid/files/` -- all paths relative to it map to the user's visible files.

---

## Folder (`OCP\Files\Folder`)

Represents a directory. Returned by `getUserFolder()`, `get()`, `newFolder()`.

### Navigation & Lookup

| Method | Return | Description |
|--------|--------|-------------|
| `get(string $path)` | `Node` | Get child node by relative path |
| `getById(int $id)` | `Node[]` | Lookup by filecache ID -- ALWAYS returns array |
| `nodeExists(string $path)` | `bool` | Check if child exists |
| `getDirectoryListing()` | `Node[]` | List all immediate children |
| `getNonExistingName(string $name)` | `string` | Generate unique name (appends ` (2)`, etc.) |

### Creation

| Method | Return | Description |
|--------|--------|-------------|
| `newFile(string $path, ?string $content = null)` | `File` | Create new file, optionally with content |
| `newFolder(string $path)` | `Folder` | Create new folder |

### Search

| Method | Return | Description |
|--------|--------|-------------|
| `search(ISearchQuery $query)` | `Node[]` | Search files within this folder |
| `searchByMime(string $mimeType)` | `Node[]` | Find by MIME type |
| `searchByTag(string $tag, string $userId)` | `Node[]` | Find by system tag |

### Search Query Construction

```php
use OCP\Files\Search\ISearchComparison;
use OCP\Files\Search\ISearchQuery;

// Via server container
$searchQuery = new \OCP\Files\Search\SearchQuery(
    new \OCP\Files\Search\SearchComparison(
        ISearchComparison::COMPARE_LIKE,
        'name',
        '%report%'
    ),
    limit: 50,
    offset: 0
);
$results = $userFolder->search($searchQuery);
```

**Searchable fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Filename (supports LIKE with `%`) |
| `mimetype` | `string` | MIME type |
| `mtime` | `int` | Modification timestamp |
| `size` | `int` | File size in bytes |
| `fileid` | `int` | Filecache ID |

---

## File (`OCP\Files\File`)

Represents a file. Extends `Node` with content access methods.

### Content Methods

| Method | Return | Description |
|--------|--------|-------------|
| `getContent()` | `string` | Read entire file into memory |
| `putContent(string $data)` | `void` | Write/overwrite entire file content |
| `fopen(string $mode)` | `resource\|false` | Open as PHP stream |
| `hash(string $type, bool $raw = false)` | `string` | Calculate file hash (md5, sha1, sha256) |

**fopen() modes:**

| Mode | Description |
|------|-------------|
| `'r'` | Read only |
| `'rb'` | Read only, binary |
| `'w'` | Write only (truncate) |
| `'wb'` | Write only, binary (truncate) |
| `'a'` | Append |
| `'r+'` | Read/write |

### Metadata Methods

| Method | Return | Description |
|--------|--------|-------------|
| `getMimeType()` | `string` | MIME type (e.g., `text/plain`) |
| `getMimePart()` | `string` | First part of MIME (e.g., `text`) |
| `getSize()` | `int\|float` | Size in bytes |
| `getChecksum()` | `string` | Server-stored checksum |

---

## Node (`OCP\Files\Node`)

Base interface for both File and Folder. All methods below are available on both.

### Identity & Path

| Method | Return | Description |
|--------|--------|-------------|
| `getId()` | `int` | Filecache ID (unique per storage) |
| `getName()` | `string` | Base name (e.g., `report.pdf`) |
| `getPath()` | `string` | Full internal path (e.g., `/admin/files/Documents/report.pdf`) |
| `getInternalPath()` | `string` | Path relative to storage root |
| `getEtag()` | `string` | ETag (changes on modification) |
| `getType()` | `int` | `FileInfo::TYPE_FILE` or `FileInfo::TYPE_FOLDER` |

### Timestamps & Permissions

| Method | Return | Description |
|--------|--------|-------------|
| `getMTime()` | `int` | Last modification Unix timestamp |
| `getCreationTime()` | `int` | Creation timestamp (NC 28+) |
| `getUploadTime()` | `int` | Upload timestamp (NC 28+) |
| `getPermissions()` | `int` | Permission bitmask |
| `isReadable()` | `bool` | Current user can read |
| `isUpdateable()` | `bool` | Current user can write |
| `isDeletable()` | `bool` | Current user can delete |
| `isShareable()` | `bool` | Current user can share |

### Operations

| Method | Return | Description |
|--------|--------|-------------|
| `delete()` | `void` | Move to trash (or permanent delete) |
| `move(string $targetPath)` | `Node` | Move or rename |
| `copy(string $targetPath)` | `Node` | Copy to target path |
| `touch(int $mtime = null)` | `void` | Update modification time |
| `getParent()` | `Folder` | Parent folder |
| `getStorage()` | `IStorage` | Underlying storage backend |

### Locking

| Method | Return | Description |
|--------|--------|-------------|
| `lock(int $type)` | `void` | Acquire lock |
| `unlock(int $type)` | `void` | Release lock |
| `changeLock(int $targetType)` | `void` | Change lock type |

Lock types: `ILockingProvider::LOCK_SHARED`, `ILockingProvider::LOCK_EXCLUSIVE`.

### Permission Constants (`OCP\Constants`)

| Constant | Value | Meaning |
|----------|-------|---------|
| `PERMISSION_READ` | 1 | Can read |
| `PERMISSION_UPDATE` | 2 | Can write |
| `PERMISSION_CREATE` | 4 | Can create children |
| `PERMISSION_DELETE` | 8 | Can delete |
| `PERMISSION_SHARE` | 16 | Can share |
| `PERMISSION_ALL` | 31 | All permissions |

---

## Storage Interface (`OCP\Files\Storage\IStorage`)

Low-level storage backend access. ALWAYS prefer the Node API (File/Folder) over direct storage access.

**When to use storage directly:**
- Custom storage backend implementation
- Migrating data between storage backends
- Direct performance-critical batch operations

| Method | Return | Description |
|--------|--------|-------------|
| `file_get_contents(string $path)` | `string\|false` | Read file from storage |
| `file_put_contents(string $path, mixed $data)` | `int\|float\|false` | Write file to storage |
| `mkdir(string $path)` | `bool` | Create directory |
| `rmdir(string $path)` | `bool` | Remove directory |
| `unlink(string $path)` | `bool` | Delete file |
| `stat(string $path)` | `array\|false` | Get file stats |
| `getMetaData(string $path)` | `?array` | Get file metadata |

**NEVER** use `IStorage` methods when `File::getContent()` / `File::putContent()` suffice -- the Node API handles events, caching, and access control automatically.
