-- EKARUS scheduler database (SQLite)

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    institute     TEXT NOT NULL DEFAULT '',
    password_hash TEXT NOT NULL,
    is_admin      INTEGER NOT NULL DEFAULT 0,
    verified      INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);

-- One row per observing night the admin opens for proposals.
-- status: open (can be requested), closed (not offered), booked (allocated)
CREATE TABLE IF NOT EXISTS nights (
    id          INTEGER PRIMARY KEY,
    date        TEXT NOT NULL UNIQUE,          -- YYYY-MM-DD, the evening the night starts
    status      TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed', 'booked')),
    note        TEXT NOT NULL DEFAULT '',
    proposal_id INTEGER REFERENCES proposals(id)
);

-- status: submitted, accepted, rejected, withdrawn
CREATE TABLE IF NOT EXISTS proposals (
    id            INTEGER PRIMARY KEY,
    code          TEXT NOT NULL UNIQUE,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    title         TEXT NOT NULL,
    summary       TEXT NOT NULL,
    science_case  TEXT NOT NULL,
    mode          TEXT NOT NULL,
    observers     TEXT NOT NULL DEFAULT '',
    constraints   TEXT NOT NULL DEFAULT '',
    min_nights    INTEGER NOT NULL DEFAULT 1,
    notes         TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'submitted'
                  CHECK (status IN ('submitted', 'accepted', 'rejected', 'withdrawn')),
    admin_message TEXT NOT NULL DEFAULT '',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS proposal_targets (
    id          INTEGER PRIMARY KEY,
    proposal_id INTEGER NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    ra          TEXT NOT NULL DEFAULT '',
    dec         TEXT NOT NULL DEFAULT '',
    mag         TEXT NOT NULL DEFAULT ''
);

-- Nights requested by a proposal
CREATE TABLE IF NOT EXISTS proposal_nights (
    proposal_id INTEGER NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    night_id    INTEGER NOT NULL REFERENCES nights(id) ON DELETE CASCADE,
    PRIMARY KEY (proposal_id, night_id)
);

-- Timeline shown on each proposal (submitted, accepted, ...)
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY,
    proposal_id INTEGER NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    created_at  TEXT NOT NULL,
    actor_id    INTEGER REFERENCES users(id),
    action      TEXT NOT NULL,
    message     TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_proposals_user ON proposals(user_id);
CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
CREATE INDEX IF NOT EXISTS idx_nights_date ON nights(date);
