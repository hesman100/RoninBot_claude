#!/usr/bin/env python3
"""
Script to add Vietnamese translations for all English quotes in the database
"""

import psycopg2
import os
from typing import Dict

def get_database_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_quotes_without_vietnamese():
    """Get all quotes that need Vietnamese translations"""
    conn = get_database_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, quote_text, author 
            FROM quotes 
            WHERE vietnamese_translation IS NULL OR vietnamese_translation = ''
            ORDER BY id
        """)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Exception as e:
        print(f"Error fetching quotes: {e}")
        return []

def add_vietnamese_translation(quote_id: int, vietnamese_text: str):
    """Add Vietnamese translation for a specific quote"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE quotes SET vietnamese_translation = %s WHERE id = %s",
            (vietnamese_text, quote_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating quote {quote_id}: {e}")
        return False

# Vietnamese translations for all remaining quotes
translations = {
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
    94: "Hôm qua tôi thông minh, nên tôi muốn thay đổi thế giới. Hôm nay tôi khôn ngoan, nên tôi đang thay đổi bản thân",
    95: "Hãy để bản thân bị thu hút một cách thầm lặng bởi sức hút kỳ lạ của những gì bạn thực sự yêu thích",
    96: "Bạn không bao giờ quá già để đặt ra một mục tiêu khác hoặc mơ một giấc mơ mới",
    97: "Chính trực là làm điều đúng khi không ai nhìn thấy",
    98: "Hãy cố gắng trở thành cầu vồng trong đám mây của ai đó",
    99: "Bạn là trung bình cộng của năm người bạn dành thời gian nhiều nhất",
    100: "Kỷ luật là cây cầu giữa mục tiêu và thành tựu",
    101: "Có khi không khó như chúng ta nghĩ đâu",
    102: "Nỗi sợ hãi có hai ý nghĩa: 'Quên Mọi Thứ Và Chạy' hoặc 'Đối Mặt Với Mọi Thứ Và Vươn Lên'",
    103: "Vấn đề không nằm ở việc chúng ta có bao nhiêu vấn đề, mà là chúng ta giải quyết chúng như thế nào",
    104: "Thất bại sẽ không bao giờ vượt qua tôi nếu quyết tâm thành công của tôi đủ mạnh",
    105: "Điều bạn nhận được bằng cách đạt được mục tiêu không quan trọng bằng những gì bạn trở thành khi đạt được chúng",
    106: "Cuộc sống là 10% những gì xảy ra với bạn và 90% cách bạn phản ứng với nó",
    107: "Thành công không phải về điểm đến, mà về hành trình và bạn trở thành ai trong suốt con đường",
    108: "Tình yêu và lòng từ bi là những điều cần thiết, không phải điều xa xỉ",
    109: "Hạnh phúc là khi những gì bạn nghĩ, nói và làm đều hài hòa",
    110: "Cuộc sống giống như đi xe đạp. Để giữ thăng bằng, bạn phải tiếp tục di chuyển",
    111: "Tôi thà có những câu hỏi không thể trả lời hơn là có những câu trả lời không thể đặt câu hỏi",
    112: "Nguyên tắc đầu tiên là bạn không được tự lừa dối mình",
    113: "Những gì tôi không thể tạo ra, tôi không hiểu",
    114: "Khoa học là một cách suy nghĩ hơn là một tập hợp kiến thức",
    115: "Hãy học chăm chỉ những gì khiến bạn quan tâm nhất theo cách không khuôn mẫu, không tôn kính và nguyên bản nhất có thể",
    116: "Tôi đã học được rất sớm sự khác biệt giữa biết tên của thứ gì đó và hiểu thứ đó",
    117: "Không quan trọng lý thuyết của bạn đẹp đến đâu, nếu nó không phù hợp với thí nghiệm, thì nó sai",
    118: "Tôi nghĩ thú vị hơn nhiều khi sống mà không biết hơn là có những câu trả lời có thể sai",
    119: "Nếu bạn muốn tìm hiểu về tự nhiên, để trân trọng tự nhiên, cần phải hiểu ngôn ngữ mà nó nói",
    120: "Hãy yêu thích một hoạt động nào đó, và làm nó! Không ai tìm ra cuộc sống là gì cả, và điều đó không quan trọng",
    121: "Tôi có một người bạn là nghệ sĩ và đôi khi có quan điểm mà tôi không đồng ý lắm",
    122: "Nếu tôi có thể giải thích nó cho người bình thường, tôi đã không xứng đáng với giải Nobel",
    123: "Tôi không cần phải biết câu trả lời. Tôi không cảm thấy sợ hãi khi không biết mọi thứ",
    124: "Để có một công nghệ thành công, thực tế phải được ưu tiên hơn quan hệ công chúng, vì tự nhiên không thể bị lừa",
    125: "Tôi sinh ra không biết gì và chỉ có một chút thời gian để thay đổi điều đó ở đây và ở đó",
    126: "Hãy học chăm chỉ những gì bạn quan tâm nhất theo cách không khuôn mẫu, không tôn kính và nguyên bản nhất có thể",
    127: "Những vấn đề đáng giá là những vấn đề bạn thực sự có thể giải quyết hoặc giúp giải quyết",
    128: "Khoa học là một cách suy nghĩ hơn là một tập hợp kiến thức",
    129: "Chính trong việc thừa nhận sự thiếu hiểu biết và thừa nhận sự không chắc chắn mà có hy vọng cho sự chuyển động liên tục của con người",
    130: "Bạn không có trách nhiệm phải sống theo những gì người khác nghĩ bạn nên đạt được",
    131: "Tự nhiên chỉ sử dụng những sợi chỉ dài nhất để dệt các mẫu của mình",
    132: "Tôn giáo là văn hóa của đức tin; khoa học là văn hóa của sự nghi ngờ",
    133: "Nếu bạn nghĩ mình hiểu cơ học lượng tử, thì bạn không hiểu cơ học lượng tử",
    134: "Vật lý giống như tình dục: chắc chắn, nó có thể mang lại một số kết quả thực tế, nhưng đó không phải lý do chúng ta làm nó",
    135: "Những hình thức hiểu biết cao nhất mà chúng ta có thể đạt được là tiếng cười và lòng từ bi của con người",
    136: "Chúng ta đang cố gắng chứng minh mình sai càng nhanh càng tốt, vì chỉ bằng cách đó chúng ta mới có thể tìm thấy tiến bộ",
    137: "Điều quan trọng là phải nhận ra rằng trong vật lý ngày nay, chúng ta không biết năng lượng là gì",
    138: "Tôi không thể định nghĩa vấn đề thực sự, do đó tôi nghi ngờ không có vấn đề thực sự nào"
}

def main():
    """Add Vietnamese translations for all quotes"""
    quotes = get_quotes_without_vietnamese()
    print(f"Found {len(quotes)} quotes needing Vietnamese translations")
    
    successful_updates = 0
    for quote_id, quote_text, author in quotes:
        if quote_id in translations:
            if add_vietnamese_translation(quote_id, translations[quote_id]):
                successful_updates += 1
                print(f"✓ Added Vietnamese translation for quote #{quote_id}")
            else:
                print(f"✗ Failed to update quote #{quote_id}")
        else:
            print(f"! No translation available for quote #{quote_id}: {quote_text[:50]}...")
    
    print(f"\nCompleted: {successful_updates} quotes updated with Vietnamese translations")

if __name__ == "__main__":
    main()