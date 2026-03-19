---
name: nextcloud-impl-testing
description: >
  Use when writing tests for Nextcloud apps, setting up test infrastructure, or mocking Nextcloud services.
  Prevents missing database transaction rollback in integration tests, incorrect mock setup, and untestable tight coupling.
  Covers PHPUnit setup with TestCase base class, unit testing with mocks, integration testing with DI container, database transaction management, frontend testing with Vue Test Utils, and phpunit.xml configuration.
  Keywords: PHPUnit, TestCase, createMock, Vue Test Utils, integration test, phpunit.xml, DI container, transaction.
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-impl-testing

## Quick Reference

### Test Types

| Type | Base Class | Bootstrap | Location |
|------|-----------|-----------|----------|
| Unit | `\Test\TestCase` | `../../tests/bootstrap.php` | `tests/Unit/` |
| Integration | `\Test\TestCase` | `../../tests/bootstrap.php` | `tests/Integration/` |
| Frontend | Jest + `@vue/test-utils` | `jest.config.js` | `tests/js/` or `src/__tests__/` |

### PHPUnit Configuration (`phpunit.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<phpunit bootstrap="../../tests/bootstrap.php"
         colors="true"
         failOnWarning="true"
         failOnRisky="true">
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
    </coverage>
</phpunit>
```

### Test Directory Structure

```
myapp/
├── phpunit.xml
├── tests/
│   ├── Unit/
│   │   ├── Controller/
│   │   │   └── NoteControllerTest.php
│   │   └── Service/
│   │       └── NoteServiceTest.php
│   └── Integration/
│       └── Service/
│           └── NoteServiceIntegrationTest.php
├── src/
│   └── __tests__/
│       └── NoteList.spec.ts
└── jest.config.js
```

### Mock Methods (PHPUnit)

| Method | Purpose |
|--------|---------|
| `$this->createMock(ClassName::class)` | Create mock with all methods stubbed |
| `$mock->method('name')->willReturn($val)` | Stub return value |
| `$mock->expects($this->once())->method('name')` | Assert method called once |
| `$mock->expects($this->never())->method('name')` | Assert method never called |
| `$mock->method('name')->willThrowException($e)` | Stub to throw exception |
| `$mock->method('name')->with($this->equalTo($v))` | Assert parameter value |

### Critical Warnings

**ALWAYS** call `parent::setUp()` in your `setUp()` method -- Nextcloud's TestCase performs essential initialization (database transaction start, cleanup hooks). Omitting it causes test pollution and random failures.

**ALWAYS** call `parent::tearDown()` in your `tearDown()` method -- Nextcloud's TestCase rolls back database transactions. Omitting it leaves test data in the database.

**ALWAYS** use `../../tests/bootstrap.php` as the PHPUnit bootstrap path -- this path is relative from your app's root to the Nextcloud server `tests/` directory. Without it, no Nextcloud classes are autoloaded.

**NEVER** use `\OCP\Server::get()` in tests to resolve services -- use constructor injection and mocks. Static container access makes tests non-isolated and order-dependent.

**NEVER** write to the real database in unit tests -- use mocks for `IDBConnection` and mappers. Reserve real database access for integration tests only.

**NEVER** skip the `phpunit.xml` configuration file -- without it, the bootstrap path is not set and test suites cannot be selected.

---

## Decision Tree: Which Test Type?

```
Need to test?
├── Pure logic (service, helper, utility)
│   └── UNIT TEST: Mock all dependencies
├── Controller request handling
│   └── UNIT TEST: Mock services, test return types/status codes
├── Database queries / mapper behavior
│   └── INTEGRATION TEST: Use real DI container + DB transactions
├── Multi-service interaction with real DI
│   └── INTEGRATION TEST: Resolve services from container
├── Vue component rendering
│   └── FRONTEND TEST: Jest + @vue/test-utils mount/shallowMount
└── API endpoint end-to-end
    └── INTEGRATION TEST: Use TestCase with real HTTP or container
```

---

## Essential Patterns

### Pattern 1: Unit Test with Mocks

```php
<?php
namespace OCA\MyApp\Tests\Unit\Service;

use OCA\MyApp\Db\NoteMapper;
use OCA\MyApp\Db\Note;
use OCA\MyApp\Service\NoteService;
use OCA\MyApp\Service\NotFoundException;
use OCP\AppFramework\Db\DoesNotExistException;
use Test\TestCase;

class NoteServiceTest extends TestCase {
    private NoteMapper $mapper;
    private NoteService $service;

    protected function setUp(): void {
        parent::setUp(); // CRITICAL: ALWAYS call parent
        $this->mapper = $this->createMock(NoteMapper::class);
        $this->service = new NoteService($this->mapper);
    }

    public function testFind(): void {
        $note = new Note();
        $note->setId(1);
        $note->setTitle('Test');

        $this->mapper->expects($this->once())
            ->method('find')
            ->with($this->equalTo(1), $this->equalTo('user1'))
            ->willReturn($note);

        $result = $this->service->find(1, 'user1');
        $this->assertEquals('Test', $result->getTitle());
    }

    public function testFindNotFound(): void {
        $this->mapper->expects($this->once())
            ->method('find')
            ->willThrowException(new DoesNotExistException(''));

        $this->expectException(NotFoundException::class);
        $this->service->find(999, 'user1');
    }
}
```

### Pattern 2: Controller Unit Test

```php
<?php
namespace OCA\MyApp\Tests\Unit\Controller;

