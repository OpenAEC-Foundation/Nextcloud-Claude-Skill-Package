# Configuration Anti-Patterns

## AP-001: Storing config.php in Version Control

**NEVER** commit `config.php` to a Git repository.

**Why:** It contains database passwords, `passwordsalt`, `secret`, and `instanceid`. Exposure allows authentication bypass and data decryption.

**Instead:** Use a `.gitignore` rule for `config/config.php`. For deployment automation, use environment variables or a templated config file that gets populated during deployment.

---

## AP-002: Forgetting trusted_domains

**NEVER** deploy Nextcloud without verifying `trusted_domains` contains all access hostnames.

**Why:** Users see "Access through untrusted domain" error and cannot log in. This is the #1 post-installation support issue.

**Instead:** Add every domain/IP that users will use to access Nextcloud:
```php
'trusted_domains' => [
    0 => 'cloud.example.com',
    1 => '192.168.1.100',
    2 => 'localhost',
],
```

---

## AP-003: Debug Logging in Production

**NEVER** set `loglevel` to `0` (Debug) in production.

**Why:** Debug logging writes extremely verbose output including full request/response data, query details, and stack traces. This degrades performance and fills disk space rapidly.

**Instead:** Use `loglevel` `2` (Warn) for production. Temporarily switch to `1` (Info) or `0` (Debug) for troubleshooting, then switch back immediately.

---

## AP-004: Using Server::get() for Config Access

**NEVER** use `\OCP\Server::get(IConfig::class)` or `\OC::$server->getConfig()` in app code.

**Why:** This bypasses dependency injection, making code untestable and hiding dependencies. The static accessor pattern is deprecated.

**Instead:** ALWAYS inject `IConfig` or `IAppConfig` via constructor:
```php
// WRONG
$config = \OCP\Server::get(IConfig::class);

// CORRECT
public function __construct(private IConfig $config) {}
```

---

## AP-005: Missing --type Flag in occ Commands

**NEVER** set boolean or integer config values via `occ config:system:set` without `--type`.

**Why:** Without `--type`, all values are stored as strings. `'true'` (string) is not the same as `true` (boolean). Code using `getSystemValueBool()` may return unexpected results.

**Instead:** ALWAYS specify `--type` for non-string values:
```bash
# WRONG
sudo -u www-data php occ config:system:set debug --value=true

# CORRECT
sudo -u www-data php occ config:system:set debug --value=true --type=boolean
sudo -u www-data php occ config:system:set loglevel --value=2 --type=integer
```

---

## AP-006: APCu for Distributed Caching

**NEVER** use `\OC\Memcache\APCu` for `memcache.distributed` in multi-server deployments.

**Why:** APCu is process-local memory. In a multi-server setup, each server has its own APCu cache with no synchronization. This causes stale data, session inconsistencies, and file locking failures.

**Instead:** Use Redis for `memcache.distributed` and `memcache.locking`. Keep APCu for `memcache.local` only:
```php
'memcache.local' => '\OC\Memcache\APCu',
'memcache.distributed' => '\OC\Memcache\Redis',
'memcache.locking' => '\OC\Memcache\Redis',
```

---

## AP-007: Missing memcache.locking with Redis

**NEVER** configure `memcache.distributed` with Redis but omit `memcache.locking`.

**Why:** Nextcloud's transactional file locking uses `memcache.locking`. Without it, file locking falls back to the database, which is slower and can cause lock contention under load.

**Instead:** ALWAYS set all three cache layers when using Redis:
```php
'memcache.local' => '\OC\Memcache\APCu',
'memcache.distributed' => '\OC\Memcache\Redis',
'memcache.locking' => '\OC\Memcache\Redis',
```

---

## AP-008: Trusting All Proxy IPs

**NEVER** set `trusted_proxies` to `['0.0.0.0/0']` or include overly broad CIDR ranges.

