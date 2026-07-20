const BASE = ''; // vite proxy handles /api → localhost:8000

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  feed: (limit = 50) =>
    apiFetch<import('../types/tap').Tweet[]>(`/api/feed?limit=${limit}`),

  stir: () =>
    apiFetch<import('../types/tap').StirEntry[]>('/api/stir'),

  status: () =>
    apiFetch<import('../types/tap').EngineStatus>('/api/status'),

  health: () =>
    apiFetch<import('../types/tap').HealthStatus>('/health'),

  stats: () =>
    apiFetch<import('../types/tap').Stats>('/api/stats'),

  ssot: () =>
    apiFetch<import('../types/tap').SsotSnapshot>('/api/ssot'),

  dpa: () =>
    apiFetch<import('../types/tap').DpaFrame>('/api/dpa'),

  followup: () =>
    apiFetch<import('../types/tap').FollowUpState>('/api/followup'),

  events: (limit = 50) =>
    apiFetch<unknown[]>(`/api/events?limit=${limit}`),

  properties: () =>
    apiFetch<unknown[]>('/api/properties'),

  generateOptions: () =>
    apiFetch<{ followup: import('../types/tap').FollowUpOption; message: string }>(
      '/api/generate-options',
      { method: 'POST' }
    ),

  // NOTE: /api/select uses query param, NOT JSON body
  selectOption: (choice: 'A' | 'B') =>
    apiFetch<{ choice: string; probe_text: string; ready_to_post: boolean }>(
      `/api/select?choice=${choice}`,
      { method: 'POST' }
    ),

  postSelected: () =>
    apiFetch<{ status: string; message: string }>('/api/post', { method: 'POST' }),

  resetEngine: () =>
    apiFetch<{ status: string; was_running: boolean; message: string }>(
      '/api/reset',
      { method: 'POST' }
    ),

  forceFetch: () =>
    apiFetch<{ status: string; count: number }>('/api/fetch', { method: 'POST' }),

  // NOTE: /api/mock uses query param, NOT JSON body
  mockReply: (text: string) =>
    apiFetch<{ status: string; tweet_id: string; text: string }>(
      `/api/mock?text=${encodeURIComponent(text)}`,
      { method: 'POST' }
    ),

  // Manual property confirmation
  confirmProperty: (key: string, value: string) =>
    apiFetch<{ status: string; key: string; value: string }>(
      `/api/confirm_property?key=${encodeURIComponent(key)}&value=${encodeURIComponent(value)}`,
      { method: 'POST' }
    ),

  // --- Technique Selection ---
  getTechniques: () =>
    apiFetch<{ techniques: import('../types/tap').AttackTechnique[]; source: string }>(
      '/api/techniques'
    ),

  selectTechnique: (techniqueId: string, customPrompt?: string) => {
    const params = new URLSearchParams({ technique_id: techniqueId });
    if (customPrompt) params.append('custom_prompt', customPrompt);
    return apiFetch<{ status: string; technique_id: string; message: string }>(
      `/api/technique/select?${params.toString()}`,
      { method: 'POST' }
    );
  },

  getSelectedTechnique: () =>
    apiFetch<import('../types/tap').SelectedTechnique>('/api/technique/selected'),

  getTechniqueRelations: (techniqueId: string) =>
    apiFetch<{ relations: import('../types/tap').TechniqueRelations }>(
      `/api/technique/relations/${techniqueId}`
    ),
};