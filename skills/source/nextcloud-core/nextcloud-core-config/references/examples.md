# Configuration Examples

## Minimal Production config.php

```php
<?php
$CONFIG = [
    'instanceid' => 'oc1a2b3c4d5e',
    'passwordsalt' => 'auto-generated-salt',
    'secret' => 'auto-generated-secret',
    'trusted_domains' => [
        0 => 'cloud.example.com',
    ],
    'datadirectory' => '/var/www/nextcloud/data',
    'dbtype' => 'pgsql',
    'dbhost' => 'localhost',
    'dbname' => 'nextcloud',
    'dbuser' => 'nextcloud',
    'dbpassword' => 'secure-password-here',
    'overwrite.cli.url' => 'https://cloud.example.com',
    'default_phone_region' => 'NL',
    'memcache.local' => '\OC\Memcache\APCu',
    'memcache.distributed' => '\OC\Memcache\Redis',
    'memcache.locking' => '\OC\Memcache\Redis',
    'redis' => [
        'host' => '/var/run/redis/redis-server.sock',
        'port' => 0,
    ],
    'loglevel' => 2,
    'maintenance_window_start' => 1,
];
```

## Behind Reverse Proxy (nginx/Traefik)

```php
<?php
$CONFIG = [
    'trusted_domains' => [
        0 => 'cloud.example.com',
    ],
    'trusted_proxies' => ['10.0.0.1', '172.18.0.0/16'],
    'overwriteprotocol' => 'https',
    'overwrite.cli.url' => 'https://cloud.example.com',
    'overwritehost' => 'cloud.example.com',
];
```

## Redis Cluster Configuration

```php
<?php
$CONFIG = [
    'memcache.distributed' => '\OC\Memcache\Redis',
    'memcache.locking' => '\OC\Memcache\Redis',
    'redis.cluster' => [
        'seeds' => [
            'redis-node1:6379',
            'redis-node2:6379',
            'redis-node3:6379',
        ],
        'password' => 'cluster-password',
        'timeout' => 0.0,
        'read_timeout' => 0.0,
        'failover_mode' => \RedisCluster::FAILOVER_ERROR,
    ],
];
```

## SMTP Mail Configuration

```php
<?php
$CONFIG = [
    'mail_smtpmode' => 'smtp',
    'mail_smtpsecure' => 'tls',
    'mail_sendmailmode' => 'smtp',
    'mail_from_address' => 'noreply',
    'mail_domain' => 'example.com',
    'mail_smtphost' => 'smtp.example.com',
    'mail_smtpport' => 587,
    'mail_smtpauth' => true,
    'mail_smtpname' => 'noreply@example.com',
    'mail_smtppassword' => 'app-password-here',
];
```

---

## occ Config Command Examples

### System Config Operations

```bash
# List all system config
sudo -u www-data php occ config:list system

# Get a specific value
sudo -u www-data php occ config:system:get trusted_domains
# Output:
# cloud.example.com

# Get a nested value by index
sudo -u www-data php occ config:system:get trusted_domains 0
# Output: cloud.example.com

# Add a trusted domain
sudo -u www-data php occ config:system:set trusted_domains 1 --value=office.example.com

# Set boolean value (MUST specify --type)
sudo -u www-data php occ config:system:set debug --value=true --type=boolean

# Set integer value (MUST specify --type)
sudo -u www-data php occ config:system:set loglevel --value=2 --type=integer

# Set float value
sudo -u www-data php occ config:system:set version.hide --value=1.5 --type=float

# Set JSON/array value
sudo -u www-data php occ config:system:set redis host --value=/var/run/redis/redis-server.sock
sudo -u www-data php occ config:system:set redis port --value=0 --type=integer

# Delete a config key
sudo -u www-data php occ config:system:delete debug
```

### App Config Operations

```bash
# List all app config
sudo -u www-data php occ config:list apps

# Get app config value
sudo -u www-data php occ config:app:get myapp api_endpoint

# Set app config value
sudo -u www-data php occ config:app:set myapp api_endpoint --value=https://api.example.com/v2

# Set with type
sudo -u www-data php occ config:app:set myapp max_retries --value=5 --type=integer

# Set sensitive value (NC 28+)
sudo -u www-data php occ config:app:set myapp api_secret --value=secret123 --sensitive=true

# Set lazy value (NC 28+)
sudo -u www-data php occ config:app:set myapp cache_ttl --value=3600 --lazy=true --type=integer

# Delete app config
sudo -u www-data php occ config:app:delete myapp api_endpoint
```

