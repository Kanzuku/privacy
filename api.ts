/**
 * ME — The Life Game | API Service
 * Typed client for all backend endpoints
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api/v1';

// ─── Core fetch wrapper ──────────────────────────────────────────────────────

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = await AsyncStorage.getItem('access_token');

  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers ?? {}),
    },
  });

  if (res.status === 401) {
    await refreshTokens();
    return request(path, options); // retry once
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? 'Request failed');
  }

  return res.json() as Promise<T>;
}

async function refreshTokens() {
  const refresh = await AsyncStorage.getItem('refresh_token');
  if (!refresh) throw new Error('Not authenticated');
  const data = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  }).then(r => r.json());
  await AsyncStorage.setItem('access_token', data.access_token);
  await AsyncStorage.setItem('refresh_token', data.refresh_token);
}

const get  = <T>(path: string) => request<T>(path, { method: 'GET' });
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body) });
const put  = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'PUT', body: JSON.stringify(body) });

// ─── Auth ────────────────────────────────────────────────────────────────────

export const authApi = {
  register: (email: string, password: string) =>
    post<{ access_token: string; refresh_token: string }>('/auth/register', { email, password }),

  login: (email: string, password: string) =>
    post<{ access_token: string; refresh_token: string }>('/auth/login', { email, password }),

  logout: async () => {
    await AsyncStorage.multiRemove(['access_token', 'refresh_token']);
  },
};

// ─── Profile ─────────────────────────────────────────────────────────────────

export const profileApi = {
  get:     () => get<UserProfile>('/profile/'),
  upsert:  (data: Partial<UserProfile>) => put('/profile/', data),
  analyze: () => get<UserModelAnalysis>('/profile/analyze'),
};

// ─── Game Stats ───────────────────────────────────────────────────────────────

export const statsApi = {
  get:     () => get<GameStats>('/stats/'),
  history: (days = 30) => get<StatSnapshot[]>(`/stats/history?days=${days}`),
};

// ─── Quests ───────────────────────────────────────────────────────────────────

export const questsApi = {
  generate: (params: { quest_type: string; focus_area?: string; count?: number }) =>
    post<{ quests: Quest[] }>('/quests/generate', params),

  getActive: () => get<Quest[]>('/quests/active'),

  complete: (questId: string) =>
    post<QuestReward>(`/quests/${questId}/complete`),

  fail: (questId: string) =>
    post(`/quests/${questId}/fail`),
};

// ─── Decision Engine ──────────────────────────────────────────────────────────

export const decisionsApi = {
  simulate: (question: string, context?: Record<string, unknown>) =>
    post<DecisionResult>('/decisions/simulate', { question, context }),

  choose: (decisionId: string, scenarioId: string) =>
    post('/decisions/choose', { decision_id: decisionId, scenario_id: scenarioId }),

  history: (limit = 20) => get<DecisionSummary[]>(`/decisions/history?limit=${limit}`),
};

// ─── Simulation & Events ──────────────────────────────────────────────────────

export const simulationApi = {
  generateFuture: () => post<FutureSimulation>('/simulation/future'),
  getLatestFuture: () => get<FutureSimulation>('/simulation/future/latest'),
  generateEvent: () => post<LifeEvent>('/simulation/event/generate'),
  chooseEvent: (eventId: string, optionId: string) =>
    post<EventConsequence>(`/simulation/event/${eventId}/choose?option_id=${optionId}`),
};

// ─── Types ────────────────────────────────────────────────────────────────────

export interface UserProfile {
  age?: number; location?: string; job?: string; industry?: string;
  income?: number; savings?: number; health?: number; energy?: number;
  happiness?: number; discipline?: number; habit_sleep?: number;
  habit_sport?: number; habit_learning?: number; risk_tolerance?: number;
  behavior_type?: string; onboarding_done?: boolean;
}

export interface GameStats {
  level: number; total_xp: number;
  stat_health: number; stat_energy: number; stat_wealth: number;
  stat_knowledge: number; stat_happiness: number; stat_discipline: number;
  stat_career: number; stat_social: number;
}

export interface StatSnapshot extends GameStats { snapshot_at: string; }

export interface Quest {
  id: string; type: string; title: string; description: string;
  action_steps?: { step: number; action: string; duration: string; done: boolean }[];
  xp_reward: number; stat_rewards?: Record<string, number>;
  buff_rewards?: { name: string; effect: string; duration_hours: number }[];
  due_at?: string; status: string; difficulty?: number; category?: string;
}

export interface QuestReward {
  message: string; xp_gained: number; new_level?: number;
  stat_changes?: Record<string, number>; buffs_activated?: unknown[];
}

export interface DecisionScenario {
  id: string; label: string; probability: number; description: string;
  financial_impact_monthly: number; financial_impact_12mo: number;
  stress_level: number; career_impact: string; lifestyle_impact: string;
  stat_changes: Record<string, number>; timeline: string;
}

export interface DecisionResult {
  decision_id: string; scenarios: DecisionScenario[];
  risk_score: number; risk_factors: { factor: string; weight: number }[];
  recommendation: 'yes' | 'no' | 'conditional';
  recommendation_rationale: string;
}

export interface DecisionSummary {
  id: string; question: string; risk_score: number;
  recommendation: string; chosen_scenario?: string; created_at: string;
}

export interface FutureSimulation {
  simulation_id: string;
  baseline_path: { summary: string; yearly: YearlyProjection[] };
  optimized_path: { summary: string; yearly: YearlyProjection[] };
  delta_at_year_10: { income_difference_monthly: number; summary: string };
}

export interface YearlyProjection {
  year: number; age: number; income_monthly: number; savings_total: number;
  health_score: number; happiness_score: number; career_level: string; key_event: string;
}

export interface LifeEvent {
  event_id: string; title: string; description: string; category: string;
  urgency: string; options: { id: string; label: string; description: string; risk_level: number }[];
  expires_hours: number;
}

export interface EventConsequence {
  immediate_outcome: string; short_term_outcome: string;
  long_term_impact: string; stat_changes: Record<string, number>;
  xp_gained: number; narrative: string; lesson: string;
}

export interface UserModelAnalysis {
  life_stage: string; archetype: string; archetype_description: string;
  main_problems: { problem: string; severity: number; evidence: string }[];
  hidden_risks: { risk: string; probability_12mo: number; trigger: string }[];
  growth_opportunities: { opportunity: string; effort_level: number; payoff_timeline: string }[];
  key_insight: string;
}
