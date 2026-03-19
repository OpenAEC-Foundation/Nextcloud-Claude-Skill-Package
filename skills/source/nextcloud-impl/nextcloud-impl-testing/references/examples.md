# Testing Examples Reference

## Example 1: Complete Unit Test for a Service

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\Tests\Unit\Service;

use OCA\MyApp\Db\Note;
use OCA\MyApp\Db\NoteMapper;
use OCA\MyApp\Service\NoteService;
use OCA\MyApp\Service\NotFoundException;
use OCP\AppFramework\Db\DoesNotExistException;
use OCP\AppFramework\Db\MultipleObjectsReturnedException;
use Test\TestCase;

class NoteServiceTest extends TestCase {
    private NoteMapper $mapper;
    private NoteService $service;

    protected function setUp(): void {
        parent::setUp(); // ALWAYS call parent
        $this->mapper = $this->createMock(NoteMapper::class);
        $this->service = new NoteService($this->mapper);
    }

    // --- find() tests ---

    public function testFind(): void {
        $note = new Note();
        $note->setId(1);
        $note->setTitle('Test Note');
        $note->setUserId('user1');

        $this->mapper->expects($this->once())
            ->method('find')
            ->with(
                $this->equalTo(1),
                $this->equalTo('user1')
            )
            ->willReturn($note);

        $result = $this->service->find(1, 'user1');
        $this->assertEquals(1, $result->getId());
        $this->assertEquals('Test Note', $result->getTitle());
    }

    public function testFindNotFound(): void {
        $this->mapper->expects($this->once())
            ->method('find')
            ->willThrowException(new DoesNotExistException(''));

        $this->expectException(NotFoundException::class);
        $this->service->find(999, 'user1');
    }

    public function testFindMultipleResults(): void {
        $this->mapper->expects($this->once())
            ->method('find')
            ->willThrowException(new MultipleObjectsReturnedException(''));

        $this->expectException(NotFoundException::class);
        $this->service->find(1, 'user1');
    }

    // --- findAll() tests ---

    public function testFindAll(): void {
        $note1 = new Note();
        $note1->setId(1);
        $note2 = new Note();
        $note2->setId(2);

        $this->mapper->expects($this->once())
            ->method('findAll')
            ->with($this->equalTo('user1'))
            ->willReturn([$note1, $note2]);

        $result = $this->service->findAll('user1');
        $this->assertCount(2, $result);
    }

    // --- create() tests ---

    public function testCreate(): void {
        $this->mapper->expects($this->once())
            ->method('insert')
            ->with($this->callback(function (Note $note) {
                return $note->getTitle() === 'New Note'
                    && $note->getUserId() === 'user1';
            }))
            ->willReturnCallback(function (Note $note) {
                $note->setId(3);
                return $note;
            });

        $result = $this->service->create('New Note', 'content', 'user1');
        $this->assertEquals(3, $result->getId());
        $this->assertEquals('New Note', $result->getTitle());
    }

    // --- delete() tests ---

