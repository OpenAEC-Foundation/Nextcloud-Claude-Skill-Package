# Complete App Example — Task Board

This example shows a complete CRUD app: database migration, entity, mapper, service, controllers (page + OCS API), and Vue.js frontend with initial state bridge.

---

## Backend: Database Migration

```php
<?php
// lib/Migration/Version1000Date20240101000000.php
namespace OCA\TaskBoard\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

class Version1000Date20240101000000 extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options) {
        /** @var ISchemaWrapper $schema */
        $schema = $schemaClosure();

        if (!$schema->hasTable('taskboard_tasks')) {
            $table = $schema->createTable('taskboard_tasks');
            $table->addColumn('id', Types::BIGINT, [
                'autoincrement' => true, 'notnull' => true,
            ]);
            $table->addColumn('title', Types::STRING, [
                'notnull' => true, 'length' => 255,
            ]);
            $table->addColumn('description', Types::TEXT, [
                'notnull' => false, 'default' => '',
            ]);
            $table->addColumn('user_id', Types::STRING, [
                'notnull' => true, 'length' => 64,
            ]);
            $table->addColumn('status', Types::STRING, [
                'notnull' => true, 'length' => 20, 'default' => 'open',
            ]);
            $table->addColumn('priority', Types::INTEGER, [
                'notnull' => true, 'default' => 0,
            ]);
            $table->addColumn('created_at', Types::DATETIME, [
                'notnull' => true,
            ]);
            $table->addColumn('updated_at', Types::DATETIME, [
                'notnull' => false,
            ]);
            $table->setPrimaryKey(['id']);
            $table->addIndex(['user_id'], 'taskboard_user_idx');
            $table->addIndex(['status'], 'taskboard_status_idx');
        }

        return $schema;
    }
}
```

---

## Backend: Entity

```php
<?php
// lib/Db/Task.php
namespace OCA\TaskBoard\Db;

use OCP\AppFramework\Db\Entity;

class Task extends Entity implements \JsonSerializable {
    protected ?string $title = null;
    protected ?string $description = null;
    protected ?string $userId = null;
    protected ?string $status = null;
    protected ?int $priority = null;
    protected ?string $createdAt = null;
    protected ?string $updatedAt = null;

    public function __construct() {
        $this->addType('priority', 'integer');
    }

    public function jsonSerialize(): array {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'description' => $this->description,
            'userId' => $this->userId,
            'status' => $this->status,
            'priority' => $this->priority,
            'createdAt' => $this->createdAt,
            'updatedAt' => $this->updatedAt,
        ];
    }
}
```

---

## Backend: Mapper

```php
<?php
// lib/Db/TaskMapper.php
namespace OCA\TaskBoard\Db;

use OCP\AppFramework\Db\DoesNotExistException;
use OCP\AppFramework\Db\MultipleObjectsReturnedException;
use OCP\AppFramework\Db\QBMapper;
use OCP\IDBConnection;

class TaskMapper extends QBMapper {
    public function __construct(IDBConnection $db) {
        parent::__construct($db, 'taskboard_tasks', Task::class);
    }

    /**
     * @throws DoesNotExistException
     * @throws MultipleObjectsReturnedException
     */
    public function find(int $id, string $userId): Task {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('id', $qb->createNamedParameter($id)))
            ->andWhere($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
        return $this->findEntity($qb);
    }

    /**
     * @return Task[]
     */
    public function findAll(string $userId): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)))
            ->orderBy('priority', 'DESC');
        return $this->findEntities($qb);
    }
}
```

---

## Backend: Service

