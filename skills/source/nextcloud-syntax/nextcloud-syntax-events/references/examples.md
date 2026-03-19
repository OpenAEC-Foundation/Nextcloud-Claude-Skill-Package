# Event System Examples

## Example 1: Complete Custom Event Lifecycle

This example shows the full cycle: defining an event, registering a listener, and dispatching.

### Step 1: Define the Event

```php
<?php
// lib/Event/DocumentApprovedEvent.php
namespace OCA\MyApp\Event;

use OCP\EventDispatcher\Event;
use OCP\IUser;

class DocumentApprovedEvent extends Event {
    public function __construct(
        private IUser $approver,
        private int $documentId,
        private string $documentPath,
    ) {
        parent::__construct();
    }

    public function getApprover(): IUser {
        return $this->approver;
    }

    public function getDocumentId(): int {
        return $this->documentId;
    }

    public function getDocumentPath(): string {
        return $this->documentPath;
    }
}
```

### Step 2: Register the Listener

```php
<?php
// lib/AppInfo/Application.php
namespace OCA\MyApp\AppInfo;

use OCA\MyApp\Event\DocumentApprovedEvent;
use OCA\MyApp\Listener\DocumentApprovedListener;
use OCA\MyApp\Listener\NotifyOnApprovalListener;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;

class Application extends App implements IBootstrap {
    public const APP_ID = 'myapp';

    public function __construct() {
        parent::__construct(self::APP_ID);
    }

    public function register(IRegistrationContext $context): void {
        // Multiple listeners for the same event
        $context->registerEventListener(
            DocumentApprovedEvent::class,
            DocumentApprovedListener::class
        );
        $context->registerEventListener(
            DocumentApprovedEvent::class,
            NotifyOnApprovalListener::class
        );
    }

    public function boot(IBootContext $context): void {
    }
}
```

### Step 3: Implement the Listener

```php
<?php
// lib/Listener/DocumentApprovedListener.php
namespace OCA\MyApp\Listener;

use OCA\MyApp\Event\DocumentApprovedEvent;
use OCA\MyApp\Service\AuditService;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;

class DocumentApprovedListener implements IEventListener {
    public function __construct(
        private AuditService $auditService,
    ) {
    }

    public function handle(Event $event): void {
        if (!($event instanceof DocumentApprovedEvent)) {
            return;
        }

        $this->auditService->logApproval(
            $event->getApprover()->getUID(),
            $event->getDocumentId(),
            $event->getDocumentPath()
        );
    }
}
```

### Step 4: Dispatch the Event

```php
<?php
// lib/Service/ApprovalService.php
namespace OCA\MyApp\Service;

use OCA\MyApp\Event\DocumentApprovedEvent;
use OCP\EventDispatcher\IEventDispatcher;
use OCP\IUserSession;

class ApprovalService {
    public function __construct(
        private IEventDispatcher $dispatcher,
        private IUserSession $userSession,
    ) {
    }

    public function approveDocument(int $documentId, string $path): void {
        // ... perform approval logic ...

        $this->dispatcher->dispatchTyped(
            new DocumentApprovedEvent(
                $this->userSession->getUser(),
                $documentId,
                $path
            )
        );
    }
}
```

---

## Example 2: Before/After Event Pattern

Use Before events to validate or modify; After events to react.

### Define Before and After Events

```php
<?php
// lib/Event/BeforeItemDeletedEvent.php
namespace OCA\MyApp\Event;

use OCP\EventDispatcher\Event;

class BeforeItemDeletedEvent extends Event {
    private bool $cancelled = false;

    public function __construct(
        private int $itemId,
        private string $userId,
    ) {
        parent::__construct();
    }

    public function getItemId(): int {
        return $this->itemId;
    }

    public function getUserId(): string {
        return $this->userId;
    }

    public function cancel(): void {
        $this->cancelled = true;
    }

    public function isCancelled(): bool {
        return $this->cancelled;
    }
}
```

```php
<?php
// lib/Event/ItemDeletedEvent.php
namespace OCA\MyApp\Event;

use OCP\EventDispatcher\Event;

class ItemDeletedEvent extends Event {
    public function __construct(
        private int $itemId,
        private string $userId,
    ) {
        parent::__construct();
    }

    public function getItemId(): int {
        return $this->itemId;
    }

    public function getUserId(): string {
        return $this->userId;
    }
}
```

### Dispatch Both Events in Service

```php
<?php
namespace OCA\MyApp\Service;

use OCA\MyApp\Event\BeforeItemDeletedEvent;
use OCA\MyApp\Event\ItemDeletedEvent;
use OCP\EventDispatcher\IEventDispatcher;

class ItemService {
    public function __construct(
        private IEventDispatcher $dispatcher,
        private ItemMapper $mapper,
    ) {
    }

    public function deleteItem(int $id, string $userId): bool {
        // Dispatch Before event -- listeners can cancel
        $beforeEvent = new BeforeItemDeletedEvent($id, $userId);
        $this->dispatcher->dispatchTyped($beforeEvent);

        if ($beforeEvent->isCancelled()) {
            return false;
        }

        // Perform the actual deletion
        $this->mapper->delete($id, $userId);

        // Dispatch After event -- informational only
        $this->dispatcher->dispatchTyped(
            new ItemDeletedEvent($id, $userId)
        );

        return true;
    }
}
```

---

## Example 3: Listening to Built-In Nextcloud Events

### React to File Uploads

```php
<?php
// lib/AppInfo/Application.php (register method)
$context->registerEventListener(
    \OCP\Files\Events\Node\NodeCreatedEvent::class,
    \OCA\MyApp\Listener\FileCreatedListener::class
);
```

