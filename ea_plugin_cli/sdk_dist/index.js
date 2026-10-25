// sdk/src/contract.ts
var PLUGIN_SDK_VERSION = "1.0.0";
var PLUGIN_UI_CONTRACT_VERSION = 1;
var EA_UI_CLASS_MAP = {
  "ea-ui-card": "settings-card",
  "ea-ui-panel": "settings-panel",
  "ea-ui-row": "settings-item-row",
  "ea-ui-row-info": "settings-item-info",
  "ea-ui-row-title": "settings-item-title",
  "ea-ui-row-desc": "settings-item-desc",
  "ea-ui-row-control": "settings-item-control",
  "ea-ui-section-title": "settings-section-title",
  "ea-ui-nav-item": "settings-nav-item",
  "ea-ui-divider": "settings-item-divider",
  "ea-ui-dropdown": "settings-dropdown-wrap",
  "ea-ui-dropdown-wrap": "settings-dropdown-wrap",
  "ea-ui-dropdown-trigger": "settings-dropdown-trigger",
  "ea-ui-dropdown-menu": "settings-dropdown",
  "ea-ui-dropdown-item": "settings-dropdown-item",
  "ea-ui-dropdown-chevron": "settings-dropdown-chevron",
  "ea-ui-input": "settings-text-input",
  "ea-ui-textarea": "setting-rich-text",
  "ea-ui-color-picker": "settings-color-picker-wrap",
  "ea-ui-color-picker-trigger": "settings-color-picker-trigger",
  "ea-ui-color-picker-dot": "settings-color-picker-dot",
  "ea-ui-color-picker-value": "settings-color-picker-value",
  "ea-ui-color-picker-panel": "settings-color-picker-panel",
  "ea-ui-color-picker-sv": "settings-color-picker-sv",
  "ea-ui-color-picker-cursor": "settings-color-picker-cursor",
  "ea-ui-color-picker-hue": "settings-color-picker-hue",
  "ea-ui-color-picker-hue-thumb": "settings-color-picker-hue-thumb",
  "ea-ui-color-picker-rgb": "settings-color-picker-rgb",
  "ea-ui-color-picker-chan": "settings-color-picker-chan",
  "ea-ui-color-picker-hex": "settings-text-input settings-color-picker-hex",
  "ea-ui-switch": "toggle-switch",
  "ea-ui-switch-slider": "toggle-slider",
  "ea-ui-switch-sm": "toggle-switch toggle-sm",
  "ea-ui-button": "btn",
  "ea-ui-button-sm": "btn btn-sm",
  "ea-ui-icon-button": "btn-icon",
  "ea-ui-button-danger": "btn-icon btn-icon--danger"
};
var EA_UI_MODULE_NAMES = [
  "ea-ui-animate",
  "ea-ui-breadcrumbs",
  "ea-ui-context-menu",
  "ea-ui-dialog",
  "ea-ui-error-card",
  "ea-ui-icon",
  "ea-ui-info-widget",
  "ea-ui-input-expand",
  "ea-ui-log-view",
  "ea-ui-permission",
  "ea-ui-progress",
  "ea-ui-scrollbar",
  "ea-ui-select",
  "ea-ui-shortcut",
  "ea-ui-slash-commands",
  "ea-ui-splash",
  "ea-ui-tab-tooltip",
  "ea-ui-toast",
  "ea-ui-tool-body",
  "ea-ui-tool-meta",
  "ea-ui-tooltip",
  "ea-ui-transition",
  "ea-ui-view"
];
var EA_UI_RPC_NAMES = [
  "context-menu.show",
  "context-menu.close",
  "context-menu.render-items",
  "context-menu.item-html",
  "dialog.confirm",
  "dialog.prompt",
  "dialog.alert",
  "tooltip.set-model",
  "tooltip.show-at",
  "tooltip.hide",
  "tab-tooltip.format-file-size",
  "tab-tooltip.format-timestamp",
  "tab-tooltip.build",
  "tab-tooltip.apply",
  "toast.show",
  "permission.show",
  "icon.platform-html",
  "icon.platform-src",
  "icon.search-engine-src",
  "icon.asset-html",
  "view.switch-to",
  "view.current",
  "transition.step",
  "transition.default-duration",
  "splash.hide",
  "tool-body.diff",
  "tool-body.terminal",
  "tool-body.web-results",
  "tool-body.web-fetched",
  "tool-body.pre",
  "tool-meta.for",
  "tool-meta.label",
  "tool-meta.icon",
  "tool-meta.source",
  "tool-meta.is-plugin",
  "tool-meta.is-hidden",
  "tool-meta.count",
  "shortcut.format",
  "shortcut.lookup",
  "shortcut.augment-title",
  "shortcut.platform-label",
  "slash-commands.find",
  "slash-commands.parse",
  "slash-commands.matching",
  "error-card.render",
  "select.render",
  "select.bind",
  "progress.bar",
  "log-view.mount",
  "log-view.destroy",
  "crumbs.render",
  "input-expand.attach",
  "scrollbar.init",
  "animate.show",
  "animate.hide",
  "animate.remove",
  "animate.show-view",
  "animate.hide-view",
  "info-widget.chip",
  "info-widget.card",
  "color-picker.render",
  "color-picker.bind"
];
var EA_UI_IFRAME_RPC_ALLOWLIST = [
  "dialog.confirm",
  "dialog.prompt",
  "dialog.alert",
  "tab-tooltip.format-file-size",
  "tab-tooltip.format-timestamp",
  "tab-tooltip.build",
  "toast.show",
  "permission.show",
  "icon.platform-html",
  "icon.platform-src",
  "icon.search-engine-src",
  "icon.asset-html",
  "view.switch-to",
  "view.current",
  "splash.hide",
  "tool-body.diff",
  "tool-body.terminal",
  "tool-body.web-results",
  "tool-body.web-fetched",
  "tool-body.pre",
  "tool-meta.for",
  "tool-meta.label",
  "tool-meta.icon",
  "tool-meta.source",
  "tool-meta.is-plugin",
  "tool-meta.is-hidden",
  "tool-meta.count",
  "shortcut.format",
  "shortcut.lookup",
  "shortcut.augment-title",
  "shortcut.platform-label",
  "slash-commands.find",
  "slash-commands.parse",
  "slash-commands.matching",
  "select.render",
  "progress.bar",
  "crumbs.render",
  "info-widget.chip",
  "info-widget.card"
];
var PLUGIN_SLOTS = {
  sessionRow: "session.row",
  modelProviderRow: "model.provider-row"
};
var PLUGIN_CONTRIBUTION_KINDS = [
  "theme",
  "settings",
  "context_menu",
  "search_mode",
  "ui_override",
  "js_module"
];