```php
<?php
// lib/Service/TaskService.php
namespace OCA\TaskBoard\Service;

use OCA\TaskBoard\Db\Task;
use OCA\TaskBoard\Db\TaskMapper;
use OCP\AppFramework\Db\DoesNotExistException;
use OCP\AppFramework\Db\MultipleObjectsReturnedException;
use Psr\Log\LoggerInterface;

class NotFoundException extends \Exception {
}

class TaskService {
    public function __construct(
        private TaskMapper $mapper,
        private LoggerInterface $logger,
    ) {
    }

    /**
     * @return Task[]
     */
    public function findAll(string $userId): array {
        return $this->mapper->findAll($userId);
    }

    /**
     * @throws NotFoundException
     */
    public function find(int $id, string $userId): Task {
        try {
            return $this->mapper->find($id, $userId);
        } catch (DoesNotExistException | MultipleObjectsReturnedException $e) {
            $this->logger->warning('Task not found', [
                'id' => $id,
                'userId' => $userId,
            ]);
            throw new NotFoundException('Task not found');
        }
    }

    public function create(string $title, string $description, string $userId): Task {
        $task = new Task();
        $task->setTitle($title);
        $task->setDescription($description);
        $task->setUserId($userId);
        $task->setStatus('open');
        $task->setPriority(0);
        $task->setCreatedAt(date('Y-m-d H:i:s'));
        return $this->mapper->insert($task);
    }

    /**
     * @throws NotFoundException
     */
    public function update(int $id, string $title, string $description,
                           string $status, int $priority, string $userId): Task {
        $task = $this->find($id, $userId);
        $task->setTitle($title);
        $task->setDescription($description);
        $task->setStatus($status);
        $task->setPriority($priority);
        $task->setUpdatedAt(date('Y-m-d H:i:s'));
        return $this->mapper->update($task);
    }

    /**
     * @throws NotFoundException
     */
    public function delete(int $id, string $userId): Task {
        $task = $this->find($id, $userId);
        $this->mapper->delete($task);
        return $task;
    }
}
```

---

## Backend: Page Controller (with Initial State)

```php
<?php
// lib/Controller/PageController.php
namespace OCA\TaskBoard\Controller;

use OCA\TaskBoard\Service\TaskService;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Services\IInitialState;
use OCP\IRequest;

class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private TaskService $service,
        private IInitialState $initialState,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        // Provide initial tasks to frontend via initial state
        $this->initialState->provideInitialState(
            'tasks',
            $this->service->findAll($this->userId)
        );

        return new TemplateResponse('taskboard', 'main');
    }
}
```

---

## Backend: OCS API Controller (Full CRUD)

```php
<?php
// lib/Controller/TaskApiController.php
namespace OCA\TaskBoard\Controller;

use OCA\TaskBoard\Service\NotFoundException;
use OCA\TaskBoard\Service\TaskService;
use OCP\AppFramework\Http;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\DataResponse;
use OCP\AppFramework\OCSController;
use OCP\IRequest;

class TaskApiController extends OCSController {
    public function __construct(
        string $appName,
        IRequest $request,
        private TaskService $service,
        private ?string $userId,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    public function index(): DataResponse {
        return new DataResponse($this->service->findAll($this->userId));
    }

    #[NoAdminRequired]
    public function show(int $id): DataResponse {
        try {
            return new DataResponse($this->service->find($id, $this->userId));
        } catch (NotFoundException $e) {
            return new DataResponse([], Http::STATUS_NOT_FOUND);
        }
    }

    #[NoAdminRequired]
    public function create(string $title, string $description = ''): DataResponse {
        $task = $this->service->create($title, $description, $this->userId);
        return new DataResponse($task, Http::STATUS_CREATED);
    }

    #[NoAdminRequired]
    public function update(int $id, string $title, string $description,
                           string $status = 'open', int $priority = 0): DataResponse {
        try {
            $task = $this->service->update(
                $id, $title, $description, $status, $priority, $this->userId
            );
            return new DataResponse($task);
        } catch (NotFoundException $e) {
            return new DataResponse([], Http::STATUS_NOT_FOUND);
        }
    }

    #[NoAdminRequired]
    public function destroy(int $id): DataResponse {
        try {
            $this->service->delete($id, $this->userId);
            return new DataResponse([], Http::STATUS_NO_CONTENT);
        } catch (NotFoundException $e) {
            return new DataResponse([], Http::STATUS_NOT_FOUND);
        }
    }
}
```

---

## Backend: Routes

