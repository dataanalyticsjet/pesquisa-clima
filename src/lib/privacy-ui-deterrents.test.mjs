import assert from "node:assert/strict";
import test from "node:test";

import { installPrivacyUiDeterrents, removePrivacyUiDeterrents } from "./privacy-ui-deterrents.ts";

class FakeEventTarget {
  listeners = [];

  addEventListener(type, listener, options) {
    this.listeners.push({ type, listener, options });
  }

  removeEventListener(type, listener, options) {
    this.listeners = this.listeners.filter(
      (entry) => entry.type !== type || entry.listener !== listener || entry.options !== options,
    );
  }

  dispatch(type, event) {
    for (const entry of [...this.listeners]) {
      if (entry.type === type) entry.listener.call(this, event);
    }
  }

  count(type) {
    return this.listeners.filter((entry) => entry.type === type).length;
  }
}

function setupMeta(contents) {
  const fakeWindow = new FakeEventTarget();
  const fakeDocument = new FakeEventTarget();
  const entries = contents.map((content) => ({
    getAttribute(name) {
      return name === "content" ? content : name === "name" ? "privacy-ui-deterrents" : null;
    },
  }));
  fakeDocument.querySelectorAll = () => {
    entries.item = (index) => entries[index] ?? null;
    return entries;
  };
  Object.defineProperty(globalThis, "window", { configurable: true, value: fakeWindow });
  Object.defineProperty(globalThis, "document", { configurable: true, value: fakeDocument });
  return { fakeWindow, fakeDocument };
}

function keyboardEvent({ key, code, ctrlKey = false, metaKey = false, shiftKey = false, altKey = false, target } = {}) {
  let prevented = false;
  let stopped = false;
  const event = {
    key,
    code,
    ctrlKey,
    metaKey,
    shiftKey,
    altKey,
    target,
    preventDefault() {
      prevented = true;
    },
    stopImmediatePropagation() {
      stopped = true;
    },
  };
  return {
    event,
    wasPrevented: () => prevented,
    wasStopped: () => stopped,
  };
}

test("server rendering does not access DOM globals", () => {
  delete globalThis.window;
  delete globalThis.document;
  assert.doesNotThrow(() => installPrivacyUiDeterrents()());
});

test("disabled, missing, or duplicated meta tags register no deterrence listeners", () => {
  for (const contents of [[], ["disabled"], ["enabled", "enabled"]]) {
    const { fakeWindow, fakeDocument } = setupMeta(contents);
    const cleanup = installPrivacyUiDeterrents();
    assert.equal(fakeWindow.count("keydown"), 0);
    assert.equal(fakeDocument.count("contextmenu"), 0);
    cleanup();
  }
});

test("enabled meta blocks only the requested shortcuts in capture phase", () => {
  const { fakeWindow, fakeDocument } = setupMeta(["enabled"]);
  const cleanup = installPrivacyUiDeterrents();
  const cases = [
    { key: "F12", code: "F12" },
    { key: "c", code: "KeyC", ctrlKey: true, shiftKey: true },
    { key: "c", code: "KeyC", metaKey: true, shiftKey: true },
    { key: "i", code: "KeyI", ctrlKey: true, shiftKey: true },
    { key: "i", code: "KeyI", metaKey: true, shiftKey: true },
    { key: "j", code: "KeyJ", ctrlKey: true, shiftKey: true },
    { key: "j", code: "KeyJ", metaKey: true, shiftKey: true },
    { key: "u", code: "KeyU", ctrlKey: true },
    { key: "u", code: "KeyU", metaKey: true },
  ];

  const keydownListener = fakeWindow.listeners.find((entry) => entry.type === "keydown");
  const contextListener = fakeDocument.listeners.find((entry) => entry.type === "contextmenu");
  assert.ok(keydownListener);
  assert.ok(contextListener);
  assert.equal(keydownListener.options, true);
  assert.equal(contextListener.options, true);

  for (const shortcut of cases) {
    const result = keyboardEvent(shortcut);
    fakeWindow.dispatch("keydown", result.event);
    assert.equal(result.wasPrevented(), true, JSON.stringify(shortcut));
    assert.equal(result.wasStopped(), true, JSON.stringify(shortcut));
  }

  let contextPrevented = false;
  let contextStopped = false;
  fakeDocument.dispatch("contextmenu", {
    preventDefault() {
      contextPrevented = true;
    },
    stopImmediatePropagation() {
      contextStopped = true;
    },
  });
  assert.equal(contextPrevented, true);
  assert.equal(contextStopped, true);
  cleanup();
});

test("ordinary shortcuts, accessible keys, and normal input typing remain usable", () => {
  const { fakeWindow } = setupMeta(["enabled"]);
  const cleanup = installPrivacyUiDeterrents();
  const cases = [
    { key: "c", code: "KeyC", ctrlKey: true },
    { key: "v", code: "KeyV", ctrlKey: true },
    { key: "x", code: "KeyX", ctrlKey: true },
    { key: "a", code: "KeyA", ctrlKey: true },
    { key: "f", code: "KeyF", ctrlKey: true },
    { key: "p", code: "KeyP", ctrlKey: true },
    { key: "s", code: "KeyS", ctrlKey: true },
    { key: "Tab", code: "Tab" },
    { key: "Enter", code: "Enter" },
    { key: "Escape", code: "Escape" },
    { key: "a", code: "KeyA", target: { tagName: "INPUT" } },
  ];

  for (const shortcut of cases) {
    const result = keyboardEvent(shortcut);
    fakeWindow.dispatch("keydown", result.event);
    assert.equal(result.wasPrevented(), false, JSON.stringify(shortcut));
    assert.equal(result.wasStopped(), false, JSON.stringify(shortcut));
  }
  cleanup();
});

test("multiple installations share listeners and clean up after the last unmount", () => {
  const { fakeWindow, fakeDocument } = setupMeta(["enabled"]);
  const firstCleanup = installPrivacyUiDeterrents();
  const secondCleanup = installPrivacyUiDeterrents();
  assert.equal(fakeWindow.count("keydown"), 1);
  assert.equal(fakeDocument.count("contextmenu"), 1);

  firstCleanup();
  assert.equal(fakeWindow.count("keydown"), 1);
  secondCleanup();
  secondCleanup();
  assert.equal(fakeWindow.count("keydown"), 0);
  assert.equal(fakeDocument.count("contextmenu"), 0);

  const thirdCleanup = installPrivacyUiDeterrents();
  removePrivacyUiDeterrents();
  assert.equal(fakeWindow.count("keydown"), 0);
  thirdCleanup();
});
