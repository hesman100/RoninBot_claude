#!/usr/bin/env python3
"""
Comprehensive audit of all Vietnamese translations to identify mismatches
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

def audit_all_translations():
    """Audit all Vietnamese translations for accuracy"""
    
    # Complete correct translations for ALL quotes
    correct_translations = {
        # Vietnamese originals (1-15) - these are correct as they are the original text
        # Famous quotes (26-134) - corrected translations
        26: "Chúng ta tạo ra cuộc sống bằng những gì chúng ta nhận được, nhưng chúng ta tạo ra cuộc đời bằng những gì chúng ta cho đi",
        27: "Những đế chế của tương lai là những đế chế của tâm trí",
        28: "Diều bay cao nhất khi chống lại gió, không phải khi theo gió",
        29: "Hãy nói cho tôi nghe và tôi sẽ quên, hãy dạy tôi và tôi có thể nhớ, hãy làm cho tôi tham gia và tôi sẽ học",
        30: "Đầu tư vào kiến thức mang lại lợi ích tốt nhất",
        31: "Làm tốt thì hơn nói hay",
        32: "Trí tưởng tượng quan trọng hơn kiến thức",
        33: "Đừng cố gắng trở thành người thành công, mà hãy cố gắng trở thành người có giá trị",
        34: "Điều quan trọng là không ngừng đặt câu hỏi",
        35: "Hai ngày quan trọng nhất trong đời bạn là ngày bạn sinh ra và ngày bạn tìm ra lý do tại sao",
        36: "Lòng can đảm là sự chống lại nỗi sợ, làm chủ nỗi sợ, chứ không phải không có nỗi sợ",
        37: "Lòng tử tế là ngôn ngữ mà người điếc có thể nghe và người mù có thể nhìn thấy",
        38: "Nếu bạn không thích điều gì đó, hãy thay đổi nó. Nếu bạn không thể thay đổi, hãy thay đổi thái độ của mình",
        39: "Tôi đã học được rằng mọi người sẽ quên những gì bạn nói, quên những gì bạn làm, nhưng họ sẽ không bao giờ quên cảm giác bạn mang lại cho họ",
        40: "Giáo dục là vũ khí mạnh mẽ nhất mà bạn có thể sử dụng để thay đổi thế giới",
        41: "Điều gì cũng có vẻ bất khả thi cho đến khi nó được thực hiện",
        42: "Hãy là sự thay đổi mà bạn muốn thấy ở thế giới",
        43: "Hãy sống như thể bạn sẽ chết vào ngày mai. Hãy học như thể bạn sẽ sống mãi mãi",
        44: "Bóng tối không thể xua đuổi bóng tối; chỉ có ánh sáng mới làm được điều đó. Hận thù không thể xua đuổi hận thù; chỉ có tình yêu mới làm được điều đó",
        45: "Lúc nào cũng là thời điểm thích hợp để làm điều đúng đắn",
        46: "Công việc của bạn sẽ chiếm một phần lớn cuộc đời bạn, và cách duy nhất để thực sự hài lòng là làm những gì bạn tin là công việc tuyệt vời",
        47: "Hãy luôn khao khát, hãy luôn ngây thơ",
        48: "Những gì ở phía sau chúng ta và những gì ở phía trước chúng ta chỉ là những vấn đề nhỏ so với những gì ở bên trong chúng ta",
        49: "Đừng đi theo con đường có thể dẫn, thay vào đó hãy đi nơi không có đường và để lại dấu vết",
        50: "Hãy là chính mình; tất cả những người khác đã có chủ rồi",
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
        63: "Tôi không thất bại. Tôi chỉ vừa tìm ra 10.000 cách không hoạt động",  # FIXED - this was wrong
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
        95: "Không phải tất cả chúng ta đều có thể làm những việc tuyệt vời. Nhưng chúng ta có thể làm những việc nhỏ với tình yêu tuyệt vời",
        96: "Hãy cho, nhưng cho đến khi nó đau đớn",
        97: "Hai con đường phân chia trong rừng, và tôi— tôi đã chọn con đường ít người đi, và điều đó đã tạo nên sự khác biệt",
        98: "Trong ba từ tôi có thể tóm tắt mọi thứ tôi đã học được về cuộc sống: nó tiếp tục",
        99: "Và, khi bạn muốn điều gì đó, toàn bộ vũ trụ sẽ đồng lòng giúp bạn đạt được nó",
        100: "Chỉ có một điều làm cho giấc mơ trở nên bất khả thi: nỗi sợ thất bại",
        101: "Hành trình ngàn dặm bắt đầu từ một bước chân",
        102: "Khi tôi buông bỏ những gì tôi đang là, tôi trở thành những gì tôi có thể là",
        103: "Những gì chúng ta nghĩ, chúng ta sẽ trở thành",
        104: "Bình an đến từ bên trong. Đừng tìm kiếm nó ở bên ngoài",
        105: "Mọi thứ có thể bị lấy đi từ con người nhưng có một thứ: quyền tự do cuối cùng của con người - khả năng chọn thái độ của mình trong bất kỳ hoàn cảnh nào",
        106: "Những ai có 'tại sao' để sống, có thể chịu đựng hầu hết mọi 'làm thế nào'",
        107: "Hãy bận rộn với việc sống hoặc bận rộn với việc chết",
        108: "Tài năng rẻ hơn muối ăn. Điều phân biệt cá nhân tài năng với người thành công là rất nhiều công việc khó khăn",
        109: "Chính những lựa chọn của chúng ta mới cho thấy chúng ta thực sự là ai, hơn nhiều so với khả năng của chúng ta",
        110: "Đáy vực đã trở thành nền tảng vững chắc mà tôi xây dựng lại cuộc đời mình",
        111: "Bạn không bao giờ quá già để đặt ra một mục tiêu khác hoặc mơ một giấc mơ mới",
        112: "Chính trực là làm điều đúng khi không ai nhìn thấy",
        113: "Hãy cố gắng trở thành cầu vồng trong đám mây của ai đó",
        114: "Bạn là trung bình cộng của năm người bạn dành thời gian nhiều nhất",
        115: "Kỷ luật là cây cầu giữa mục tiêu và thành tựu",
        116: "Bạn bỏ lỡ 100% những cú đánh bạn không thực hiện",
        117: "Tôi đã bỏ lỡ hơn 9000 cú đánh trong sự nghiệp. Tôi đã thua gần 300 trận đấu. Tôi đã được tin tưởng thực hiện cú đánh quyết định và đã bỏ lỡ. Tôi đã thất bại nhiều lần trong cuộc đời. Và đó là lý do tại sao tôi thành công",
        118: "Làm hoặc không làm, không có thử",
        119: "Nếu bạn làm những gì dễ dàng, cuộc sống của bạn sẽ khó khăn. Nhưng nếu bạn làm những gì khó khăn, cuộc sống của bạn sẽ dễ dàng",
        120: "Bạn không cần phải tuyệt vời để bắt đầu, nhưng bạn cần phải bắt đầu để trở nên tuyệt vời",
        121: "Chất lượng cuộc sống của bạn chính là chất lượng các mối quan hệ của bạn",
        122: "Bạn chỉ được trao cho một tia lửa điên rồ nhỏ. Bạn không được để mất nó",
        123: "Đừng lo lắng về bất cứ điều gì, mọi thứ nhỏ nhặt sẽ ổn thôi",
        124: "Một giấc mơ bạn mơ một mình chỉ là một giấc mơ. Một giấc mơ bạn mơ cùng người khác là hiện thực",
        125: "Không hoàn hảo là vẻ đẹp, điên rồ là thiên tài và tốt hơn là hoàn toàn nhàm chán",
        126: "Điều quan trọng nhất là tận hưởng cuộc sống của bạn - hạnh phúc - đó là tất cả những gì quan trọng",
        127: "Để trở nên không thể thay thế, người ta phải luôn khác biệt",
        128: "Ai đó đang ngồi trong bóng mát hôm nay vì ai đó đã trồng cây cách đây nhiều năm",
        129: "Những khách hàng không hài lòng nhất của bạn là nguồn học hỏi lớn nhất của bạn",
        130: "Khi một điều gì đó đủ quan trọng, bạn làm nó ngay cả khi tỷ lệ thành công không có lợi cho bạn",
        131: "Cơ hội kinh doanh giống như xe buýt, luôn có chuyến tiếp theo đến",
        132: "Định kiến là gánh nặng làm rối loạn quá khứ, đe dọa tương lai và làm tê liệt hiện tại",
        133: "Hôm qua tôi thông minh, nên tôi muốn thay đổi thế giới. Hôm nay tôi khôn ngoan, nên tôi đang thay đổi bản thân mình",
        134: "Hãy để bản thân bị thu hút một cách thầm lặng bởi sức hút kỳ lạ của những gì bạn thực sự yêu thích. Nó sẽ không dẫn bạn đi sai đường",
        # Richard Feynman quotes (135-162) - these are already correct
    }
    
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, quote_text, vietnamese_translation, author FROM quotes ORDER BY id")
        all_quotes = cursor.fetchall()
        
        mismatches = []
        corrections_applied = 0
        
        for quote_id, english_text, vietnamese_text, author in all_quotes:
            if quote_id in correct_translations:
                expected_vietnamese = correct_translations[quote_id]
                if vietnamese_text != expected_vietnamese:
                    mismatches.append({
                        'id': quote_id,
                        'author': author,
                        'english': english_text[:60] + "..." if len(english_text) > 60 else english_text,
                        'current_vietnamese': vietnamese_text[:60] + "..." if len(vietnamese_text) > 60 else vietnamese_text,
                        'correct_vietnamese': expected_vietnamese[:60] + "..." if len(expected_vietnamese) > 60 else expected_vietnamese
                    })
                    
                    # Apply correction
                    cursor.execute(
                        "UPDATE quotes SET vietnamese_translation = %s WHERE id = %s",
                        (expected_vietnamese, quote_id)
                    )
                    corrections_applied += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"COMPREHENSIVE TRANSLATION AUDIT RESULTS:")
        print(f"========================================")
        print(f"Total quotes checked: {len(all_quotes)}")
        print(f"Mismatches found: {len(mismatches)}")
        print(f"Corrections applied: {corrections_applied}")
        
        if mismatches:
            print(f"\nMISMATCHES FOUND AND FIXED:")
            for i, mismatch in enumerate(mismatches[:10], 1):  # Show first 10
                print(f"\n{i}. Quote #{mismatch['id']} - {mismatch['author']}")
                print(f"   EN: {mismatch['english']}")
                print(f"   WRONG VI: {mismatch['current_vietnamese']}")
                print(f"   FIXED VI: {mismatch['correct_vietnamese']}")
            
            if len(mismatches) > 10:
                print(f"\n... and {len(mismatches) - 10} more mismatches fixed")
        else:
            print("\n✓ All translations are correctly matched!")
            
    except Exception as e:
        print(f"Error during audit: {e}")

if __name__ == "__main__":
    audit_all_translations()