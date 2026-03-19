# Frontend Examples

## Example 1: Complete Vue App Setup

### Directory Structure

```
myapp/
├── appinfo/
│   ├── info.xml
│   └── routes.php
├── lib/
│   └── Controller/
│       └── PageController.php
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── components/
│   │   └── ItemList.vue
│   └── services/
│       └── ItemService.js
├── templates/
│   └── main.php
├── css/
│   └── style.scss
├── webpack.config.js
└── package.json
```

### package.json

```json
{
  "name": "myapp",
  "scripts": {
    "build": "webpack --node-env production --progress",
    "dev": "webpack --node-env development --progress",
    "watch": "webpack --node-env development --progress --watch",
    "serve": "webpack --node-env development serve --progress"
  },
  "dependencies": {
    "@nextcloud/axios": "^2.0.0",
    "@nextcloud/dialogs": "^5.0.0",
    "@nextcloud/initial-state": "^2.0.0",
    "@nextcloud/router": "^3.0.0",
    "@nextcloud/vue": "^8.0.0",
    "vue": "^2.7.0"
  },
  "devDependencies": {
    "@nextcloud/webpack-vue-config": "^6.0.0"
  }
}
```

### webpack.config.js

```javascript
const webpackConfig = require('@nextcloud/webpack-vue-config')
module.exports = webpackConfig
```

### templates/main.php

```php
<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
script('myapp', 'myapp-main');  // loads js/myapp-main.js
style('myapp', 'style');         // loads css/style.(s)css
?>
<div id="content"></div>
```

### src/main.js

```javascript
import Vue from 'vue'
import App from './App.vue'

const appElement = document.getElementById('content')

new Vue({
    el: appElement,
    render: h => h(App),
})
```

### src/App.vue

```vue
<template>
    <NcContent app-name="myapp">
        <NcAppNavigation>
            <template #list>
                <NcAppNavigationItem v-for="item in items"
                    :key="item.id"
                    :name="item.title"
                    :class="{ active: item.id === selectedId }"
                    @click="selectItem(item)" />
            </template>
        </NcAppNavigation>
        <NcAppContent>
            <NcEmptyContent v-if="items.length === 0"
                :name="t('myapp', 'No items yet')">
                <template #icon>
                    <IconFolder :size="64" />
                </template>
                <template #action>
                    <NcButton type="primary" @click="createItem">
                        {{ t('myapp', 'Create item') }}
                    </NcButton>
                </template>
            </NcEmptyContent>
            <ItemList v-else :items="items" :selected-id="selectedId" />
        </NcAppContent>
    </NcContent>
</template>

<script>
import NcContent from '@nextcloud/vue/components/NcContent'
import NcAppContent from '@nextcloud/vue/components/NcAppContent'
import NcAppNavigation from '@nextcloud/vue/components/NcAppNavigation'
import NcAppNavigationItem from '@nextcloud/vue/components/NcAppNavigationItem'
import NcButton from '@nextcloud/vue/components/NcButton'
import NcEmptyContent from '@nextcloud/vue/components/NcEmptyContent'
import { loadState } from '@nextcloud/initial-state'
import ItemList from './components/ItemList.vue'
import { fetchItems, createItem } from './services/ItemService.js'

export default {
    name: 'App',
    components: {
        NcContent,
        NcAppContent,
        NcAppNavigation,
        NcAppNavigationItem,
        NcButton,
        NcEmptyContent,
        ItemList,
    },
    data() {
        return {
            items: [],
            selectedId: null,
            config: loadState('myapp', 'config', { maxItems: 50 }),
        }
    },
    async mounted() {
        this.items = await fetchItems()
    },
    methods: {
        selectItem(item) {
            this.selectedId = item.id
        },
        async createItem() {
            const newItem = await createItem({ title: 'New Item' })
            this.items.push(newItem)
        },
    },
}
</script>

<style scoped>
.active {
    background-color: var(--color-primary-element-light);
}
</style>
```

### PageController.php (providing initial state)

