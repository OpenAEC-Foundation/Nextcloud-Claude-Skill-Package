# Background Jobs Methods Reference

## OCP\BackgroundJob\TimedJob

Abstract base class for recurring background jobs. The job runs repeatedly, with a minimum interval between executions.

**Constructor requirement:**
```php
public function __construct(ITimeFactory $time) {
    parent::__construct($time);
    $this->setInterval(3600); // ALWAYS set interval in constructor
}
```

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `setInterval` | `setInterval(int $seconds): void` | Set minimum seconds between runs. ALWAYS call in constructor. Default is 0 (runs every cron cycle). |
| `setTimeSensitivity` | `setTimeSensitivity(int $sensitivity): void` | `IJob::TIME_SENSITIVE` (default) or `IJob::TIME_INSENSITIVE`. Insensitive jobs are skipped when cron is under time pressure. |
| `setAllowParallelRuns` | `setAllowParallelRuns(bool $allow): void` | NC 27+. When `false`, prevents concurrent execution of the same job class. Default is `true`. |
| `run` | `abstract protected run(mixed $arguments): void` | Override this with your job logic. Called by the framework on each execution. |

**Inherited from Job:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `getId` | `getId(): int` | Get the job's database ID |
| `getLastRun` | `getLastRun(): int` | UNIX timestamp of last execution |
| `getArgument` | `getArgument(): mixed` | Get the stored argument (usually from info.xml registration) |

---

## OCP\BackgroundJob\QueuedJob

Abstract base class for one-time background jobs. The job is automatically removed from the job list after successful execution.

**Constructor requirement:**
```php
public function __construct(ITimeFactory $time) {
    parent::__construct($time);
}
```

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `setTimeSensitivity` | `setTimeSensitivity(int $sensitivity): void` | Same as TimedJob. Use `IJob::TIME_INSENSITIVE` for heavy one-time tasks. |
| `setAllowParallelRuns` | `setAllowParallelRuns(bool $allow): void` | NC 27+. Prevents concurrent runs of jobs with the same class AND arguments. |
| `run` | `abstract protected run(mixed $arguments): void` | Override with job logic. The `$arguments` parameter contains whatever was passed to `IJobList::add()`. |

**Behavior notes:**
- QueuedJob is automatically removed after `run()` completes without throwing an exception.
- If `run()` throws an exception, the job remains in the queue and retries on the next cron cycle.
- Each call to `IJobList::add()` with different arguments creates a separate job entry.

---

## OCP\BackgroundJob\IJobList

Interface for programmatic job management. Inject via constructor: `private IJobList $jobList`.

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `add` | `add(string $class, mixed $argument = null): void` | Add a job to the list. For TimedJob, this is idempotent (same class + argument = no duplicate). For QueuedJob, each call with unique arguments creates a new entry. |
| `remove` | `remove(string $class, mixed $argument = null): void` | Remove a job by class and argument. |
| `removeById` | `removeById(int $id): void` | Remove a job by its database ID. |
| `has` | `has(string $class, mixed $argument): bool` | Check if a job with the given class and argument exists. |
| `scheduleAfter` | `scheduleAfter(string $class, mixed $argument, int $afterTimestamp): void` | Register a job that will not execute until after the given UNIX timestamp. The job is still subject to cron scheduling -- it runs on the first cron cycle after the timestamp. |
| `getById` | `getById(int $id): ?IJob` | Retrieve a job by database ID. Returns `null` if not found. |
| `getJobs` | `getJobs(?string $class = null, int $limit = null, int $offset = null): array` | List jobs, optionally filtered by class. |

---

## OCP\BackgroundJob\IJob

Interface implemented by all job types. Constants:

| Constant | Value | Description |
|----------|-------|-------------|
| `IJob::TIME_SENSITIVE` | `0` | Default. Job runs on every eligible cron cycle. |
| `IJob::TIME_INSENSITIVE` | `1` | Job may be deferred when cron is under time pressure. ALWAYS use for heavy/slow jobs. |

---

## OCP\AppFramework\Utility\ITimeFactory

Required dependency for all background job constructors. Provides the current time to the job framework for interval tracking.

**ALWAYS inject via constructor:**
```php
public function __construct(ITimeFactory $time) {
    parent::__construct($time);
}
```

**NEVER** instantiate `ITimeFactory` manually or use `time()` -- the framework tracks job execution timestamps through this factory.

---

## info.xml Registration Syntax

```xml
<info xmlns="https://apps.nextcloud.com/schema/apps/info.xsd">
    <!-- other elements -->
    <background-jobs>
        <job>OCA\MyApp\BackgroundJob\CleanupTask</job>
        <job>OCA\MyApp\BackgroundJob\SyncJob</job>
    </background-jobs>
</info>
```

**Behavior:**
- Jobs listed here are automatically added to `IJobList` when the app is enabled.
- Jobs are automatically removed from `IJobList` when the app is disabled.
- This is the preferred registration method for TimedJob classes.
- QueuedJob classes CAN be listed here but they will run once with `null` arguments on app enable -- rarely useful.

---

## OCC Commands for Background Jobs

| Command | Description |
|---------|-------------|
| `occ background:cron` | Set background job mode to system cron |
| `occ background:webcron` | Set background job mode to webcron |
| `occ background:ajax` | Set background job mode to AJAX (NOT for production) |
| `occ background:job:list` | List all registered background jobs with status |
| `occ background:job:execute <id>` | Manually execute a specific job by ID (NC 27+) |
