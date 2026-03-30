---
name: nextcloud-agents-review
description: >
  Use when reviewing Nextcloud app code, validating before deployment, or checking for common mistakes.
  Prevents deploying code with missing security attributes, incorrect DI patterns, and known anti-patterns.
  Covers controller security attributes, OCS endpoint patterns, database migration integrity, DI patterns, frontend import paths, CSRF handling, file API usage, and known anti-patterns.
  Keywords: code review, validation, security attributes, anti-pattern, DI check, migration check, CSRF check, deployment, check my code, review before deploy, find mistakes, validate app quality..
license: MIT
compatibility: "Designed for Claude Code. Requires Nextcloud 28+."
metadata:
  author: OpenAEC-Foundation
  version: "1.0"
---

# nextcloud-agents-review

## Purpose

This skill guides Claude through a systematic code review of Nextcloud app code. Run this checklist BEFORE merging, deploying, or accepting generated code. Each check specifies WHAT to verify, the EXPECTED state, and the COMMON failure.

## Review Process

ALWAYS follow this sequence:

1. **Gather scope** -- Identify all files changed or generated
2. **Run area checklists** -- Apply each relevant section below
3. **Report findings** -- List every violation with file, line, and fix
4. **Block on critical** -- NEVER approve code with critical violations

---

## Area 1: Controller Security Attributes

ALWAYS verify every public controller method has explicit security attributes.

| Check | Expected State | Common Failure |
|-------|---------------|----------------|
| Security attributes present | Every public method has at least one of `#[NoAdminRequired]`, `#[PublicPage]`, or is intentionally admin-only | Missing attributes -- method silently defaults to admin-only |
| No unprotected state-changing endpoints | `#[PublicPage]` + `#[NoCSRFRequired]` NEVER appear together on POST/PUT/DELETE methods | CSRF bypass on public write endpoints |
| Brute force protection on auth endpoints | `#[BruteForceProtection]` present on login/token/password methods | Missing throttle on authentication |
| Throttle only on failure | `$response->throttle()` called ONLY in failure branches | Throttle on success degrades legitimate users |
| Rate limiting on sensitive endpoints | `#[UserRateLimit]` or `#[AnonRateLimit]` on expensive operations | Unlimited calls to resource-heavy endpoints |

**Decision tree:**

```
Method is public?
├── YES: Has security attributes?
│   ├── NO → CRITICAL: Add explicit attributes
│   └── YES: Is state-changing (POST/PUT/DELETE)?
│       ├── YES: Has #[PublicPage] + #[NoCSRFRequired]?
│       │   ├── YES → CRITICAL: Remove one or add alternative auth
│       │   └── NO → OK
│       └── NO → OK
└── NO → SKIP (private/protected methods)
```

---

## Area 2: OCS Endpoint Validation

ALWAYS verify OCS controllers and routes follow the v2 pattern.

| Check | Expected State | Common Failure |
|-------|---------------|----------------|
| Extends OCSController | OCS route controllers extend `OCSController`, NOT `Controller` | Using `Controller` breaks response envelope |
| Routes in `ocs` array | OCS endpoints listed in the `ocs` array of `routes.php` | Listed in `routes` array -- wrong URL prefix |
| Returns DataResponse | OCS methods return `DataResponse`, not `JSONResponse` | JSONResponse bypasses OCS envelope |
| OCS-APIRequest header | API documentation/tests include `OCS-APIRequest: true` | Requests rejected without header |
| v2 endpoints only | All OCS URLs use `/ocs/v2.php/` prefix | Using v1 with wrong status code assumptions |

---

## Area 3: Database Migration Integrity

ALWAYS verify migrations follow Nextcloud conventions.

| Check | Expected State | Common Failure |
|-------|---------------|----------------|
| Naming convention | Class: `Version{MajorMinor}Date{Timestamp}` | Wrong naming breaks migration order |
| No modified migrations | Existing migration files NEVER changed | Modified migration skipped on instances that already ran it |
| Primary key exists | Every table has `setPrimaryKey(['id'])` | Galera Cluster replication fails |
| Auto-increment id | Every table has `id BIGINT autoincrement` | Missing primary key column |
| Table name length | Table name max 23 chars (27 with `oc_` prefix) | Oracle compatibility failure |
| Column name length | Column/index names max 30 chars | Oracle compatibility failure |
| Uses query builder | No raw SQL strings in migrations `postSchemaChange` | Database portability broken |
| Index names explicit | All indices have named identifiers | Cannot reference index for future modification |

**Decision tree:**

```
Is this a schema change?
├── Existing migration file modified?
│   └── YES → CRITICAL: Create new migration instead
├── New table without primary key?
│   └── YES → CRITICAL: Add setPrimaryKey(['id'])
├── Table name > 23 chars?
│   └── YES → CRITICAL: Shorten name
└── All checks pass → OK
```

---

## Area 4: Dependency Injection

ALWAYS verify services use constructor injection.