```php
<?php
namespace OCA\MyApp\Controller;

use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Services\IInitialState;
use OCP\IRequest;

class PageController extends Controller {
    public function __construct(
        string $appName,
        IRequest $request,
        private IInitialState $initialState,
        private ItemService $service,
    ) {
        parent::__construct($appName, $request);
    }

    #[NoAdminRequired]
    #[NoCSRFRequired]
    public function index(): TemplateResponse {
        $this->initialState->provideInitialState('config', [
            'maxItems' => 50,
        ]);
        $this->initialState->provideLazyInitialState('categories', function () {
            return $this->service->getCategories();
        });
        return new TemplateResponse('myapp', 'main');
    }
}
```

---

## Example 2: API Service Layer

### src/services/ItemService.js

```javascript
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'
import { showError } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'

const baseUrl = generateUrl('/apps/myapp/api')

export async function fetchItems() {
    try {
        const response = await axios.get(`${baseUrl}/items`)
        return response.data
    } catch (error) {
        showError('Failed to load items')
        console.error('fetchItems error:', error)
        return []
    }
}

export async function fetchItem(id) {
    const response = await axios.get(`${baseUrl}/items/${id}`)
    return response.data
}

export async function createItem(data) {
    const response = await axios.post(`${baseUrl}/items`, data)
    return response.data
}

export async function updateItem(id, data) {
    const response = await axios.put(`${baseUrl}/items/${id}`, data)
    return response.data
}

export async function deleteItem(id) {
    await axios.delete(`${baseUrl}/items/${id}`)
}
```

---

## Example 3: OCS API Calls

```typescript
import axios from '@nextcloud/axios'
import { generateOcsUrl } from '@nextcloud/router'

// Fetch OCS data (response wrapped in ocs.data envelope)
async function fetchOcsItems() {
    const url = generateOcsUrl('/apps/myapp/api/v1/items')
    const response = await axios.get(url, {
        headers: { 'OCS-APIRequest': 'true' },
        params: { format: 'json' },
    })
    return response.data.ocs.data
}

// Get server capabilities
async function getCapabilities() {
    const url = generateOcsUrl('/cloud/capabilities')
    const response = await axios.get(url, {
        headers: { 'OCS-APIRequest': 'true' },
        params: { format: 'json' },
    })
    return response.data.ocs.data
}
```

---

## Example 4: File Picker Integration

```vue
<template>
    <div>
        <NcButton @click="openFilePicker">
            {{ t('myapp', 'Select file') }}
        </NcButton>
        <p v-if="selectedPath">Selected: {{ selectedPath }}</p>
    </div>
</template>

<script>
import NcButton from '@nextcloud/vue/components/NcButton'
import { getFilePickerBuilder } from '@nextcloud/dialogs'
import '@nextcloud/dialogs/style.css'

export default {
    components: { NcButton },
    data() {
        return { selectedPath: null }
    },
    methods: {
        async openFilePicker() {
            const picker = getFilePickerBuilder(t('myapp', 'Choose a file'))
                .addMimeTypeFilter('text/plain')
                .addMimeTypeFilter('application/pdf')
                .addButton({
                    label: t('myapp', 'Select'),
                    callback: (nodes) => {
                        this.selectedPath = nodes[0]?.path || null
                    },
                })
                .build()

            await picker.pick()
        },
    },
}
</script>
```

---

## Example 5: WebDAV File Operations from Frontend

```typescript
import { getClient, getDefaultPropfind, resultToNode } from '@nextcloud/files/dav'
import { Permission } from '@nextcloud/files'

const client = getClient()

// List directory
async function listDirectory(path: string) {
    const results = await client.getDirectoryContents(`/files/${getCurrentUser()?.uid}/${path}`, {
        details: true,
        data: getDefaultPropfind(),
    })
    return results.data.map(r => resultToNode(r))
}

// Check permissions before action
function canDelete(node) {
    return (node.permissions & Permission.DELETE) !== 0
}

function canEdit(node) {
    return (node.permissions & Permission.UPDATE) !== 0
}
```

---

## Example 6: Event Bus Communication

