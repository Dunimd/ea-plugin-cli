/**
 * Encre Plugin UI SDK — one entry point for every plugin-facing surface.
 *
 * It merges the four things plugins previously had to discover separately:
 *   - the `ea-ui-*` control classes (EA_UI_CLASS_MAP),
 *   - module-level components (EA_UI_MODULE_NAMES),
 *   - the JSON-safe RPC methods (EA_UI_RPC_NAMES),
 *   - slots / declarative contributions (PLUGIN_SLOTS, builders below).
 *
 * The same module runs in both supported plugin frontends:
 *   - worker modules injected with `globalThis.Encre`;
 *   - iframe providers injected with `window.encre`.
 */
import { EA_UI_CLASS_MAP, EA_UI_MODULE_NAMES, EA_UI_RPC_NAMES, EA_UI_IFRAME_RPC_ALLOWLIST, PLUGIN_SLOTS, PLUGIN_CONTRIBUTION_KINDS, PLUGIN_SDK_VERSION, PLUGIN_UI_CONTRACT_VERSION, type EaUiClassAlias, type EaUiModuleName, type EaUiRpcName, type PluginSlotId, type PluginContributionKind } from "./contract.js";
export { EA_UI_CLASS_MAP, EA_UI_MODULE_NAMES, EA_UI_RPC_NAMES, EA_UI_IFRAME_RPC_ALLOWLIST, PLUGIN_SLOTS, PLUGIN_CONTRIBUTION_KINDS, PLUGIN_SDK_VERSION, PLUGIN_UI_CONTRACT_VERSION, };
export type { EaUiClassAlias, EaUiModuleName, EaUiRpcName, PluginSlotId, PluginContributionKind };
export interface PluginWorkerHost {
    /** Injected by the worker preamble; authorises actions.send. */
    plugin?: string;
    ui?: {
        render?: (html: string) => unknown;
        setSlot?: (slot: string, html: string) => unknown;
    };
    eaui?: {
        call?: (name: string, ...args: unknown[]) => Promise<unknown>;
    };
    actions?: {
        send?: (kind: string, plugin: string, action: string, payload?: unknown) => unknown;
    };
    on?: (event: string, cb: (detail: unknown) => void) => void;
}
export interface PluginIframeHost {
    base?: string;
    provider?: Record<string, unknown>;
    post?: (type: string, payload?: unknown) => void;
    call?: (name: string, ...args: unknown[]) => Promise<unknown>;
    on?: (event: string, cb: (detail: unknown) => void) => void;
}
export interface PluginUiDefinition {
    plugin?: string;
    /** Worker modules only: replace the plugin's own root with this markup. */
    render?: () => string;
    /** Named slot overrides: slot id -> markup producer. */
    slots?: Partial<Record<PluginSlotId, () => string>>;
    /** Backend `plugin_ui_result` / EA-UI callback sink. */
    onAction?: (event: {
        kind: string;
        action?: string;
        data?: unknown;
        ok?: boolean;
    }) => void;
}
export interface PluginSettingsRow {
    id: string;
    type: "toggle" | "select" | "text" | "number" | "textarea" | "color" | "button";
    label: string;
    desc?: string;
    key?: string;
    options?: {
        id: string;
        label: string;
    }[];
    default?: string | boolean;
    placeholder?: string;
    min?: number;
    max?: number;
    step?: number;
    rows?: number;
    action?: string;
    button_label?: string;
}
export interface PluginContribution<T = Record<string, unknown>> {
    kind: PluginContributionKind;
    spec: T;
}
export declare function workerHost(): PluginWorkerHost | null;
export declare function iframeHost(): PluginIframeHost | null;
export declare function host(): PluginWorkerHost | PluginIframeHost | null;
export declare function isWorkerRuntime(): boolean;
export declare function isIframeRuntime(): boolean;
/** Replace the plugin's own worker root with `html`. */
export declare function render(html: string): void;
/** Take over one first-party slot with `html`. */
export declare function setSlot(slot: string, html: string): void;
/** Invoke an EA-UI method by its stable contract name. */
export declare function call<T = unknown>(name: EaUiRpcName, ...args: unknown[]): Promise<T>;
export declare const actions: {
    /** Send a typed action to the owning plugin's backend handler. */
    send(kind: string, action: string, payload?: Record<string, unknown>, plugin?: string): void;
};
/** Subscribe to host events (`ui_result`, `contributions_changed`, `eaui_event`). */
export declare function on(eventName: string, cb: (detail: unknown) => void): void;
export declare const ui: {
    settingsSection(input: {
        title: string;
        icon?: string;
        rows: PluginSettingsRow[];
    }): PluginContribution;
    settingsPage(input: {
        pageId: string;
        title: string;
        icon?: string;
        rows: PluginSettingsRow[];
    }): PluginContribution;
    contextMenu(input: {
        label: string;
        surface?: string;
        icon?: string;
        danger?: boolean;
        action?: string;
    }): PluginContribution;
    searchMode(input: {
        id: string;
        label: string;
        description?: string;
        icon?: string;
    }): PluginContribution;
    theme(css: string): PluginContribution;
    override(input: {
        slot: string;
        template: string;
        priority?: number;
    }): PluginContribution;
    jsModule(input: {
        path?: string;
        code?: string;
    }): PluginContribution;
};
/**
 * Define a worker/iframe plugin UI.  Worker modules call this at module scope;
 * iframe providers can use the same file (render() is skipped where the host
 * owns the document).
 */
export declare function definePluginUi(definition: PluginUiDefinition): PluginUiDefinition;
