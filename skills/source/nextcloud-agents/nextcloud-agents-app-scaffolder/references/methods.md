# File Templates and Generation Patterns

## Template: appinfo/info.xml

```xml
<?xml version="1.0"?>
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>{appid}</id>
    <name>{AppName}</name>
    <summary>{Short description}</summary>
    <description><![CDATA[{Full **markdown** description}]]></description>
    <version>0.1.0</version>
    <licence>{licence}</licence>
    <author mail="{email}" homepage="{homepage}">{Author Name}</author>
    <namespace>{Namespace}</namespace>
    <category>{category}</category>
    <bugs>{bugs_url}</bugs>
    <repository type="git">{repo_url}</repository>
    <dependencies>
        <nextcloud min-version="{min}" max-version="{max}"/>
        <php min-version="8.1"/>
    </dependencies>

    <!-- CONDITIONAL: Navigation entry -->
    <navigations>
        <navigation>
            <name>{AppName}</name>
            <route>{appid}.page.index</route>
            <icon>app.svg</icon>
            <order>10</order>
        </navigation>
    </navigations>

    <!-- CONDITIONAL: Background jobs -->
    <background-jobs>
        <job>OCA\{Namespace}\Cron\{JobClass}</job>
    </background-jobs>

    <!-- CONDITIONAL: OCC commands -->
    <commands>
        <command>OCA\{Namespace}\Command\{CommandClass}</command>
    </commands>

    <!-- CONDITIONAL: Settings pages -->
    <settings>
        <admin>OCA\{Namespace}\Settings\Admin</admin>
        <admin-section>OCA\{Namespace}\Settings\AdminSection</admin-section>
    </settings>
</info>
```

**Substitution rules:**
- `{appid}` -- lowercase ASCII + underscore only, MUST match directory name
- `{Namespace}` -- PascalCase, maps to `OCA\{Namespace}\*`
- `{min}` / `{max}` -- integer NC version numbers (e.g., `28`, `32`)
- `{licence}` -- SPDX identifier (e.g., `AGPL-3.0-or-later`, `MIT`)
- `{category}` -- one of: customization, files, games, integration, monitoring, multimedia, office, organization, security, social, tools

---

## Template: appinfo/routes.php

```php
<?php

declare(strict_types=1);

return [
    'routes' => [
        ['name' => 'page#index', 'url' => '/', 'verb' => 'GET'],
        // CONDITIONAL: Entity CRUD routes
        ['name' => '{entity}#index', 'url' => '/api/{entities}', 'verb' => 'GET'],
        ['name' => '{entity}#show', 'url' => '/api/{entities}/{id}', 'verb' => 'GET'],
        ['name' => '{entity}#create', 'url' => '/api/{entities}', 'verb' => 'POST'],
        ['name' => '{entity}#update', 'url' => '/api/{entities}/{id}', 'verb' => 'PUT'],
        ['name' => '{entity}#destroy', 'url' => '/api/{entities}/{id}', 'verb' => 'DELETE'],
    ],
    // CONDITIONAL: OCS API routes
    'ocs' => [
        ['name' => 'api#getData', 'url' => '/api/v1/data', 'verb' => 'GET'],
    ],
];
```

**Route name resolution:** `{entity}#index` resolves to `{Entity}Controller::index()`. Underscored names resolve to camelCase: `item_api#get_data` resolves to `ItemApiController::getData()`.

---

## Template: lib/AppInfo/Application.php

```php
<?php

declare(strict_types=1);

namespace OCA\{Namespace}\AppInfo;

use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
    public const APP_ID = '{appid}';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        // CONDITIONAL: Event listeners
        // $context->registerEventListener(SomeEvent::class, SomeListener::class);

        // CONDITIONAL: Middleware
        // $context->registerMiddleware(SomeMiddleware::class);

        // CONDITIONAL: Service aliases (only when auto-wiring fails)
        // $context->registerServiceAlias(IInterface::class, Implementation::class);
    }

    public function boot(IBootContext $context): void {
        // Post-registration initialization (all services available)
    }
}
```

---

## Template: lib/Controller/PageController.php

```php
<?php

declare(strict_types=1);

namespace OCA\{Namespace}\Controller;

use OCA\{Namespace}\AppInfo\Application;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Services\IInitialState;
use OCP\IRequest;

class PageController extends Controller {
    public function __construct(
        IRequest $request,
        private IInitialState $initialState,
    ) {
        parent::__construct(Application::APP_ID, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        // CONDITIONAL: Provide initial state to frontend
        // $this->initialState->provideInitialState('key', $value);

        return new TemplateResponse(Application::APP_ID, 'main');
    }
}
```

