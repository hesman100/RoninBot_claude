"""
Quotes collector from open sources
"""

import requests
import json
import time
from quotes_database import QuotesDatabase
import logging

logger = logging.getLogger(__name__)

class QuotesCollector:
    def __init__(self):
        self.db = QuotesDatabase()
        
    def collect_vietnamese_quotes(self):
        """Collect Vietnamese quotes from various sources"""
        # Vietnamese wisdom quotes dataset
        vietnamese_quotes = [
            {
                "quote": "Học, học nữa, học mãi",
                "author": "Hồ Chí Minh",
                "category": "Giáo dục",
                "source": "Trích từ tác phẩm của Chủ tịch Hồ Chí Minh",
                "source_type": "book",
                "source_url": "https://www.hochiminh.org.vn/"
            },
            {
                "quote": "Không có gì quý hơn độc lập tự do",
                "author": "Hồ Chí Minh", 
                "category": "Yêu nước",
                "source": "Tuyên ngôn độc lập"
            },
            {
                "quote": "Đoàn kết là sức mạnh",
                "author": "Hồ Chí Minh",
                "category": "Đoàn kết",
                "source": "Lời dạy của Bác"
            },
            {
                "quote": "Thất bại là mẹ thành công",
                "author": "Câu ngạn ngữ Việt Nam",
                "category": "Động lực",
                "source": "Dân gian Việt Nam"
            },
            {
                "quote": "Có công mài sắt có ngày nên kim",
                "author": "Câu ngạn ngữ Việt Nam",
                "category": "Kiên trì",
                "source": "Dân gian Việt Nam"
            },
            {
                "quote": "Muốn đi nhanh thì đi một mình, muốn đi xa thì đi cùng nhau",
                "author": "Câu ngạn ngữ châu Phi",
                "category": "Hợp tác",
                "source": "Tư tưởng châu Phi"
            },
            {
                "quote": "Tri thức là sức mạnh",
                "author": "Francis Bacon",
                "category": "Tri thức",
                "source": "Triết học phương Tây"
            },
            {
                "quote": "Tương lai thuộc về những ai tin vào vẻ đẹp của ước mơ",
                "author": "Eleanor Roosevelt",
                "category": "Ước mơ",
                "source": "Chính trị gia Mỹ"
            },
            {
                "quote": "Hành trình ngàn dặm bắt đầu từ một bước chân",
                "author": "Lão Tử",
                "category": "Khởi đầu",
                "source": "Triết học Trung Quốc"
            },
            {
                "quote": "Đừng đợi cơ hội, hãy tạo ra cơ hội",
                "author": "George Bernard Shaw",
                "category": "Cơ hội",
                "source": "Văn học Anh"
            },
            {
                "quote": "Thành công không phải là chìa khóa của hạnh phúc. Hạnh phúc mới là chìa khóa của thành công",
                "author": "Albert Schweitzer",
                "category": "Hạnh phúc",
                "source": "Triết học hiện đại"
            },
            {
                "quote": "Chỉ có một cách để tránh sự chỉ trích: không làm gì, không nói gì và không là gì cả",
                "author": "Aristotle",
                "category": "Hành động",
                "source": "Triết học Hy Lạp"
            },
            {
                "quote": "Nước chảy đá mòn",
                "author": "Câu ngạn ngữ Việt Nam",
                "category": "Kiên trì",
                "source": "Dân gian Việt Nam"
            },
            {
                "quote": "Giọt nước làm tràn ly",
                "author": "Câu ngạn ngữ Việt Nam",
                "category": "Giới hạn",
                "source": "Dân gian Việt Nam"
            },
            {
                "quote": "Một cây làm chẳng nên non, ba cây chụm lại nên hòn núi cao",
                "author": "Câu ngạn ngữ Việt Nam",
                "category": "Đoàn kết",
                "source": "Dân gian Việt Nam"
            }
        ]
        
        # Insert Vietnamese quotes
        for quote_data in vietnamese_quotes:
            try:
                self.db.insert_quote(
                    quote_text=quote_data["quote"],
                    author=quote_data["author"],
                    source=quote_data["source"],
                    category=quote_data["category"],
                    language="vi"
                )
                logger.info(f"Inserted Vietnamese quote: {quote_data['quote'][:50]}...")
            except Exception as e:
                logger.error(f"Failed to insert quote: {e}")
                
    def collect_english_quotes(self):
        """Collect English quotes from open sources"""
        english_quotes = [
            {
                "quote": "The only way to do great work is to love what you do",
                "author": "Steve Jobs",
                "category": "Work",
                "source": "Stanford Commencement Speech"
            },
            {
                "quote": "Innovation distinguishes between a leader and a follower",
                "author": "Steve Jobs",
                "category": "Innovation",
                "source": "Apple Inc."
            },
            {
                "quote": "Life is what happens when you're busy making other plans",
                "author": "John Lennon",
                "category": "Life",
                "source": "Beautiful Boy song"
            },
            {
                "quote": "The future belongs to those who believe in the beauty of their dreams",
                "author": "Eleanor Roosevelt",
                "category": "Dreams",
                "source": "Political speeches"
            },
            {
                "quote": "It is during our darkest moments that we must focus to see the light",
                "author": "Aristotle",
                "category": "Hope",
                "source": "Greek Philosophy"
            },
            {
                "quote": "Success is not final, failure is not fatal: it is the courage to continue that counts",
                "author": "Winston Churchill",
                "category": "Courage",
                "source": "Political speeches"
            },
            {
                "quote": "The only impossible journey is the one you never begin",
                "author": "Tony Robbins",
                "category": "Beginning",
                "source": "Motivational speaking"
            },
            {
                "quote": "In the middle of difficulty lies opportunity",
                "author": "Albert Einstein",
                "category": "Opportunity",
                "source": "Scientific philosophy"
            },
            {
                "quote": "Believe you can and you're halfway there",
                "author": "Theodore Roosevelt",
                "category": "Confidence",
                "source": "Presidential speeches"
            },
            {
                "quote": "It does not matter how slowly you go as long as you do not stop",
                "author": "Confucius",
                "category": "Persistence",
                "source": "Chinese Philosophy"
            }
        ]
        
        # Insert English quotes
        for quote_data in english_quotes:
            try:
                self.db.insert_quote(
                    quote_text=quote_data["quote"],
                    author=quote_data["author"],
                    source=quote_data["source"],
                    category=quote_data["category"],
                    language="en"
                )
                logger.info(f"Inserted English quote: {quote_data['quote'][:50]}...")
            except Exception as e:
                logger.error(f"Failed to insert quote: {e}")
                
    def populate_database(self):
        """Initialize and populate the quotes database"""
        try:
            # Create tables
            self.db.create_tables()
            
            # Check if database is empty
            count = self.db.get_quote_count()
            if count == 0:
                logger.info("Database is empty, populating with initial quotes...")
                self.collect_vietnamese_quotes()
                self.collect_english_quotes()
                logger.info(f"Database populated with {self.db.get_quote_count()} quotes")
            else:
                logger.info(f"Database already contains {count} quotes")
                
        except Exception as e:
            logger.error(f"Failed to populate database: {e}")
            raise
            
    def get_random_quote(self, category=None, language='vi'):
        """Get a random quote from the database"""
        return self.db.get_random_quote(category, language)
        
    def search_quotes(self, keyword, language='vi'):
        """Search quotes by keyword"""
        return self.db.search_quotes(keyword, language)
        
    def get_categories(self):
        """Get all available categories"""
        return self.db.get_categories()

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize and populate database
    collector = QuotesCollector()
    collector.populate_database()
    
    # Test functionality
    print("Testing random quote retrieval...")
    quote = collector.get_random_quote()
    if quote:
        print(f"Quote: {quote['quote_text']}")
        print(f"Author: {quote['author']}")
        print(f"Category: {quote['category']}")
    
    print(f"\nAvailable categories: {collector.get_categories()}")
    print(f"Total quotes in database: {collector.db.get_quote_count()}")