```vue
<script>
import { subscribe, unsubscribe, emit } from '@nextcloud/event-bus'

export default {
    mounted() {
        this._fileUploadHandler = (node) => {
            this.items.push(node)
        }
        subscribe('files:node:uploaded', this._fileUploadHandler)
    },
    beforeDestroy() {
        // ALWAYS clean up subscriptions
        unsubscribe('files:node:uploaded', this._fileUploadHandler)
    },
    methods: {
        notifyItemCreated(item) {
            emit('myapp:item:created', item)
        },
    },
}
</script>
```

---

## Example 7: Webpack with Custom Entry Points

```javascript
// webpack.config.js -- extending base config
const path = require('path')
const webpackConfig = require('@nextcloud/webpack-vue-config')

// Add additional entry point for admin settings page
webpackConfig.entry['admin-settings'] = path.join(__dirname, 'src', 'admin-settings.js')

// Add additional entry point for dashboard widget
webpackConfig.entry['dashboard'] = path.join(__dirname, 'src', 'dashboard.js')

module.exports = webpackConfig
```

---

## Example 8: Dark Mode Compatible Styling

```scss
// css/style.scss
.myapp-container {
    padding: 16px;
    background-color: var(--color-main-background);
    color: var(--color-main-text);
}

.myapp-card {
    background-color: var(--color-main-background);
    border: 1px solid var(--color-border);
    border-radius: var(--border-radius-large);
    padding: 16px;
    margin-bottom: 12px;

    &:hover {
        background-color: var(--color-background-hover);
    }

    &--selected {
        background-color: var(--color-primary-element-light);
        border-color: var(--color-primary-element);
    }
}

.myapp-status {
    &--success { color: var(--color-success); }
    &--warning { color: var(--color-warning); }
    &--error { color: var(--color-error); }
    &--info { color: var(--color-info); }
}

.myapp-muted {
    color: var(--color-text-maxcontrast);
    font-size: var(--default-font-size);
}
```

---

## Example 9: Settings Page with NcSettingsSection

```vue
<template>
    <NcSettingsSection :name="t('myapp', 'General')"
        :description="t('myapp', 'Configure your application settings')">
        <NcTextField :value.sync="apiKey"
            :label="t('myapp', 'API Key')"
            :placeholder="t('myapp', 'Enter your API key')" />
        <NcSelect v-model="refreshInterval"
            :options="intervalOptions"
            :placeholder="t('myapp', 'Refresh interval')" />
        <NcButton type="primary"
            :disabled="saving"
            @click="saveSettings">
            {{ t('myapp', 'Save') }}
        </NcButton>
    </NcSettingsSection>
</template>

<script>
import NcSettingsSection from '@nextcloud/vue/components/NcSettingsSection'
import NcTextField from '@nextcloud/vue/components/NcTextField'
import NcSelect from '@nextcloud/vue/components/NcSelect'
import NcButton from '@nextcloud/vue/components/NcButton'
import axios from '@nextcloud/axios'
import { generateUrl } from '@nextcloud/router'
import { showSuccess, showError } from '@nextcloud/dialogs'
import { loadState } from '@nextcloud/initial-state'
import '@nextcloud/dialogs/style.css'

export default {
    components: { NcSettingsSection, NcTextField, NcSelect, NcButton },
    data() {
        const settings = loadState('myapp', 'admin-settings', {})
        return {
            apiKey: settings.apiKey || '',
            refreshInterval: settings.refreshInterval || 15000,
            intervalOptions: [5000, 15000, 30000, 60000],
            saving: false,
        }
    },
    methods: {
        async saveSettings() {
            this.saving = true
            try {
                await axios.put(generateUrl('/apps/myapp/api/settings'), {
                    apiKey: this.apiKey,
                    refreshInterval: this.refreshInterval,
                })
                showSuccess(t('myapp', 'Settings saved'))
            } catch (error) {
                showError(t('myapp', 'Failed to save settings'))
            } finally {
                this.saving = false
            }
        },
    },
}
</script>
```
