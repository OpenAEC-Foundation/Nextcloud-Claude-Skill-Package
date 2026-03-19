---
name: nextcloud-impl-occ-commands
description: >
  Use when using occ commands, creating custom CLI commands, or administering Nextcloud from the command line.
  Prevents running occ as wrong user, missing command registration in info.xml, and forgetting maintenance mode.
  Covers built-in commands for maintenance, user management, app management, file scanning, and configuration, plus custom command development with Symfony Console.
  Keywords: occ, php occ, maintenance:mode, app:enable, files:scan, Symfony Console, Command, info.xml commands.
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-impl-occ-commands

## Quick Reference

### Invocation

```bash
sudo -u www-data php occ [command] [arguments] [options]
```

**NEVER** run occ as root -- file permissions will break and Nextcloud will become inaccessible. ALWAYS use the web server user (`www-data` on Debian/Ubuntu, `apache` on RHEL/CentOS, `nginx` on Alpine).

### Built-in Command Categories

| Category | Prefix | Purpose |
|----------|--------|---------|
| Maintenance | `maintenance:` | Maintenance mode, repair, updates |
| User Management | `user:` | Add, delete, list, enable/disable users |
| App Management | `app:` | Enable, disable, list, update apps |
| Configuration | `config:` | System and app config get/set |
| Files | `files:` | Scan, cleanup, transfer ownership |
| Background Jobs | `background:` | Set background job mode |
| Database | `db:` | Migrations, conversions |
| Encryption | `encryption:` | Enable, disable, key management |
| Logging | `log:` | Log level management |
| Status | `status` | Installation status as JSON |

### Essential Built-in Commands

| Command | Description |
|---------|-------------|
| `maintenance:mode --on` | Enable maintenance mode |
| `maintenance:mode --off` | Disable maintenance mode |
| `maintenance:repair` | Run repair steps |
| `upgrade` | Run database upgrade after Nextcloud update |
| `user:add --display-name="Name" --group="group" userid` | Create user |
| `user:delete userid` | Delete user |
| `user:list` | List all users |
| `user:enable userid` | Enable user |
| `user:disable userid` | Disable user |
| `app:enable appid` | Enable an app |
| `app:disable appid` | Disable an app |
| `app:list` | List installed apps and status |
| `app:update --all` | Update all apps |
| `config:system:set key --value=val` | Set system config |
| `config:system:set key --value=val --type=boolean` | Set typed system config |
| `config:system:get key` | Get system config value |
| `config:app:set appid key --value=val` | Set app config |
| `config:app:get appid key` | Get app config value |
| `config:list` | Export all config as JSON |
| `files:scan --all` | Scan all user files |
| `files:scan --path="/user/files/folder"` | Scan specific path |
| `files:cleanup` | Clean up orphaned file cache entries |
| `files:transfer-ownership source dest` | Transfer file ownership |
| `background:cron` | Set background jobs to cron mode |
| `background:ajax` | Set background jobs to AJAX mode |
| `background:webcron` | Set background jobs to webcron mode |
| `status --output=json` | Show installation status as JSON |

### Common Config Commands

```bash
# Set trusted domain
sudo -u www-data php occ config:system:set trusted_domains 1 --value=cloud.example.com

# Enable debug mode
sudo -u www-data php occ config:system:set debug --value=true --type=boolean

# Set Redis memcache
sudo -u www-data php occ config:system:set memcache.distributed --value='\OC\Memcache\Redis'

# Set overwrite CLI URL (required for cron)
sudo -u www-data php occ config:system:set overwrite.cli.url --value='https://cloud.example.com'

# Set default phone region (NC 28+)
sudo -u www-data php occ config:system:set default_phone_region --value='NL'
```

### Critical Warnings

**NEVER** run occ as root -- this changes file ownership and breaks Nextcloud. ALWAYS use `sudo -u www-data php occ`.

**NEVER** use `files:scan --all` on large installations without scheduling during off-peak hours -- it locks the file cache and degrades performance. ALWAYS target specific paths with `--path` when possible.

**NEVER** forget to run `maintenance:mode --on` before major operations (upgrades, migrations) -- users may corrupt data during the operation.

**NEVER** run `upgrade` without a database backup -- failed upgrades can leave the database in an inconsistent state.

**ALWAYS** use `--type=boolean` when setting boolean config values -- without it, `true` is stored as a string, not a boolean.

**ALWAYS** use `--type=integer` when setting numeric config values -- without it, numbers are stored as strings.

**ALWAYS** run `maintenance:repair` after manual file system changes -- the file cache must be synchronized.

---

## Decision Tree: Which Command to Use

```
Need to administer Nextcloud from CLI?
├── Managing users? → user:add / user:delete / user:list / user:enable / user:disable
├── Managing apps? → app:enable / app:disable / app:list / app:update
├── Changing config? → config:system:set / config:app:set
├── File operations? → files:scan / files:cleanup / files:transfer-ownership
├── Upgrading? → maintenance:mode --on → upgrade → maintenance:mode --off
├── Background jobs? → background:cron (recommended for production)
└── Creating custom command? → Extend Symfony Command (see Pattern 1 below)
```

---

## Essential Patterns

### Pattern 1: Custom Command with Arguments and Options

