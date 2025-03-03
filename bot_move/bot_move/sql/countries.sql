-- Countries table backup
CREATE TABLE IF NOT EXISTS countries_backup (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    capital TEXT,
    region TEXT,
    subregion TEXT,
    population BIGINT,
    area DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    iso2_code TEXT,
    iso3_code TEXT,
    currency TEXT,
    language TEXT,
    description TEXT,
    last_updated INTEGER,
    not_a_country BOOLEAN DEFAULT FALSE
);

-- Insert this data with:
-- \copy countries_backup(id, name, capital, region, subregion, population, area, latitude, longitude, iso2_code, iso3_code, currency, language, description, last_updated, not_a_country) FROM 'countries_data.csv' WITH CSV HEADER;