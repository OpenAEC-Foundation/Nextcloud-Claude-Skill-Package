# Config Methods Reference

## config.php Key Reference

### Core Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `instanceid` | `string` | auto-generated | Unique instance identifier -- NEVER change after install |
| `passwordsalt` | `string` | auto-generated | Salt for password hashing -- NEVER change |
| `secret` | `string` | auto-generated | Server secret for security tokens -- NEVER change |
| `trusted_domains` | `array` | `['localhost']` | Hostnames allowed for login |
| `datadirectory` | `string` | `$INSTALL/data` | Absolute path to user file storage |
| `version` | `string` | auto-set | Internal Nextcloud version string -- NEVER manually edit |
| `installed` | `bool` | `false` | Whether installation is complete -- NEVER manually edit |

### Database Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `dbtype` | `string` | `sqlite3` | Database type: `mysql`, `pgsql`, `sqlite3` |
| `dbhost` | `string` | `localhost` | Database host. Unix socket: `localhost:/path/to/socket` |
| `dbport` | `string` | `''` | Database port (empty = default) |
| `dbname` | `string` | `nextcloud` | Database name |
| `dbuser` | `string` | `''` | Database username |
| `dbpassword` | `string` | `''` | Database password |
| `dbtableprefix` | `string` | `oc_` | Table name prefix |

### URL and Proxy Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `overwrite.cli.url` | `string` | `''` | Base URL for CLI link generation |
| `overwriteprotocol` | `string` | `''` | Force protocol: `http` or `https` |
| `overwritehost` | `string` | `''` | Force hostname |
| `overwritewebroot` | `string` | `''` | Force web root path |
| `overwritecondaddr` | `string` | `''` | Regex: only apply overwrites when proxy matches |
| `trusted_proxies` | `array` | `[]` | Trusted reverse proxy IPs/CIDRs |
| `forwarded_for_headers` | `array` | `['HTTP_X_FORWARDED_FOR']` | Headers to read client IP from |

### Caching Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `memcache.local` | `string` | `none` | Local cache class: `\OC\Memcache\APCu` |
| `memcache.distributed` | `string` | `none` | Distributed cache: `\OC\Memcache\Redis` |
| `memcache.locking` | `string` | `none` | File locking cache: `\OC\Memcache\Redis` |
| `redis` | `array` | `[]` | Redis connection config |
| `redis.cluster` | `array` | `[]` | Redis Cluster connection config |

#### Redis Connection Options

| Key | Type | Description |
|-----|------|-------------|
| `host` | `string` | Hostname, IP, or Unix socket path |
| `port` | `int` | TCP port (0 for Unix socket) |
| `password` | `string` | Redis AUTH password |
| `dbindex` | `int` | Redis database index (0-15) |
| `timeout` | `float` | Connection timeout in seconds |
| `read_timeout` | `float` | Read timeout in seconds |

### Logging Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `log_type` | `string` | `file` | Log backend: `file`, `syslog`, `errorlog`, `systemd` |
| `logfile` | `string` | `$datadirectory/nextcloud.log` | Log file path |
| `loglevel` | `int` | `2` | 0=Debug, 1=Info, 2=Warn, 3=Error, 4=Fatal |
| `logdateformat` | `string` | ISO 8601 | PHP date format for log timestamps |
| `logtimezone` | `string` | `UTC` | Timezone for log timestamps |
| `log_type_audit` | `string` | `''` | Audit log backend |
| `logfile_audit` | `string` | `''` | Audit log file path |
| `log_rotate_size` | `int` | `104857600` | Max log file size in bytes (default 100MB, 0=disable) |

### Mail Settings

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `mail_smtpmode` | `string` | `smtp` | Mail mode: `smtp`, `sendmail`, `qmail` |
| `mail_smtpsecure` | `string` | `''` | Encryption: `tls` (STARTTLS) or `ssl` |
| `mail_smtphost` | `string` | `127.0.0.1` | SMTP server hostname |
| `mail_smtpport` | `int` | `25` | SMTP port (587 for TLS, 465 for SSL) |
| `mail_smtpauth` | `bool` | `false` | Enable SMTP authentication |
| `mail_smtpname` | `string` | `''` | SMTP username |
| `mail_smtppassword` | `string` | `''` | SMTP password |
| `mail_from_address` | `string` | `no-reply` | Sender address (without domain) |
| `mail_domain` | `string` | `''` | Sender domain |

### Maintenance and Performance

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `maintenance` | `bool` | `false` | Enable maintenance mode |
| `maintenance_window_start` | `int` | not set | Hour (UTC) for heavy background jobs (NC 28+) |
| `default_phone_region` | `string` | `''` | ISO 3166-1 country code |
| `debug` | `bool` | `false` | Enable debug mode |
| `updater.release.channel` | `string` | `stable` | Update channel: `stable`, `beta`, `daily` |
| `tempdirectory` | `string` | system default | Temporary files directory |
| `check_for_working_wellknown_setup` | `bool` | `true` | Check .well-known redirects |
| `check_data_directory_permissions` | `bool` | `true` | Verify data dir permissions |
| `filelocking.enabled` | `bool` | `true` | Enable transactional file locking |
| `filesystem_check_changes` | `int` | `0` | Check for external storage changes (0=never, 1=on access) |

### App Store and Updates

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `appstoreenabled` | `bool` | `true` | Enable the Nextcloud App Store |
| `apps_paths` | `array` | auto-set | Directories to search for apps |
| `appcodechecker` | `bool` | `true` | Validate app code signatures |
| `updatechecker` | `bool` | `true` | Check for Nextcloud updates |

