CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS economy (
    user_id BIGINT PRIMARY KEY,
    quid INTEGER NOT NULL DEFAULT 0,
    xp_converted INTEGER NOT NULL DEFAULT 0,
    negative_since TIMESTAMP
);

CREATE TABLE IF NOT EXISTS fish_caught (user_id BIGINT, fish_id TEXT, PRIMARY KEY (user_id, fish_id));
CREATE TABLE IF NOT EXISTS user_bait (user_id BIGINT PRIMARY KEY, common_bait INT DEFAULT 0, deep_bait INT DEFAULT 0);

CREATE TABLE IF NOT EXISTS user_owned_rods (
    user_id BIGINT NOT NULL,
    rod_id TEXT NOT NULL,
    PRIMARY KEY (user_id, rod_id)
);

CREATE TABLE IF NOT EXISTS fish_sales (
    user_id BIGINT PRIMARY KEY,
    total_sold INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_rods (
    user_id BIGINT PRIMARY KEY,
    rod_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fish_inventory (
    user_id BIGINT NOT NULL,
    fish_id TEXT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id, fish_id)
);

CREATE TABLE IF NOT EXISTS error_counter (
    id TEXT PRIMARY KEY,
    error_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS feedback_commands (
    command_name TEXT PRIMARY KEY,
    role_that_can_use BIGINT,
    channel_id BIGINT
);

CREATE TABLE IF NOT EXISTS lottery_state (
    id BOOLEAN PRIMARY KEY DEFAULT true,
    ends_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS marriages (
    user1 BIGINT PRIMARY KEY,
    user2 BIGINT UNIQUE NOT NULL,
    married_at TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS amputations (
    user_id BIGINT PRIMARY KEY,
    until TIMESTAMP
);

CREATE TABLE IF NOT EXISTS quick_commands (
    command_name TEXT PRIMARY KEY,
    command_respond TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_unlocks (
    user_id BIGINT PRIMARY KEY,
    crime_pass BOOLEAN DEFAULT false,
    marriage_pass BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS xp (
    user_id BIGINT PRIMARY KEY,
    xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 0,
    short_name TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS xp_optout (
    user_id BIGINT PRIMARY KEY,
    optout BOOLEAN NOT NULL DEFAULT false,
    name TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS yo_global (
    word TEXT PRIMARY KEY,
    yo_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS yo_user (
    user_id BIGINT PRIMARY KEY,
    yo_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS enemy_cooldowns (
    user_id BIGINT,
    enemy TEXT,
    last_fight TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id, enemy)
);

ALTER TABLE user_unlocks 
ADD COLUMN IF NOT EXISTS sigshark_rod BOOLEAN DEFAULT FALSE;

ALTER TABLE user_unlocks 
ADD COLUMN IF NOT EXISTS philosopher_soul BOOLEAN DEFAULT FALSE;

ALTER TABLE user_unlocks 
ADD COLUMN IF NOT EXISTS house_edge BOOLEAN DEFAULT FALSE;

ALTER TABLE user_unlocks
ADD COLUMN IF NOT EXISTS heaven_used BOOLEAN DEFAULT false;

ALTER TABLE user_unlocks
ADD COLUMN IF NOT EXISTS cologne BOOLEAN DEFAULT FALSE;

ALTER TABLE user_unlocks
ADD COLUMN IF NOT EXISTS bone_emblem BOOLEAN DEFAULT FALSE;

ALTER TABLE user_bait ADD COLUMN IF NOT EXISTS rare_bait INT DEFAULT 0;
ALTER TABLE user_bait ADD COLUMN IF NOT EXISTS legendary_bait INT DEFAULT 0;
ALTER TABLE user_unlocks ADD COLUMN IF NOT EXISTS fish_bag_upgrade INT DEFAULT 0;
ALTER TABLE fish_sales ADD COLUMN IF NOT EXISTS last_sell TIMESTAMPTZ;

ALTER TABLE user_unlocks ADD COLUMN IF NOT EXISTS spark_of_hatred BOOLEAN DEFAULT FALSE;
ALTER TABLE user_unlocks ADD COLUMN IF NOT EXISTS shark_liver BOOLEAN DEFAULT FALSE;
ALTER TABLE user_unlocks ADD COLUMN IF NOT EXISTS workers_tear BOOLEAN DEFAULT FALSE;
ALTER TABLE user_unlocks ADD COLUMN IF NOT EXISTS snow_globe BOOLEAN DEFAULT FALSE;
ALTER TABLE user_unlocks ADD COLUMN IF NOT EXISTS bone_key_cutter BOOLEAN DEFAULT FALSE;
ALTER TABLE user_unlocks ADD COLUMN IF NOT EXISTS outlandish_key BOOLEAN DEFAULT FALSE;
ALTER TABLE user_unlocks ADD COLUMN IF NOT EXISTS anti_vlad_joined BOOLEAN DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS evil_quid (
    user_id BIGINT PRIMARY KEY,
    amount  INTEGER NOT NULL DEFAULT 0
);
 
CREATE TABLE IF NOT EXISTS hell_progress (
    user_id BIGINT NOT NULL,
    layer_name TEXT NOT NULL,
    cleared_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, layer_name)
);
 
CREATE TABLE IF NOT EXISTS hell_progress_meta (
    user_id BIGINT PRIMARY KEY,
    gluttony_discarded INTEGER NOT NULL DEFAULT 0,
    greed_contributed INTEGER NOT NULL DEFAULT 0
);
 
CREATE TABLE IF NOT EXISTS greed_pool (
    id INTEGER PRIMARY KEY DEFAULT 1,
    total INTEGER NOT NULL DEFAULT 0,
    CHECK (id = 1)
);
INSERT INTO greed_pool (id, total) VALUES (1, 0) ON CONFLICT DO NOTHING;
 
CREATE TABLE IF NOT EXISTS enemy_cooldowns (
    user_id BIGINT NOT NULL,
    enemy TEXT NOT NULL,
    last_fight TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (user_id, enemy)
);

UPDATE user_inventory SET expires_at = NULL WHERE expires_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS finance_bank (
    user_id BIGINT PRIMARY KEY,
    savings INT DEFAULT 0,
    loan_amount INT DEFAULT 0,
    loan_taken_at TIMESTAMPTZ,
    cd_amount INT DEFAULT 0,
    cd_matures_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS finance_stock_prices (
    ticker TEXT PRIMARY KEY,
    price INT NOT NULL
);

CREATE TABLE IF NOT EXISTS finance_portfolio (
    user_id BIGINT,
    ticker TEXT,
    shares INT NOT NULL,
    avg_cost INT DEFAULT 0,
    PRIMARY KEY (user_id, ticker)
);

CREATE TABLE IF NOT EXISTS finance_index_investments (
    user_id BIGINT,
    fund TEXT,
    amount INT NOT NULL,
    invested_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, fund)
);

CREATE TABLE IF NOT EXISTS finance_transactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    type TEXT,
    amount INT,
    note TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS finance_net_worth_log (
    user_id BIGINT,
    recorded_at TIMESTAMPTZ,
    net_worth INT
);

CREATE TABLE IF NOT EXISTS finance_margin (
    user_id     BIGINT PRIMARY KEY,
    margin_used INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS finance_stock_frac (
    ticker TEXT PRIMARY KEY,
    frac    DOUBLE PRECISION NOT NULL DEFAULT 0.0
);

ALTER TABLE user_unlocks ADD COLUMN IF NOT EXISTS parthenon_entry BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE finance_portfolio
    ADD COLUMN IF NOT EXISTS bought_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS pets (
    user_id BIGINT PRIMARY KEY,
    species TEXT NOT NULL,
    name TEXT NOT NULL,
    level INT NOT NULL DEFAULT 1,
    xp INT NOT NULL DEFAULT 0,
    hunger INT NOT NULL DEFAULT 100,
    happiness INT NOT NULL DEFAULT 100,
    health INT NOT NULL DEFAULT 100,
    age_days INT NOT NULL DEFAULT 0,
    adopted_at TIMESTAMPTZ DEFAULT NOW(),
    last_fed TIMESTAMPTZ,
    last_played TIMESTAMPTZ,
    last_trained TIMESTAMPTZ,
    is_wild BOOLEAN NOT NULL DEFAULT FALSE,
    is_dead BOOLEAN NOT NULL DEFAULT FALSE,
    outfit TEXT,                           
    accessory TEXT,                       
    background TEXT,           
    battles_won INT NOT NULL DEFAULT 0,
    battles_lost INT NOT NULL DEFAULT 0,
    tricks_learned TEXT[] NOT NULL DEFAULT '{}'
);

ALTER TABLE pets ADD COLUMN IF NOT EXISTS skill_xp INT DEFAULT 0;

CREATE TABLE IF NOT EXISTS pet_inventory (
    user_id BIGINT NOT NULL,
    item_id TEXT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id, item_id)
);

CREATE TABLE IF NOT EXISTS pet_wild_encounters (
    user_id BIGINT PRIMARY KEY,
    last_encounter TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS pet_battle_log (
    id SERIAL PRIMARY KEY,
    challenger BIGINT NOT NULL,
    opponent BIGINT NOT NULL,
    winner BIGINT,
    fought_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS parthenon_stats (
    user_id BIGINT PRIMARY KEY,
    clears  INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_jobs (
    user_id BIGINT PRIMARY KEY,
    job_id TEXT NOT NULL,
    hired_at TIMESTAMPTZ DEFAULT NOW(),
    last_collected TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS social_gifts (
    id SERIAL PRIMARY KEY,
    sender_id BIGINT NOT NULL,
    receiver_id BIGINT NOT NULL,
    item TEXT NOT NULL,
    message TEXT,
    sent_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS social_rep (
    giver_id BIGINT NOT NULL,
    receiver_id BIGINT NOT NULL,
    given_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (giver_id, receiver_id)
);

CREATE TABLE IF NOT EXISTS social_rep_totals (
    user_id BIGINT PRIMARY KEY,
    rep INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS social_wills (
    user_id BIGINT PRIMARY KEY,
    beneficiary BIGINT NOT NULL,
    amount INT NOT NULL,
    message TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS social_feuds (
    user1 BIGINT NOT NULL,
    user2 BIGINT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user1, user2)
);

CREATE TABLE IF NOT EXISTS social_stats (
    user_id BIGINT PRIMARY KEY,
    gifts_given INT NOT NULL DEFAULT 0,
    gifts_received INT NOT NULL DEFAULT 0,
    rep_given INT NOT NULL DEFAULT 0,
    rep_received INT NOT NULL DEFAULT 0,
    feuds_started INT NOT NULL DEFAULT 0,
    feuds_won INT NOT NULL DEFAULT 0,
    marriages INT NOT NULL DEFAULT 0,
    divorces INT NOT NULL DEFAULT 0,
    children INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS adoptions (
    child   BIGINT PRIMARY KEY,
    parent1 BIGINT NOT NULL,
    parent2 BIGINT,
    CHECK (child <> parent1),
    CHECK (parent2 IS NULL OR child <> parent2),
    CHECK (parent2 IS NULL OR parent1 <> parent2)
);


ALTER TABLE economy
    ADD COLUMN IF NOT EXISTS streak INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_claim_date DATE,
    ADD COLUMN IF NOT EXISTS last_weekly TIMESTAMPTZ;

ALTER TABLE user_unlocks
    ADD COLUMN IF NOT EXISTS golden_gate_key BOOLEAN NOT NULL DEFAULT FALSE;

DELETE FROM user_achievements WHERE achievement_id IN ('gambling.blackjack_21', 'gambling.coin_flipper', 'xp.gain.15', 'pet.pet', 'pet.level_up', 'social.generous', 'pets.healed_pet', 'pets.wild_tamed');
DELETE FROM achievements WHERE id IN ('gambling.blackjack_21', 'gambling.coin_flipper', 'xp.gain.15', 'pet.pet', 'pet.level_up', 'social.generous', 'pets.healed_pet', 'pets.wild_tamed');
DELETE FROM achievement_progress WHERE achievement_id IN ('gambling.coin_flipper', 'xp.gain.15', 'social.generous', 'pets.healed_pet', 'pets.wild_tamed');

CREATE TABLE IF NOT EXISTS achievements (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL,
    points INT DEFAULT 0,
    hidden BOOLEAN DEFAULT false,
    repeatable BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_achievements (
    user_id BIGINT,
    achievement_id TEXT,
    unlocked_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, achievement_id),
    FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS achievement_progress (
    user_id BIGINT,
    achievement_id TEXT,
    progress INT DEFAULT 0,
    target INT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, achievement_id),
    FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS achievement_events (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    achievement_id TEXT,
    source TEXT NOT NULL,
    value INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_inventory (
    user_id BIGINT,
    item_id TEXT,
    expires_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, item_id)
);

CREATE TABLE IF NOT EXISTS wordle_games (
    user_id BIGINT,
    date DATE,
    solved BOOLEAN DEFAULT false,
    attempts INT DEFAULT 0,
    guesses TEXT[] DEFAULT '{}',
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, date)
);

CREATE TABLE IF NOT EXISTS wordle_stats (
    user_id BIGINT PRIMARY KEY,
    wins INT DEFAULT 0,
    losses INT DEFAULT 0,
    streak INT DEFAULT 0,
    max_streak INT DEFAULT 0
);

ALTER TABLE user_inventory ADD COLUMN IF NOT EXISTS quantity INT NOT NULL DEFAULT 1;

CREATE OR REPLACE FUNCTION set_negative_since()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.quid < 0 AND OLD.quid >= 0 THEN
    NEW.negative_since := NOW();
  ELSIF NEW.quid >= 0 THEN
    NEW.negative_since := NULL;
  END IF;
  RETURN NEW;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_trigger WHERE tgname = 'economy_negative_tracker'
  ) THEN
    CREATE TRIGGER economy_negative_tracker
    BEFORE UPDATE OF quid ON economy
    FOR EACH ROW
    EXECUTE FUNCTION set_negative_since();
  END IF;
END;
$$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='economy' AND column_name='last_daily'
    ) THEN
        ALTER TABLE economy ADD COLUMN last_daily TIMESTAMP WITH TIME ZONE;
    ELSE
        ALTER TABLE economy ALTER COLUMN last_daily TYPE TIMESTAMP WITH TIME ZONE;
    END IF;
END$$;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name='enemy_cooldowns'
        AND column_name='last_fight'
        AND data_type='timestamp without time zone'
    ) THEN
        ALTER TABLE enemy_cooldowns
        ALTER COLUMN last_fight TYPE TIMESTAMPTZ;
    END IF;
END$$;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM finance_bank WHERE savings > 0) THEN
        INSERT INTO economy (user_id, quid)
        SELECT user_id, savings
        FROM finance_bank
        WHERE savings > 0
        ON CONFLICT (user_id) DO UPDATE
            SET quid = economy.quid + EXCLUDED.quid;

        INSERT INTO finance_transactions (user_id, type, amount, note)
        SELECT user_id, 'refund', savings, 'savings deposit feature removed'
        FROM finance_bank
        WHERE savings > 0;

        UPDATE finance_bank
        SET savings = 0
        WHERE savings > 0;
    END IF;
END$$;