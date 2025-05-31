#!/usr/bin/env python3
"""
Script to fix Vietnamese translation mismatches in the quotes database
"""

import psycopg2
import os

def get_database_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def fix_translation_mismatches():
    """Fix all Vietnamese translation mismatches"""
    
    # Correct Vietnamese translations for each quote
    corrections = {
        95: "Không phải tất cả chúng ta đều có thể làm những việc tuyệt vời. Nhưng chúng ta có thể làm những việc nhỏ với tình yêu tuyệt vời",
        96: "Hãy cho, nhưng cho đến khi nó đau đớn", 
        97: "Hai con đường phân chia trong rừng, và tôi— tôi đã chọn con đường ít người đi, và điều đó đã tạo nên sự khác biệt",
        98: "Trong ba từ tôi có thể tóm tắt mọi thứ tôi đã học được về cuộc sống: nó tiếp tục",
        99: "Và, khi bạn muốn điều gì đó, toàn bộ vũ trụ sẽ đồng lòng giúp bạn đạt được nó",
        100: "Chỉ có một điều làm cho giấc mơ trở nên bất khả thi: nỗi sợ thất bại",
        # Additional corrections for other potentially mismatched quotes
        51: "Tất cả chúng ta đều ở trong rãnh, nhưng một số người trong chúng ta đang nhìn lên những vì sao",
        52: "Hạnh phúc không phải là điều gì đó sẵn có. Nó đến từ hành động của chính bạn",
        53: "Đời người chỉ có một lần, nhưng nếu bạn sống đúng cách, một lần là đủ",
        54: "Thành công là đi từ thất bại này đến thất bại khác mà không mất đi nhiệt tình",
        55: "Bạn không thể quay lại và thay đổi khởi đầu, nhưng bạn có thể bắt đầu từ nơi bạn đang đứng và thay đổi kết thúc",
        56: "Cách tốt nhất để dự đoán tương lai là tạo ra nó",
        57: "Cuộc sống thực sự đơn giản, nhưng chúng ta cứ khăng khăng làm nó phức tạp",
        58: "Người hiểu biết học từ mọi người. Người bình thường học từ kinh nghiệm của họ. Kẻ ngốc nghệch không học hỏi gì cả",
        59: "Thời gian bạn thích lãng phí không phải là thời gian lãng phí",
        60: "Tôi không thất bại. Tôi chỉ vừa tìm ra 10.000 cách không hoạt động",
        61: "Thiên tài là một phần trăm cảm hứng và chín mươi chín phần trăm mồ hôi",
        62: "Cơ hội thường được ngụy trang dưới dạng công việc khó khăn",
        63: "Hãy nhớ rằng không nhận được điều bạn muốn đôi khi là một món quà tuyệt vời của số phận",
        64: "Một người chưa bao giờ mắc lỗi thì chưa bao giờ thử làm điều gì mới",
        65: "Hãy cư xử như thể những gì bạn làm tạo ra sự khác biệt. Bởi vì nó thật sự tạo ra sự khác biệt",
        66: "Tình yêu không làm cho thế giới quay, nhưng nó làm cho cuộc hành trình trở nên đáng giá",
        67: "Cuộc sống không phải về việc tìm kiếm bản thân. Cuộc sống là về việc tạo ra bản thân",
        68: "Cách duy nhất để thực hiện công việc tuyệt vời là yêu thích những gì bạn làm",
        69: "Sự khác biệt giữa những người thành công và những người khác không phải là thiếu sức mạnh, thiếu kiến thức, mà là thiếu ý chí",
        70: "Đừng chờ đợi cơ hội. Hãy tạo ra chúng",
        71: "Tương lai thuộc về những ai chuẩn bị cho nó ngay hôm nay",
        72: "Thành công thường đến với những người quá bận rộn để tìm kiếm nó",
        73: "Đừng sợ từ bỏ điều tốt để theo đuổi điều tuyệt vời",
        74: "Cách duy nhất để làm điều bất khả thi là tin rằng nó có thể thực hiện được",
        75: "Cuộc sống không đo bằng số hơi thở bạn thở, mà bằng những khoảnh khắc khiến bạn nín thở",
        76: "Hạnh phúc không phải là đích đến, nó là cách thức di chuyển",
        77: "Bạn bỏ lỡ 100% những cú đánh bạn không thực hiện",
        78: "Tôi đã bỏ lỡ hơn 9000 cú đánh trong sự nghiệp. Tôi đã thua 300 trận đấu",
        79: "Làm hoặc không làm, không có thử",
        80: "Nếu bạn làm những gì dễ dàng, cuộc sống của bạn sẽ khó khăn",
        81: "Bạn không cần phải tuyệt vời để bắt đầu, nhưng bạn cần phải bắt đầu để trở nên tuyệt vời",
        82: "Chất lượng cuộc sống của bạn chính là chất lượng các mối quan hệ của bạn",
        83: "Bạn chỉ được trao cho một tia lửa điên rồ nhỏ. Bạn không được để mất nó",
        84: "Đừng lo lắng về bất cứ điều gì, mọi thứ nhỏ nhặt sẽ ổn thôi",
        85: "Một giấc mơ bạn mơ một mình chỉ là một giấc mơ. Một giấc mơ bạn mơ cùng người khác là hiện thực",
        86: "Không hoàn hảo là vẻ đẹp, điên rồ là thiên tài",
        87: "Điều quan trọng nhất là tận hưởng cuộc sống của bạn",
        88: "Để trở nên không thể thay thế, người ta phải luôn khác biệt",
        89: "Ai đó đang ngồi trong bóng mát hôm nay vì ai đó đã trồng cây cách đây nhiều năm",
        90: "Những khách hàng không hài lòng nhất của bạn là nguồn học hỏi lớn nhất của bạn",
        91: "Khi một điều gì đó đủ quan trọng, bạn làm nó ngay cả khi tỷ lệ thành công không có lợi cho bạn",
        92: "Cơ hội kinh doanh giống như xe buýt, luôn có chuyến tiếp theo",
        93: "Định kiến là gánh nặng làm rối loạn quá khứ, đe dọa tương lai",
        94: "Hôm qua tôi thông minh, nên tôi muốn thay đổi thế giới. Hôm nay tôi khôn ngoan, nên tôi đang thay đổi bản thân"
    }
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        successful_updates = 0
        for quote_id, correct_translation in corrections.items():
            cursor.execute(
                "UPDATE quotes SET vietnamese_translation = %s WHERE id = %s",
                (correct_translation, quote_id)
            )
            successful_updates += 1
            print(f"✓ Fixed translation for quote #{quote_id}")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\nCompleted: {successful_updates} translation corrections applied")
        return True
        
    except Exception as e:
        print(f"Error updating translations: {e}")
        return False

def verify_translations():
    """Verify that translations match their quotes"""
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, quote_text, vietnamese_translation, author FROM quotes WHERE id BETWEEN 95 AND 100 ORDER BY id")
        results = cursor.fetchall()
        
        print("\nVerification of corrected quotes:")
        for quote_id, english_text, vietnamese_text, author in results:
            print(f"\n#{quote_id} - {author}")
            print(f"EN: {english_text[:80]}...")
            print(f"VI: {vietnamese_text[:80]}...")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error verifying translations: {e}")

if __name__ == "__main__":
    print("Fixing Vietnamese translation mismatches...")
    if fix_translation_mismatches():
        verify_translations()
    else:
        print("Failed to fix translation mismatches")