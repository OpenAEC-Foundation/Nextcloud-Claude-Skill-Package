# Testing Anti-Patterns Reference

## Setup & Teardown Anti-Patterns

### AP-01: Missing parent::setUp() Call

**WRONG** -- Skipping the parent call:
```php
class NoteServiceTest extends TestCase {
    protected function setUp(): void {
        // Missing parent::setUp() — database transactions not started,
        // cleanup hooks not registered, test environment not initialized
        $this->mapper = $this->createMock(NoteMapper::class);
        $this->service = new NoteService($this->mapper);
    }
}
```
Result: Test pollution, random failures, database state leaking between tests.

**RIGHT** -- ALWAYS call parent::setUp() as the FIRST line:
```php
class NoteServiceTest extends TestCase {
    protected function setUp(): void {
        parent::setUp(); // ALWAYS first
        $this->mapper = $this->createMock(NoteMapper::class);
        $this->service = new NoteService($this->mapper);
    }
}
```

### AP-02: Missing parent::tearDown() Call

**WRONG** -- Custom tearDown without parent call:
```php
protected function tearDown(): void {
    $this->cleanupTestFiles();
    // Missing parent::tearDown() — database transaction not rolled back
}
```
Result: Test data persists in the database, affecting subsequent tests.

**RIGHT** -- ALWAYS call parent::tearDown() as the LAST line:
```php
protected function tearDown(): void {
    $this->cleanupTestFiles();
    parent::tearDown(); // ALWAYS last
}
```

### AP-03: Wrong Bootstrap Path

**WRONG** -- Incorrect or missing bootstrap in phpunit.xml:
```xml
<phpunit bootstrap="vendor/autoload.php">
```
Result: Nextcloud classes are not loaded. `\Test\TestCase` is undefined.

**RIGHT** -- ALWAYS use the Nextcloud test bootstrap:
```xml
<phpunit bootstrap="../../tests/bootstrap.php">
```
This path is relative from your app root (`apps/myapp/`) to the server `tests/` directory.

---

## Mocking Anti-Patterns

### AP-04: Static Container Access in Tests

**WRONG** -- Using Server::get() in test code:
```php
protected function setUp(): void {
    parent::setUp();
    $this->service = \OCP\Server::get(NoteService::class); // WRONG in unit tests
}
```
Result: Pulls in real dependencies, making tests slow, fragile, and order-dependent.

**RIGHT** -- ALWAYS mock dependencies for unit tests:
```php
protected function setUp(): void {
    parent::setUp();
    $this->mapper = $this->createMock(NoteMapper::class);
    $this->service = new NoteService($this->mapper);
}
```

Use `Server::get()` or container resolution ONLY in integration tests where real dependencies are the point.

### AP-05: Mocking the Class Under Test

**WRONG** -- Creating a mock of the class you are testing:
```php
public function testCreate(): void {
    $service = $this->createMock(NoteService::class); // WRONG: testing a mock
    $service->method('create')->willReturn(new Note());
    $result = $service->create('title', 'content', 'user');
    $this->assertNotNull($result);
}
```
Result: You are testing PHPUnit's mock framework, not your code.

**RIGHT** -- ALWAYS instantiate the real class, mock only its DEPENDENCIES:
```php
public function testCreate(): void {
    $mapper = $this->createMock(NoteMapper::class);
    $mapper->method('insert')->willReturnCallback(function (Note $n) {
        $n->setId(1);
        return $n;
    });
    $service = new NoteService($mapper);
    $result = $service->create('title', 'content', 'user');
    $this->assertNotNull($result->getId());
}
```

### AP-06: Over-Mocking (Mocking Value Objects)

**WRONG** -- Mocking simple data objects:
```php
$note = $this->createMock(Note::class); // WRONG: Note is a simple entity
$note->method('getTitle')->willReturn('Test');
$note->method('getId')->willReturn(1);
```
Result: Fragile tests that break when entity methods change. Hides bugs in entity logic.

**RIGHT** -- ALWAYS use real instances for entities and value objects:
```php
$note = new Note();
$note->setId(1);
$note->setTitle('Test');
```

### AP-07: No Expectations on Critical Mocks

**WRONG** -- Stubbing without verifying the call happens:
```php
$this->mapper->method('delete')->willReturn(true);
$this->service->delete(1, 'user1');
// Test passes even if delete() was never called
```

**RIGHT** -- ALWAYS use expects() when the method call IS the behavior you are testing:
```php
$this->mapper->expects($this->once())
    ->method('delete')
    ->with($this->callback(fn(Note $n) => $n->getId() === 1));
$this->service->delete(1, 'user1');
```

---

## Test Structure Anti-Patterns

### AP-08: Testing Multiple Behaviors in One Test

**WRONG** -- One test method testing many things:
```php
public function testNoteService(): void {
    $created = $this->service->create('Test', '', 'user1');
    $this->assertNotNull($created);
    $found = $this->service->find($created->getId(), 'user1');
    $this->assertEquals('Test', $found->getTitle());
    $this->service->delete($created->getId(), 'user1');
    $this->expectException(NotFoundException::class);
    $this->service->find($created->getId(), 'user1');
}
```
Result: When this test fails, you cannot tell WHICH behavior broke.