---

## Template: lib/Controller/{Entity}Controller.php

```php
<?php

declare(strict_types=1);

namespace OCA\{Namespace}\Controller;

use OCA\{Namespace}\AppInfo\Application;
use OCA\{Namespace}\Service\{Entity}Service;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\JSONResponse;
use OCP\AppFramework\Http;
use OCP\IRequest;

class {Entity}Controller extends Controller {
    public function __construct(
        IRequest $request,
        private {Entity}Service $service,
        private ?string $userId,
    ) {
        parent::__construct(Application::APP_ID, $request);
    }

    #[NoAdminRequired]
    public function index(): JSONResponse {
        return new JSONResponse($this->service->findAll($this->userId));
    }

    #[NoAdminRequired]
    public function show(int $id): JSONResponse {
        return $this->handleNotFound(fn () => $this->service->find($id, $this->userId));
    }

    #[NoAdminRequired]
    public function create(string $title, string $content = ''): JSONResponse {
        return new JSONResponse(
            $this->service->create($title, $content, $this->userId),
            Http::STATUS_CREATED
        );
    }

    #[NoAdminRequired]
    public function update(int $id, string $title, string $content = ''): JSONResponse {
        return $this->handleNotFound(
            fn () => $this->service->update($id, $title, $content, $this->userId)
        );
    }

    #[NoAdminRequired]
    public function destroy(int $id): JSONResponse {
        return $this->handleNotFound(
            fn () => $this->service->delete($id, $this->userId)
        );
    }

    private function handleNotFound(callable $callback): JSONResponse {
        try {
            return new JSONResponse($callback());
        } catch (\OCP\AppFramework\Db\DoesNotExistException $e) {
            return new JSONResponse([], Http::STATUS_NOT_FOUND);
        }
    }
}
```

---

## Template: lib/Service/{Entity}Service.php

```php
<?php

declare(strict_types=1);

namespace OCA\{Namespace}\Service;

use OCA\{Namespace}\Db\{Entity};
use OCA\{Namespace}\Db\{Entity}Mapper;
use OCP\AppFramework\Db\DoesNotExistException;
use OCP\AppFramework\Db\MultipleObjectsReturnedException;
use Psr\Log\LoggerInterface;

class {Entity}Service {
    public function __construct(
        private {Entity}Mapper $mapper,
        private LoggerInterface $logger,
    ) {
    }

    /** @return {Entity}[] */
    public function findAll(string $userId): array {
        return $this->mapper->findAll($userId);
    }

    /** @throws DoesNotExistException */
    public function find(int $id, string $userId): {Entity} {
        return $this->mapper->find($id, $userId);
    }

    public function create(string $title, string $content, string $userId): {Entity} {
        $entity = new {Entity}();
        $entity->setTitle($title);
        $entity->setContent($content);
        $entity->setUserId($userId);
        return $this->mapper->insert($entity);
    }

    /** @throws DoesNotExistException */
    public function update(int $id, string $title, string $content, string $userId): {Entity} {
        $entity = $this->mapper->find($id, $userId);
        $entity->setTitle($title);
        $entity->setContent($content);
        return $this->mapper->update($entity);
    }

    /** @throws DoesNotExistException */
    public function delete(int $id, string $userId): {Entity} {
        $entity = $this->mapper->find($id, $userId);
        $this->mapper->delete($entity);
        return $entity;
    }
}
```

---

## Template: lib/Db/{Entity}.php

```php
<?php

declare(strict_types=1);

namespace OCA\{Namespace}\Db;

use OCP\AppFramework\Db\Entity;

/**
 * @method string getTitle()
 * @method void setTitle(string $title)
 * @method string getContent()
 * @method void setContent(string $content)
 * @method string getUserId()
 * @method void setUserId(string $userId)
 */
class {Entity} extends Entity implements \JsonSerializable {
    protected ?string $title = null;
    protected ?string $content = null;
    protected ?string $userId = null;

    public function __construct() {
        $this->addType('id', 'integer');
    }

    public function jsonSerialize(): array {
        return [
            'id' => $this->id,
            'title' => $this->title,
            'content' => $this->content,
            'userId' => $this->userId,
        ];
    }
}
```

**Property rules:**
- Properties MUST be `protected` with nullable types
- camelCase property maps to snake_case column automatically (`userId` -> `user_id`)
- ALWAYS implement `JsonSerializable` for API responses
- ALWAYS add `@method` docblocks for auto-generated getters/setters

---

## Template: lib/Db/{Entity}Mapper.php

