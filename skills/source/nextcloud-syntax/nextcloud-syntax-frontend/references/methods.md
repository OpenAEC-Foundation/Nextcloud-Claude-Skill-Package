# @nextcloud/* Package API Reference

## @nextcloud/vue -- Component Library

### Installation

```bash
# For NC 28-30 (Vue 2)
npm i @nextcloud/vue@^8.0.0

# For NC 31+ (Vue 3)
npm i @nextcloud/vue@next
```

### Layout Components

#### NcContent

Root wrapper for the entire app content area. ALWAYS use as the outermost component.

```vue
<template>
    <NcContent app-name="myapp">
        <NcAppNavigation>
            <!-- sidebar content -->
        </NcAppNavigation>
        <NcAppContent>
            <!-- main content -->
        </NcAppContent>
    </NcContent>
</template>

<script>
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppNavigation from '@nextcloud/vue/components/NcAppNavigation'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'

export default {
    components: { NcContent, NcAppNavigation, NcAppContent },
}
</script>
```

#### NcAppNavigation

Left sidebar navigation panel. Supports items, settings footer, and custom content.

```vue
<NcAppNavigation>
    <template #list>
        <NcAppNavigationItem v-for="item in items"
            :key="item.id"
            :name="item.title"
            :to="{ name: 'item', params: { id: item.id } }" />
    </template>
    <template #footer>
        <NcAppNavigationSettings>
            <!-- settings form -->
        </NcAppNavigationSettings>
    </template>
</NcAppNavigation>
```

#### NcAppSidebar

Right detail sidebar. Supports tabs, header actions, and star toggle.

```vue
<NcAppSidebar
    :name="selectedItem.title"
    :subtitle="selectedItem.description"
    :starred="selectedItem.favorite"
    @close="closeSidebar"
    @update:starred="toggleFavorite">
    <NcAppSidebarTab id="details" name="Details" icon="icon-info">
        <!-- tab content -->
    </NcAppSidebarTab>
</NcAppSidebar>
```

### Interactive Components

#### NcButton

```vue
<NcButton type="primary" @click="handleClick">
    <template #icon>
        <IconPlus :size="20" />
    </template>
    Create Item
</NcButton>
```

**Props:**
| Prop | Type | Values |
|------|------|--------|
| `type` | String | `primary`, `secondary`, `tertiary`, `tertiary-no-background`, `error`, `warning`, `success` |
| `disabled` | Boolean | Disables interaction |
| `wide` | Boolean | Full width button |
| `pressed` | Boolean | Toggle state (for tertiary buttons) |

#### NcActions

Dropdown menu container for action items.

```vue
<NcActions>
    <NcActionButton @click="editItem">
        <template #icon><IconPencil :size="20" /></template>
        Edit
    </NcActionButton>
    <NcActionButton @click="deleteItem" :close-after-click="true">
        <template #icon><IconDelete :size="20" /></template>
        Delete
    </NcActionButton>
    <NcActionSeparator />
    <NcActionLink :href="externalUrl">
        Open external
    </NcActionLink>
</NcActions>
```

#### NcDialog

```vue
<NcDialog :open.sync="showDialog"
    name="Confirm Action"
    :buttons="dialogButtons">
    <p>Are you sure you want to proceed?</p>
</NcDialog>

<script>
export default {
    data() {
        return {
            showDialog: false,
            dialogButtons: [
                { label: 'Cancel', callback: () => { this.showDialog = false } },
                { label: 'Confirm', type: 'primary', callback: () => this.confirm() },
            ],
        }
    },
}
</script>
```

#### NcSelect

```vue
<NcSelect v-model="selected"
    :options="options"
    :placeholder="t('myapp', 'Select an option')"
    label="name"
    track-by="id" />
```

#### NcTextField

```vue
<NcTextField :value.sync="searchQuery"
    :label="t('myapp', 'Search')"
    :placeholder="t('myapp', 'Type to search...')"
    :show-trailing-button="searchQuery !== ''"
    @trailing-button-click="clearSearch" />
```

### Display Components

#### NcEmptyContent