### Export and Import

```bash
# Export all config (excludes sensitive values)
sudo -u www-data php occ config:list > config-export.json

# Export including sensitive values
sudo -u www-data php occ config:list --private > config-export-private.json

# Import config from JSON
sudo -u www-data php occ config:import config-export.json
```

### Maintenance Mode

```bash
# Enable maintenance mode
sudo -u www-data php occ maintenance:mode --on

# Disable maintenance mode
sudo -u www-data php occ maintenance:mode --off

# Set maintenance window (NC 28+)
sudo -u www-data php occ config:system:set maintenance_window_start --value=1 --type=integer
```

---

## PHP Code Patterns

### Reading Config in a Controller

```php
use OCA\MyApp\AppInfo\Application;
use OCP\AppFramework\Controller;
use OCP\IConfig;
use OCP\IRequest;

class SettingsController extends Controller {
    public function __construct(
        IRequest $request,
        private IConfig $config,
        private string $userId,
    ) {
        parent::__construct(Application::APP_ID, $request);
    }

    /**
     * @NoAdminRequired
     */
    public function getSettings(): JSONResponse {
        return new JSONResponse([
            'theme' => $this->config->getUserValue(
                $this->userId, Application::APP_ID, 'theme', 'light'
            ),
            'notifications' => $this->config->getUserValue(
                $this->userId, Application::APP_ID, 'notifications', 'enabled'
            ),
        ]);
    }

    /**
     * @NoAdminRequired
     */
    public function setTheme(string $theme): JSONResponse {
        $this->config->setUserValue(
            $this->userId, Application::APP_ID, 'theme', $theme
        );
        return new JSONResponse(['status' => 'ok']);
    }
}
```

### Using IAppConfig for Typed App Settings (NC 28+)

```php
use OCP\IAppConfig;

class AppSettingsService {
    public function __construct(
        private IAppConfig $appConfig,
        private string $appId,
    ) {}

    public function getMaxUploadSize(): int {
        return $this->appConfig->getValueInt($this->appId, 'max_upload_mb', 512);
    }

    public function setApiCredentials(string $key, string $secret): void {
        $this->appConfig->setValueString($this->appId, 'api_key', $key, sensitive: true);
        $this->appConfig->setValueString($this->appId, 'api_secret', $secret, sensitive: true);
    }

    public function isFeatureEnabled(string $feature): bool {
        return $this->appConfig->getValueBool($this->appId, "feature_$feature", false);
    }

    public function getCacheConfig(): array {
        return [
            'ttl' => $this->appConfig->getValueInt($this->appId, 'cache_ttl', 3600, lazy: true),
            'enabled' => $this->appConfig->getValueBool($this->appId, 'cache_enabled', true),
        ];
    }
}
```

### Admin Settings Page with Config

```php
use OCP\AppFramework\Http\TemplateResponse;
use OCP\IConfig;
use OCP\Settings\ISettings;

class AdminSettings implements ISettings {
    public function __construct(
        private IConfig $config,
        private string $appName,
    ) {}

    public function getForm(): TemplateResponse {
        return new TemplateResponse($this->appName, 'admin', [
            'api_endpoint' => $this->config->getAppValue($this->appName, 'api_endpoint', ''),
            'sync_interval' => $this->config->getAppValue($this->appName, 'sync_interval', '3600'),
        ]);
    }

    public function getSection(): string {
        return $this->appName;
    }

    public function getPriority(): int {
        return 50;
    }
}
```

### Checking System Requirements via Config

```php
use OCP\IConfig;
use Psr\Log\LoggerInterface;

class SystemCheck {
    public function __construct(
        private IConfig $config,
        private LoggerInterface $logger,
    ) {}

    public function verifyProductionSetup(): array {
        $warnings = [];

        if ($this->config->getSystemValueBool('debug', false)) {
            $warnings[] = 'Debug mode is enabled -- disable for production';
        }

        if ($this->config->getSystemValueInt('loglevel', 2) < 2) {
            $warnings[] = 'Log level is below Warning -- set to 2 for production';
        }

        $memcacheLocal = $this->config->getSystemValue('memcache.local', '');
        if (empty($memcacheLocal)) {
            $warnings[] = 'No local memory cache configured -- set memcache.local';
        }

        $phoneRegion = $this->config->getSystemValueString('default_phone_region', '');
        if (empty($phoneRegion)) {
            $warnings[] = 'default_phone_region not set';
        }

        return $warnings;
    }
}
```
