# @encre/plugin-ui-sdk

One SDK for every Encre Agent plugin frontend surface. It merges the control
class aliases, module-level components, EA-UI RPC methods, slots and
declarative contribution builders into one import.

```ts
import {
  definePluginUi,
  ui,
  actions,
  call,
  setSlot,
  PLUGIN_SLOTS,
} from "./vendor/encre-plugin-ui-sdk/index.js";

definePluginUi({
  render: () => `
    <div class="ea-ui-card" style="padding:12px">
      <div class="ea-ui-row">
        <div class="ea-ui-row-info">
          <div class="ea-ui-row-title">Hello from the plugin</div>
          <div class="ea-ui-row-desc">This card uses first-party classes.</div>
        </div>
        <button class="ea-ui-button" data-plugin-action>Run</button>
      </div>
    </div>`,
});
```

## Surfaces

- `EA_UI_CLASS_MAP` / `EA_UI_CLASS_ALIASES`: stable `ea-ui-*` classes.
- `EA_UI_MODULE_NAMES`: module-level controls exposed by the host.
- `EA_UI_RPC_NAMES` / `call()`: host capabilities. Worker modules can call
  every method; iframe providers get the safe subset listed in
  `EA_UI_IFRAME_RPC_ALLOWLIST`.
- `PLUGIN_SLOTS`: first-party slots that may be overridden (`setSlot` or the
  declarative `ui.override` builder).
- `actions.send()`: the unified backend action channel.
- `ui.settingsSection()`, `ui.settingsPage()`, `ui.contextMenu()`,
  `ui.searchMode()`, `ui.theme()`, `ui.override()`, `ui.jsModule()`:
  declarations the backend can register without shipping raw markup.

## Runtimes

- **Worker module**: the host injects `Encre`; `render()` replaces the
  plugin's own root, `setSlot()` takes a slot.
- **Iframe provider**: the host injects `window.encre`; the SDK routes
  `call()` / `setSlot()` / `actions.send()` through the parent bridge with a
  per-provider identity. Iframe UIs own their document, so `render()` is not
  used there.

## Build

```sh
node sdk/build.mjs
```

The CLI copies this package into a scaffolded plugin's `ui/vendor/` and
bundles `ui/src/index.ts` into `ui/plugin.js` during `encre-plugin build`.
Unknown `ea-ui-*` aliases or RPC names fail the build before a wheel is
created.