```php
<?php

declare(strict_types=1);

namespace OCA\{Namespace}\Db;

use OCP\AppFramework\Db\QBMapper;
use OCP\IDBConnection;

/** @extends QBMapper<{Entity}> */
class {Entity}Mapper extends QBMapper {
    public function __construct(IDBConnection $db) {
        parent::__construct($db, '{appid}_{entities}');
    }

    /** @throws \OCP\AppFramework\Db\DoesNotExistException */
    public function find(int $id, string $userId): {Entity} {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('id', $qb->createNamedParameter($id)))
            ->andWhere($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
        return $this->findEntity($qb);
    }

    /** @return {Entity}[] */
    public function findAll(string $userId): array {
        $qb = $this->db->getQueryBuilder();
        $qb->select('*')
            ->from($this->getTableName())
            ->where($qb->expr()->eq('user_id', $qb->createNamedParameter($userId)));
        return $this->findEntities($qb);
    }
}
```

**Table name rules:**
- ALWAYS prefix with `{appid}_` (e.g., `myapp_items`)
- Max 23 characters (27 with `oc_` prefix for Oracle compatibility)
- Pass table name WITHOUT `oc_` prefix to `parent::__construct()`

---

## Template: lib/Migration/Version1000Date{Timestamp}.php

```php
<?php

declare(strict_types=1);

namespace OCA\{Namespace}\Migration;

use Closure;
use OCP\DB\ISchemaWrapper;
use OCP\DB\Types;
use OCP\Migration\IOutput;
use OCP\Migration\SimpleMigrationStep;

class Version1000Date{Timestamp} extends SimpleMigrationStep {
    public function changeSchema(IOutput $output, Closure $schemaClosure, array $options): ?ISchemaWrapper {
        /** @var ISchemaWrapper $schema */
        $schema = $schemaClosure();

        if (!$schema->hasTable('{appid}_{entities}')) {
            $table = $schema->createTable('{appid}_{entities}');

            $table->addColumn('id', Types::BIGINT, [
                'autoincrement' => true,
                'notnull' => true,
            ]);
            $table->addColumn('title', Types::STRING, [
                'notnull' => true,
                'length' => 255,
            ]);
            $table->addColumn('content', Types::TEXT, [
                'notnull' => false,
                'default' => '',
            ]);
            $table->addColumn('user_id', Types::STRING, [
                'notnull' => true,
                'length' => 64,
            ]);

            $table->setPrimaryKey(['id']);
            $table->addIndex(['user_id'], '{appid}_{entity}_uid_idx');
        }

        return $schema;
    }
}
```

**Migration naming:** `Version{MajorMinor}Date{YYYYMMDDHHMMSS}` where `1.0.x => 1000`, `2.34.x => 2034`.

**Column type constants:** Use `OCP\DB\Types::BIGINT`, `Types::STRING`, `Types::TEXT`, `Types::BOOLEAN`, `Types::INTEGER`, `Types::JSON`, `Types::DATETIME`.

---

## Template: src/main.js

```javascript
import Vue from 'vue'
import App from './App.vue'

const appElement = document.getElementById('content')

// eslint-disable-next-line no-new
new Vue({
    el: appElement,
    render: h => h(App),
})
```

---

## Template: src/App.vue

```vue
<template>
    <NcContent app-name="{appid}">
        <NcAppContent>
            <div class="{appid}-main">
                <NcEmptyContent v-if="items.length === 0"
                    name="No items yet"
                    description="Create your first item to get started">
                </NcEmptyContent>
                <div v-else>
                    <NcListItem v-for="item in items"
                        :key="item.id"
                        :name="item.title"
                        @click="selectItem(item)">
                    </NcListItem>
                </div>
            </div>
        </NcAppContent>
    </NcContent>
</template>

<script>
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'
import NcEmptyContent from '@nextcloud/vue/components/NcEmptyContent'
import NcListItem from '@nextcloud/vue/components/NcListItem'
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'
import { showError, showSuccess } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'

export default {
    name: 'App',
    components: {
        NcContent,
        NcAppContent,
        NcEmptyContent,
        NcListItem,
    },
    data() {
        return {
            items: [],
            selectedItem: null,
        }
    },
    async mounted() {
        try {
            const response = await axios.get(generateUrl('/apps/{appid}/api/{entities}'))
            this.items = response.data
        } catch (e) {
            showError('Could not load items')
            console.error(e)
        }
    },
    methods: {
        selectItem(item) {
            this.selectedItem = item
        },
    },
}
</script>

<style scoped lang="scss">
.{appid}-main {
    padding: 20px;
    color: var(--color-main-text);
    background-color: var(--color-main-background);
}
</style>
```

