-- Create table for storing user statistics for the country game
CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER,
    game_mode TEXT,
    total INTEGER DEFAULT 0,
    correct INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, game_mode)
);
