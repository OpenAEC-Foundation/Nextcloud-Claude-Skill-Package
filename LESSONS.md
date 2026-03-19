# Lessons Learned

Observations and findings captured during skill package development.

---

## L-001: Nextcloud is a Multi-Layer Platform

- **Date**: 2026-03-19
- **Context**: Nextcloud combines PHP backend, TypeScript/Vue.js frontend, OCS REST API, WebDAV, and server administration in one platform.
- **Finding**: Skills must be organized by API surface (OCS, DAV, app framework) rather than by language. A single feature like file sharing spans PHP controllers, OCS endpoints, DAV operations, and Vue.js components. The skill structure must reflect these API boundaries, not language boundaries.

---

## L-002: NC 28+ Marks a Significant Frontend Shift

- **Date**: 2026-03-19
- **Context**: Nextcloud 28 introduced Vue 3 migration and updated @nextcloud/* packages.
- **Finding**: Frontend code from NC 27 and earlier uses Vue 2 patterns that are incompatible with NC 28+. Skills MUST target Vue 3 patterns and the latest @nextcloud/vue library. This is why D-007 restricts coverage to NC 28+ only — mixing Vue 2 and Vue 3 patterns in skills would cause confusion and broken code.