```php
<?php
// appinfo/routes.php
return [
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
    ],
    'ocs' => [
        ['name' => 'task_api#index', 'url' => '/api/v1/tasks', 'verb' => 'GET'],
        ['name' => 'task_api#show', 'url' => '/api/v1/tasks/{id}', 'verb' => 'GET'],
        ['name' => 'task_api#create', 'url' => '/api/v1/tasks', 'verb' => 'POST'],
        ['name' => 'task_api#update', 'url' => '/api/v1/tasks/{id}', 'verb' => 'PUT'],
        ['name' => 'task_api#destroy', 'url' => '/api/v1/tasks/{id}', 'verb' => 'DELETE'],
    ],
];
```

---

## Backend: Template

```php
<!-- templates/main.php -->
<?php
script('taskboard', 'taskboard-main');
style('taskboard', 'main');
?>
<div id="content"></div>
```

---

## Frontend: Entry Point

```javascript
// src/main.js
import Vue from 'vue'
import App from './App.vue'

const appElement = document.getElementById('content')
new Vue({
    el: appElement,
    render: h => h(App),
})
```

---

## Frontend: API Service

```javascript
// src/services/TaskService.js
import axios from '@nextcloud/axios'
import { generateOcsUrl } from '@nextcloud/router'

const baseUrl = generateOcsUrl('/apps/taskboard/api/v1')

export async function fetchTasks() {
    const response = await axios.get(`${baseUrl}/tasks`)
    return response.data.ocs.data
}

export async function fetchTask(id) {
    const response = await axios.get(`${baseUrl}/tasks/${id}`)
    return response.data.ocs.data
}

export async function createTask(title, description = '') {
    const response = await axios.post(`${baseUrl}/tasks`, { title, description })
    return response.data.ocs.data
}

export async function updateTask(id, data) {
    const response = await axios.put(`${baseUrl}/tasks/${id}`, data)
    return response.data.ocs.data
}

export async function deleteTask(id) {
    await axios.delete(`${baseUrl}/tasks/${id}`)
}
```

---

## Frontend: Root Component

```vue
<!-- src/App.vue -->
<template>
    <NcContent app-name="taskboard">
        <NcAppNavigation>
            <template #list>
                <NcAppNavigationItem v-for="task in tasks"
                    :key="task.id"
                    :name="task.title"
                    :class="{ active: selectedTask && selectedTask.id === task.id }"
                    @click="selectTask(task)">
                    <template #actions>
                        <NcActionButton @click="removeTask(task.id)">
                            Delete
                        </NcActionButton>
                    </template>
                </NcAppNavigationItem>
            </template>
            <template #footer>
                <div class="new-task">
                    <NcTextField :value.sync="newTaskTitle"
                        label="New task"
                        @keyup.enter="addTask" />
                    <NcButton type="primary" @click="addTask">Add</NcButton>
                </div>
            </template>
        </NcAppNavigation>

        <NcAppContent>
            <NcEmptyContent v-if="!selectedTask"
                name="No task selected"
                description="Select a task from the sidebar or create a new one">
            </NcEmptyContent>
            <div v-else class="task-detail">
                <h2>{{ selectedTask.title }}</h2>
                <p>{{ selectedTask.description }}</p>
                <span class="status-badge">{{ selectedTask.status }}</span>
            </div>
        </NcAppContent>
    </NcContent>
</template>

<script>
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'
import NcAppNavigation from '@nextcloud/vue/components/NcAppNavigation'
import NcAppNavigationItem from '@nextcloud/vue/components/NcAppNavigationItem'
import NcActionButton from '@nextcloud/vue/components/NcActionButton'
import NcButton from '@nextcloud/vue/components/NcButton'
import NcTextField from '@nextcloud/vue/components/NcTextField'
import NcEmptyContent from '@nextcloud/vue/components/NcEmptyContent'
import { loadState } from '@nextcloud/initial-state'
import { showSuccess, showError } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'
import { fetchTasks, createTask, deleteTask } from './services/TaskService'

export default {
    name: 'App',
    components: {
        NcContent,
        NcAppContent,
        NcAppNavigation,
        NcAppNavigationItem,
        NcActionButton,
        NcButton,
        NcTextField,
        NcEmptyContent,
    },
    data() {
        return {
            // Load initial tasks from PHP via initial state bridge
            tasks: loadState('taskboard', 'tasks', []),
            selectedTask: null,
            newTaskTitle: '',
        }
    },
    methods: {
        selectTask(task) {
            this.selectedTask = task
        },

        async addTask() {
            if (!this.newTaskTitle.trim()) return
            try {
                const task = await createTask(this.newTaskTitle)
                this.tasks.push(task)
                this.newTaskTitle = ''
                showSuccess('Task created')
            } catch (e) {
                showError('Failed to create task')
                console.error(e)
            }
        },

        async removeTask(id) {
            try {
                await deleteTask(id)
                this.tasks = this.tasks.filter(t => t.id !== id)
                if (this.selectedTask?.id === id) {
                    this.selectedTask = null
                }
                showSuccess('Task deleted')
            } catch (e) {
                showError('Failed to delete task')
                console.error(e)
            }
        },

        async refreshTasks() {
            try {
                this.tasks = await fetchTasks()
            } catch (e) {
                showError('Failed to load tasks')
                console.error(e)
            }
        },
    },
}
</script>

<style scoped>
.task-detail {
    padding: 20px;
    color: var(--color-main-text);
}

.task-detail h2 {
    margin-bottom: 10px;
}

.status-badge {
    display: inline-block;
    padding: 4px 8px;
    border-radius: 4px;
    background-color: var(--color-primary-element);
    color: var(--color-primary-element-text);
    font-size: 12px;
}

.new-task {
    display: flex;
    gap: 8px;
    padding: 8px;
}
</style>
```

