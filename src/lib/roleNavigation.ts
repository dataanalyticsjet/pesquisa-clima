const managementRoles = new Set(["MANAGEMENT", "SURVEY_ADMIN", "ADMIN"]);
const feishuPostLoginKey = "pesquisaclima:feishu-post-login";

export function canAccessManagement(roles: readonly string[]) {
  return roles.some((role) => managementRoles.has(role));
}

export function getAuthenticatedLandingPath(roles: readonly string[]): "/management" | "/home" {
  return canAccessManagement(roles) ? "/management" : "/home";
}

export function markFeishuPostLoginRedirect() {
  try {
    window.sessionStorage.setItem(feishuPostLoginKey, "1");
  } catch {
    // Navigation still succeeds if the browser blocks session storage.
  }
}

export function hasFeishuPostLoginRedirect() {
  try {
    return window.sessionStorage.getItem(feishuPostLoginKey) === "1";
  } catch {
    return false;
  }
}

export function clearFeishuPostLoginRedirect() {
  try {
    window.sessionStorage.removeItem(feishuPostLoginKey);
  } catch {
    // No persistent auth data is stored here; the flag is only a navigation hint.
  }
}
