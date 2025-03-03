-- Hints table backup
CREATE TABLE IF NOT EXISTS hints_backup (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES countries_backup(id),
    hint_type TEXT,
    hint_text TEXT
);

-- Insert this data with:
-- \copy hints_backup(id, country_id, hint_type, hint_text) FROM 'hints_data.csv' WITH CSV HEADER;