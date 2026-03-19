# File Operations Implementation Methods Reference

> This reference focuses on method usage in implementation workflows. For raw API signatures, see [nextcloud-syntax-file-api methods](../../../nextcloud-syntax/nextcloud-syntax-file-api/references/methods.md).

## IRootFolder — Entry Point Methods

| Method | Return | Implementation Usage |
|--------|--------|---------------------|
| `getUserFolder(string $userId)` | `Folder` | ALWAYS the first call in any service method |
| `getById(int $id)` | `Node[]` | System-level file lookup (admin tools) |

**ALWAYS** inject `IRootFolder` and call `getUserFolder()` per-request. NEVER cache the user folder across requests.

```php
// CORRECT: Get user folder per method call
public function doWork(string $userId): void {
    $userFolder = $this->rootFolder->getUserFolder($userId);
}

// WRONG: Caching user folder as class property
private Folder $userFolder; // NEVER do this
```

---

## Folder — CRUD Workflow Methods

### Existence Checking

| Method | Return | When to Use |
|--------|--------|-------------|
| `nodeExists(string $path)` | `bool` | Before `newFile()` / `newFolder()` to avoid exceptions |
| `get(string $path)` | `Node` | When you need the node AND know it should exist |

**Pattern: Check-then-act vs. try-catch**

```php
// PREFERRED for upsert workflows: try-catch (atomic)
try {
    $file = $userFolder->get($path);
    $file->putContent($content);
} catch (NotFoundException) {
    $userFolder->newFile($path, $content);
}

// ACCEPTABLE for conditional logic: check-then-act
if ($userFolder->nodeExists($path)) {
    $file = $userFolder->get($path);
    // ... modify existing
} else {
    // ... create new
}
```

**ALWAYS** prefer try-catch for upsert operations -- `nodeExists()` followed by `get()` has a race condition window in multi-user environments.

### Creation

| Method | Return | Throws | Notes |
|--------|--------|--------|-------|
| `newFile(string $path, ?string $content)` | `File` | `NotPermittedException` | Throws if file exists |
| `newFolder(string $path)` | `Folder` | `NotPermittedException` | Throws if folder exists |
| `getNonExistingName(string $name)` | `string` | — | Returns `file (2).txt` style names |

**ALWAYS** use `getNonExistingName()` when users upload files to avoid silent overwrites:

```php
$safeName = $targetFolder->getNonExistingName($originalName);
$targetFolder->newFile($safeName, $content);
```

### Listing & Search

| Method | Return | Performance Notes |
|--------|--------|-------------------|
| `getDirectoryListing()` | `Node[]` | Fine for folders with <1000 items |
| `search(ISearchQuery $query)` | `Node[]` | ALWAYS set limit parameter |
| `searchByMime(string $mime)` | `Node[]` | Convenience, no limit param — use with caution |
| `searchByTag(string $tag, string $userId)` | `Node[]` | Requires system tags app |

---

## File — Content Methods

| Method | Max File Size | Use Case |
|--------|---------------|----------|
| `getContent()` | <5MB recommended | Config files, JSON, small text |
| `putContent(string $data)` | <5MB recommended | Writing config, small data |
| `fopen(string $mode)` | Unlimited | Large files, binary data, streaming |

### Stream Mode Selection

| Mode | Use Case | Creates File? |
|------|----------|---------------|
| `'r'` | Read file contents | No |
| `'w'` | Overwrite entire file | No (must exist) |
| `'a'` | Append to file (logs) | No (must exist) |
| `'r+'` | Read and write | No (must exist) |

**ALWAYS** check the return value of `fopen()` -- it returns `false` on failure:

```php
$handle = $file->fopen('r');
if ($handle === false) {
    throw new \RuntimeException('Cannot open file: ' . $file->getPath());
}
```

---

## Node — Operation Methods

### Move & Copy

| Method | Path Type | Returns |
|--------|-----------|---------|
| `move(string $targetPath)` | Full internal path | `Node` at new location |
| `copy(string $targetPath)` | Full internal path | New `Node` (copy) |

