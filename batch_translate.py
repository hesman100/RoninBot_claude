#!/usr/bin/env python3
"""
Batch translation script - processes 20 quotes at a time
"""

import psycopg2
import os
import time
import requests
import sys

def get_database_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def translate_with_google(english_text):
    """Translate English quote to Vietnamese using Google Translate"""
    try:
        text_to_translate = english_text.strip()
        
        url = "https://translate.googleapis.com/translate_a/single"
        
        params = {
            'client': 'gtx',
            'sl': 'en',
            'tl': 'vi',
            'dt': 't',
            'q': text_to_translate
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result and len(result) > 0 and len(result[0]) > 0:
                vietnamese_translation = result[0][0][0]
                return vietnamese_translation.strip()
        
        return None
        
    except Exception as e:
        print(f"Error translating: {e}")
        return None

def process_batch(start_id=1, batch_size=20):
    """Process a batch of quotes"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get quotes that need translation
        cursor.execute("""
            SELECT id, quote_text, author, language 
            FROM quotes 
            WHERE id >= %s AND id < %s AND vietnamese_translation IS NULL
            ORDER BY id
        """, (start_id, start_id + batch_size))
        
        quotes_to_translate = cursor.fetchall()
        
        if not quotes_to_translate:
            print(f"No quotes to translate in batch {start_id}-{start_id + batch_size - 1}")
            return True
        
        print(f"Processing batch {start_id}-{start_id + batch_size - 1}: {len(quotes_to_translate)} quotes")
        
        for quote_id, english_text, author, language in quotes_to_translate:
            print(f"  #{quote_id}: {author} - {english_text[:40]}...")
            
            # For Vietnamese originals, use the original text
            if language == 'vi' or author in ["Hồ Chí Minh", "Câu ngạn ngữ Việt Nam"]:
                vietnamese_translation = english_text
            else:
                vietnamese_translation = translate_with_google(english_text)
                time.sleep(1)  # Rate limiting
            
            if vietnamese_translation:
                cursor.execute(
                    "UPDATE quotes SET vietnamese_translation = %s WHERE id = %s",
                    (vietnamese_translation, quote_id)
                )
                print(f"    ✓ {vietnamese_translation[:50]}...")
            else:
                print(f"    ❌ Failed to translate")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Error processing batch: {e}")
        return False

def main():
    """Process all quotes in batches"""
    batch_size = 20
    start_id = 1
    
    if len(sys.argv) > 1:
        start_id = int(sys.argv[1])
    
    print(f"Starting batch translation from ID {start_id}")
    
    while start_id <= 162:
        success = process_batch(start_id, batch_size)
        if not success:
            print(f"Failed at batch starting with ID {start_id}")
            break
        
        start_id += batch_size
        
        if start_id <= 162:
            print(f"Waiting 2 seconds before next batch...")
            time.sleep(2)
    
    # Check completion
    conn = get_database_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE vietnamese_translation IS NULL")
        remaining = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM quotes")
        total = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"\nStatus: {total - remaining}/{total} quotes translated")
        print(f"Remaining: {remaining}")

if __name__ == "__main__":
    main()