    public function testDelete(): void {
        $note = new Note();
        $note->setId(1);

        $this->mapper->expects($this->once())
            ->method('find')
            ->willReturn($note);

        $this->mapper->expects($this->once())
            ->method('delete')
            ->with($this->identicalTo($note));

        $this->service->delete(1, 'user1');
    }
}
```

---

## Example 2: Complete Unit Test for a Controller

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\Tests\Unit\Controller;

use OCA\MyApp\Controller\NoteApiController;
use OCA\MyApp\Db\Note;
use OCA\MyApp\Service\NoteService;
use OCA\MyApp\Service\NotFoundException;
use OCP\AppFramework\Http;
use OCP\IRequest;
use Test\TestCase;

class NoteApiControllerTest extends TestCase {
    private NoteApiController $controller;
    private NoteService $service;
    private string $userId = 'testuser';

    protected function setUp(): void {
        parent::setUp(); // ALWAYS call parent
        $request = $this->createMock(IRequest::class);
        $this->service = $this->createMock(NoteService::class);
        $this->controller = new NoteApiController(
            'myapp',
            $request,
            $this->service,
            $this->userId,
        );
    }

    public function testIndex(): void {
        $note = new Note();
        $note->setId(1);
        $this->service->method('findAll')
            ->with($this->equalTo($this->userId))
            ->willReturn([$note]);

        $result = $this->controller->index();
        $this->assertEquals(Http::STATUS_OK, $result->getStatus());
        $this->assertCount(1, $result->getData());
    }

    public function testShow(): void {
        $note = new Note();
        $note->setId(1);
        $this->service->method('find')
            ->with($this->equalTo(1), $this->equalTo($this->userId))
            ->willReturn($note);

        $result = $this->controller->show(1);
        $this->assertEquals(Http::STATUS_OK, $result->getStatus());
    }

    public function testShowNotFound(): void {
        $this->service->method('find')
            ->willThrowException(new NotFoundException());

        $result = $this->controller->show(999);
        $this->assertEquals(Http::STATUS_NOT_FOUND, $result->getStatus());
    }

    public function testCreate(): void {
        $note = new Note();
        $note->setId(3);
        $note->setTitle('Created');

        $this->service->expects($this->once())
            ->method('create')
            ->with(
                $this->equalTo('Created'),
                $this->equalTo('content'),
                $this->equalTo($this->userId),
            )
            ->willReturn($note);

        $result = $this->controller->create('Created', 'content');
        $this->assertEquals(Http::STATUS_OK, $result->getStatus());
    }

    public function testDelete(): void {
        $note = new Note();
        $note->setId(1);
        $this->service->expects($this->once())
            ->method('delete')
            ->with($this->equalTo(1), $this->equalTo($this->userId))
            ->willReturn($note);

        $result = $this->controller->destroy(1);
        $this->assertEquals(Http::STATUS_OK, $result->getStatus());
    }

    public function testDeleteNotFound(): void {
        $this->service->method('delete')
            ->willThrowException(new NotFoundException());

        $result = $this->controller->destroy(999);
        $this->assertEquals(Http::STATUS_NOT_FOUND, $result->getStatus());
    }
}
```

---

## Example 3: Integration Test with Real Database

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\Tests\Integration\Service;

use OCA\MyApp\Db\NoteMapper;
use OCA\MyApp\Service\NoteService;
use OCA\MyApp\Service\NotFoundException;
use OCP\AppFramework\App;
use Test\TestCase;

/**
 * @group DB
 */
class NoteServiceIntegrationTest extends TestCase {
    private NoteService $service;
    private NoteMapper $mapper;
    private string $testUser = 'integration_test_user';

    protected function setUp(): void {
        parent::setUp(); // ALWAYS call parent — starts DB transaction
        $app = new App('myapp');
        $container = $app->getContainer();

        // Resolve real services from DI container
        $this->mapper = $container->get(NoteMapper::class);
        $this->service = $container->get(NoteService::class);
    }

    public function testCreateAndRetrieve(): void {
        // Create via service (writes to real DB)
        $created = $this->service->create('Integration Test', 'body', $this->testUser);
        $this->assertNotNull($created->getId());

        // Retrieve and verify
        $found = $this->service->find($created->getId(), $this->testUser);
        $this->assertEquals('Integration Test', $found->getTitle());
        $this->assertEquals('body', $found->getContent());
    }

    public function testDeleteRemovesFromDatabase(): void {
        $created = $this->service->create('To Delete', '', $this->testUser);
        $id = $created->getId();

        $this->service->delete($id, $this->testUser);

        $this->expectException(NotFoundException::class);
        $this->service->find($id, $this->testUser);
    }

    public function testFindAllReturnsOnlyUserNotes(): void {
        $this->service->create('Note A', '', $this->testUser);
        $this->service->create('Note B', '', $this->testUser);
        $this->service->create('Other User Note', '', 'other_user');

        $results = $this->service->findAll($this->testUser);
        foreach ($results as $note) {
            $this->assertEquals($this->testUser, $note->getUserId());
        }
    }

    protected function tearDown(): void {
        parent::tearDown(); // ALWAYS call parent — rolls back DB transaction
    }
}
```

---

## Example 4: Frontend Component Test

```typescript
// src/__tests__/NoteEditor.spec.ts
import { mount } from '@vue/test-utils'
import NoteEditor from '../components/NoteEditor.vue'
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'

jest.mock('@nextcloud/axios')
jest.mock('@nextcloud/router')

const mockedAxios = axios as jest.Mocked<typeof axios>
const mockedGenerateUrl = generateUrl as jest.MockedFunction<typeof generateUrl>