**ALWAYS** construct full paths for `move()` and `copy()`:

```php
// Build target path from user folder root
$targetFullPath = $userFolder->getPath() . '/' . $newRelativePath;
$node->move($targetFullPath);
```

**NEVER** pass relative paths to `move()` or `copy()` -- they require the full internal path starting with `/{userId}/files/`.

### Delete

| Method | Behavior |
|--------|----------|
| `delete()` | Moves to trash (if trashbin app enabled), otherwise permanent |

**ALWAYS** handle delete idempotently -- wrap in try/catch for `NotFoundException`:

```php
try {
    $node = $userFolder->get($path);
    $node->delete();
} catch (NotFoundException) {
    // Already gone -- no action needed
}
```

### Metadata for API Responses

**ALWAYS** use `getRelativePath()` when returning paths to the frontend:

```php
$userFolder = $this->rootFolder->getUserFolder($userId);
$relativePath = $userFolder->getRelativePath($node->getPath());
// Returns "Documents/report.pdf" instead of "/admin/files/Documents/report.pdf"
```

---

## Search Query Construction

### SearchComparison Operators

| Operator | Constant | Example |
|----------|----------|---------|
| `=` | `COMPARE_EQUAL` | Exact match |
| `>` | `COMPARE_GREATER_THAN` | Size/date filtering |
| `<` | `COMPARE_LESS_THAN` | Size/date filtering |
| `>=` | `COMPARE_GREATER_THAN_OR_EQUAL` | Size/date filtering |
| `<=` | `COMPARE_LESS_THAN_OR_EQUAL` | Size/date filtering |
| `LIKE` | `COMPARE_LIKE` | Wildcard name search (`%pattern%`) |
| `DEFINED` | `COMPARE_DEFINED` | Field exists |

### Combining Conditions

```php
use OCP\Files\Search\SearchBinaryOperator;

// AND: both conditions must match
$query = new SearchQuery(
    new SearchBinaryOperator(
        SearchBinaryOperator::OPERATOR_AND,
        [
            new SearchComparison(ISearchComparison::COMPARE_LIKE, 'name', '%.pdf'),
            new SearchComparison(ISearchComparison::COMPARE_GREATER_THAN, 'size', 1024 * 1024),
        ]
    ),
    limit: 100,
    offset: 0
);

// OR: either condition matches
$query = new SearchQuery(
    new SearchBinaryOperator(
        SearchBinaryOperator::OPERATOR_OR,
        [
            new SearchComparison(ISearchComparison::COMPARE_LIKE, 'mimetype', 'image/%'),
            new SearchComparison(ISearchComparison::COMPARE_LIKE, 'mimetype', 'video/%'),
        ]
    ),
    limit: 50,
    offset: 0
);
```

---

## Event Method Reference

### Single-Node Events

| Event Class | Method | Returns |
|-------------|--------|---------|
| `NodeCreatedEvent` | `getNode()` | Created `Node` |
| `NodeWrittenEvent` | `getNode()` | Written `File` |
| `NodeDeletedEvent` | `getNode()` | Deleted `Node` (still accessible in handler) |
| `NodeTouchedEvent` | `getNode()` | Touched `Node` |

### Two-Node Events (Move/Copy)

| Event Class | Methods | Returns |
|-------------|---------|---------|
| `NodeRenamedEvent` | `getSource()`, `getTarget()` | Old and new `Node` |
| `NodeCopiedEvent` | `getSource()`, `getTarget()` | Original and copy `Node` |

### Favorite Events (NC 28+)

| Event Class | Method | Returns |
|-------------|--------|---------|
| `NodeAddedToFavorite` | `getNode()` | Favorited `Node` |
| `NodeRemovedFromFavorite` | `getNode()` | Unfavorited `Node` |

**ALWAYS** filter by event type AND node type in handlers:

```php
public function handle(Event $event): void {
    if (!($event instanceof NodeWrittenEvent)) {
        return;
    }
    $node = $event->getNode();
    if (!($node instanceof File)) {
        return;
    }
    // Now safe to use File-specific methods
}
```
