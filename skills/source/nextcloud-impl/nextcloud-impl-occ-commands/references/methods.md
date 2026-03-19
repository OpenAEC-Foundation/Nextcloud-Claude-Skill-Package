# OCC Commands Methods Reference

## Symfony Console Command Class

### Base Class

All custom Nextcloud CLI commands extend `Symfony\Component\Console\Command\Command`.

**Required methods:**

| Method | Return | Description |
|--------|--------|-------------|
| `configure()` | `void` | Set command name, description, arguments, options |
| `execute(InputInterface $input, OutputInterface $output)` | `int` | Run command logic, return exit code |

**Optional methods:**

| Method | Return | Description |
|--------|--------|-------------|
| `initialize(InputInterface $input, OutputInterface $output)` | `void` | Run before execute, after input validation |
| `interact(InputInterface $input, OutputInterface $output)` | `void` | Ask user for missing arguments interactively |

### Configuration Methods (called in `configure()`)

| Method | Parameters | Description |
|--------|-----------|-------------|
| `setName(string $name)` | Command name (e.g., `myapp:process`) | Set the command name used on CLI |
| `setDescription(string $description)` | Short description | Shown in `occ list` output |
| `setHelp(string $help)` | Long help text | Shown with `occ help myapp:process` |
| `addArgument(string $name, int $mode, string $desc, $default)` | See InputArgument modes | Add positional argument |
| `addOption(string $name, string $shortcut, int $mode, string $desc, $default)` | See InputOption modes | Add named option |
| `setHidden(bool $hidden)` | `true` to hide | Hide from `occ list` |

### InputInterface Methods (used in `execute()`)

| Method | Return | Description |
|--------|--------|-------------|
| `getArgument(string $name)` | `mixed` | Get argument value |
| `getOption(string $name)` | `mixed` | Get option value |
| `hasArgument(string $name)` | `bool` | Check if argument is defined |
| `hasOption(string $name)` | `bool` | Check if option is defined |
| `isInteractive()` | `bool` | Whether input is interactive |

### OutputInterface Methods (used in `execute()`)

| Method | Parameters | Description |
|--------|-----------|-------------|
| `writeln(string $message)` | Message with optional formatting tags | Write line to stdout |
| `write(string $message)` | Message without trailing newline | Write without newline |
| `setVerbosity(int $level)` | `OutputInterface::VERBOSITY_*` | Set output verbosity |
| `isVerbose()` | -- | Check if `-v` flag is set |
| `isVeryVerbose()` | -- | Check if `-vv` flag is set |
| `isDebug()` | -- | Check if `-vvv` flag is set |

### Exit Codes

| Constant | Value | Meaning |
|----------|-------|---------|
| `Command::SUCCESS` | `0` | Command completed successfully |
| `Command::FAILURE` | `1` | Command failed |
| `Command::INVALID` | `2` | Invalid input (wrong arguments/options) |

**ALWAYS** return `Command::SUCCESS`, `Command::FAILURE`, or `Command::INVALID` from `execute()` -- never return arbitrary integers or forget the return statement.

---

## Built-in Commands Reference

### maintenance: Commands

| Command | Options | Description |
|---------|---------|-------------|
| `maintenance:mode` | `--on`, `--off` | Toggle maintenance mode |
| `maintenance:repair` | `--include-expensive` | Run repair steps |
| `maintenance:update:htaccess` | -- | Update .htaccess file |
| `maintenance:mimetype:update-db` | `--repair-filecache` | Update mimetype list |
| `maintenance:mimetype:update-js` | -- | Update mimetype JS file |

### user: Commands

| Command | Options | Description |
|---------|---------|-------------|
| `user:add` | `--display-name`, `--group`, `--password-from-env` | Create user |
| `user:delete` | -- | Delete user |
| `user:disable` | -- | Disable user |
| `user:enable` | -- | Enable user |
| `user:info` | `--output=json` | Show user info |
| `user:list` | `--limit`, `--offset`, `--output=json` | List users |
| `user:report` | -- | Show user count summary |
| `user:resetpassword` | `--password-from-env` | Reset user password |
| `user:setting` | `--value`, `--delete` | Get/set user settings |

### app: Commands

| Command | Options | Description |
|---------|---------|-------------|
| `app:enable` | `--force`, `--groups` | Enable app |
| `app:disable` | -- | Disable app |
| `app:list` | `--output=json` | List installed apps |
| `app:update` | `--all` | Update app(s) |
| `app:install` | -- | Install app from app store |
| `app:remove` | -- | Remove app |
| `app:getpath` | -- | Show app install path |
| `app:check-code` | -- | Check app code compliance |

### config: Commands

| Command | Options | Description |
|---------|---------|-------------|
| `config:system:set` | `--value`, `--type`, `--update-only` | Set system config |
| `config:system:get` | `--default-value` | Get system config |
| `config:system:delete` | -- | Delete system config key |
| `config:app:set` | `--value`, `--type`, `--update-only` | Set app config |
| `config:app:get` | `--default-value` | Get app config |
| `config:app:delete` | -- | Delete app config key |
| `config:list` | `--private` | Export config as JSON |
| `config:import` | -- | Import config from JSON |

**Type values for `--type`:** `string` (default), `boolean`, `integer`, `float`.

### files: Commands

| Command | Options | Description |
|---------|---------|-------------|
| `files:scan` | `--all`, `--path`, `--unscanned` | Scan filesystem |
| `files:scan-app-data` | -- | Scan app data folder |
| `files:cleanup` | -- | Clean up orphaned entries |
| `files:transfer-ownership` | `--path`, `--move` | Transfer file ownership |
| `files:reminders:list` | `--user`, `--output=json` | List file reminders |

### background: Commands

| Command | Description |
|---------|-------------|
| `background:cron` | Use system cron (recommended) |
| `background:ajax` | Use AJAX (development only) |
| `background:webcron` | Use webcron service |

### db: Commands

| Command | Options | Description |
|---------|---------|-------------|
| `db:add-missing-indices` | -- | Add missing database indices |
| `db:add-missing-columns` | -- | Add missing database columns |
| `db:add-missing-primary-keys` | -- | Add missing primary keys |
| `db:convert-filecache-bigint` | -- | Convert filecache IDs to bigint |

### Other Useful Commands

| Command | Description |
|---------|-------------|
| `status` | Show installation status |
| `check` | Check system dependencies |
| `log:manage` | Set log level and backend |
| `encryption:enable` | Enable server-side encryption |
| `encryption:disable` | Disable server-side encryption |
| `security:certificates` | List trusted certificates |
| `security:certificates:import` | Import trusted certificate |
| `trashbin:cleanup` | Empty trash for user(s) |
| `versions:cleanup` | Remove old file versions |
