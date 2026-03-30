---
name: nextcloud-core-config
description: >
  Use when configuring Nextcloud server, reading/writing app configuration, or troubleshooting config issues.
  Prevents direct config.php editing when IAppConfig should be used, and misconfigured caching or proxy settings.
  Covers config.php parameters, IConfig/IAppConfig interfaces, occ config commands, caching setup, proxy configuration, mail settings, and logging configuration.
  Keywords: config.php, IConfig, IAppConfig, occ config, APCu, Redis, memcache, trusted_proxies, settings, config.php, change setting, configure cache, proxy setup, mail settings..
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-core-config

## Quick Reference

### Configuration File Location

The main server configuration file lives at `config/config.php` in the Nextcloud installation root. Nextcloud auto-generates this file during installation. Additional config files can be placed in `config/` with the naming pattern `*.config.php` -- they are merged alphabetically.

### Critical config.php Keys

| Key | Type | Description |
|-----|------|-------------|
| `trusted_domains` | `array` | Allowed hostnames for login -- MUST be set |
| `datadirectory` | `string` | Absolute path to user data storage |
| `dbtype` | `string` | Database backend: `mysql`, `pgsql`, `sqlite3` |
| `dbhost` | `string` | Database host (use `localhost:/path/to/socket` for Unix sockets) |
| `dbname` | `string` | Database name |
| `dbuser` / `dbpassword` | `string` | Database credentials |
| `overwrite.cli.url` | `string` | Base URL for CLI-generated links (e.g., `https://cloud.example.com`) |
| `overwriteprotocol` | `string` | Force protocol behind reverse proxy: `https` |
| `overwritehost` | `string` | Force hostname behind reverse proxy |
| `overwritecondaddr` | `string` | Regex for proxy IP to conditionally apply overwrites |
| `trusted_proxies` | `array` | IP addresses of trusted reverse proxies |
| `default_phone_region` | `string` | ISO 3166-1 country code (e.g., `NL`, `DE`, `US`) |
| `maintenance` | `bool` | Enable/disable maintenance mode |
| `maintenance_window_start` | `int` | Hour (UTC, 0-23) when heavy background jobs may run (NC 28+) |

### Critical Warnings

**NEVER** store `config.php` in version control -- it contains database passwords, instance secrets, and the `passwordsalt`.

**NEVER** forget to set `trusted_domains` after installation -- this is the most common post-install issue. Users will see "Access through untrusted domain" errors.

**NEVER** set `loglevel` to `0` (debug) in production -- it generates massive log output and degrades performance.

**NEVER** edit `config.php` while Nextcloud is under heavy load without enabling maintenance mode first for critical changes.

**ALWAYS** set `overwrite.cli.url` when running behind a reverse proxy -- without it, CLI-generated URLs (cron, occ commands, email links) will be incorrect.

**ALWAYS** set `default_phone_region` -- Nextcloud shows a persistent admin warning until this is configured.

**ALWAYS** run occ commands as the web server user: `sudo -u www-data php occ ...`

---

## Caching Configuration

Nextcloud supports multiple caching backends. ALWAYS configure caching for production deployments.

### APCu (Local Cache)

```php
'memcache.local' => '\OC\Memcache\APCu',
```

APCu provides per-server in-memory caching. ALWAYS use for `memcache.local` on single-server setups.

### Redis (Distributed Cache + Locking)

```php
'memcache.distributed' => '\OC\Memcache\Redis',
'memcache.locking' => '\OC\Memcache\Redis',
'redis' => [
    'host' => '/var/run/redis/redis-server.sock',
    'port' => 0,
    'dbindex' => 0,
    'timeout' => 1.5,
],
```

For TCP connections, use `'host' => '127.0.0.1'` and `'port' => 6379`.

### Caching Rules

- **ALWAYS** set `memcache.local` for production -- APCu is the standard choice
- **ALWAYS** set `memcache.locking` to Redis when using Redis -- prevents file locking race conditions
- **ALWAYS** use Unix sockets for Redis when on the same server -- lower latency than TCP
- **NEVER** use APCu for `memcache.distributed` on multi-server setups -- APCu is process-local only
- **NEVER** omit `memcache.locking` when using Redis -- transactional file locking requires it