describe('NoteEditor', () => {
    const note = { id: 1, title: 'Test Note', content: 'Hello world' }

    beforeEach(() => {
        jest.clearAllMocks()
        mockedGenerateUrl.mockImplementation((url: string) => `/apps/myapp${url}`)
    })

    it('renders note title in input', () => {
        const wrapper = mount(NoteEditor, {
            props: { note },
        })
        const input = wrapper.find('input[data-testid="note-title"]')
        expect((input.element as HTMLInputElement).value).toBe('Test Note')
    })

    it('emits save event with updated data', async () => {
        mockedAxios.put.mockResolvedValue({ data: { ...note, title: 'Updated' } })

        const wrapper = mount(NoteEditor, {
            props: { note },
        })

        const input = wrapper.find('input[data-testid="note-title"]')
        await input.setValue('Updated')
        await wrapper.find('button[data-testid="save-btn"]').trigger('click')

        expect(mockedAxios.put).toHaveBeenCalledWith(
            '/apps/myapp/notes/1',
            expect.objectContaining({ title: 'Updated' }),
        )
        expect(wrapper.emitted('saved')).toBeTruthy()
    })

    it('shows error message on save failure', async () => {
        mockedAxios.put.mockRejectedValue(new Error('Network Error'))

        const wrapper = mount(NoteEditor, {
            props: { note },
        })

        await wrapper.find('button[data-testid="save-btn"]').trigger('click')
        await wrapper.vm.$nextTick()

        expect(wrapper.find('.error-message').exists()).toBe(true)
    })
})
```

---

## Example 5: Mocking Nextcloud Services in a Service Test

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\Tests\Unit\Service;

use OCA\MyApp\Service\ConfigService;
use OCP\IConfig;
use OCP\IUserSession;
use OCP\IUser;
use Psr\Log\LoggerInterface;
use Test\TestCase;

class ConfigServiceTest extends TestCase {
    private IConfig $config;
    private IUserSession $userSession;
    private LoggerInterface $logger;
    private ConfigService $service;

    protected function setUp(): void {
        parent::setUp(); // ALWAYS call parent

        $this->config = $this->createMock(IConfig::class);
        $this->userSession = $this->createMock(IUserSession::class);
        $this->logger = $this->createMock(LoggerInterface::class);

        $this->service = new ConfigService(
            $this->config,
            $this->userSession,
            $this->logger,
        );
    }

    public function testGetUserSetting(): void {
        $user = $this->createMock(IUser::class);
        $user->method('getUID')->willReturn('testuser');
        $this->userSession->method('getUser')->willReturn($user);

        $this->config->expects($this->once())
            ->method('getUserValue')
            ->with('testuser', 'myapp', 'theme', 'light')
            ->willReturn('dark');

        $result = $this->service->getUserTheme();
        $this->assertEquals('dark', $result);
    }

    public function testGetUserSettingNoSession(): void {
        $this->userSession->method('getUser')->willReturn(null);

        $this->logger->expects($this->once())
            ->method('warning')
            ->with($this->stringContains('No active user session'));

        $result = $this->service->getUserTheme();
        $this->assertEquals('light', $result); // Returns default
    }
}
```

---

## Example 6: Testing with Data Providers

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\Tests\Unit\Service;

use OCA\MyApp\Service\ValidationService;
use Test\TestCase;

class ValidationServiceTest extends TestCase {
    private ValidationService $service;

    protected function setUp(): void {
        parent::setUp(); // ALWAYS call parent
        $this->service = new ValidationService();
    }

    /**
     * @dataProvider validTitleProvider
     */
    public function testValidTitle(string $title): void {
        $this->assertTrue($this->service->isValidTitle($title));
    }

    public static function validTitleProvider(): array {
        return [
            'simple title' => ['My Note'],
            'with numbers' => ['Note 123'],
            'with special chars' => ['Meeting (2024-01-15)'],
            'minimum length' => ['AB'],
        ];
    }

    /**
     * @dataProvider invalidTitleProvider
     */
    public function testInvalidTitle(string $title, string $reason): void {
        $this->assertFalse(
            $this->service->isValidTitle($title),
            "Expected '$title' to be invalid because: $reason"
        );
    }

    public static function invalidTitleProvider(): array {
        return [
            'empty string' => ['', 'titles must not be empty'],
            'single char' => ['A', 'titles must be at least 2 characters'],
            'too long' => [str_repeat('a', 256), 'titles must not exceed 255 characters'],
        ];
    }
}
```
