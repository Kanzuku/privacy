-- ============================================================
-- ME — The Life Game | PostgreSQL Schema
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ------------------------------------------------------------
-- USERS
-- ------------------------------------------------------------
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    last_active_at  TIMESTAMPTZ,
    is_premium      BOOLEAN DEFAULT FALSE,
    streak_days     INT DEFAULT 0,
    last_streak_at  DATE
);

-- ------------------------------------------------------------
-- USER PROFILE  (structured life model)
-- ------------------------------------------------------------
CREATE TABLE user_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    -- Demographics
    age             INT CHECK (age BETWEEN 13 AND 120),
    location        TEXT,
    -- Professional
    job             TEXT,
    industry        TEXT,
    income          NUMERIC(12,2),        -- monthly, USD
    savings         NUMERIC(12,2),
    -- Lifestyle scores (0–100)
    health          SMALLINT CHECK (health BETWEEN 0 AND 100),
    energy          SMALLINT CHECK (energy BETWEEN 0 AND 100),
    happiness       SMALLINT CHECK (happiness BETWEEN 0 AND 100),
    discipline      SMALLINT CHECK (discipline BETWEEN 0 AND 100),
    -- Habits (1–10)
    habit_sleep     SMALLINT CHECK (habit_sleep BETWEEN 1 AND 10),
    habit_sport     SMALLINT CHECK (habit_sport BETWEEN 1 AND 10),
    habit_learning  SMALLINT CHECK (habit_learning BETWEEN 1 AND 10),
    -- Personality
    risk_tolerance  SMALLINT CHECK (risk_tolerance BETWEEN 1 AND 10),
    behavior_type   TEXT CHECK (behavior_type IN ('planner','impulsive','balanced','risk_taker','conservative')),
    -- Meta
    onboarding_done BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- SKILLS  (many per user)
-- ------------------------------------------------------------
CREATE TABLE user_skills (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    level       SMALLINT DEFAULT 1 CHECK (level BETWEEN 1 AND 10),
    xp          INT DEFAULT 0,
    category    TEXT,       -- tech, soft, creative, physical
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- GOALS
-- ------------------------------------------------------------
CREATE TABLE user_goals (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    title        TEXT NOT NULL,
    description  TEXT,
    category     TEXT,    -- career, financial, health, social, personal
    target_date  DATE,
    progress     SMALLINT DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    status       TEXT DEFAULT 'active' CHECK (status IN ('active','completed','abandoned')),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- GAME STATS  (the RPG layer)
-- ------------------------------------------------------------
CREATE TABLE game_stats (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    level       INT DEFAULT 1,
    total_xp    INT DEFAULT 0,
    -- Core stats (0–100)
    stat_health     SMALLINT DEFAULT 50,
    stat_energy     SMALLINT DEFAULT 50,
    stat_wealth     SMALLINT DEFAULT 50,
    stat_knowledge  SMALLINT DEFAULT 50,
    stat_happiness  SMALLINT DEFAULT 50,
    stat_discipline SMALLINT DEFAULT 50,
    stat_career     SMALLINT DEFAULT 50,
    stat_social     SMALLINT DEFAULT 50,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- STAT HISTORY  (for charts & future sim)
-- ------------------------------------------------------------
CREATE TABLE stat_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    snapshot_at TIMESTAMPTZ DEFAULT NOW(),
    level       INT,
    stat_health     SMALLINT,
    stat_energy     SMALLINT,
    stat_wealth     SMALLINT,
    stat_knowledge  SMALLINT,
    stat_happiness  SMALLINT,
    stat_discipline SMALLINT,
    stat_career     SMALLINT,
    stat_social     SMALLINT
);

-- ------------------------------------------------------------
-- QUESTS
-- ------------------------------------------------------------
CREATE TYPE quest_type AS ENUM ('daily','weekly','main','skill');
CREATE TYPE quest_status AS ENUM ('active','completed','failed','expired');

CREATE TABLE quests (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    type            quest_type NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    action_steps    JSONB,           -- [{step, measurable, done}]
    xp_reward       INT DEFAULT 0,
    stat_rewards    JSONB,           -- {"health": +5, "energy": +3}
    buff_rewards    JSONB,           -- {"focus": "+10%", "duration": "24h"}
    status          quest_status DEFAULT 'active',
    due_at          TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    ai_generated    BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- DECISIONS
-- ------------------------------------------------------------
CREATE TABLE decisions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    question        TEXT NOT NULL,
    context         JSONB,
    scenarios       JSONB NOT NULL,  -- array of scenario objects
    risk_score      SMALLINT CHECK (risk_score BETWEEN 0 AND 100),
    risk_factors    JSONB,
    recommendation  TEXT CHECK (recommendation IN ('yes','no','conditional')),
    chosen_scenario TEXT,            -- which scenario user selected
    outcome_tracked BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- RANDOM EVENTS
-- ------------------------------------------------------------
CREATE TYPE event_status AS ENUM ('pending','resolved','ignored','expired');

CREATE TABLE life_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,
    category    TEXT CHECK (category IN ('job','financial','social','health','relocation','opportunity','risk')),
    options     JSONB NOT NULL,   -- [{label, consequence_preview}]
    chosen_option TEXT,
    consequence JSONB,            -- simulated outcome after choice
    status      event_status DEFAULT 'pending',
    expires_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- AI MEMORY (vector embeddings for personalization)
-- ------------------------------------------------------------
CREATE TABLE memory_embeddings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    embedding   vector(1536),
    memory_type TEXT CHECK (memory_type IN ('decision','goal','event','preference','habit')),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memory_embedding ON memory_embeddings USING ivfflat (embedding vector_cosine_ops);

-- ------------------------------------------------------------
-- FUTURE SIMULATION  (viral feature)
-- ------------------------------------------------------------
CREATE TABLE future_simulations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    baseline_path   JSONB,    -- "if nothing changes" — yearly projections
    optimized_path  JSONB,    -- "if you follow the plan" — yearly projections
    horizon_years   SMALLINT DEFAULT 10,
    generated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- SUBSCRIPTIONS / MONETIZATION
-- ------------------------------------------------------------
CREATE TYPE plan_type AS ENUM ('free','premium','enterprise');

CREATE TABLE subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    plan            plan_type DEFAULT 'free',
    stripe_id       TEXT,
    starts_at       TIMESTAMPTZ,
    ends_at         TIMESTAMPTZ,
    auto_renew      BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------
CREATE INDEX idx_quests_user_status   ON quests(user_id, status);
CREATE INDEX idx_decisions_user       ON decisions(user_id);
CREATE INDEX idx_events_user_status   ON life_events(user_id, status);
CREATE INDEX idx_stat_history_user    ON stat_history(user_id, snapshot_at DESC);
CREATE INDEX idx_skills_user          ON user_skills(user_id);
CREATE INDEX idx_goals_user_status    ON user_goals(user_id, status);

-- ------------------------------------------------------------
-- AUTO-UPDATE updated_at
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;

CREATE TRIGGER trg_users_updated        BEFORE UPDATE ON users          FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_profiles_updated     BEFORE UPDATE ON user_profiles  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_goals_updated        BEFORE UPDATE ON user_goals     FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_game_stats_updated   BEFORE UPDATE ON game_stats     FOR EACH ROW EXECUTE FUNCTION update_updated_at();
