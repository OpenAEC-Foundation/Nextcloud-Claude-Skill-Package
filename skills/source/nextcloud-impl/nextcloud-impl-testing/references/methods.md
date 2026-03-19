# Testing Methods Reference

## TestCase Base Class (`\Test\TestCase`)

Nextcloud provides its own TestCase that extends PHPUnit's `TestCase`. It manages database transactions, temporary files, and cleanup hooks.

### Inherited Lifecycle Methods

| Method | When Called | Purpose |
|--------|------------|---------|
| `setUp(): void` | Before each test | Initialize test fixtures. ALWAYS call `parent::setUp()` first. |
| `tearDown(): void` | After each test | Clean up resources. ALWAYS call `parent::tearDown()` last. |
| `setUpBeforeClass(): void` | Before first test in class | One-time class setup (static) |
| `tearDownAfterClass(): void` | After last test in class | One-time class cleanup (static) |

### What `parent::setUp()` Does

1. Starts a database transaction (for automatic rollback)
2. Registers cleanup hooks for temporary files
3. Resets global state that could leak between tests
4. Initializes the Nextcloud test environment

### What `parent::tearDown()` Does

1. Rolls back the database transaction (removes all test data)
2. Cleans up registered temporary files
3. Restores global state

---

## PHPUnit Mock Methods

### Creating Mocks

| Method | Description |
|--------|-------------|
| `$this->createMock(ClassName::class)` | Mock with all methods stubbed to return default values |
| `$this->createPartialMock(ClassName::class, ['method1', 'method2'])` | Only specified methods are mocked; others execute real code |
| `$this->createStub(ClassName::class)` | Stub without expectation tracking (lighter than mock) |
| `$this->getMockBuilder(ClassName::class)->...->getMock()` | Full control over mock construction |

### Configuring Mock Behavior

| Chain | Example | Description |
|-------|---------|-------------|
| `->method('name')->willReturn($val)` | `$mock->method('find')->willReturn($note)` | Return specific value |
| `->method('name')->willReturnMap($map)` | `$mock->method('find')->willReturnMap([[1, $note1], [2, $note2]])` | Return based on arguments |
| `->method('name')->willReturnCallback($fn)` | `$mock->method('find')->willReturnCallback(fn($id) => ...)` | Return via callback |
| `->method('name')->willReturnSelf()` | `$mock->method('setTitle')->willReturnSelf()` | Return the mock itself (fluent) |
| `->method('name')->willThrowException($e)` | `$mock->method('find')->willThrowException(new \Exception())` | Throw on call |
| `->method('name')->willReturnOnConsecutiveCalls($a, $b)` | Multiple return values in sequence | Different value per call |

### Expectation Methods

| Method | Description |
|--------|-------------|
| `$mock->expects($this->once())->method('name')` | Assert method called exactly once |
| `$mock->expects($this->exactly(3))->method('name')` | Assert method called exactly 3 times |
| `$mock->expects($this->never())->method('name')` | Assert method never called |
| `$mock->expects($this->atLeastOnce())->method('name')` | Assert method called at least once |
| `$mock->expects($this->any())->method('name')` | No call count assertion |

### Argument Matching

| Constraint | Example | Description |
|-----------|---------|-------------|
| `$this->equalTo($val)` | `->with($this->equalTo(42))` | Exact value match |
| `$this->identicalTo($val)` | `->with($this->identicalTo($obj))` | Same instance (===) |
| `$this->stringContains($str)` | `->with($this->stringContains('test'))` | String contains substring |
| `$this->isInstanceOf(Class::class)` | `->with($this->isInstanceOf(Note::class))` | Type check |
| `$this->anything()` | `->with($this->anything())` | Accept any value |
| `$this->callback(fn)` | `->with($this->callback(fn($v) => $v > 0))` | Custom predicate |

---

## Common Assertion Methods

