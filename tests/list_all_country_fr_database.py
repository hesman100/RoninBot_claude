import sqlite3

def fetch_all_country_names():
    db_path = "country_game/database/countries.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT name FROM countries")
        country_names = [row[0] for row in cursor.fetchall()]
        return country_names
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
    finally:
        conn.close()

# Example usage
if __name__ == "__main__":
    countries = fetch_all_country_names()
    print("Country Names:", countries)
