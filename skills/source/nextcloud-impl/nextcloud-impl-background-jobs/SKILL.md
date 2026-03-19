---
name: nextcloud-impl-background-jobs
description: "Guides Nextcloud background jobs including QueuedJob for one-time tasks, TimedJob for recurring tasks, IJobList for programmatic management, scheduleAfter for delayed execution, cron configuration modes, time sensitivity, and parallel run control. Activates when implementing background processing, scheduling recurring tasks, or configuring cron."
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-impl-background-jobs

## Quick Reference

### Job Types

| Class | Namespace | Execution | Use Case |
|-------|-----------|-----------|----------|
| `TimedJob` | `OCP\BackgroundJob\TimedJob` | Recurring at interval | Periodic cleanup, sync, notifications |
| `QueuedJob` | `OCP\BackgroundJob\QueuedJob` | Once, then auto-removed | Process upload, send email, one-time migration |

### Key Methods

| Method | Available On | Description |
|--------|-------------|-------------|
| `setInterval(int $seconds)` | `TimedJob` | Minimum seconds between runs |
| `setTimeSensitivity(int $sensitivity)` | Both | `IJob::TIME_INSENSITIVE` for heavy jobs |
| `setAllowParallelRuns(bool $allow)` | Both (NC 27+) | Prevent concurrent execution |
| `run(mixed $arguments)` | Both | Override this -- your job logic goes here |

### IJobList API (Programmatic Management)

| Method | Description |
|--------|-------------|
| `add(string $class, mixed $argument = null)` | Register a job (idempotent for TimedJob) |
| `remove(string $class, mixed $argument = null)` | Remove a registered job |
| `has(string $class, mixed $argument)` | Check if job is registered |
| `scheduleAfter(string $class, mixed $argument, int $timestamp)` | Schedule job after UNIX timestamp |
| `getById(int $id)` | Get specific job by ID |

### Registration Methods

| Method | Location | When to Use |
|--------|----------|-------------|
| `info.xml` `<background-jobs>` | `appinfo/info.xml` | Static recurring jobs (TimedJob) |
| `IJobList::add()` | PHP code | Dynamic jobs, QueuedJob with arguments |
| `IJobList::scheduleAfter()` | PHP code | Delayed execution after specific time |

### Cron Mode Comparison

| Mode | Trigger | Interval | Production Use |
|------|---------|----------|----------------|
| **System cron** | OS crontab | Every 5 min (recommended) | YES -- ALWAYS use this |
| **Webcron** | External HTTP call | Depends on caller | Acceptable if system cron unavailable |
| **AJAX** | Page load by user | Unreliable, on-demand | **NEVER** use in production |

### Critical Warnings

**NEVER** use AJAX cron mode in production -- it depends on user page loads and will miss jobs when no users are active. System cron is the ONLY reliable option.

**NEVER** assume `setInterval()` provides exact timing -- it sets the MINIMUM time between runs. The actual interval depends on cron frequency and job queue length.

**NEVER** forget to inject `ITimeFactory` in the TimedJob constructor -- the parent class requires it. Omitting it causes a fatal error.

**NEVER** perform long-running operations without `setTimeSensitivity(IJob::TIME_INSENSITIVE)` -- time-sensitive jobs block the queue and delay other jobs.

**ALWAYS** call `parent::__construct($time)` in TimedJob constructors -- skipping this breaks interval tracking.

**ALWAYS** call `setInterval()` in the TimedJob constructor -- without it, the default interval is 0 and the job runs on every cron cycle.

**ALWAYS** use `setAllowParallelRuns(false)` for jobs that modify shared state -- concurrent runs cause race conditions and data corruption.

**ALWAYS** register TimedJob classes in `info.xml` -- they are automatically managed by the app lifecycle (added on enable, removed on disable).

**ALWAYS** use `IJobList::add()` for QueuedJob -- queued jobs require arguments and cannot be statically registered for meaningful use.

---

## Decision Tree: Which Job Type?

