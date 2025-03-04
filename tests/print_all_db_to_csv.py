import sqlite3
import csv

def export_countries_to_csv(db_path, csv_file_path):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Execute SQL query to fetch all data from the countries table
        cursor.execute("SELECT * FROM countries")
        rows = cursor.fetchall()

        # Get column names from the cursor
        column_names = [description[0] for description in cursor.description]

        # Write to CSV file
        with open(csv_file_path, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # Write header
            writer.writerow(column_names)
            # Write data
            writer.writerows(rows)

        print(f"Data exported successfully to {csv_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

# Usage example
if __name__ == "__main__":
    db_path = "country_game/database/countries.db"  # Adjust the path as necessary
    csv_file_path = "countries_export.csv"
    export_countries_to_csv(db_path, csv_file_path)

