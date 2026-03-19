# OCC Commands Anti-Patterns Reference

## AP-01: Running occ as Root

**WRONG** -- Running occ as root:
```bash
php occ maintenance:mode --on
# or
sudo php occ maintenance:mode --on
```
Result: File ownership changes to root. Nextcloud web interface becomes inaccessible with permission errors. The web server user can no longer read or write files.

**RIGHT** -- ALWAYS run as the web server user:
```bash
# Debian/Ubuntu
sudo -u www-data php occ maintenance:mode --on

# RHEL/CentOS
sudo -u apache php occ maintenance:mode --on

# Alpine/nginx
sudo -u nginx php occ maintenance:mode --on
```

---

## AP-02: Scanning All Files on Large Instances

**WRONG** -- Blanket scan on a large installation:
```bash
sudo -u www-data php occ files:scan --all
```
Result: Locks the file cache for hours. All users experience degraded performance. May time out and leave cache in inconsistent state.

**RIGHT** -- ALWAYS target specific paths or users:
```bash
# Scan specific user
sudo -u www-data php occ files:scan alice

# Scan specific directory
sudo -u www-data php occ files:scan --path="/alice/files/Documents"

# Scan only unscanned files
sudo -u www-data php occ files:scan --unscanned alice
```

---

## AP-03: Setting Boolean/Integer Config Without --type

**WRONG** -- Setting boolean without type flag:
```bash
sudo -u www-data php occ config:system:set debug --value=true
```
Result: Stores the string `"true"` instead of boolean `true`. PHP's `config.php` will contain `'debug' => 'true'` which is always truthy (even `"false"` is truthy in PHP).

**RIGHT** -- ALWAYS specify `--type` for non-string values:
```bash
# Boolean
sudo -u www-data php occ config:system:set debug --value=true --type=boolean

# Integer
sudo -u www-data php occ config:system:set loglevel --value=2 --type=integer

# Float
sudo -u www-data php occ config:system:set some_threshold --value=0.5 --type=float
```

---

## AP-04: Upgrading Without Maintenance Mode

**WRONG** -- Running upgrade while users are active:
```bash
sudo -u www-data php occ upgrade
```
Result: Users may write data during migration. Database schema changes may fail. File cache may become corrupted.

**RIGHT** -- ALWAYS enable maintenance mode first:
```bash
sudo -u www-data php occ maintenance:mode --on
sudo -u www-data php occ upgrade
sudo -u www-data php occ maintenance:mode --off
```

---

## AP-05: Upgrading Without Database Backup

**WRONG** -- Running upgrade without backup:
```bash
sudo -u www-data php occ maintenance:mode --on
sudo -u www-data php occ upgrade
```
Result: If the upgrade fails mid-migration, the database is left in an inconsistent state with no way to roll back.

**RIGHT** -- ALWAYS back up the database before upgrading:
```bash
sudo -u www-data php occ maintenance:mode --on
mysqldump --single-transaction -u nextcloud -p nextcloud_db > backup_$(date +%Y%m%d).sql
sudo -u www-data php occ upgrade
sudo -u www-data php occ maintenance:mode --off
```

---

## AP-06: Forgetting to Register Command in info.xml

**WRONG** -- Creating a command class without registration:
```php
// lib/Command/MyCommand.php exists but...
// appinfo/info.xml has no <commands> section
```
Result: Running `sudo -u www-data php occ myapp:my-command` produces "Command not found". The command class is never loaded by occ.

**RIGHT** -- ALWAYS register in `appinfo/info.xml`:
```xml
<commands>
    <command>OCA\MyApp\Command\MyCommand</command>
</commands>
```

---

## AP-07: Using Wrong Namespace in info.xml Registration

**WRONG** -- Incorrect namespace in registration:
```xml
<commands>
    <command>MyApp\Command\ProcessItems</command>
</commands>
```
Result: Class not found error. The autoloader cannot resolve the class.

**RIGHT** -- ALWAYS use the full `OCA\` namespace:
```xml
<commands>
    <command>OCA\MyApp\Command\ProcessItems</command>
</commands>
```

---

## AP-08: Missing Return Statement in execute()

**WRONG** -- No return value from execute:
```php
protected function execute(InputInterface $input, OutputInterface $output): int {
    $this->service->process();
    $output->writeln('Done');
    // forgot return statement
}
```
Result: PHP returns `null` implicitly, which is not a valid exit code. May trigger type errors in strict mode.

**RIGHT** -- ALWAYS return an exit code constant:
```php
protected function execute(InputInterface $input, OutputInterface $output): int {
    $this->service->process();
    $output->writeln('Done');
    return Command::SUCCESS;
}
```

---

## AP-09: Not Calling parent::__construct() in Command

**WRONG** -- Missing parent constructor call:
```php
class MyCommand extends Command {
    public function __construct(private MyService $service) {
        // forgot parent::__construct()
    }
}
```
Result: Fatal error -- the Symfony Command base class is not initialized. The command name is never set and command registration fails.

**RIGHT** -- ALWAYS call the parent constructor:
```php
class MyCommand extends Command {
    public function __construct(private MyService $service) {
        parent::__construct();
    }
}
```

---

## AP-10: Using echo Instead of OutputInterface

**WRONG** -- Using PHP echo for output:
```php
protected function execute(InputInterface $input, OutputInterface $output): int {
    echo "Processing...\n";
    echo "Done!\n";
    return Command::SUCCESS;
}
```
Result: Output bypasses Symfony Console formatting. Verbosity flags (`-v`, `-vv`, `-q`) have no effect. Output redirection and piping may behave unexpectedly.

**RIGHT** -- ALWAYS use the OutputInterface:
```php
protected function execute(InputInterface $input, OutputInterface $output): int {
    $output->writeln('Processing...');
    $output->writeln('<info>Done!</info>');
    return Command::SUCCESS;
}
```

---

## AP-11: Hardcoding Web Server User

**WRONG** -- Hardcoding www-data in scripts:
```bash
#!/bin/bash
sudo -u www-data php occ files:scan --all
```
Result: Fails on RHEL/CentOS (user is `apache`) or Alpine (user is `nginx`).

**RIGHT** -- Detect or parameterize the web server user:
```bash
#!/bin/bash
WEB_USER="${WEB_USER:-www-data}"
sudo -u "$WEB_USER" php occ files:scan --all
```

---

## AP-12: Not Handling Exceptions in Custom Commands

**WRONG** -- Letting exceptions bubble up:
```php
protected function execute(InputInterface $input, OutputInterface $output): int {
    $this->service->riskyOperation(); // may throw
    return Command::SUCCESS;
}
```
Result: Unhandled exception produces a raw stack trace. Exit code is unreliable. No user-friendly error message.

**RIGHT** -- ALWAYS catch and handle exceptions:
```php
protected function execute(InputInterface $input, OutputInterface $output): int {
    try {
        $this->service->riskyOperation();
        return Command::SUCCESS;
    } catch (\Exception $e) {
        $output->writeln("<error>Operation failed: {$e->getMessage()}</error>");
        if ($output->isVerbose()) {
            $output->writeln($e->getTraceAsString());
        }
        return Command::FAILURE;
    }
}
```