---

## Template: webpack.config.js

```javascript
const webpackConfig = require('@nextcloud/webpack-vue-config')

module.exports = webpackConfig
```

---

## Template: package.json

```json
{
    "name": "{appid}",
    "version": "0.1.0",
    "private": true,
    "scripts": {
        "build": "webpack --node-env production --progress",
        "dev": "webpack --node-env development --progress",
        "watch": "webpack --node-env development --progress --watch",
        "serve": "webpack --node-env development serve --progress",
        "lint": "eslint --ext .js,.vue src",
        "lint:fix": "eslint --ext .js,.vue src --fix"
    },
    "dependencies": {
        "@nextcloud/axios": "^2.4.0",
        "@nextcloud/dialogs": "^5.0.0",
        "@nextcloud/initial-state": "^2.1.0",
        "@nextcloud/router": "^3.0.0",
        "@nextcloud/vue": "^8.0.0",
        "vue": "^2.7.16"
    },
    "devDependencies": {
        "@nextcloud/eslint-config": "^8.3.0",
        "@nextcloud/webpack-vue-config": "^6.0.0",
        "vue-loader": "^15.11.1"
    }
}
```

---

## Template: composer.json

```json
{
    "name": "{vendor}/{appid}",
    "description": "{description}",
    "type": "project",
    "license": "{licence}",
    "require": {
        "php": ">=8.1"
    },
    "require-dev": {
        "phpunit/phpunit": "^10.0",
        "nextcloud/ocp": "dev-master"
    },
    "autoload": {
        "psr-4": {
            "OCA\\{Namespace}\\": "lib/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "OCA\\{Namespace}\\Tests\\": "tests/"
        }
    },
    "config": {
        "optimize-autoloader": true
    }
}
```

---

## Template: templates/main.php

```php
<?php

script('{appid}', '{appid}-main');
style('{appid}', 'style');
?>

<div id="app-content">
    <div id="content"></div>
</div>
```

---

## Template: css/style.scss

```scss
#app-content {
    .{appid}-main {
        min-height: 100%;
        padding: 20px;
    }
}
```

---

## Template: phpunit.xml

```xml
<?xml version="1.0" encoding="utf-8" ?>
<phpunit bootstrap="tests/bootstrap.php"
         colors="true"
         failOnRisky="true"
         failOnWarning="true">
    <testsuites>
        <testsuite name="unit">
            <directory>./tests/Unit</directory>
        </testsuite>
    </testsuites>
    <coverage>
        <include>
            <directory suffix=".php">./lib</directory>
        </include>
    </coverage>
</phpunit>
```

---

## Template: tests/bootstrap.php

```php
<?php

declare(strict_types=1);

require_once __DIR__ . '/../../../tests/bootstrap.php';
```

---

## Template: tests/Unit/Service/{Entity}ServiceTest.php

```php
<?php

declare(strict_types=1);

namespace OCA\{Namespace}\Tests\Unit\Service;

use OCA\{Namespace}\Db\{Entity};
use OCA\{Namespace}\Db\{Entity}Mapper;
use OCA\{Namespace}\Service\{Entity}Service;
use OCP\AppFramework\Db\DoesNotExistException;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

class {Entity}ServiceTest extends TestCase {
    private {Entity}Service $service;
    private {Entity}Mapper $mapper;
    private LoggerInterface $logger;

    protected function setUp(): void {
        parent::setUp();

        $this->mapper = $this->createMock({Entity}Mapper::class);
        $this->logger = $this->createMock(LoggerInterface::class);
        $this->service = new {Entity}Service($this->mapper, $this->logger);
    }

    public function testFindAll(): void {
        $userId = 'testuser';
        $entities = [new {Entity}(), new {Entity}()];

        $this->mapper->expects($this->once())
            ->method('findAll')
            ->with($userId)
            ->willReturn($entities);

        $result = $this->service->findAll($userId);
        $this->assertCount(2, $result);
    }

    public function testFindNotFound(): void {
        $this->mapper->expects($this->once())
            ->method('find')
            ->willThrowException(new DoesNotExistException(''));

        $this->expectException(DoesNotExistException::class);
        $this->service->find(999, 'testuser');
    }
}
```

---

## Template: img/app.svg

```xml
<svg xmlns="http://www.w3.org/2000/svg" height="16" width="16" viewBox="0 0 16 16">
    <path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm0 1a6 6 0 1 1 0 12A6 6 0 0 1 8 2z" fill="#222"/>
</svg>
```

ALWAYS replace with a proper app-specific icon. This placeholder ensures the build does not fail.
