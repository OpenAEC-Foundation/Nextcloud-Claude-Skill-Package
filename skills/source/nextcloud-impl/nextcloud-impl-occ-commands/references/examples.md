# OCC Commands Examples Reference

## Custom Command Examples

### Complete Custom Command with Service Injection

```php
<?php
namespace OCA\MyApp\Command;

use OCA\MyApp\Service\ReportService;
use OCP\IUserManager;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Helper\ProgressBar;
use Symfony\Component\Console\Helper\Table;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

class GenerateReport extends Command {
    public function __construct(
        private ReportService $reportService,
        private IUserManager $userManager,
    ) {
        parent::__construct();
    }

    protected function configure(): void {
        $this->setName('myapp:generate-report')
            ->setDescription('Generate usage report for users')
            ->setHelp('Generates a detailed usage report. Use --format=csv to export.')
            ->addArgument(
                'user',
                InputArgument::OPTIONAL,
                'Generate report for specific user only'
            )
            ->addOption(
                'format',
                null,
                InputOption::VALUE_REQUIRED,
                'Output format: table or csv',
                'table'
            )
            ->addOption(
                'since',
                's',
                InputOption::VALUE_REQUIRED,
                'Report start date (Y-m-d)',
                date('Y-m-d', strtotime('-30 days'))
            )
            ->addOption(
                'quiet-progress',
                null,
                InputOption::VALUE_NONE,
                'Suppress progress bar output'
            );
    }

    protected function execute(InputInterface $input, OutputInterface $output): int {
        $userId = $input->getArgument('user');
        $format = $input->getOption('format');
        $since = $input->getOption('since');

        // Validate date format
        $date = \DateTime::createFromFormat('Y-m-d', $since);
        if (!$date) {
            $output->writeln('<error>Invalid date format. Use Y-m-d.</error>');
            return Command::INVALID;
        }

        // Collect users
        if ($userId !== null) {
            if (!$this->userManager->userExists($userId)) {
                $output->writeln("<error>User '{$userId}' does not exist.</error>");
                return Command::FAILURE;
            }
            $userIds = [$userId];
        } else {
            $userIds = [];
            $this->userManager->callForAllUsers(function ($user) use (&$userIds) {
                $userIds[] = $user->getUID();
            });
        }

        $output->writeln("<info>Generating report for " . count($userIds) . " user(s) since {$since}</info>");

        // Process with progress bar
        $results = [];
        if (!$input->getOption('quiet-progress')) {
            $progressBar = new ProgressBar($output, count($userIds));
            $progressBar->start();
        }

        foreach ($userIds as $uid) {
            try {
                $results[] = $this->reportService->generateForUser($uid, $date);
            } catch (\Exception $e) {
                $output->writeln("\n<error>Failed for {$uid}: {$e->getMessage()}</error>");
            }
            if (isset($progressBar)) {
                $progressBar->advance();
            }
        }

        if (isset($progressBar)) {
            $progressBar->finish();
            $output->writeln('');
        }

        // Output results
        if ($format === 'csv') {
            $output->writeln('user,files,storage_used,last_login');
            foreach ($results as $row) {
                $output->writeln(implode(',', [
                    $row['user'],
                    $row['files'],
                    $row['storage'],
                    $row['lastLogin'],
                ]));
            }
        } else {
            $table = new Table($output);
            $table->setHeaders(['User', 'Files', 'Storage Used', 'Last Login']);
            foreach ($results as $row) {
                $table->addRow([
                    $row['user'],
                    $row['files'],
                    $row['storage'],
                    $row['lastLogin'],
                ]);
            }
            $table->render();
        }

        $output->writeln("<info>Report complete.</info>");
        return Command::SUCCESS;
    }
}
```

### Registration in info.xml

```xml
<commands>
    <command>OCA\MyApp\Command\GenerateReport</command>
</commands>
```

### Command with Array Arguments

```php
<?php
namespace OCA\MyApp\Command;

use OCA\MyApp\Service\TagService;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

class TagFiles extends Command {
    public function __construct(
        private TagService $tagService,
    ) {
        parent::__construct();
    }

    protected function configure(): void {
        $this->setName('myapp:tag-files')
            ->setDescription('Apply tags to files')
            ->addArgument('tag', InputArgument::REQUIRED, 'Tag name to apply')
            ->addArgument(
                'files',
                InputArgument::IS_ARRAY | InputArgument::REQUIRED,
                'File paths to tag (space-separated)'
            );
    }

    protected function execute(InputInterface $input, OutputInterface $output): int {
        $tag = $input->getArgument('tag');
        $files = $input->getArgument('files');

        foreach ($files as $file) {
            $this->tagService->applyTag($file, $tag);
            $output->writeln("Tagged: <info>{$file}</info>");
        }

        return Command::SUCCESS;
    }
}
```

