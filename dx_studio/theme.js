/* Shared browser preference, applied in <head> before the workspace paints. */
(() => {
  const key = 'dx-studio:theme:v1';
  const valid = value => ['system', 'light', 'dark'].includes(value) ? value : 'system';
  const system = window.matchMedia?.('(prefers-color-scheme: dark)');
  let preference = 'system';
  try { preference = valid(window.localStorage.getItem(key)); } catch (_) {}

  function apply() {
    const resolved = preference === 'system' ? (system?.matches ? 'dark' : 'light') : preference;
    document.documentElement.dataset.theme = resolved;
    document.documentElement.dataset.themePreference = preference;
    document.documentElement.style.colorScheme = resolved;
    for (const picker of document.querySelectorAll('[data-theme-picker]')) picker.value = preference;
  }

  function bind() {
    for (const picker of document.querySelectorAll('[data-theme-picker]')) {
      picker.addEventListener('change', () => {
        preference = valid(picker.value);
        try { window.localStorage.setItem(key, preference); } catch (_) {}
        apply();
      });
    }
    apply();
  }

  apply();
  system?.addEventListener('change', () => { if (preference === 'system') apply(); });
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) {
      preference = valid(event.newValue);
      apply();
    }
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind, {once:true});
  else bind();
})();
