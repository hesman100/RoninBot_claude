#!/usr/bin/env python3
"""
Complete rebuild of Vietnamese translations:
1. Remove all existing Vietnamese translations
2. Generate fresh translations for each quote using OpenAI
"""

import psycopg2
import os
import time
import requests
import urllib.parse
import json
import re

def get_database_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def clear_all_vietnamese_translations():
    """Step 1: Remove all Vietnamese translations"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE quotes SET vietnamese_translation = NULL")
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE vietnamese_translation IS NULL")
        cleared_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"✓ Cleared {cleared_count} Vietnamese translations")
        return True
        
    except Exception as e:
        print(f"Error clearing translations: {e}")
        return False

def translate_with_google(english_text, author):
    """Translate English quote to Vietnamese using Google Translate"""
    try:
        # Clean the text for better translation
        text_to_translate = english_text.strip()
        
        # Google Translate API endpoint
        url = "https://translate.googleapis.com/translate_a/single"
        
        params = {
            'client': 'gtx',
            'sl': 'en',  # source language: English
            'tl': 'vi',  # target language: Vietnamese
            'dt': 't',   # return translation
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
        print(f"Error translating with Google Translate: {e}")
        return None

def rebuild_all_translations():
    """Step 2: Generate fresh translations for all quotes"""
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get all quotes that need Vietnamese translations (excluding Vietnamese originals)
        cursor.execute("""
            SELECT id, quote_text, author, language 
            FROM quotes 
            WHERE vietnamese_translation IS NULL 
            ORDER BY id
        """)
        
        quotes_to_translate = cursor.fetchall()
        total_quotes = len(quotes_to_translate)
        
        print(f"Starting translation of {total_quotes} quotes...")
        
        translated_count = 0
        failed_count = 0
        
        for quote_id, english_text, author, language in quotes_to_translate:
            print(f"Translating #{quote_id}: {author} - {english_text[:50]}...")
            
            # For Vietnamese originals, copy the quote_text as the vietnamese_translation
            if language == 'vi' or author in ["Hồ Chí Minh", "Câu ngạn ngữ Việt Nam"]:
                vietnamese_translation = english_text
            else:
                vietnamese_translation = translate_with_google(english_text, author)
                # Add small delay to avoid rate limiting
                time.sleep(1)
            
            if vietnamese_translation:
                cursor.execute(
                    "UPDATE quotes SET vietnamese_translation = %s WHERE id = %s",
                    (vietnamese_translation, quote_id)
                )
                translated_count += 1
                print(f"  ✓ Translated: {vietnamese_translation[:60]}...")
            else:
                failed_count += 1
                print(f"  ❌ Failed to translate quote #{quote_id}")
            
            # Commit every 10 translations
            if translated_count % 10 == 0:
                conn.commit()
                print(f"  💾 Saved progress: {translated_count}/{total_quotes}")
        
        # Final commit
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n🎉 TRANSLATION REBUILD COMPLETE:")
        print(f"   ✓ Successfully translated: {translated_count}")
        print(f"   ❌ Failed translations: {failed_count}")
        print(f"   📊 Success rate: {(translated_count/total_quotes)*100:.1f}%")
        
        return translated_count > 0
        
    except Exception as e:
        print(f"Error during translation rebuild: {e}")
        return False

def verify_translations():
    """Verify that all quotes now have Vietnamese translations"""
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE vietnamese_translation IS NULL")
        missing_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM quotes")
        total_count = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        print(f"\nVERIFICATION:")
        print(f"Total quotes: {total_count}")
        print(f"Missing translations: {missing_count}")
        print(f"Complete translations: {total_count - missing_count}")
        
        if missing_count == 0:
            print("✅ All quotes have Vietnamese translations!")
        else:
            print(f"⚠️  {missing_count} quotes still missing translations")
            
    except Exception as e:
        print(f"Error during verification: {e}")

def main():
    """Execute the complete rebuild process"""
    print("🔄 REBUILDING VIETNAMESE TRANSLATIONS")
    print("=====================================")
    
    # Step 1: Clear all existing translations
    print("\nStep 1: Clearing all existing Vietnamese translations...")
    if not clear_all_vietnamese_translations():
        print("❌ Failed to clear existing translations")
        return
    
    # Step 2: Generate fresh translations
    print("\nStep 2: Generating fresh translations...")
    if not rebuild_all_translations():
        print("❌ Failed to rebuild translations")
        return
    
    # Step 3: Verify completion
    print("\nStep 3: Verifying translations...")
    verify_translations()
    
    print("\n🎉 Translation rebuild process completed!")

if __name__ == "__main__":
    main()