---

## Frontend: Build Configuration

```javascript
// webpack.config.js
const webpackConfig = require('@nextcloud/webpack-vue-config')
module.exports = webpackConfig
```

```json
// package.json
{
    "name": "taskboard",
    "version": "1.0.0",
    "scripts": {
        "build": "webpack --node-env production --progress",
        "dev": "webpack --node-env development --progress",
        "watch": "webpack --node-env development --progress --watch",
        "serve": "webpack --node-env development serve --progress"
    },
    "dependencies": {
        "@nextcloud/axios": "^2.0.0",
        "@nextcloud/dialogs": "^5.0.0",
        "@nextcloud/initial-state": "^2.0.0",
        "@nextcloud/router": "^3.0.0",
        "@nextcloud/vue": "^8.0.0",
        "vue": "^2.7.0"
    },
    "devDependencies": {
        "@nextcloud/webpack-vue-config": "^6.0.0"
    }
}
```

---

## Application Bootstrap

```php
<?php
// lib/AppInfo/Application.php
namespace OCA\TaskBoard\AppInfo;

use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
    public const APP_ID = 'taskboard';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        // Auto-wiring handles all services -- no explicit registration needed
        // Add listeners, middleware, or service aliases here if required
    }

    public function boot(IBootContext $context): void {
        // Cross-app initialization if needed
    }
}
```

---

## App Manifest

```xml
<?xml version="1.0"?>
<!-- appinfo/info.xml -->
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>taskboard</id>
    <name>Task Board</name>
    <summary>Simple task management for Nextcloud</summary>
    <description>A full-stack task board app with CRUD operations</description>
    <version>1.0.0</version>
    <licence>AGPL-3.0-or-later</licence>
    <author>Developer Name</author>
    <namespace>TaskBoard</namespace>
    <category>organization</category>
    <dependencies>
        <nextcloud min-version="28" max-version="32"/>
    </dependencies>
    <navigations>
        <navigation>
            <name>Task Board</name>
            <route>taskboard.page.index</route>
            <icon>app.svg</icon>
        </navigation>
    </navigations>
</info>
```

---

## Complete Directory Structure

```
taskboard/
├── appinfo/
│   ├── info.xml
│   └── routes.php
├── lib/
│   ├── AppInfo/
│   │   └── Application.php
│   ├── Controller/
│   │   ├── PageController.php
│   │   └── TaskApiController.php
│   ├── Db/
│   │   ├── Task.php
│   │   └── TaskMapper.php
│   ├── Migration/
│   │   └── Version1000Date20240101000000.php
│   └── Service/
│       └── TaskService.php
├── src/
│   ├── main.js
│   ├── App.vue
│   └── services/
│       └── TaskService.js
├── templates/
│   └── main.php
├── css/
│   └── main.scss
├── img/
│   └── app.svg
├── webpack.config.js
└── package.json
```