```php
<?php
// lib/Listener/FileCreatedListener.php
namespace OCA\MyApp\Listener;

use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Files\Events\Node\NodeCreatedEvent;
use OCP\Files\File;
use Psr\Log\LoggerInterface;

class FileCreatedListener implements IEventListener {
    public function __construct(
        private LoggerInterface $logger,
    ) {
    }

    public function handle(Event $event): void {
        if (!($event instanceof NodeCreatedEvent)) {
            return;
        }

        $node = $event->getNode();

        // Only process files, not folders
        if (!($node instanceof File)) {
            return;
        }

        $this->logger->info('New file uploaded: {path}', [
            'path' => $node->getPath(),
            'size' => $node->getSize(),
            'mime' => $node->getMimeType(),
        ]);
    }
}
```

### React to User Login

```php
<?php
// lib/AppInfo/Application.php (register method)
$context->registerEventListener(
    \OCP\User\Events\UserLoggedInEvent::class,
    \OCA\MyApp\Listener\LoginListener::class
);
```

```php
<?php
// lib/Listener/LoginListener.php
namespace OCA\MyApp\Listener;

use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\User\Events\UserLoggedInEvent;

class LoginListener implements IEventListener {
    public function __construct(
        private \OCA\MyApp\Service\SessionService $sessionService,
    ) {
    }

    public function handle(Event $event): void {
        if (!($event instanceof UserLoggedInEvent)) {
            return;
        }

        $this->sessionService->recordLogin(
            $event->getUser()->getUID()
        );
    }
}
```

### React to Share Creation

```php
<?php
// lib/Listener/ShareCreatedListener.php
namespace OCA\MyApp\Listener;

use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Share\Events\ShareCreatedEvent;

class ShareCreatedListener implements IEventListener {
    public function __construct(
        private \OCA\MyApp\Service\AuditService $auditService,
    ) {
    }

    public function handle(Event $event): void {
        if (!($event instanceof ShareCreatedEvent)) {
            return;
        }

        $share = $event->getShare();
        $this->auditService->logShare(
            $share->getSharedBy(),
            $share->getSharedWith(),
            $share->getNodeId(),
            $share->getShareType()
        );
    }
}
```

---

## Example 4: Multiple Listeners for One Event

Register multiple listeners in `Application::register()`:

```php
public function register(IRegistrationContext $context): void {
    // All three listeners fire when a user is deleted
    $context->registerEventListener(
        \OCP\User\Events\UserDeletedEvent::class,
        \OCA\MyApp\Listener\CleanupUserDataListener::class
    );
    $context->registerEventListener(
        \OCP\User\Events\UserDeletedEvent::class,
        \OCA\MyApp\Listener\NotifyAdminListener::class
    );
    $context->registerEventListener(
        \OCP\User\Events\UserDeletedEvent::class,
        \OCA\MyApp\Listener\RevokeSharesListener::class
    );
}
```

Use the `$priority` parameter (third argument) to control execution order. Higher priority executes first:

```php
$context->registerEventListener(
    UserDeletedEvent::class,
    RevokeSharesListener::class,
    100  // Runs first
);
$context->registerEventListener(
    UserDeletedEvent::class,
    CleanupUserDataListener::class,
    50   // Runs second
);
$context->registerEventListener(
    UserDeletedEvent::class,
    NotifyAdminListener::class,
    0    // Runs last (default priority)
);
```

---

## Example 5: Frontend Event Bus -- Vue Component

### Options API (Vue 2 / NC 28+)

```vue
<template>
    <div>
        <p>{{ latestUpload }}</p>
        <NcButton @click="notifyOtherComponents">
            Notify
        </NcButton>
    </div>
</template>

<script>
import { subscribe, unsubscribe, emit } from '@nextcloud/event-bus'
import NcButton from '@nextcloud/vue/components/NcButton'

export default {
    name: 'MyComponent',
    components: { NcButton },
    data() {
        return {
            latestUpload: '',
        }
    },
    created() {
        this._handleUpload = (node) => {
            this.latestUpload = node.path
        }
        subscribe('files:node:uploaded', this._handleUpload)
    },
    beforeDestroy() {
        unsubscribe('files:node:uploaded', this._handleUpload)
    },
    methods: {
        notifyOtherComponents() {
            emit('myapp:action:completed', { timestamp: Date.now() })
        },
    },
}
</script>
```

### Composition API (Vue 3 / NC 31+)

```vue
<template>
    <div>
        <p>{{ latestUpload }}</p>
    </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { subscribe, unsubscribe } from '@nextcloud/event-bus'

const latestUpload = ref('')

const handleUpload = (node: { path: string }) => {
    latestUpload.value = node.path
}

subscribe('files:node:uploaded', handleUpload)

onBeforeUnmount(() => {
    unsubscribe('files:node:uploaded', handleUpload)
})
</script>
```

---

## Example 6: Inject Scripts via BeforeTemplateRenderedEvent

Add custom JavaScript/CSS to the Nextcloud page:

```php
<?php
// lib/AppInfo/Application.php (register method)
$context->registerEventListener(
    \OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent::class,
    \OCA\MyApp\Listener\InjectScriptsListener::class
);
```

```php
<?php
// lib/Listener/InjectScriptsListener.php
namespace OCA\MyApp\Listener;

use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\Util;

class InjectScriptsListener implements IEventListener {
    public function handle(Event $event): void {
        if (!($event instanceof BeforeTemplateRenderedEvent)) {
            return;
        }

        // Only inject for logged-in users
        if (!$event->isLoggedIn()) {
            return;
        }

        Util::addScript('myapp', 'myapp-main');
        Util::addStyle('myapp', 'myapp-styles');
    }
}
```
