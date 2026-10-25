/**
 * Plugin UI contract — the single source of truth for every surface a
 * plugin may reach.  The renderer registries (`ui/ea_ui.ts`,
 * `ui/components.ts`) and the distributable SDK are generated/validated
 * against this file; do not add a second alias list anywhere else.
 */
export declare const PLUGIN_SDK_VERSION = "1.0.0";
export declare const PLUGIN_UI_CONTRACT_VERSION = 1;
/** External `ea-ui-*` class -> first-party class(es). */
export declare const EA_UI_CLASS_MAP: {
    readonly "ea-ui-card": "settings-card";
    readonly "ea-ui-panel": "settings-panel";
    readonly "ea-ui-row": "settings-item-row";
    readonly "ea-ui-row-info": "settings-item-info";
    readonly "ea-ui-row-title": "settings-item-title";
    readonly "ea-ui-row-desc": "settings-item-desc";
    readonly "ea-ui-row-control": "settings-item-control";
    readonly "ea-ui-section-title": "settings-section-title";
    readonly "ea-ui-nav-item": "settings-nav-item";
    readonly "ea-ui-divider": "settings-item-divider";
    readonly "ea-ui-dropdown": "settings-dropdown-wrap";
    readonly "ea-ui-dropdown-wrap": "settings-dropdown-wrap";
    readonly "ea-ui-dropdown-trigger": "settings-dropdown-trigger";
    readonly "ea-ui-dropdown-menu": "settings-dropdown";
    readonly "ea-ui-dropdown-item": "settings-dropdown-item";
    readonly "ea-ui-dropdown-chevron": "settings-dropdown-chevron";
    readonly "ea-ui-input": "settings-text-input";
    readonly "ea-ui-textarea": "setting-rich-text";
    readonly "ea-ui-color-picker": "settings-color-picker-wrap";
    readonly "ea-ui-color-picker-trigger": "settings-color-picker-trigger";
    readonly "ea-ui-color-picker-dot": "settings-color-picker-dot";
    readonly "ea-ui-color-picker-value": "settings-color-picker-value";
    readonly "ea-ui-color-picker-panel": "settings-color-picker-panel";
    readonly "ea-ui-color-picker-sv": "settings-color-picker-sv";
    readonly "ea-ui-color-picker-cursor": "settings-color-picker-cursor";
    readonly "ea-ui-color-picker-hue": "settings-color-picker-hue";
    readonly "ea-ui-color-picker-hue-thumb": "settings-color-picker-hue-thumb";
    readonly "ea-ui-color-picker-rgb": "settings-color-picker-rgb";
    readonly "ea-ui-color-picker-chan": "settings-color-picker-chan";
    readonly "ea-ui-color-picker-hex": "settings-text-input settings-color-picker-hex";
    readonly "ea-ui-switch": "toggle-switch";
    readonly "ea-ui-switch-slider": "toggle-slider";
    readonly "ea-ui-switch-sm": "toggle-switch toggle-sm";
    readonly "ea-ui-button": "btn";
    readonly "ea-ui-button-sm": "btn btn-sm";
    readonly "ea-ui-icon-button": "btn-icon";
    readonly "ea-ui-button-danger": "btn-icon btn-icon--danger";
};
export type EaUiClassAlias = keyof typeof EA_UI_CLASS_MAP;
/** Module-level controls exposed through `EA_UI_MODULES`. */
export declare const EA_UI_MODULE_NAMES: readonly ["ea-ui-animate", "ea-ui-breadcrumbs", "ea-ui-context-menu", "ea-ui-dialog", "ea-ui-error-card", "ea-ui-icon", "ea-ui-info-widget", "ea-ui-input-expand", "ea-ui-log-view", "ea-ui-permission", "ea-ui-progress", "ea-ui-scrollbar", "ea-ui-select", "ea-ui-shortcut", "ea-ui-slash-commands", "ea-ui-splash", "ea-ui-tab-tooltip", "ea-ui-toast", "ea-ui-tool-body", "ea-ui-tool-meta", "ea-ui-tooltip", "ea-ui-transition", "ea-ui-view"];
export type EaUiModuleName = (typeof EA_UI_MODULE_NAMES)[number];
/** JSON-safe RPC methods a plugin worker may invoke. */
export declare const EA_UI_RPC_NAMES: readonly ["context-menu.show", "context-menu.close", "context-menu.render-items", "context-menu.item-html", "dialog.confirm", "dialog.prompt", "dialog.alert", "tooltip.set-model", "tooltip.show-at", "tooltip.hide", "tab-tooltip.format-file-size", "tab-tooltip.format-timestamp", "tab-tooltip.build", "tab-tooltip.apply", "toast.show", "permission.show", "icon.platform-html", "icon.platform-src", "icon.search-engine-src", "icon.asset-html", "view.switch-to", "view.current", "transition.step", "transition.default-duration", "splash.hide", "tool-body.diff", "tool-body.terminal", "tool-body.web-results", "tool-body.web-fetched", "tool-body.pre", "tool-meta.for", "tool-meta.label", "tool-meta.icon", "tool-meta.source", "tool-meta.is-plugin", "tool-meta.is-hidden", "tool-meta.count", "shortcut.format", "shortcut.lookup", "shortcut.augment-title", "shortcut.platform-label", "slash-commands.find", "slash-commands.parse", "slash-commands.matching", "error-card.render", "select.render", "select.bind", "progress.bar", "log-view.mount", "log-view.destroy", "crumbs.render", "input-expand.attach", "scrollbar.init", "animate.show", "animate.hide", "animate.remove", "animate.show-view", "animate.hide-view", "info-widget.chip", "info-widget.card", "color-picker.render", "color-picker.bind"];
export type EaUiRpcName = (typeof EA_UI_RPC_NAMES)[number];
/** RPC methods safe to expose to an iframe (no parent-DOM selectors). */
export declare const EA_UI_IFRAME_RPC_ALLOWLIST: readonly ["dialog.confirm", "dialog.prompt", "dialog.alert", "tab-tooltip.format-file-size", "tab-tooltip.format-timestamp", "tab-tooltip.build", "toast.show", "permission.show", "icon.platform-html", "icon.platform-src", "icon.search-engine-src", "icon.asset-html", "view.switch-to", "view.current", "splash.hide", "tool-body.diff", "tool-body.terminal", "tool-body.web-results", "tool-body.web-fetched", "tool-body.pre", "tool-meta.for", "tool-meta.label", "tool-meta.icon", "tool-meta.source", "tool-meta.is-plugin", "tool-meta.is-hidden", "tool-meta.count", "shortcut.format", "shortcut.lookup", "shortcut.augment-title", "shortcut.platform-label", "slash-commands.find", "slash-commands.parse", "slash-commands.matching", "select.render", "progress.bar", "crumbs.render", "info-widget.chip", "info-widget.card"];
/** Stable slot ids a plugin may override declaratively or dynamically. */
export declare const PLUGIN_SLOTS: {
    readonly sessionRow: "session.row";
    readonly modelProviderRow: "model.provider-row";
};
export type PluginSlotId = (typeof PLUGIN_SLOTS)[keyof typeof PLUGIN_SLOTS];
/** Contribution kinds accepted by the backend and renderer. */
export declare const PLUGIN_CONTRIBUTION_KINDS: readonly ["theme", "settings", "context_menu", "search_mode", "ui_override", "js_module"];
export type PluginContributionKind = (typeof PLUGIN_CONTRIBUTION_KINDS)[number];
