-- Maps table backup
CREATE TABLE IF NOT EXISTS maps_backup (
    id SERIAL PRIMARY KEY,
    country_id INTEGER REFERENCES countries_backup(id),
    map_url TEXT,
    map_type TEXT,
    width INTEGER,
    height INTEGER,
    last_updated INTEGER
);

-- Insert this data with:
-- \copy maps_backup(id, country_id, map_url, map_type, width, height, last_updated) FROM 'maps_data.csv' WITH CSV HEADER;