| Check | Expected State | Common Failure |
|-------|---------------|----------------|
| No Server::get() | Zero occurrences of `\OCP\Server::get()` | Service locator breaks testability |
| Constructor injection | All dependencies passed via constructor | Runtime resolution via container |
| No ILogger | Zero imports of `OCP\ILogger` | Deprecated since NC 24 -- use `Psr\Log\LoggerInterface` |
| Namespace in info.xml | `<namespace>` element present | Auto-wiring silently fails |
| No service queries in register() | `register()` only calls `IRegistrationContext` methods | Queries fail -- other apps not yet registered |
| No side effects in constructors | Constructors only assign dependencies | I/O in constructor breaks lazy loading |

---

## Area 5: Frontend Validation

ALWAYS verify frontend code uses @nextcloud/* packages.

| Check | Expected State | Common Failure |
|-------|---------------|----------------|
| No OC.generateUrl() | Zero uses of `OC.generateUrl` | Legacy global -- use `@nextcloud/router` |
| No OC.requestToken | Zero direct uses of `OC.requestToken` | Use `@nextcloud/axios` which handles CSRF |
| No raw fetch/axios | Zero imports of plain `axios` or `fetch()` | Missing auth headers -- use `@nextcloud/axios` |
| @nextcloud/vue imports | Components from `@nextcloud/vue`, not custom UI | Inconsistent look, no dark mode support |
| No hardcoded colors | CSS uses `var(--color-*)` variables | Breaks dark mode and custom themes |
| Dialog styles imported | `@nextcloud/dialogs/style.css` imported when using toasts | Toasts render without styling |
| loadState has fallback | `loadState()` calls include third argument | Throws on missing key without fallback |

---

## Area 6: File API Validation

ALWAYS verify file operations use the Node API correctly.

| Check | Expected State | Common Failure |
|-------|---------------|----------------|
| NotFoundException handled | Every `get()` call wrapped in try/catch for `NotFoundException` | Unhandled exception crashes request |
| getById() array check | `getById()` result checked as array before access | Assumes single result -- returns array |
| No hardcoded paths | File access via `getUserFolder()`, not string paths | Bypasses storage abstraction |
| IRootFolder injected | `IRootFolder` as constructor dependency, not `IUserFolder` | Cannot access other users' files when needed |
| instanceof check | `get()` result checked with `instanceof File` or `instanceof Folder` | Type confusion between files and folders |

---

## Area 7: Event System Validation

ALWAYS verify events use the modern typed system.

| Check | Expected State | Common Failure |
|-------|---------------|----------------|
| Typed events only | All events extend `OCP\EventDispatcher\Event` | Using deprecated `GenericEvent` |
| No deprecated hooks | Zero uses of `$manager->listen()` | Legacy hook system -- use `IEventDispatcher` |
| instanceof check in handle() | `handle()` method checks `$event instanceof SpecificEvent` | Base `Event` type causes runtime errors |
| Listeners in register() | Listeners registered via `IRegistrationContext::registerEventListener()` | Registered in `boot()` -- may miss early events |
| parent::__construct() called | Custom event constructors call `parent::__construct()` | Event base class not initialized |
| No dispatch in constructors | Events dispatched in service methods, not constructors | Services may not be fully initialized |

---

## Area 8: Security Cross-Checks

ALWAYS run these cross-cutting security checks.

| Check | Expected State | Common Failure |
|-------|---------------|----------------|
| CSRF on state change | POST/PUT/DELETE endpoints have CSRF protection OR `OCS-APIRequest` | State changes without CSRF protection |
| No PublicPage on admin endpoints | Admin-settings controllers have NO `#[PublicPage]` | Settings exposed to anonymous users |
| Password not logged | No `$password` or credential values in logger calls | Credentials in log files |
| SQL injection prevention | All query builder params use `createNamedParameter()` | Raw string concatenation in queries |
| Input validation | Controller params have type hints | Untyped string injection |

---

## Severity Levels

| Level | Action | Examples |
|-------|--------|---------|
| CRITICAL | MUST fix before merge | Missing CSRF, modified migration, no primary key, PublicPage+NoCSRFRequired on POST |
| WARNING | SHOULD fix before merge | Missing rate limiting, no NotFoundException handling, deprecated ILogger |
| INFO | Consider fixing | Missing explicit security attributes on admin-only method, barrel imports |

---

## Review Report Template

```
## Nextcloud Code Review

### Summary
- Files reviewed: {count}
- Critical: {count}
- Warnings: {count}
- Info: {count}

### Critical Issues
- [{file}:{line}] {area}: {description} → Fix: {action}

### Warnings
- [{file}:{line}] {area}: {description} → Fix: {action}

### Info
- [{file}:{line}] {area}: {description} → Fix: {action}

### Verdict: {PASS | BLOCK}
```

---

## Reference Links

- [references/methods.md](references/methods.md) -- Complete validation checklist with code patterns
- [references/examples.md](references/examples.md) -- Review scenarios: good code, bad code, fixes
- [references/anti-patterns.md](references/anti-patterns.md) -- All anti-patterns consolidated by area

### Official Sources

- https://docs.nextcloud.com/server/latest/developer_manual/digging_deeper/controllers.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/routing.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/storage/database.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/dependency_injection.html
- https://docs.nextcloud.com/server/latest/developer_manual/basics/events.html