---

## IConfig Interface Methods

**Namespace:** `OCP\IConfig`

### System Config (config.php)

| Method | Signature | Description |
|--------|-----------|-------------|
| `getSystemValue` | `getSystemValue(string $key, mixed $default = '')` | Read a config.php value |
| `getSystemValueBool` | `getSystemValueBool(string $key, bool $default = false)` | Read boolean config.php value |
| `getSystemValueInt` | `getSystemValueInt(string $key, int $default = 0)` | Read integer config.php value |
| `getSystemValueString` | `getSystemValueString(string $key, string $default = '')` | Read string config.php value |
| `setSystemValue` | `setSystemValue(string $key, mixed $value): void` | Write a config.php value |
| `deleteSystemValue` | `deleteSystemValue(string $key): void` | Remove a config.php value |
| `getSystemValues` | `getSystemValues(): array` | Get all config.php values as array |

### App Config (Database-Stored)

| Method | Signature | Description |
|--------|-----------|-------------|
| `getAppValue` | `getAppValue(string $app, string $key, string $default = '')` | Read app config |
| `setAppValue` | `setAppValue(string $app, string $key, string $value): void` | Write app config |
| `deleteAppValue` | `deleteAppValue(string $app, string $key): void` | Delete app config key |
| `deleteAppValues` | `deleteAppValues(string $app): void` | Delete all config for an app |
| `getAppKeys` | `getAppKeys(string $app): array` | List all config keys for an app |

### User Config (Per-User Preferences)

| Method | Signature | Description |
|--------|-----------|-------------|
| `getUserValue` | `getUserValue(string $userId, string $app, string $key, string $default = '')` | Read user preference |
| `setUserValue` | `setUserValue(string $userId, string $app, string $key, string $value): void` | Write user preference |
| `deleteUserValue` | `deleteUserValue(string $userId, string $app, string $key): void` | Delete user preference |
| `deleteAllUserValues` | `deleteAllUserValues(string $userId): void` | Delete all prefs for a user |
| `getUserValueForUsers` | `getUserValueForUsers(string $app, string $key, array $userIds): array` | Batch read prefs for multiple users |
| `getUsersForUserValue` | `getUsersForUserValue(string $app, string $key, string $value): array` | Find users by preference value |

---

## IAppConfig Interface Methods (NC 28+)

**Namespace:** `OCP\IAppConfig`

### Typed Getters

| Method | Signature | Description |
|--------|-----------|-------------|
| `getValueString` | `getValueString(string $app, string $key, string $default = '', bool $lazy = false, ?bool $sensitive = null)` | Read string value |
| `getValueInt` | `getValueInt(string $app, string $key, int $default = 0, bool $lazy = false, ?bool $sensitive = null)` | Read integer value |
| `getValueFloat` | `getValueFloat(string $app, string $key, float $default = 0.0, bool $lazy = false, ?bool $sensitive = null)` | Read float value |
| `getValueBool` | `getValueBool(string $app, string $key, bool $default = false, bool $lazy = false, ?bool $sensitive = null)` | Read boolean value |
| `getValueArray` | `getValueArray(string $app, string $key, array $default = [], bool $lazy = false, ?bool $sensitive = null)` | Read array value (JSON-decoded) |

### Typed Setters

| Method | Signature | Description |
|--------|-----------|-------------|
| `setValueString` | `setValueString(string $app, string $key, string $value, bool $lazy = false, bool $sensitive = false): bool` | Write string |
| `setValueInt` | `setValueInt(string $app, string $key, int $value, bool $lazy = false, bool $sensitive = false): bool` | Write integer |
| `setValueFloat` | `setValueFloat(string $app, string $key, float $value, bool $lazy = false, bool $sensitive = false): bool` | Write float |
| `setValueBool` | `setValueBool(string $app, string $key, bool $value, bool $lazy = false): bool` | Write boolean |
| `setValueArray` | `setValueArray(string $app, string $key, array $value, bool $lazy = false, bool $sensitive = false): bool` | Write array (JSON-encoded) |

### Management Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `hasKey` | `hasKey(string $app, string $key, ?bool $lazy = null): bool` | Check if key exists |
| `getKeys` | `getKeys(string $app): array` | List all keys for an app |
| `deleteKey` | `deleteKey(string $app, string $key): void` | Delete a key |
| `deleteApp` | `deleteApp(string $app): void` | Delete all config for an app |
| `isSensitive` | `isSensitive(string $app, string $key, ?bool $lazy = null): bool` | Check if value is sensitive |
| `isLazy` | `isLazy(string $app, string $key): bool` | Check if value is lazy-loaded |
| `updateSensitive` | `updateSensitive(string $app, string $key, bool $sensitive): bool` | Change sensitive flag |
| `updateLazy` | `updateLazy(string $app, string $key, bool $lazy): bool` | Change lazy flag |

### IAppConfig Parameter Notes

- **`lazy`**: When `true`, the value is NOT loaded on every page request. Use for values accessed only during background jobs or specific actions. ALWAYS set `lazy: true` for config values not needed on every request.
- **`sensitive`**: When `true`, the value is stored encrypted in the database. ALWAYS use for API keys, tokens, passwords, and secrets.
- Setters return `true` if the value actually changed, `false` if the new value equals the existing value.