| Method | Description |
|--------|-------------|
| `$this->assertEquals($expected, $actual)` | Value equality (==) |
| `$this->assertSame($expected, $actual)` | Type + value identity (===) |
| `$this->assertTrue($value)` | Assert true |
| `$this->assertFalse($value)` | Assert false |
| `$this->assertNull($value)` | Assert null |
| `$this->assertNotNull($value)` | Assert not null |
| `$this->assertCount($expected, $array)` | Assert array length |
| `$this->assertEmpty($value)` | Assert empty |
| `$this->assertInstanceOf(Class::class, $obj)` | Assert type |
| `$this->assertArrayHasKey($key, $array)` | Assert key exists |
| `$this->assertStringContainsString($needle, $haystack)` | String contains |
| `$this->expectException(Class::class)` | Expect exception type (call before triggering code) |
| `$this->expectExceptionMessage($msg)` | Expect exception message |

---

## phpunit.xml Configuration Options

### Full Configuration Example

```xml
<?xml version="1.0" encoding="utf-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="https://schema.phpunit.de/10.5/phpunit.xsd"
         bootstrap="../../tests/bootstrap.php"
         colors="true"
         failOnWarning="true"
         failOnRisky="true"
         cacheDirectory=".phpunit.cache">
    <testsuites>
        <testsuite name="unit">
            <directory>./tests/Unit</directory>
        </testsuite>
        <testsuite name="integration">
            <directory>./tests/Integration</directory>
        </testsuite>
    </testsuites>
    <coverage>
        <include>
            <directory suffix=".php">./lib</directory>
        </include>
        <exclude>
            <directory suffix=".php">./lib/Migration</directory>
        </exclude>
    </coverage>
</phpunit>
```

### Key Attributes

| Attribute | Value | Purpose |
|-----------|-------|---------|
| `bootstrap` | `../../tests/bootstrap.php` | Path to Nextcloud test bootstrap (REQUIRED) |
| `colors` | `true` | Colored output in terminal |
| `failOnWarning` | `true` | Treat warnings as failures |
| `failOnRisky` | `true` | Treat risky tests as failures |
| `cacheDirectory` | `.phpunit.cache` | Cache directory for PHPUnit 10+ |

### Test Suite Selection

```bash
# Run only unit tests
../../lib/composer/bin/phpunit --testsuite unit

# Run only integration tests
../../lib/composer/bin/phpunit --testsuite integration
```

---

## Nextcloud-Specific Test Helpers

### Database Transactions

Nextcloud's `\Test\TestCase` automatically wraps each test in a database transaction that is rolled back in `tearDown()`. This means:

- Integration tests CAN write to the real database
- All changes are automatically undone after each test
- Tests do NOT interfere with each other
- This ONLY works if you call `parent::setUp()` and `parent::tearDown()`

### Resolving Services in Integration Tests

```php
$app = new \OCP\AppFramework\App('myapp');
$container = $app->getContainer();
$service = $container->get(MyService::class);
```

ALWAYS use the DI container in integration tests to resolve services with their real dependencies. This verifies that dependency injection is correctly configured.

### Mocking Nextcloud Services

Common services to mock in unit tests:

| Service Interface | Purpose | Mock Pattern |
|-------------------|---------|-------------|
| `OCP\IDBConnection` | Database access | `$this->createMock(IDBConnection::class)` |
| `OCP\IConfig` | App/system config | `$this->createMock(IConfig::class)` |
| `OCP\IL10N` | Translations | `$this->createMock(IL10N::class)` |
| `OCP\IRequest` | HTTP request | `$this->createMock(IRequest::class)` |
| `OCP\IUserSession` | Current user | `$this->createMock(IUserSession::class)` |
| `OCP\IURLGenerator` | URL generation | `$this->createMock(IURLGenerator::class)` |
| `OCP\Files\IRootFolder` | File system | `$this->createMock(IRootFolder::class)` |
| `Psr\Log\LoggerInterface` | Logging | `$this->createMock(LoggerInterface::class)` |