```php
<?php
namespace OCA\MyApp\Command;

use OCA\MyApp\Service\ItemService;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

class ProcessItems extends Command {
    public function __construct(
        private ItemService $service,
    ) {
        parent::__construct();
    }

    protected function configure(): void {
        $this->setName('myapp:process-items')
            ->setDescription('Process pending items for a user')
            ->addArgument(
                'user',
                InputArgument::REQUIRED,
                'The user ID to process items for'
            )
            ->addOption(
                'force',
                'f',
                InputOption::VALUE_NONE,
                'Force reprocessing of already processed items'
            )
            ->addOption(
                'limit',
                'l',
                InputOption::VALUE_REQUIRED,
                'Maximum number of items to process',
                100 // default value
            );
    }

    protected function execute(InputInterface $input, OutputInterface $output): int {
        $userId = $input->getArgument('user');
        $force = $input->getOption('force');
        $limit = (int) $input->getOption('limit');

        $output->writeln("Processing items for user: <info>{$userId}</info>");

        $count = $this->service->processItems($userId, $force, $limit);

        $output->writeln("<info>Processed {$count} items successfully.</info>");
        return Command::SUCCESS;
    }
}
```

### Pattern 2: Register Command in info.xml

```xml
<?xml version="1.0"?>
<info xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:noNamespaceSchemaLocation="https://apps.nextcloud.com/schema/apps/info.xsd">
    <id>myapp</id>
    <name>My App</name>
    <!-- ... other entries ... -->
    <commands>
        <command>OCA\MyApp\Command\ProcessItems</command>
        <command>OCA\MyApp\Command\CleanupData</command>
    </commands>
</info>
```

**ALWAYS** register commands in `appinfo/info.xml` -- unregistered commands are invisible to occ.

**ALWAYS** use the fully qualified class name (FQCN) including the `OCA\` namespace.

### Pattern 3: Output Formatting with Tables and Progress Bars

```php
use Symfony\Component\Console\Helper\Table;
use Symfony\Component\Console\Helper\ProgressBar;

protected function execute(InputInterface $input, OutputInterface $output): int {
    // Table output
    $table = new Table($output);
    $table->setHeaders(['User', 'Files', 'Quota Used']);
    $table->addRow(['alice', '1,234', '4.2 GB']);
    $table->addRow(['bob', '567', '1.8 GB']);
    $table->render();

    // Progress bar
    $items = $this->service->getPendingItems();
    $progressBar = new ProgressBar($output, count($items));
    $progressBar->start();

    foreach ($items as $item) {
        $this->service->process($item);
        $progressBar->advance();
    }

    $progressBar->finish();
    $output->writeln(''); // newline after progress bar
    return Command::SUCCESS;
}
```

### Pattern 4: Command with Confirmation and Error Handling

```php
use Symfony\Component\Console\Question\ConfirmationQuestion;

protected function execute(InputInterface $input, OutputInterface $output): int {
    $userId = $input->getArgument('user');

    if (!$input->getOption('force')) {
        $helper = $this->getHelper('question');
        $question = new ConfirmationQuestion(
            "Delete all data for user {$userId}? (y/N) ",
            false
        );
        if (!$helper->ask($input, $output, $question)) {
            $output->writeln('Aborted.');
            return Command::SUCCESS;
        }
    }

    try {
        $this->service->deleteUserData($userId);
        $output->writeln("<info>Data deleted for {$userId}.</info>");
        return Command::SUCCESS;
    } catch (\Exception $e) {
        $output->writeln("<error>Failed: {$e->getMessage()}</error>");
        return Command::FAILURE;
    }
}
```

### Pattern 5: Upgrade Workflow

```bash
# 1. Enable maintenance mode
sudo -u www-data php occ maintenance:mode --on

# 2. Create database backup
mysqldump --single-transaction -u nextcloud -p nextcloud_db > backup.sql

# 3. Update Nextcloud files (download or package manager)

# 4. Run database upgrade
sudo -u www-data php occ upgrade

# 5. Run repair steps
sudo -u www-data php occ maintenance:repair

# 6. Disable maintenance mode
sudo -u www-data php occ maintenance:mode --off

# 7. Verify status
sudo -u www-data php occ status --output=json
```

**ALWAYS** follow this exact sequence for upgrades -- skipping steps leads to broken installations.

---

## Symfony Console Argument and Option Types

### InputArgument Modes

| Mode | Behavior |
|------|----------|
| `InputArgument::REQUIRED` | Must be provided |
| `InputArgument::OPTIONAL` | May be omitted (provide default) |
| `InputArgument::IS_ARRAY` | Accepts multiple values |

### InputOption Modes

| Mode | Behavior |
|------|----------|
| `InputOption::VALUE_NONE` | Boolean flag (`--force`) |
| `InputOption::VALUE_REQUIRED` | Must have value (`--limit=10`) |
| `InputOption::VALUE_OPTIONAL` | Value optional (`--format` or `--format=json`) |
| `InputOption::VALUE_IS_ARRAY` | Multiple values (`--exclude=a --exclude=b`) |

### Output Formatting Tags

| Tag | Appearance |
|-----|------------|
| `<info>text</info>` | Green text |
| `<comment>text</comment>` | Yellow text |
| `<question>text</question>` | Black text on cyan background |
| `<error>text</error>` | White text on red background |

---

## Reference Links

- [references/methods.md](references/methods.md) -- Command class, built-in commands reference
- [references/examples.md](references/examples.md) -- Custom command and built-in command usage examples
- [references/anti-patterns.md](references/anti-patterns.md) -- Common occ mistakes and corrections

### Official Sources

- https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/occ_command.html
- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/commands.html
- https://symfony.com/doc/current/console.html
