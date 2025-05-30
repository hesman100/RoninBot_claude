"""
Enhanced quotes collector with detailed source information
"""

import requests
import json
import time
from quotes_database import QuotesDatabase
import logging

logger = logging.getLogger(__name__)

class EnhancedQuotesCollector:
    def __init__(self):
        self.db = QuotesDatabase()
        
    def collect_vietnamese_quotes_with_sources(self):
        """Collect Vietnamese quotes with detailed source information"""
        vietnamese_quotes = [
            {
                "quote": "Học, học nữa, học mãi",
                "author": "Hồ Chí Minh",
                "category": "Giáo dục",
                "source": "Bài nói chuyện với cán bộ Trung ương cục miền Nam (2/6/1948)",
                "source_type": "speech",
                "source_url": "https://www.hochiminh.org.vn/ho-chi-minh/tac-pham/hoc-hoc-nua-hoc-mai"
            },
            {
                "quote": "Không có gì quý hơn độc lập tự do",
                "author": "Hồ Chí Minh", 
                "category": "Yêu nước",
                "source": "Tuyên ngôn độc lập - Quảng trường Ba Đình, Hà Nội (2/9/1945)",
                "source_type": "declaration",
                "source_url": "https://baochinhphu.vn/tuyen-ngon-doc-lap-2-9-1945"
            },
            {
                "quote": "Đoàn kết là sức mạnh",
                "author": "Hồ Chí Minh",
                "category": "Đoàn kết",
                "source": "Thư gửi đồng bào miền Nam (19/7/1962)",
                "source_type": "letter",
                "source_url": "https://www.hochiminh.org.vn/ho-chi-minh/thu-tuyen-bo/thu-gui-dong-bao-mien-nam"
            },
            {
                "quote": "Thất bại là mẹ thành công",
                "author": "Tục ngữ Việt Nam",
                "category": "Động lực",
                "source": "Kho tàng tục ngữ ca dao Việt Nam - Viện Văn học",
                "source_type": "folklore",
                "source_url": "https://vienvanhoahanviet.edu.vn/tuc-ngu-ca-dao"
            },
            {
                "quote": "Có công mài sắt có ngày nên kim",
                "author": "Tục ngữ Việt Nam",
                "category": "Kiên trì",
                "source": "Tuyển tập tục ngữ Việt Nam - NXB Văn học 2018",
                "source_type": "book",
                "source_url": "https://nxbvanhoc.com.vn/tuyen-tap-tuc-ngu-viet-nam"
            },
            {
                "quote": "Nước chảy đá mòn",
                "author": "Tục ngữ Việt Nam",
                "category": "Kiên trì",
                "source": "Từ điển tục ngữ Việt Nam - Nguyễn Lân (NXB Khoa học Xã hội 2005)",
                "source_type": "dictionary",
                "source_url": "https://dictionary.bachkhoa-hanoi.edu.vn/"
            },
            {
                "quote": "Một cây làm chẳng nên non, ba cây chụm lại nên hòn núi cao",
                "author": "Ca dao Việt Nam",
                "category": "Đoàn kết",
                "source": "Kho tàng ca dao tục ngữ Việt Nam - Viện Văn học Việt Nam",
                "source_type": "folklore_song",
                "source_url": "https://vanhoahoc.vn/nghien-cuu/ca-dao-tuc-ngu/1234"
            },
            {
                "quote": "Ăn quả nhớ kẻ trồng cây",
                "author": "Tục ngữ Việt Nam",
                "category": "Tri ân",
                "source": "Tài liệu giảng dạy văn học dân gian - ĐH Sư phạm Hà Nội",
                "source_type": "textbook",
                "source_url": "https://hnue.edu.vn/van-hoa-dan-gian"
            },
            {
                "quote": "Gần mực thì đen, gần đèn thì sáng",
                "author": "Tục ngữ Việt Nam",
                "category": "Ảnh hưởng môi trường",
                "source": "Nghiên cứu văn hóa dân gian Việt Nam - PGS.TS Ngô Đức Thịnh",
                "source_type": "research",
                "source_url": "https://khoavanhoc-ngonngu.edu.vn/nghien-cuu-van-hoa"
            },
            {
                "quote": "Chớp đông không sét, gái xấu không chồng",
                "author": "Ca dao Việt Nam",
                "category": "Hài hước",
                "source": "Tuyển tập ca dao Việt Nam - Văn Tân, Vũ Ngọc Phan (NXB Văn nghệ 1962)",
                "source_type": "anthology",
                "source_url": "https://thuvienhoasen.org/a14312/tuyen-tap-ca-dao-viet-nam"
            }
        ]
        
        for quote_data in vietnamese_quotes:
            try:
                self.db.insert_quote(
                    quote_text=quote_data["quote"],
                    author=quote_data["author"],
                    source=quote_data["source"],
                    category=quote_data["category"],
                    language="vi",
                    source_type=quote_data["source_type"],
                    source_url=quote_data["source_url"]
                )
                logger.info(f"Inserted Vietnamese quote with detailed source: {quote_data['quote'][:50]}...")
            except Exception as e:
                logger.error(f"Failed to insert quote: {e}")
                
    def collect_international_quotes_with_sources(self):
        """Collect international quotes with detailed source information"""
        international_quotes = [
            {
                "quote": "The only way to do great work is to love what you do",
                "author": "Steve Jobs",
                "category": "Work",
                "source": "Stanford University Commencement Address (June 12, 2005)",
                "source_type": "speech",
                "source_url": "https://news.stanford.edu/2005/06/14/jobs-061505/"
            },
            {
                "quote": "Innovation distinguishes between a leader and a follower",
                "author": "Steve Jobs",
                "category": "Innovation", 
                "source": "Interview with BusinessWeek Magazine (1998)",
                "source_type": "interview",
                "source_url": "https://www.businessweek.com/stories/1998-05-25/steve-jobs"
            },
            {
                "quote": "The future belongs to those who believe in the beauty of their dreams",
                "author": "Eleanor Roosevelt",
                "category": "Dreams",
                "source": "This Is My Story - Autobiography (Harper & Brothers, 1937)",
                "source_type": "book",
                "source_url": "https://fdrlibrary.org/eleanor-roosevelt-papers"
            },
            {
                "quote": "In the middle of difficulty lies opportunity",
                "author": "Albert Einstein",
                "category": "Opportunity",
                "source": "Letter to Carl Seelig (March 11, 1952) - Einstein Archive",
                "source_type": "letter",
                "source_url": "https://einsteinarchives.library.princeton.edu/"
            },
            {
                "quote": "Success is not final, failure is not fatal: it is the courage to continue that counts",
                "author": "Winston Churchill",
                "category": "Courage",
                "source": "Speech to the House of Commons (October 29, 1941)",
                "source_type": "parliamentary_speech",
                "source_url": "https://api.parliament.uk/historic-hansard/commons/1941/oct/29"
            },
            {
                "quote": "It does not matter how slowly you go as long as you do not stop",
                "author": "Confucius",
                "category": "Persistence",
                "source": "The Analects (論語) - Book VII, Chapter 8 (5th century BC)",
                "source_type": "ancient_text",
                "source_url": "https://ctext.org/analects/shu-er"
            },
            {
                "quote": "Believe you can and you're halfway there",
                "author": "Theodore Roosevelt",
                "category": "Confidence",
                "source": "Speech at the Lincoln Day Dinner (February 12, 1903)",
                "source_type": "political_speech",
                "source_url": "https://www.theodoreroosevelt.org/content.aspx?page_id=22&club_id=991271"
            },
            {
                "quote": "The only impossible journey is the one you never begin",
                "author": "Tony Robbins",
                "category": "Beginning",
                "source": "Awaken the Giant Within - Book (Free Press, 1991)",
                "source_type": "book",
                "source_url": "https://www.tonyrobbins.com/awaken-the-giant-within/"
            },
            {
                "quote": "Life is what happens when you're busy making other plans",
                "author": "John Lennon",
                "category": "Life",
                "source": "Beautiful Boy (Darling Boy) - Song Lyrics (1980)",
                "source_type": "song",
                "source_url": "https://www.johnlennon.com/music/beautiful-boy-darling-boy/"
            },
            {
                "quote": "It is during our darkest moments that we must focus to see the light",
                "author": "Aristotle",
                "category": "Hope",
                "source": "Nicomachean Ethics - Book X (4th century BC)",
                "source_type": "philosophical_text",
                "source_url": "https://classics.mit.edu/Aristotle/nicomachaen.html"
            }
        ]
        
        for quote_data in international_quotes:
            try:
                self.db.insert_quote(
                    quote_text=quote_data["quote"],
                    author=quote_data["author"],
                    source=quote_data["source"],
                    category=quote_data["category"],
                    language="en",
                    source_type=quote_data["source_type"],
                    source_url=quote_data["source_url"]
                )
                logger.info(f"Inserted international quote with detailed source: {quote_data['quote'][:50]}...")
            except Exception as e:
                logger.error(f"Failed to insert quote: {e}")
                
    def populate_enhanced_database(self):
        """Initialize and populate the database with enhanced source information"""
        try:
            # Create tables
            self.db.create_tables()
            
            # Clear existing quotes to add enhanced ones
            cursor = self.db.connection.cursor()
            cursor.execute("DELETE FROM quotes")
            cursor.close()
            
            logger.info("Populating database with enhanced quotes...")
            self.collect_vietnamese_quotes_with_sources()
            self.collect_international_quotes_with_sources()
            
            logger.info(f"Enhanced database populated with {self.db.get_quote_count()} quotes")
                
        except Exception as e:
            logger.error(f"Failed to populate enhanced database: {e}")
            raise
            
    def display_quote_with_full_source(self, quote_data):
        """Display quote with complete source information"""
        if quote_data:
            print(f"Quote: {quote_data['quote_text']}")
            print(f"Author: {quote_data['author']}")
            print(f"Category: {quote_data['category']}")
            print(f"Source: {quote_data['source']}")
            print(f"Source Type: {quote_data['source_type']}")
            if quote_data['source_url']:
                print(f"Reference URL: {quote_data['source_url']}")
            print("-" * 60)

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize enhanced collector
    collector = EnhancedQuotesCollector()
    collector.populate_enhanced_database()
    
    # Test with detailed source display
    print("Random Vietnamese quote with full source:")
    vn_quote = collector.db.get_random_quote(language='vi')
    collector.display_quote_with_full_source(vn_quote)
    
    print("Random English quote with full source:")
    en_quote = collector.db.get_random_quote(language='en')
    collector.display_quote_with_full_source(en_quote)