---

## Proxy Configuration

When running Nextcloud behind a reverse proxy (nginx, Apache, Traefik, Caddy):

```php
'trusted_proxies' => ['10.0.0.1', '172.16.0.0/12'],
'overwriteprotocol' => 'https',
'overwrite.cli.url' => 'https://cloud.example.com',
'overwritehost' => 'cloud.example.com',
```

- **ALWAYS** set `trusted_proxies` -- without it, Nextcloud ignores `X-Forwarded-For` headers and all requests appear to come from the proxy IP
- **ALWAYS** set `overwriteprotocol` to `https` when TLS terminates at the proxy
- **NEVER** add `0.0.0.0/0` to `trusted_proxies` -- this trusts ALL IPs and allows header spoofing

---

## Mail Configuration

```php
'mail_smtpmode' => 'smtp',
'mail_smtpsecure' => 'tls',
'mail_sendmailmode' => 'smtp',
'mail_from_address' => 'nextcloud',
'mail_domain' => 'example.com',
'mail_smtphost' => 'smtp.example.com',
'mail_smtpport' => 587,
'mail_smtpauth' => true,
'mail_smtpname' => 'user@example.com',
'mail_smtppassword' => 'password',
```

- **ALWAYS** use `tls` (STARTTLS on port 587) or `ssl` (implicit TLS on port 465)
- **NEVER** leave `mail_smtpmode` as `sendmail` on containerized deployments -- use `smtp`

---

## Logging Configuration

```php
'log_type' => 'file',
'logfile' => '/var/log/nextcloud/nextcloud.log',
'loglevel' => 2,
'log_type_audit' => 'file',
'logfile_audit' => '/var/log/nextcloud/audit.log',
```

| Level | Name | Use |
|-------|------|-----|
| 0 | Debug | Development only |
| 1 | Info | Verbose production logging |
| 2 | Warn | **Recommended for production** |
| 3 | Error | Errors only |
| 4 | Fatal | Critical failures only |

- **ALWAYS** set `loglevel` to `2` (Warn) for production
- **ALWAYS** configure `logfile_audit` separately when compliance logging is required
- **NEVER** set `log_type` to `syslog` without confirming syslog is configured to handle the volume

---

## Programmatic Configuration Access

### IConfig Interface (System + App + User Config)

```php
use OCP\IConfig;

class MyService {
    public function __construct(private IConfig $config) {}

    public function example(): void {
        // System config (config.php values)
        $maintenance = $this->config->getSystemValue('maintenance', false);
        $this->config->setSystemValue('maintenance', true);

        // App config (per-app key-value store)
        $apiKey = $this->config->getAppValue('myapp', 'api_key', '');
        $this->config->setAppValue('myapp', 'api_key', 'new-key');
        $this->config->deleteAppValue('myapp', 'api_key');

        // User preferences (per-user per-app)
        $pref = $this->config->getUserValue('john', 'myapp', 'theme', 'light');
        $this->config->setUserValue('john', 'myapp', 'theme', 'dark');
        $this->config->deleteUserValue('john', 'myapp', 'theme');
    }
}
```

### IAppConfig Interface (NC 28+ Typed App Config)

```php
use OCP\IAppConfig;

class MyService {
    public function __construct(private IAppConfig $appConfig) {}

    public function example(): void {
        // Typed getters (NC 28+)
        $limit = $this->appConfig->getValueInt('myapp', 'max_items', 100);
        $enabled = $this->appConfig->getValueBool('myapp', 'feature_flag', false);
        $ratio = $this->appConfig->getValueFloat('myapp', 'threshold', 0.75);
        $name = $this->appConfig->getValueString('myapp', 'instance_name', 'default');

        // Typed setters
        $this->appConfig->setValueInt('myapp', 'max_items', 200);
        $this->appConfig->setValueBool('myapp', 'feature_flag', true);

        // Sensitive values (stored encrypted)
        $secret = $this->appConfig->getValueString('myapp', 'api_secret', '', sensitive: true);
        $this->appConfig->setValueString('myapp', 'api_secret', 'xyz', sensitive: true);

        // Check existence
        $exists = $this->appConfig->hasKey('myapp', 'api_key');

        // Get all keys for an app
        $keys = $this->appConfig->getKeys('myapp');
    }
}
```