// sdk/src/index.ts
var MAX_HTML = 256 * 1024;
var IFRAME_CALL_TIMEOUT_MS = 15e3;
var _seq = 0;
var _pending = /* @__PURE__ */ new Map();
var _bridgeInstalled = false;
var _iframeListeners = /* @__PURE__ */ new Map();
function globalObject() {
  return globalThis;
}
function workerHost() {
  const g = globalObject();
  const host2 = g.Encre;
  return host2 && typeof host2 === "object" ? host2 : null;
}
function iframeHost() {
  const g = globalObject();
  const host2 = g.window?.encre;
  return host2 && typeof host2 === "object" ? host2 : null;
}
function host() {
  return workerHost() || iframeHost();
}
function isWorkerRuntime() {
  return workerHost() !== null;
}
function isIframeRuntime() {
  return workerHost() === null && iframeHost() !== null;
}
function checkHtml(html) {
  if (typeof html !== "string" || !html) throw new Error("Encre plugin SDK: html must be a non-empty string");
  if (html.length > MAX_HTML) throw new Error(`Encre plugin SDK: html exceeds ${MAX_HTML} bytes`);
  return html;
}
function installIframeBridge() {
  const h = iframeHost();
  if (!h || _bridgeInstalled) return h;
  _bridgeInstalled = true;
  const g = globalObject();
  g.window?.addEventListener("message", (event) => {
    const data = event.data;
    if (!data || data.source !== "encre-plugin-host") return;
    if (data.type === "eaui.result" && typeof data.id === "number") {
      const pending = _pending.get(data.id);
      if (!pending) return;
      _pending.delete(data.id);
      clearTimeout(pending.timer);
      if (data.ok) pending.resolve(data.value);
      else pending.reject(new Error(data.error || "EA-UI call failed"));
      return;
    }
    if (data.type === "event" && typeof data.name === "string") {
      const listeners = _iframeListeners.get(data.name);
      if (listeners) {
        for (const fn of Array.from(listeners)) {
          try {
            fn(data.detail);
          } catch {
          }
        }
      }
    }
  });
  return h;
}
function render(html) {
  const safe = checkHtml(html);
  const h = workerHost();
  if (!h?.ui?.render) {
    throw new Error("Encre plugin SDK: render() is only available in a worker module; iframe UIs own their DOM");
  }
  h.ui.render(safe);
}
function setSlot(slot, html) {
  if (!slot) throw new Error("Encre plugin SDK: slot id is required");
  const safe = checkHtml(html);
  const worker = workerHost();
  if (worker?.ui?.setSlot) {
    worker.ui.setSlot(slot, safe);
    return;
  }
  const frame = installIframeBridge();
  if (!frame?.post) throw new Error("Encre plugin SDK: setSlot() needs a worker or iframe bridge");
  frame.post("ui.setSlot", { slot, html: safe });
}
async function call(name, ...args) {
  if (!name) throw new Error("Encre plugin SDK: EA-UI method name is required");
  const worker = workerHost();
  if (worker?.eaui?.call) {
    return await worker.eaui.call(name, ...args);
  }
  const frame = installIframeBridge();
  if (!frame?.post) throw new Error("Encre plugin SDK: call() needs a worker or iframe bridge");
  if (!EA_UI_IFRAME_RPC_ALLOWLIST.includes(name)) {
    throw new Error(
      `Encre plugin SDK: '${name}' is not available to iframe providers (element-scoped RPCs require a worker)`
    );
  }
  const id = ++_seq;
  return await new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      _pending.delete(id);
      reject(new Error(`Encre plugin SDK: '${name}' timed out`));
    }, IFRAME_CALL_TIMEOUT_MS);
    _pending.set(id, { resolve, reject, timer });
    frame.post("eaui.call", { id, name, args });
  });
}
var actions = {
  /** Send a typed action to the owning plugin's backend handler. */
  send(kind, action, payload, plugin) {
    if (!kind || !action) throw new Error("Encre plugin SDK: action kind and id are required");
    const worker = workerHost();
    if (worker?.actions?.send) {
      worker.actions.send(kind, plugin || worker.plugin || "", action, payload || {});
      return;
    }
    const frame = installIframeBridge();
    if (!frame?.post) throw new Error("Encre plugin SDK: actions.send() needs a worker or iframe bridge");
    frame.post("action", { kind, action, payload: payload || {} });
  }
};
function on(eventName, cb) {
  const worker = workerHost();
  if (worker?.on) {
    worker.on(eventName, cb);
    return;
  }
  const frame = installIframeBridge();
  if (!frame) throw new Error("Encre plugin SDK: on() needs a host bridge");
  let set = _iframeListeners.get(eventName);
  if (!set) {
    set = /* @__PURE__ */ new Set();
    _iframeListeners.set(eventName, set);
  }
  set.add(cb);
}
function validateContribution(value) {
  if (!value || typeof value !== "object") throw new Error("Encre plugin SDK: contribution must be an object");
  if (!PLUGIN_CONTRIBUTION_KINDS.includes(value.kind)) {
    throw new Error(`Encre plugin SDK: unknown contribution kind '${String(value.kind)}'`);
  }
  if (!value.spec || typeof value.spec !== "object" || Array.isArray(value.spec)) {
    throw new Error("Encre plugin SDK: contribution.spec must be an object");
  }
  return value;
}
var ui = {
  settingsSection(input) {
    return validateContribution({ kind: "settings", spec: { page: "general", ...input } });
  },
  settingsPage(input) {
    return validateContribution({
      kind: "settings",
      spec: { page: "new", page_id: input.pageId, title: input.title, icon: input.icon, rows: input.rows }
    });
  },
  contextMenu(input) {
    return validateContribution({ kind: "context_menu", spec: { ...input } });
  },
  searchMode(input) {
    return validateContribution({ kind: "search_mode", spec: { ...input } });
  },
  theme(css) {
    return validateContribution({ kind: "theme", spec: { css } });
  },
  override(input) {
    if (!input.slot || !input.template) throw new Error("Encre plugin SDK: override needs slot + template");
    return validateContribution({ kind: "ui_override", spec: { ...input } });
  },
  jsModule(input) {
    if (!input.path && !input.code) throw new Error("Encre plugin SDK: jsModule needs path or code");
    return validateContribution({ kind: "js_module", spec: { ...input } });
  }
};
function definePluginUi(definition) {
  if (!definition || typeof definition !== "object") throw new Error("Encre plugin SDK: definition is required");
  if (definition.onAction) {
    on("ui_result", (detail) => definition.onAction?.({ kind: "ui_result", data: detail }));
    on("eaui_event", (detail) => definition.onAction?.({ kind: "eaui_event", data: detail }));
  }
  if (typeof definition.render === "function" && isWorkerRuntime()) {
    render(definition.render());
  }
  if (definition.slots) {
    for (const [slot, producer] of Object.entries(definition.slots)) {
      if (typeof producer === "function") setSlot(slot, producer());
    }
  }
  return definition;
}
export {
  EA_UI_CLASS_MAP,
  EA_UI_IFRAME_RPC_ALLOWLIST,
  EA_UI_MODULE_NAMES,
  EA_UI_RPC_NAMES,
  PLUGIN_CONTRIBUTION_KINDS,
  PLUGIN_SDK_VERSION,
  PLUGIN_SLOTS,
  PLUGIN_UI_CONTRACT_VERSION,
  actions,
  call,
  definePluginUi,
  host,
  iframeHost,
  isIframeRuntime,
  isWorkerRuntime,
  on,
  render,
  setSlot,
  ui,
  workerHost
};