Usage: `sudo -u www-data php occ myapp:tag-files important /alice/files/doc1.pdf /alice/files/doc2.pdf`

### Command with Verbose Output

```php
protected function execute(InputInterface $input, OutputInterface $output): int {
    $output->writeln('Starting cleanup...');

    $items = $this->service->getExpiredItems();

    if ($output->isVerbose()) {
        $output->writeln("Found " . count($items) . " expired items");
    }

    foreach ($items as $item) {
        if ($output->isVeryVerbose()) {
            $output->writeln("  Removing item #{$item->getId()}: {$item->getName()}");
        }
        $this->service->remove($item);
    }

    $output->writeln('<info>Cleanup complete.</info>');
    return Command::SUCCESS;
}
```

Usage with verbosity flags:
- `sudo -u www-data php occ myapp:cleanup` -- normal output
- `sudo -u www-data php occ myapp:cleanup -v` -- verbose
- `sudo -u www-data php occ myapp:cleanup -vv` -- very verbose
- `sudo -u www-data php occ myapp:cleanup -vvv` -- debug

---

## Built-in Command Usage Examples

### User Management

```bash
# Create user with display name and group
sudo -u www-data php occ user:add --display-name="Alice Smith" --group="engineering" alice

# Create user with password from environment (for scripts)
export OC_PASS=secretpassword
sudo -u www-data php occ user:add --password-from-env --display-name="Bob" bob

# List all users as JSON
sudo -u www-data php occ user:list --output=json

# Get user info
sudo -u www-data php occ user:info alice --output=json

# Disable and re-enable user
sudo -u www-data php occ user:disable alice
sudo -u www-data php occ user:enable alice

# Reset password from environment
export OC_PASS=newpassword
sudo -u www-data php occ user:resetpassword --password-from-env alice
```

### App Management

```bash
# List all apps with status
sudo -u www-data php occ app:list

# Enable app for specific groups only
sudo -u www-data php occ app:enable calendar --groups="engineering" --groups="management"

# Disable app
sudo -u www-data php occ app:disable weather

# Update all apps
sudo -u www-data php occ app:update --all

# Check app code compliance
sudo -u www-data php occ app:check-code myapp
```

### Configuration

```bash
# Set trusted domain
sudo -u www-data php occ config:system:set trusted_domains 1 --value=cloud.example.com

# Set boolean config
sudo -u www-data php occ config:system:set debug --value=true --type=boolean

# Set integer config
sudo -u www-data php occ config:system:set loglevel --value=2 --type=integer

# Set nested array value (Redis config)
sudo -u www-data php occ config:system:set redis host --value=localhost
sudo -u www-data php occ config:system:set redis port --value=6379 --type=integer

# Export full config (redacted)
sudo -u www-data php occ config:list

# Export full config (including secrets)
sudo -u www-data php occ config:list --private
```

### File Operations

```bash
# Scan all files (use sparingly on large instances)
sudo -u www-data php occ files:scan --all

# Scan specific user
sudo -u www-data php occ files:scan alice

# Scan specific path
sudo -u www-data php occ files:scan --path="/alice/files/Documents"

# Clean up orphaned file cache entries
sudo -u www-data php occ files:cleanup

# Transfer ownership (all files)
sudo -u www-data php occ files:transfer-ownership alice bob

# Transfer specific folder
sudo -u www-data php occ files:transfer-ownership --path="Projects" alice bob
```

### Database Maintenance

```bash
# Add missing indices (run after upgrade warnings)
sudo -u www-data php occ db:add-missing-indices

# Add missing columns
sudo -u www-data php occ db:add-missing-columns

# Add missing primary keys
sudo -u www-data php occ db:add-missing-primary-keys

# Convert filecache to bigint (run in maintenance mode)
sudo -u www-data php occ maintenance:mode --on
sudo -u www-data php occ db:convert-filecache-bigint
sudo -u www-data php occ maintenance:mode --off
```

### Cleanup Operations

```bash
# Empty trash for specific user
sudo -u www-data php occ trashbin:cleanup alice

# Empty trash for all users
sudo -u www-data php occ trashbin:cleanup --all-users

# Remove old file versions for specific user
sudo -u www-data php occ versions:cleanup alice

# Remove old file versions for all users
sudo -u www-data php occ versions:cleanup --all-users
```