**RIGHT** -- ALWAYS test one behavior per test method:
```php
public function testCreate(): void {
    $result = $this->service->create('Test', '', 'user1');
    $this->assertNotNull($result->getId());
}

public function testFind(): void {
    // separate setup and assertion
}

public function testDelete(): void {
    // separate setup and assertion
}
```

### AP-09: Missing Error Path Tests

**WRONG** -- Only testing the happy path:
```php
public function testFind(): void {
    $this->mapper->method('find')->willReturn($note);
    $result = $this->service->find(1, 'user1');
    $this->assertNotNull($result);
}
// No test for: What if the note does not exist?
// No test for: What if the user does not own the note?
```

**RIGHT** -- ALWAYS test both success and failure paths:
```php
public function testFind(): void { /* happy path */ }
public function testFindNotFound(): void { /* DoesNotExistException */ }
public function testFindWrongUser(): void { /* unauthorized access */ }
```

### AP-10: Hardcoded Test Data Without Meaning

**WRONG** -- Magic numbers and strings with no context:
```php
$this->service->create('abc', 'xyz', 'u1');
$result = $this->service->find(42, 'u1');
```

**RIGHT** -- ALWAYS use descriptive test data:
```php
$this->service->create('Meeting Notes', 'Q4 Planning discussion', 'alice');
$result = $this->service->find($createdNote->getId(), 'alice');
```

---

## Integration Test Anti-Patterns

### AP-11: Real Database in Unit Tests

**WRONG** -- Hitting the database in a unit test:
```php
// In tests/Unit/Service/NoteServiceTest.php
protected function setUp(): void {
    parent::setUp();
    $app = new App('myapp');
    $this->service = $app->getContainer()->get(NoteService::class);
    // This resolves real DB connections — wrong for unit tests
}
```
Result: Slow tests, dependency on database state, not isolated.

**RIGHT** -- ALWAYS mock database access in unit tests. Use real DB only in integration tests:
```php
// Unit test: mock everything
$this->mapper = $this->createMock(NoteMapper::class);
$this->service = new NoteService($this->mapper);

// Integration test: use real DI container
$app = new App('myapp');
$this->service = $app->getContainer()->get(NoteService::class);
```

### AP-12: Not Using @group DB Annotation

**WRONG** -- Integration test without the DB group:
```php
class NoteServiceIntegrationTest extends TestCase {
    // Missing @group DB — test may run in unit test suite
}
```

**RIGHT** -- ALWAYS annotate integration tests that use the database:
```php
/**
 * @group DB
 */
class NoteServiceIntegrationTest extends TestCase {
    // Now correctly categorized
}
```

---

## Frontend Test Anti-Patterns

### AP-13: Not Mocking @nextcloud Packages

**WRONG** -- Importing real @nextcloud packages in tests:
```typescript
import axios from '@nextcloud/axios' // Tries to import real package
// Fails because @nextcloud/axios depends on browser globals
```

**RIGHT** -- ALWAYS mock @nextcloud packages:
```typescript
jest.mock('@nextcloud/axios')
jest.mock('@nextcloud/router')
```

Or use moduleNameMapper in jest.config.js for automatic mocking.

### AP-14: Not Awaiting Async Updates

**WRONG** -- Asserting immediately after triggering async operation:
```typescript
wrapper.find('button').trigger('click')
expect(wrapper.find('.result').text()).toBe('Loaded') // WRONG: async not resolved
```

**RIGHT** -- ALWAYS await nextTick or flushPromises after async triggers:
```typescript
await wrapper.find('button').trigger('click')
await wrapper.vm.$nextTick()
expect(wrapper.find('.result').text()).toBe('Loaded')
```

---

## Summary Table

| ID | Anti-Pattern | Rule |
|----|-------------|------|
| AP-01 | Missing parent::setUp() | ALWAYS call parent::setUp() as the first line |
| AP-02 | Missing parent::tearDown() | ALWAYS call parent::tearDown() as the last line |
| AP-03 | Wrong bootstrap path | ALWAYS use `../../tests/bootstrap.php` |
| AP-04 | Static container in unit tests | NEVER use Server::get() in unit tests |
| AP-05 | Mocking class under test | ALWAYS test real class, mock dependencies only |
| AP-06 | Mocking value objects | ALWAYS use real instances for entities |
| AP-07 | No expectations on mocks | ALWAYS use expects() for behavior verification |
| AP-08 | Multiple behaviors per test | ALWAYS test one behavior per method |
| AP-09 | Missing error path tests | ALWAYS test both success and failure paths |
| AP-10 | Meaningless test data | ALWAYS use descriptive test data |
| AP-11 | Real DB in unit tests | NEVER use real database in unit tests |
| AP-12 | Missing @group DB | ALWAYS annotate DB-dependent integration tests |
| AP-13 | Unmocked @nextcloud packages | ALWAYS mock @nextcloud packages in frontend tests |
| AP-14 | Not awaiting async | ALWAYS await nextTick after async triggers |