### Configuration Access Rules

- **ALWAYS** use constructor injection for `IConfig` and `IAppConfig` -- NEVER use `\OCP\Server::get()`
- **ALWAYS** use `IAppConfig` typed methods (NC 28+) over `IConfig::getAppValue()` for new code -- they provide type safety
- **ALWAYS** mark sensitive values with `sensitive: true` -- they are stored encrypted in the database
- **ALWAYS** provide sensible default values in getters -- NEVER assume a config key exists
- **NEVER** use `setSystemValue()` in app code to modify core Nextcloud settings -- only modify your own app's config
- **NEVER** store large data blobs in config -- use the database or file storage instead

---

## Maintenance Mode

```php
// Enable via config.php
'maintenance' => true,

// Or via occ
// sudo -u www-data php occ maintenance:mode --on
// sudo -u www-data php occ maintenance:mode --off
```

### Maintenance Window (NC 28+)

```php
'maintenance_window_start' => 1,  // 1:00 UTC
```

This tells Nextcloud to schedule heavy background tasks (like cleanup, expiry) during a 4-hour window starting at the specified hour. **ALWAYS** set this in production to avoid performance impact during business hours.

---

## occ Config Commands

```bash
# Read system config
sudo -u www-data php occ config:system:get trusted_domains

# Set system config (string)
sudo -u www-data php occ config:system:set trusted_domains 1 --value=cloud.example.com

# Set system config (typed)
sudo -u www-data php occ config:system:set debug --value=true --type=boolean
sudo -u www-data php occ config:system:set loglevel --value=2 --type=integer

# Delete system config
sudo -u www-data php occ config:system:delete debug

# Read app config
sudo -u www-data php occ config:app:get myapp api_key

# Set app config
sudo -u www-data php occ config:app:set myapp api_key --value=new-key

# Delete app config
sudo -u www-data php occ config:app:delete myapp api_key

# List all config
sudo -u www-data php occ config:list
sudo -u www-data php occ config:list --private  # includes sensitive values
```

- **ALWAYS** use `--type` flag when setting non-string system values -- without it, booleans and integers are stored as strings
- **NEVER** use `config:list --private` in scripts that log output -- it exposes passwords and secrets

---

## Decision Tree

### Which config interface to use?

```
Need to read/write config.php values?
  YES --> Use IConfig::getSystemValue() / setSystemValue()
  NO --> Is it app-specific configuration?
    YES --> Is it NC 28+?
      YES --> Use IAppConfig (typed methods)
      NO  --> Use IConfig::getAppValue() / setAppValue()
    NO --> Is it per-user preference?
      YES --> Use IConfig::getUserValue() / setUserValue()
      NO  --> Re-evaluate: config might belong in database table
```

### Which caching backend?

```
Single server?
  YES --> memcache.local = APCu
          Need file locking? --> Add Redis for memcache.locking
  NO  --> memcache.distributed = Redis
          memcache.locking = Redis
          memcache.local = APCu (still per-server)
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- Complete config.php key reference, IConfig methods, IAppConfig methods
- [references/examples.md](references/examples.md) -- Configuration patterns and occ command examples
- [references/anti-patterns.md](references/anti-patterns.md) -- Common configuration mistakes and how to avoid them

### Official Sources

- https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/config_sample_php_parameters.html
- https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/occ_command.html
- https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/caching_configuration.html
- https://docs.nextcloud.com/server/latest/admin_manual/configuration_server/reverse_proxy_configuration.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/storage/configuration.html
