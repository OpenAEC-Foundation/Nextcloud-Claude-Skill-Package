# Background Jobs Anti-Patterns Reference

## Registration Anti-Patterns

### AP-01: Missing ITimeFactory in Constructor

**WRONG** -- Omitting `ITimeFactory` from the constructor:
```php
class CleanupTask extends TimedJob {
    public function __construct(private CleanupService $service) {
        // Fatal error: parent constructor requires ITimeFactory
        $this->setInterval(3600);
    }

    protected function run(mixed $arguments): void {
        $this->service->cleanup();
    }
}
```

**RIGHT** -- ALWAYS inject `ITimeFactory` and pass to parent:
```php
class CleanupTask extends TimedJob {
    public function __construct(
        ITimeFactory $time,
        private CleanupService $service,
    ) {
        parent::__construct($time);
        $this->setInterval(3600);
    }

    protected function run(mixed $arguments): void {
        $this->service->cleanup();
    }
}
```

### AP-02: Forgetting setInterval()

**WRONG** -- No interval set in TimedJob constructor:
```php
class SyncJob extends TimedJob {
    public function __construct(ITimeFactory $time) {
        parent::__construct($time);
        // Missing: $this->setInterval()
        // Result: default interval is 0, job runs on EVERY cron cycle
    }

    protected function run(mixed $arguments): void {
        $this->syncData(); // Runs every 5 minutes -- likely too frequent
    }
}
```

**RIGHT** -- ALWAYS call `setInterval()` in the constructor:
```php
class SyncJob extends TimedJob {
    public function __construct(ITimeFactory $time) {
        parent::__construct($time);
        $this->setInterval(1800); // Every 30 minutes minimum
    }

    protected function run(mixed $arguments): void {
        $this->syncData();
    }
}
```

### AP-03: Registering QueuedJob in info.xml Without Purpose

**WRONG** -- QueuedJob in info.xml runs once with `null` arguments on app enable:
```xml
<background-jobs>
    <job>OCA\MyApp\BackgroundJob\ProcessFileJob</job>
</background-jobs>
```
```php
class ProcessFileJob extends QueuedJob {
    protected function run(mixed $arguments): void {
        // $arguments is null when registered via info.xml
        // This job does nothing useful on app enable
        $fileId = $arguments['fileId']; // TypeError: null
    }
}
```

**RIGHT** -- Register QueuedJob programmatically with required arguments:
```php
$jobList->add(ProcessFileJob::class, ['fileId' => 42, 'userId' => 'admin']);
```

Only use info.xml for TimedJob classes that need no arguments.

---

## Execution Anti-Patterns

### AP-04: Assuming Exact Timing

**WRONG** -- Relying on exact interval timing:
```php
class TokenRefreshJob extends TimedJob {
    public function __construct(ITimeFactory $time) {
        parent::__construct($time);
        // Token expires in exactly 3600 seconds
        // Setting interval to 3600 means the job MAY run AFTER expiry
        $this->setInterval(3600);
    }

    protected function run(mixed $arguments): void {
        $this->tokenService->refresh(); // May already be expired
    }
}
```

**RIGHT** -- ALWAYS account for timing uncertainty by using a shorter interval:
```php
class TokenRefreshJob extends TimedJob {
    public function __construct(ITimeFactory $time) {
        parent::__construct($time);
        // Token expires in 3600s, refresh 10 minutes early
        $this->setInterval(3000);
    }

    protected function run(mixed $arguments): void {
        $this->tokenService->refresh();
    }
}
```

### AP-05: Heavy Jobs Without TIME_INSENSITIVE

**WRONG** -- Long-running job blocks time-sensitive queue:
```php
class FullReindexJob extends TimedJob {
    public function __construct(ITimeFactory $time) {
        parent::__construct($time);
        $this->setInterval(86400); // Daily
        // Missing: setTimeSensitivity
        // This 20-minute job blocks notifications, share expiry, etc.
    }

    protected function run(mixed $arguments): void {
        $this->indexer->rebuildAll(); // Takes 20 minutes
    }
}
```

**RIGHT** -- ALWAYS mark heavy jobs as time-insensitive:
```php
class FullReindexJob extends TimedJob {
    public function __construct(ITimeFactory $time) {
        parent::__construct($time);
        $this->setInterval(86400);
        $this->setTimeSensitivity(IJob::TIME_INSENSITIVE);
        $this->setAllowParallelRuns(false);
    }

    protected function run(mixed $arguments): void {
        $this->indexer->rebuildAll();
    }
}
```

### AP-06: Parallel Runs on Shared State

