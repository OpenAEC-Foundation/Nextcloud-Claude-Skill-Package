# Background Jobs Examples Reference

## Example 1: Complete TimedJob with All Options

A recurring cleanup job that runs hourly, is not time-sensitive, and prevents parallel execution.

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\BackgroundJob;

use OCA\MyApp\Service\CleanupService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJob;
use OCP\BackgroundJob\TimedJob;
use Psr\Log\LoggerInterface;

class CleanupExpiredItems extends TimedJob {
    public function __construct(
        ITimeFactory $time,
        private CleanupService $cleanupService,
        private LoggerInterface $logger,
    ) {
        parent::__construct($time);

        // Run at most once per hour
        $this->setInterval(3600);

        // Heavy operation -- do not block time-sensitive jobs
        $this->setTimeSensitivity(IJob::TIME_INSENSITIVE);

        // Prevent overlapping runs
        $this->setAllowParallelRuns(false);
    }

    protected function run(mixed $arguments): void {
        $count = $this->cleanupService->deleteExpired();
        $this->logger->info('Cleaned up {count} expired items', [
            'count' => $count,
            'app' => 'myapp',
        ]);
    }
}
```

Registration in `appinfo/info.xml`:
```xml
<info xmlns="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>myapp</id>
    <name>My App</name>
    <namespace>MyApp</namespace>
    <!-- other elements -->
    <background-jobs>
        <job>OCA\MyApp\BackgroundJob\CleanupExpiredItems</job>
    </background-jobs>
</info>
```

---

## Example 2: QueuedJob with Arguments

A one-time job that processes an uploaded file. Dispatched programmatically when a file is uploaded.

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\BackgroundJob;

use OCA\MyApp\Service\FileAnalyzer;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\QueuedJob;
use Psr\Log\LoggerInterface;

class AnalyzeFileJob extends QueuedJob {
    public function __construct(
        ITimeFactory $time,
        private FileAnalyzer $analyzer,
        private LoggerInterface $logger,
    ) {
        parent::__construct($time);
        // File analysis can be slow -- mark as non-urgent
        $this->setTimeSensitivity(\OCP\BackgroundJob\IJob::TIME_INSENSITIVE);
    }

    protected function run(mixed $arguments): void {
        $fileId = (int)$arguments['fileId'];
        $userId = (string)$arguments['userId'];

        $this->logger->debug('Analyzing file {fileId} for user {userId}', [
            'fileId' => $fileId,
            'userId' => $userId,
            'app' => 'myapp',
        ]);

        $this->analyzer->analyze($fileId, $userId);
    }
}
```

Dispatching from a service:
```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\Service;

use OCA\MyApp\BackgroundJob\AnalyzeFileJob;
use OCP\BackgroundJob\IJobList;

class UploadService {
    public function __construct(
        private IJobList $jobList,
    ) {}

    public function handleUpload(int $fileId, string $userId): void {
        // Queue background analysis -- runs on next cron cycle
        $this->jobList->add(AnalyzeFileJob::class, [
            'fileId' => $fileId,
            'userId' => $userId,
        ]);
    }
}
```

---

## Example 3: Scheduled Job (Delayed Execution)

A job that revokes a share after its expiration time.

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\BackgroundJob;

use OCA\MyApp\Service\ShareManager;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\QueuedJob;
use Psr\Log\LoggerInterface;

class RevokeExpiredShareJob extends QueuedJob {
    public function __construct(
        ITimeFactory $time,
        private ShareManager $shareManager,
        private LoggerInterface $logger,
    ) {
        parent::__construct($time);
    }

    protected function run(mixed $arguments): void {
        $shareId = (int)$arguments['shareId'];

        try {
            $this->shareManager->revokeShare($shareId);
            $this->logger->info('Revoked expired share {shareId}', [
                'shareId' => $shareId,
                'app' => 'myapp',
            ]);
        } catch (\OCP\Share\Exceptions\ShareNotFound $e) {
            // Share already deleted -- nothing to do
            $this->logger->debug('Share {shareId} already removed', [
                'shareId' => $shareId,
                'app' => 'myapp',
            ]);
        }
    }
}
```

Scheduling from a service:
```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\Service;

use OCA\MyApp\BackgroundJob\RevokeExpiredShareJob;
use OCP\BackgroundJob\IJobList;

class ShareService {
    public function __construct(
        private IJobList $jobList,
    ) {}

    public function createTimedShare(int $shareId, \DateTimeInterface $expiresAt): void {
        // Schedule revocation for after the expiration timestamp
        $this->jobList->scheduleAfter(
            RevokeExpiredShareJob::class,
            ['shareId' => $shareId],
            $expiresAt->getTimestamp(),
        );
    }
}
```

---

## Example 4: Programmatic Job Management

Managing jobs dynamically from an admin controller or service.

```php
<?php
declare(strict_types=1);

namespace OCA\MyApp\Service;

use OCA\MyApp\BackgroundJob\SyncExternalData;
use OCP\BackgroundJob\IJobList;

class SyncConfigService {
    public function __construct(
        private IJobList $jobList,
    ) {}

    /**
     * Enable or disable the sync background job based on admin settings.
     */
    public function setSyncEnabled(bool $enabled): void {
        if ($enabled) {
            // add() is idempotent for TimedJob -- safe to call multiple times
            $this->jobList->add(SyncExternalData::class);
        } else {
            $this->jobList->remove(SyncExternalData::class);
        }
    }

    /**
     * Check if the sync job is currently registered.
     */
    public function isSyncEnabled(): bool {
        return $this->jobList->has(SyncExternalData::class, null);
    }
}
```

---

## Example 5: Multiple TimedJobs in info.xml

```xml
<info xmlns="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>myapp</id>
    <name>My App</name>
    <namespace>MyApp</namespace>
    <version>1.0.0</version>
    <background-jobs>
        <job>OCA\MyApp\BackgroundJob\CleanupExpiredItems</job>
        <job>OCA\MyApp\BackgroundJob\SyncExternalData</job>
        <job>OCA\MyApp\BackgroundJob\SendDigestNotifications</job>
    </background-jobs>
</info>
```

---

## Example 6: System Cron Setup

### Linux (recommended)
```bash
# Add cron entry for the web server user
sudo crontab -u www-data -e

# Add this line (runs every 5 minutes):
*/5 * * * * php -f /var/www/nextcloud/cron.php

# Set Nextcloud to use system cron
sudo -u www-data php /var/www/nextcloud/occ background:cron
```

### Docker
```bash
# In docker-compose.yml, add a cron service:
# cron:
#   image: nextcloud:apache
#   entrypoint: /cron.sh
#   depends_on:
#     - app
#   volumes_from:
#     - app
```

### Verify cron is working
```bash
# List all background jobs and their last run time
sudo -u www-data php /var/www/nextcloud/occ background:job:list

# Manually trigger a specific job (useful for debugging)
sudo -u www-data php /var/www/nextcloud/occ background:job:execute <job-id>
```