```vue
<NcEmptyContent :name="t('myapp', 'No items yet')"
    :description="t('myapp', 'Create your first item to get started')">
    <template #icon>
        <IconFolder :size="64" />
    </template>
    <template #action>
        <NcButton type="primary" @click="createItem">
            Create item
        </NcButton>
    </template>
</NcEmptyContent>
```

#### NcListItem

```vue
<NcListItem :name="item.title"
    :details="item.date"
    :bold="item.unread"
    :active="item.id === selectedId"
    @click="selectItem(item)">
    <template #icon>
        <NcAvatar :user="item.userId" :size="44" />
    </template>
    <template #subname>
        {{ item.description }}
    </template>
    <template #actions>
        <NcActionButton @click="deleteItem(item)">Delete</NcActionButton>
    </template>
</NcListItem>
```

#### NcSettingsSection

```vue
<NcSettingsSection :name="t('myapp', 'General Settings')"
    :description="t('myapp', 'Configure the main application settings')">
    <!-- settings form fields -->
</NcSettingsSection>
```

---

## @nextcloud/axios -- HTTP Client

### Installation

```bash
npm install @nextcloud/axios
```

### API

ALWAYS import as default export. This is a pre-configured Axios instance with authentication headers.

```typescript
import axios from '@nextcloud/axios'
```

| Method | Signature |
|--------|-----------|
| `axios.get(url, config?)` | GET request |
| `axios.post(url, data?, config?)` | POST request |
| `axios.put(url, data?, config?)` | PUT request |
| `axios.delete(url, config?)` | DELETE request |
| `axios.patch(url, data?, config?)` | PATCH request |

### Nextcloud-Specific Config Options

| Option | Type | Purpose |
|--------|------|---------|
| `retryIfMaintenanceMode` | boolean | Auto-retry when server is in maintenance |
| `reloadExpiredSession` | boolean | Auto-reload page when session expires |

### Setting Base URL

```typescript
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'

axios.defaults.baseURL = generateUrl('/apps/myapp/api')
const items = await axios.get('/items')
const item = await axios.get('/items/42')
```

---

## @nextcloud/router -- URL Generation

### Installation

```bash
npm install @nextcloud/router
```

### Functions

| Function | Purpose | Example Output |
|----------|---------|----------------|
| `generateUrl(path, params?)` | App route URL | `/index.php/apps/myapp/api/items/42` |
| `generateOcsUrl(path, params?)` | OCS API URL | `/ocs/v2.php/apps/myapp/api/v1/items` |
| `generateRemoteUrl(service)` | Remote endpoint | `/remote.php/dav` |
| `generateFilePath(app, type, file)` | Static asset URL | `/apps/myapp/img/icon.svg` |

### Usage

```typescript
import { generateUrl, generateOcsUrl, generateRemoteUrl, generateFilePath } from '@nextcloud/router'

// App route with parameter substitution
const url = generateUrl('/apps/myapp/api/items/{id}', { id: 42 })

// OCS endpoint
const ocsUrl = generateOcsUrl('/apps/myapp/api/v1/items')

// WebDAV endpoint
const davUrl = generateRemoteUrl('dav')

// Static asset
const iconUrl = generateFilePath('myapp', 'img', 'icon.svg')
```

---

## @nextcloud/initial-state -- Server-to-Client Data

### Installation

```bash
npm install @nextcloud/initial-state
```

### PHP Side (Provider)

```php
use OCP\AppFramework\Services\IInitialState;

// Eager: ALWAYS serialized on page load
$this->initialState->provideInitialState('key', $value);

// Lazy: only serialized when loadState() is called
$this->initialState->provideLazyInitialState('key', function() {
    return $this->expensiveQuery();
});
```

### JavaScript Side (Consumer)

```typescript
import { loadState } from '@nextcloud/initial-state'

// Basic usage (throws if key not found)
const value = loadState('myapp', 'key')

// With fallback (ALWAYS use for optional data)
const value = loadState('myapp', 'key', defaultValue)

// TypeScript typed
const config = loadState<MyInterface>('myapp', 'config', defaults)
```

**CRITICAL:** `loadState()` throws an `Error` if the key is not found and no fallback is provided. ALWAYS provide a fallback for optional state.