**Why:** This allows any client to spoof `X-Forwarded-For` headers, bypassing IP-based brute-force protection, rate limiting, and audit logging. All requests appear to come from spoofed IPs.

**Instead:** List ONLY the specific IP addresses or narrow CIDR ranges of your actual reverse proxies:
```php
'trusted_proxies' => ['10.0.0.1'],        // specific IP
'trusted_proxies' => ['172.18.0.0/16'],    // Docker network
```

---

## AP-009: Modifying Core Config from App Code

**NEVER** use `IConfig::setSystemValue()` in app code to change core Nextcloud settings like `maintenance`, `trusted_domains`, or `loglevel`.

**Why:** Apps should not modify server-wide settings. This can break other apps, lock out administrators, or create security holes. System config changes should be done by admins via occ or the admin UI.

**Instead:** Use `IConfig::setAppValue()` or `IAppConfig` for app-specific configuration only. If you need system-level changes, document them as admin instructions.

---

## AP-010: Storing Secrets Without Sensitive Flag

**NEVER** store API keys, tokens, or passwords using `IAppConfig` without `sensitive: true` (NC 28+).

**Why:** Without the sensitive flag, values are stored in plaintext in the database and exposed by `occ config:list`. With `sensitive: true`, values are encrypted at rest.

**Instead:** ALWAYS mark sensitive values:
```php
// WRONG
$this->appConfig->setValueString('myapp', 'api_secret', $secret);

// CORRECT
$this->appConfig->setValueString('myapp', 'api_secret', $secret, sensitive: true);
```

---

## AP-011: Running occ as Root

**NEVER** run `php occ` as the root user directly.

**Why:** Files created or modified by occ will be owned by root, not the web server user. This causes permission errors when Nextcloud tries to access those files via the web interface.

**Instead:** ALWAYS run as the web server user:
```bash
# WRONG
php occ maintenance:mode --on

# CORRECT
sudo -u www-data php occ maintenance:mode --on

# Or in Docker
docker exec -u www-data nextcloud php occ maintenance:mode --on
```

---

## AP-012: Not Setting maintenance_window_start

**NEVER** leave `maintenance_window_start` unset on production servers (NC 28+).

**Why:** Without this setting, Nextcloud schedules heavy background tasks (cleanup, expiry, file scans) at any time, potentially degrading performance during business hours.

**Instead:** Set it to a low-traffic hour in UTC:
```php
'maintenance_window_start' => 1,  // 1:00 UTC = 2:00 CET
```

---

## AP-013: Assuming Config Keys Exist

**NEVER** call config getters without providing a default value.

**Why:** If a key does not exist, the return value depends on the method. Without a default, you may get `null`, empty string, or `false` unpredictably, causing type errors downstream.

**Instead:** ALWAYS provide explicit defaults:
```php
// WRONG
$value = $this->config->getAppValue('myapp', 'threshold');

// CORRECT
$value = $this->config->getAppValue('myapp', 'threshold', '0.5');

// BEST (NC 28+ typed)
$value = $this->appConfig->getValueFloat('myapp', 'threshold', 0.5);
```

---

## AP-014: Storing Large Data in Config

**NEVER** store large JSON blobs, file contents, or data arrays exceeding a few KB in app config.

**Why:** Config values are loaded into memory on every page request (unless marked `lazy`). Large values waste memory and slow down every request.

**Instead:** Store large data in a dedicated database table or in the filesystem via the Node API. Use config only for small settings (strings, numbers, flags). If you must store moderate data, mark it `lazy: true` so it is only loaded when explicitly accessed.

---

## AP-015: Using config:list --private in Scripts

**NEVER** use `occ config:list --private` in automated scripts that log output or pipe to external systems.

**Why:** The `--private` flag includes all sensitive values (database passwords, API keys, secrets) in the output. If this output is logged, stored, or transmitted, it exposes all credentials.

**Instead:** Use `occ config:list` (without `--private`) for automated exports. Access individual sensitive values only when needed with `config:app:get`.