```
Need background processing?
├── Runs repeatedly on a schedule?
│   └── YES → TimedJob
│       ├── Heavy/slow work? → setTimeSensitivity(TIME_INSENSITIVE)
│       ├── Must not overlap? → setAllowParallelRuns(false)
│       └── Register in info.xml <background-jobs>
├── Runs once then done?
│   └── YES → QueuedJob
│       ├── Run immediately (next cron)? → IJobList::add()
│       └── Run after specific time? → IJobList::scheduleAfter()
└── Needs to run at exact time?
    └── Nextcloud background jobs do NOT guarantee exact timing.
        Use setInterval() for minimum delay, system cron for best precision.
```

---

## Essential Patterns

### Pattern 1: TimedJob (Recurring)

```php
<?php
namespace OCA\MyApp\BackgroundJob;

use OCA\MyApp\Service\CleanupService;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJob;
use OCP\BackgroundJob\TimedJob;

class CleanupTask extends TimedJob {
    public function __construct(
        ITimeFactory $time,
        private CleanupService $service,
    ) {
        parent::__construct($time);
        // Run at most once per hour (3600 seconds)
        $this->setInterval(3600);
        // Mark as non-urgent so it does not block time-sensitive jobs
        $this->setTimeSensitivity(IJob::TIME_INSENSITIVE);
    }

    protected function run(mixed $arguments): void {
        $this->service->deleteExpiredItems();
    }
}
```

Register in `appinfo/info.xml`:
```xml
<info>
    <background-jobs>
        <job>OCA\MyApp\BackgroundJob\CleanupTask</job>
    </background-jobs>
</info>
```

### Pattern 2: QueuedJob (One-Time)

```php
<?php
namespace OCA\MyApp\BackgroundJob;

use OCA\MyApp\Service\FileProcessor;
use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\QueuedJob;

class ProcessFileJob extends QueuedJob {
    public function __construct(
        ITimeFactory $time,
        private FileProcessor $processor,
    ) {
        parent::__construct($time);
    }

    protected function run(mixed $arguments): void {
        $fileId = $arguments['fileId'];
        $userId = $arguments['userId'];
        $this->processor->process($fileId, $userId);
    }
}
```

Dispatch from a service or controller:
```php
use OCP\BackgroundJob\IJobList;

class FileService {
    public function __construct(
        private IJobList $jobList,
    ) {}

    public function queueProcessing(int $fileId, string $userId): void {
        $this->jobList->add(ProcessFileJob::class, [
            'fileId' => $fileId,
            'userId' => $userId,
        ]);
    }
}
```

### Pattern 3: Scheduled Delayed Execution

```php
use OCP\BackgroundJob\IJobList;

class ShareService {
    public function __construct(
        private IJobList $jobList,
    ) {}

    public function createExpiringShare(int $shareId, int $expiresAt): void {
        // Job will execute after the expiration timestamp
        $this->jobList->scheduleAfter(
            RevokeShareJob::class,
            ['shareId' => $shareId],
            $expiresAt,
        );
    }
}
```

### Pattern 4: Preventing Parallel Runs

```php
<?php
namespace OCA\MyApp\BackgroundJob;

use OCP\AppFramework\Utility\ITimeFactory;
use OCP\BackgroundJob\IJob;
use OCP\BackgroundJob\TimedJob;

class SyncExternalData extends TimedJob {
    public function __construct(
        ITimeFactory $time,
        private ExternalApiClient $client,
        private DataStore $store,
    ) {
        parent::__construct($time);
        $this->setInterval(900); // Every 15 minutes
        $this->setTimeSensitivity(IJob::TIME_INSENSITIVE);
        // Prevent overlapping runs -- critical for data consistency
        $this->setAllowParallelRuns(false);
    }

    protected function run(mixed $arguments): void {
        $data = $this->client->fetchLatest();
        $this->store->upsert($data);
    }
}
```

### Pattern 5: System Cron Configuration

Add to the server's crontab (`crontab -u www-data -e`):
```
*/5 * * * * php -f /var/www/nextcloud/cron.php
```

Verify in admin settings or via OCC:
```bash
sudo -u www-data php occ background:cron
```

Check last cron execution:
```bash
sudo -u www-data php occ background:job:list
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- QueuedJob, TimedJob, IJobList complete API
- [references/examples.md](references/examples.md) -- Timed job, queued job, scheduled job, registration patterns
- [references/anti-patterns.md](references/anti-patterns.md) -- Background job mistakes and corrections

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/backgroundjobs.html
- https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/background_jobs_configuration.html
