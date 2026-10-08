/*
 * Frontend inspection deterrent only. Not a security boundary.
 * Disable by removing the privacy-ui-deterrents meta tag or changing its content,
 * then reload the page.
 */

let activeCleanup: (() => void) | null = null;
let activeGeneration: symbol | null = null;
let installationCount = 0;

function isEnabledByMeta(): boolean {
  if (typeof document === "undefined") return false;
  const entries = document.querySelectorAll('meta[name="privacy-ui-deterrents"]');
  return entries.length === 1 && entries.item(0)?.getAttribute("content") === "enabled";
}

function isInspectionShortcut(event: KeyboardEvent): boolean {
  const key = event.key.toLowerCase();
  const codeKey = event.code.toLowerCase().replace(/^key/, "");
  const normalizedKey = key === "unidentified" ? codeKey : key;
  const hasSinglePlatformModifier = event.ctrlKey !== event.metaKey;

  if (normalizedKey === "f12") {
    return !event.ctrlKey && !event.metaKey && !event.altKey && !event.shiftKey;
  }

  if (!hasSinglePlatformModifier || event.altKey) return false;
  if (event.shiftKey) {
    return normalizedKey === "c" || normalizedKey === "i" || normalizedKey === "j";
  }
  return normalizedKey === "u";
}

export function installPrivacyUiDeterrents(): () => void {
  if (typeof window === "undefined" || typeof document === "undefined" || !isEnabledByMeta()) {
    return () => undefined;
  }

  if (!activeCleanup) {
    const generation = Symbol("privacy-ui-deterrents");
    const capture = true;
    activeGeneration = generation;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isInspectionShortcut(event)) return;
      event.preventDefault();
      event.stopImmediatePropagation();
    };
    const handleContextMenu = (event: MouseEvent) => {
      event.preventDefault();
      event.stopImmediatePropagation();
    };

    window.addEventListener("keydown", handleKeyDown, capture);
    document.addEventListener("contextmenu", handleContextMenu, capture);
    activeCleanup = () => {
      window.removeEventListener("keydown", handleKeyDown, capture);
      document.removeEventListener("contextmenu", handleContextMenu, capture);
      if (activeGeneration === generation) {
        activeCleanup = null;
        activeGeneration = null;
        installationCount = 0;
      }
    };
  }

  const generation = activeGeneration;
  installationCount += 1;
  let isCleanedUp = false;
  return () => {
    if (isCleanedUp || generation === null || generation !== activeGeneration) return;
    isCleanedUp = true;
    installationCount -= 1;
    if (installationCount === 0) activeCleanup?.();
  };
}

export function removePrivacyUiDeterrents(): void {
  if (!activeCleanup) return;
  const cleanup = activeCleanup;
  activeCleanup = null;
  activeGeneration = null;
  installationCount = 0;
  cleanup();
}
