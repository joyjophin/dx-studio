/* Autosave and browser recovery. No DOM dependencies; exercised with Node's test runner. */
(function (root) {
  'use strict';
  const copy = value => JSON.parse(JSON.stringify(value));
  const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
  class EditorSession {
    constructor(options) {
      this.api = options.api;
      this.storage = options.storage;
      this.saved = copy(options.values);
      this.desired = copy(options.values);
      this.revision = options.revision;
      this.sourceRevision = options.sourceRevision;
      this.onStatus = options.onStatus || (() => {});
      this.onSaved = options.onSaved || (() => {});
      this.delay = options.delay ?? 1000;
      this.retryDelay = options.retryDelay ?? 5000;
      this.prefix = 'dx-studio:draft:' + options.projectId + ':';
      this.key = this.prefix + (root.crypto?.randomUUID?.() || Date.now() + '-' + Math.random());
      this.timer = null;
      this.active = null;
      this.blocked = false;
      this.disposed = false;
      this.recoveryAvailable = !!this.storage;
    }
    get dirty() { return !same(this.saved, this.desired); }
    status(kind, message) { this.onStatus({kind, message, dirty: this.dirty, recoveryAvailable: this.recoveryAvailable}); }
    remember() {
      if (!this.storage) return;
      try {
        this.storage.setItem(this.key, JSON.stringify({values: this.desired, revision: this.revision,
          source_revision: this.sourceRevision, updated_at: new Date().toISOString()}));
      } catch (_) { this.recoveryAvailable = false; }
    }
    clearOwnDraft() {
      try { this.storage?.removeItem(this.key); } catch (_) { this.recoveryAvailable = false; }
    }
    drafts() {
      if (!this.storage) return [];
      const drafts = [];
      try {
        for (let i = 0; i < this.storage.length; i++) {
          const key = this.storage.key(i);
          if (!key?.startsWith(this.prefix) || key === this.key) continue;
          try {
            const draft = JSON.parse(this.storage.getItem(key));
            if (draft && draft.values && typeof draft.values === 'object' && !Array.isArray(draft.values) &&
                typeof draft.updated_at === 'string' && !same(draft.values, this.saved)) drafts.push({...draft, key});
          } catch (_) { /* A damaged draft must not hide a good one. */ }
        }
      } catch (_) { this.recoveryAvailable = false; }
      return drafts.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
    }
    discard(key) {
      if (!key.startsWith(this.prefix)) throw new Error('This draft belongs to another project');
      this.storage?.removeItem(key);
    }
    changed(values) {
      this.desired = copy(values);
      if (this.dirty) this.remember();
      else this.clearOwnDraft();
      if (this.blocked) return this.status('conflict', 'Save paused: project changed elsewhere');
      this.status(this.dirty ? 'pending' : 'saved', this.dirty ? 'Changes waiting to save' : 'All changes saved');
      this.schedule(this.delay);
    }
    schedule(delay) {
      clearTimeout(this.timer);
      if (!this.disposed && !this.blocked && this.dirty) this.timer = setTimeout(() => this.flush().catch(() => {}), delay);
    }
    flush() {
      clearTimeout(this.timer);
      if (this.active) return this.active;
      if (this.blocked) return Promise.reject(new Error('Reload the saved project before continuing. Your browser draft is retained.'));
      if (this.disposed || !this.dirty) return Promise.resolve();
      this.active = this.saveLoop().finally(() => { this.active = null; });
      return this.active;
    }
    async saveLoop() {
      while (this.dirty && !this.disposed) {
        const snapshot = copy(this.desired);
        this.status('saving', 'Saving…');
        try {
          const result = await this.api('/api/save', {values: snapshot, revision: this.revision, autosave: true});
          this.revision = result.revision;
          this.saved = copy(result.values || snapshot);
          if (same(this.desired, snapshot)) this.desired = copy(this.saved);
          this.onSaved(copy(this.saved), snapshot);
          if (this.dirty) this.remember(); else this.clearOwnDraft();
        } catch (error) {
          this.remember();
          if (error.status === 409) {
            this.blocked = true;
            this.status('conflict', 'Save paused: project changed elsewhere');
          } else {
            this.status('error', this.recoveryAvailable ? 'Save failed · browser draft kept · retrying' : 'Save failed · keep this tab open');
            this.schedule(this.retryDelay);
          }
          throw error;
        }
      }
      this.status('saved', 'All changes saved');
    }
    adopt(values, revision) {
      this.revision = revision;
      this.saved = copy(values);
      this.desired = copy(values);
      this.blocked = false;
      this.clearOwnDraft();
      this.onSaved(copy(values), copy(values));
      this.status('saved', 'All changes saved');
    }
    dispose() { this.disposed = true; clearTimeout(this.timer); }
  }
  root.DXEditorSession = EditorSession;
  if (typeof module !== 'undefined' && module.exports) module.exports = EditorSession;
})(typeof globalThis !== 'undefined' ? globalThis : this);