use OCA\MyApp\Controller\NoteController;
use OCA\MyApp\Service\NoteService;
use OCA\MyApp\Service\NotFoundException;
use OCP\AppFramework\Http;
use OCP\IRequest;
use Test\TestCase;

class NoteControllerTest extends TestCase {
    private NoteController $controller;
    private NoteService $service;

    protected function setUp(): void {
        parent::setUp(); // CRITICAL: ALWAYS call parent
        $request = $this->createMock(IRequest::class);
        $this->service = $this->createMock(NoteService::class);
        $this->controller = new NoteController(
            'myapp', $request, $this->service, 'user1'
        );
    }

    public function testShow(): void {
        $this->service->method('find')->willReturn(['id' => 1]);
        $result = $this->controller->show(1);
        $this->assertEquals(Http::STATUS_OK, $result->getStatus());
    }

    public function testShowNotFound(): void {
        $this->service->method('find')
            ->willThrowException(new NotFoundException());
        $result = $this->controller->show(999);
        $this->assertEquals(Http::STATUS_NOT_FOUND, $result->getStatus());
    }
}
```

### Pattern 3: Integration Test with DI Container

```php
<?php
namespace OCA\MyApp\Tests\Integration\Service;

use OCA\MyApp\Db\NoteMapper;
use OCA\MyApp\Service\NoteService;
use OCP\AppFramework\App;
use Test\TestCase;

/**
 * @group DB
 */
class NoteServiceIntegrationTest extends TestCase {
    private NoteService $service;
    private NoteMapper $mapper;

    protected function setUp(): void {
        parent::setUp(); // CRITICAL: ALWAYS call parent
        $app = new App('myapp');
        $container = $app->getContainer();
        $this->service = $container->get(NoteService::class);
        $this->mapper = $container->get(NoteMapper::class);
    }

    public function testCreateAndFind(): void {
        $note = $this->service->create('Integration Test', 'content', 'testuser');
        $this->assertNotNull($note->getId());

        $found = $this->service->find($note->getId(), 'testuser');
        $this->assertEquals('Integration Test', $found->getTitle());
    }

    protected function tearDown(): void {
        parent::tearDown(); // CRITICAL: ALWAYS call parent (rolls back transaction)
    }
}
```

### Pattern 4: Frontend Test with Vue Test Utils

```typescript
// src/__tests__/NoteList.spec.ts
import { shallowMount } from '@vue/test-utils'
import NoteList from '../components/NoteList.vue'
import axios from '@nextcloud/axios'

jest.mock('@nextcloud/axios')
const mockedAxios = axios as jest.Mocked<typeof axios>

describe('NoteList', () => {
    beforeEach(() => {
        jest.clearAllMocks()
    })

    it('renders notes after fetch', async () => {
        mockedAxios.get.mockResolvedValue({
            data: [{ id: 1, title: 'Note 1' }, { id: 2, title: 'Note 2' }],
        })

        const wrapper = shallowMount(NoteList)
        await wrapper.vm.$nextTick()
        await wrapper.vm.$nextTick() // Wait for async data

        expect(wrapper.findAll('.note-item')).toHaveLength(2)
    })

    it('shows empty state when no notes', async () => {
        mockedAxios.get.mockResolvedValue({ data: [] })

        const wrapper = shallowMount(NoteList)
        await wrapper.vm.$nextTick()
        await wrapper.vm.$nextTick()

        expect(wrapper.find('.empty-content').exists()).toBe(true)
    })
})
```

### Pattern 5: Jest Configuration

```javascript
// jest.config.js
module.exports = {
    testEnvironment: 'jsdom',
    moduleFileExtensions: ['js', 'ts', 'vue'],
    transform: {
        '^.+\\.ts$': 'ts-jest',
        '^.+\\.vue$': '@vue/vue3-jest',
        '^.+\\.js$': 'babel-jest',
    },
    moduleNameMapper: {
        '^@nextcloud/axios$': '<rootDir>/src/__mocks__/@nextcloud/axios.ts',
        '^@nextcloud/router$': '<rootDir>/src/__mocks__/@nextcloud/router.ts',
    },
    collectCoverageFrom: ['src/**/*.{ts,vue}', '!src/**/*.d.ts'],
}
```

---

## Running Tests

### PHP Tests

```bash
# Run all tests from app directory
cd apps/myapp
../../lib/composer/bin/phpunit

# Run specific test suite
../../lib/composer/bin/phpunit --testsuite unit
../../lib/composer/bin/phpunit --testsuite integration

# Run single test file
../../lib/composer/bin/phpunit tests/Unit/Service/NoteServiceTest.php

# Run single test method
../../lib/composer/bin/phpunit --filter testFind tests/Unit/Service/NoteServiceTest.php
```

### Frontend Tests

```bash
# Run from app directory
cd apps/myapp
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npx jest src/__tests__/NoteList.spec.ts
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- TestCase base class, mock methods, assertion methods, phpunit.xml options
- [references/examples.md](references/examples.md) -- Complete unit test, integration test, and frontend test examples
- [references/anti-patterns.md](references/anti-patterns.md) -- Common testing mistakes and corrections

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/testing.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/front-end/testing.html
- https://phpunit.de/documentation.html
- https://test-utils.vuejs.org/