**WRONG** -- Concurrent runs corrupt shared data:
```php
class AggregateStatsJob extends TimedJob {
    public function __construct(ITimeFactory $time) {
        parent::__construct($time);
        $this->setInterval(300);
        // Missing: setAllowParallelRuns(false)
        // If cron runs overlap, stats are calculated twice and overwritten
    }

    protected function run(mixed $arguments): void {
        $this->statsService->truncateAndRecalculate(); // Race condition
    }
}
```

**RIGHT** -- ALWAYS prevent parallel runs when modifying shared state:
```php
class AggregateStatsJob extends TimedJob {
    public function __construct(ITimeFactory $time) {
        parent::__construct($time);
        $this->setInterval(300);
        $this->setAllowParallelRuns(false);
    }

    protected function run(mixed $arguments): void {
        $this->statsService->truncateAndRecalculate();
    }
}
```

---

## Cron Configuration Anti-Patterns

### AP-07: Using AJAX Mode in Production

**WRONG** -- AJAX cron in production:
```
Admin Settings → Basic settings → Background jobs → AJAX
```
Problems:
- Jobs only run when a user loads a page
- No users online at night = no jobs run for hours
- Unreliable timing for time-sensitive operations
- Notification delivery, share expiry, and cleanup are all delayed

**RIGHT** -- ALWAYS configure system cron for production:
```bash
# Add system crontab entry
sudo crontab -u www-data -e
*/5 * * * * php -f /var/www/nextcloud/cron.php

# Tell Nextcloud to use system cron
sudo -u www-data php occ background:cron
```

### AP-08: Running cron.php as Root

**WRONG** -- Executing cron as root user:
```bash
*/5 * * * * php -f /var/www/nextcloud/cron.php
# Runs as root -- creates files owned by root that www-data cannot access
```

**RIGHT** -- ALWAYS run as the web server user:
```bash
*/5 * * * * sudo -u www-data php -f /var/www/nextcloud/cron.php
# Or use crontab for the www-data user directly:
sudo crontab -u www-data -e
*/5 * * * * php -f /var/www/nextcloud/cron.php
```

---

## Error Handling Anti-Patterns

### AP-09: Unhandled Exceptions in run()

**WRONG** -- Letting exceptions propagate without logging:
```php
protected function run(mixed $arguments): void {
    $data = $this->externalApi->fetch(); // May throw HttpException
    $this->store->save($data);
    // If fetch() throws, the job fails silently (for QueuedJob: stays in queue and retries forever)
}
```

**RIGHT** -- ALWAYS handle exceptions with logging:
```php
protected function run(mixed $arguments): void {
    try {
        $data = $this->externalApi->fetch();
        $this->store->save($data);
    } catch (HttpException $e) {
        $this->logger->error('External API fetch failed: {message}', [
            'message' => $e->getMessage(),
            'app' => 'myapp',
        ]);
        // For QueuedJob: re-throw to keep in queue for retry
        // For TimedJob: swallow to prevent blocking next scheduled run
        throw $e; // Or don't, depending on retry strategy
    }
}
```

### AP-10: Missing Argument Validation

**WRONG** -- Trusting arguments without validation:
```php
protected function run(mixed $arguments): void {
    // $arguments may be null, missing keys, or wrong types
    $fileId = $arguments['fileId'];
    $this->processor->process($fileId);
}
```

**RIGHT** -- ALWAYS validate arguments before use:
```php
protected function run(mixed $arguments): void {
    if (!is_array($arguments) || !isset($arguments['fileId'])) {
        $this->logger->error('Invalid arguments for ProcessFileJob', [
            'arguments' => $arguments,
            'app' => 'myapp',
        ]);
        return; // Exit gracefully -- removes QueuedJob from queue
    }

    $fileId = (int)$arguments['fileId'];
    $this->processor->process($fileId);
}
```

---

## Summary Table

| ID | Anti-Pattern | Rule |
|----|-------------|------|
| AP-01 | Missing ITimeFactory | ALWAYS inject ITimeFactory and call parent::__construct($time) |
| AP-02 | Forgetting setInterval | ALWAYS call setInterval() in TimedJob constructor |
| AP-03 | QueuedJob in info.xml | ALWAYS register QueuedJob programmatically with arguments |
| AP-04 | Assuming exact timing | NEVER rely on exact interval -- use shorter interval with safety margin |
| AP-05 | Heavy job without TIME_INSENSITIVE | ALWAYS mark slow jobs as TIME_INSENSITIVE |
| AP-06 | Parallel runs on shared state | ALWAYS use setAllowParallelRuns(false) for state-modifying jobs |
| AP-07 | AJAX mode in production | NEVER use AJAX cron mode in production |
| AP-08 | Running cron as root | ALWAYS run cron.php as the web server user |
| AP-09 | Unhandled exceptions | ALWAYS handle exceptions with proper logging |
| AP-10 | Missing argument validation | ALWAYS validate job arguments before use |