---

## @nextcloud/dialogs -- Toasts & File Picker

### Installation

```bash
npm install @nextcloud/dialogs
```

### Toast Notifications

**ALWAYS import the stylesheet -- toasts render unstyled without it:**

```typescript
import { showSuccess, showError, showWarning, showInfo, showMessage } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'
```

| Function | Purpose |
|----------|---------|
| `showSuccess(text, options?)` | Green success toast |
| `showError(text, options?)` | Red error toast |
| `showWarning(text, options?)` | Yellow warning toast |
| `showInfo(text, options?)` | Blue info toast |
| `showMessage(text, options?)` | Neutral toast |

**Options:**
| Option | Type | Default | Purpose |
|--------|------|---------|---------|
| `timeout` | number | 7000 | Auto-dismiss (ms). Set `-1` for persistent |
| `isHTML` | boolean | false | Render HTML content |

### File Picker

```typescript
import { getFilePickerBuilder } from '@nextcloud/dialogs'

const picker = getFilePickerBuilder('Select a file')
    .addMimeTypeFilter('text/plain')
    .addButton({
        label: 'Pick',
        callback: (nodes) => console.log('Selected:', nodes),
    })
    .build()

const paths = await picker.pick()
```

---

## @nextcloud/files -- DAV Client & File Types

### Installation

```bash
# For NC 28-32
npm install @nextcloud/files@^3.0.0

# For NC 33+
npm install @nextcloud/files@^4.0.0
```

### WebDAV Client

```typescript
import { getClient, getDefaultPropfind, resultToNode } from '@nextcloud/files/dav'

const client = getClient()

// List directory contents
const results = await client.getDirectoryContents('/files/username/Documents', {
    details: true,
    data: getDefaultPropfind(),
})
const nodes = results.data.map(r => resultToNode(r))

// Get favorites
import { getFavoriteNodes } from '@nextcloud/files/dav'
const favorites = await getFavoriteNodes(client)
```

### Permission Enum

```typescript
import { Permission } from '@nextcloud/files'

Permission.READ    // 1
Permission.UPDATE  // 2
Permission.CREATE  // 4
Permission.DELETE  // 8
Permission.SHARE   // 16
```

### Files App Integration -- "New" Menu Entry

```typescript
import type { Entry } from '@nextcloud/files'
import { addNewFileMenuEntry } from '@nextcloud/files'

const entry: Entry = {
    id: 'my-app-new-doc',
    displayName: t('myapp', 'New Document'),
    iconSvgInline: '<svg>...</svg>',
    handler(context, content) {
        // Create new file in context folder
    },
}
addNewFileMenuEntry(entry)
```

### Sidebar Tab Registration

```typescript
import { getSidebar } from '@nextcloud/files'

getSidebar().registerTab({
    id: 'my-app-tab',
    displayName: 'My Tab',
    iconSvgInline: '<svg>...</svg>',
    order: 50,
    tagName: 'my-app-sidebar-tab',
    enabled({ node, folder, view }) {
        return node.mime === 'application/pdf'
    },
})
```

---

## @nextcloud/event-bus -- Frontend Events

### Installation

```bash
npm install @nextcloud/event-bus
```

### API

```typescript
import { emit, subscribe, unsubscribe } from '@nextcloud/event-bus'

// Subscribe
const handler = (event) => console.log('Uploaded:', event)
subscribe('files:node:uploaded', handler)

// Emit
emit('myapp:item:updated', { id: 42, title: 'Updated' })

// Unsubscribe (ALWAYS clean up in component teardown)
unsubscribe('files:node:uploaded', handler)
```

### Event Naming Convention

Format: `app-id:object:verb`

Built-in events:
- `files:node:uploading` / `files:node:uploaded` / `files:node:deleted`
- `nextcloud:unified-search:closed`

### TypeScript Typed Events

```typescript
// In a .d.ts file
declare module '@nextcloud/event-bus' {
    interface NextcloudEvents {
        'myapp:item:created': { id: number; name: string }
        'myapp:item:deleted': { id: number }
    }
}
export {}
```
