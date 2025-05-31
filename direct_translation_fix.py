#!/usr/bin/env python3
"""
Direct translation fix using predefined accurate Vietnamese translations
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

def apply_direct_translations():
    """Apply accurate Vietnamese translations directly"""
    
    # Complete accurate translations for all quotes
    translations = {
        # Vietnamese originals (keep as is)
        1: "Study, study more, study forever",
        2: "Nothing is more precious than independence and freedom",
        3: "Unity is strength",
        4: "Failure is the mother of success",
        5: "With perseverance, an iron rod can be ground into a needle",
        6: "If you want to go fast, go alone. If you want to go far, go together",
        7: "Kiến thức là sức mạnh",
        8: "Tương lai thuộc về những người tin vào vẻ đẹp của giấc mơ",
        9: "Hành trình nghìn dặm bắt đầu từ một bước chân",
        10: "Đừng chờ đợi cơ hội, hãy tạo ra nó",
        11: "Thành công không phải là chìa khóa của hạnh phúc. Hạnh phúc là chìa khóa của thành công",
        12: "Chỉ có một cách để tránh chỉ trích: không làm gì, không nói gì và không là gì cả",
        13: "Water flowing constantly wears away stone",
        14: "The last drop makes the cup overflow",
        15: "One tree cannot make a forest, but three trees together can create green shade",
        16: "Cách duy nhất để làm việc tuyệt vời là yêu thích những gì bạn làm",
        17: "Cuộc sống là những gì xảy ra với bạn khi bạn đang bận rộn lập kế hoạch khác",
        18: "Hãy là chính mình; tất cả những người khác đã có chủ rồi",
        19: "Tương lai thuộc về những ai tin vào vẻ đẹp của giấc mơ của họ",
        20: "Cách tốt nhất để dự đoán tương lai là tạo ra nó",
        21: "Cuộc sống thực sự đơn giản, nhưng chúng ta cứ khăng khăng làm nó phức tạp",
        22: "Cơ hội thường được ngụy trang dưới dạng công việc khó khăn",
        23: "Tôi không thất bại. Tôi chỉ vừa tìm ra 10.000 cách không hoạt động",
        24: "Thiên tài là một phần trăm cảm hứng và chín mươi chín phần trăm mồ hôi",
        25: "Hãy cư xử như thể những gì bạn làm tạo ra sự khác biệt. Bởi vì nó thật sự tạo ra sự khác biệt",
        26: "Chúng ta kiếm sống bằng những gì chúng ta có được, nhưng chúng ta tạo dựng cuộc sống bằng những gì chúng ta cho đi",
        27: "Những đế chế của tương lai là những đế chế của tâm trí",
        28: "Diều bay cao nhất khi bay ngược gió, không phải khi bay xuôi gió",
        29: "Hãy nói cho tôi nghe và tôi sẽ quên. Hãy dạy tôi và tôi có thể nhớ. Hãy để tôi tham gia và tôi sẽ học",
        30: "Đầu tư vào kiến thức luôn mang lại lợi nhuận tốt nhất",
        31: "Làm tốt hơn nói hay",
        32: "Trí tưởng tượng quan trọng hơn kiến thức",
        33: "Đừng cố gắng trở thành người thành công, mà hãy cố gắng trở thành người có giá trị",
        34: "Điều quan trọng là không bao giờ ngừng đặt câu hỏi",
        35: "Hai ngày quan trọng nhất trong đời bạn là ngày bạn sinh ra và ngày bạn tìm ra lý do tại sao",
        36: "Lòng can đảm không phải là không có sợ hãi, mà là đánh giá rằng có điều gì đó quan trọng hơn nỗi sợ",
        37: "Lòng tử tế là ngôn ngữ mà người điếc có thể nghe và người mù có thể nhìn thấy",
        38: "Nếu bạn không thích điều gì đó, hãy thay đổi nó. Nếu bạn không thể thay đổi, hãy thay đổi thái độ của mình",
        39: "Tôi đã học được rằng mọi người sẽ quên những gì bạn nói, quên những gì bạn làm, nhưng họ sẽ không bao giờ quên cảm giác bạn mang lại cho họ",
        40: "Giáo dục là vũ khí mạnh mẽ nhất bạn có thể sử dụng để thay đổi thế giới",
        41: "Điều gì cũng có vẻ bất khả thi cho đến khi nó được thực hiện",
        42: "Hãy là sự thay đổi mà bạn muốn thấy ở thế giới",
        43: "Hãy sống như thể bạn sẽ chết vào ngày mai. Hãy học như thể bạn sẽ sống mãi mãi",
        44: "Bóng tối không thể xua đuổi bóng tối; chỉ có ánh sáng mới làm được điều đó. Hận thù không thể xua đuổi hận thù; chỉ có tình yêu mới làm được điều đó",
        45: "Lúc nào cũng là thời điểm thích hợp để làm điều đúng đắn",
        46: "Công việc của bạn sẽ chiếm một phần lớn cuộc đời bạn, và cách duy nhất để thực sự hài lòng là làm những gì bạn tin là công việc tuyệt vời",
        47: "Hãy luôn khao khát, hãy luôn ngây thơ",
        48: "Những gì ở phía sau chúng ta và những gì ở phía trước chúng ta chỉ là những vấn đề nhỏ so với những gì ở bên trong chúng ta",
        49: "Đừng đi theo con đường có sẵn, thay vào đó hãy đi nơi không có đường và để lại dấu vết",
        50: "Hãy là chính mình; tất cả những người khác đã có chủ rồi",
        51: "Tất cả chúng ta đều ở trong rãnh, nhưng một số người trong chúng ta đang nhìn lên những vì sao",
        52: "Hạnh phúc không phải là điều gì đó có sẵn. Nó đến từ hành động của chính bạn",
        53: "Bạn chỉ sống một lần, nhưng nếu bạn sống đúng cách, một lần là đủ",
        54: "Thành công là đi từ thất bại này đến thất bại khác mà không mất đi nhiệt tình",
        55: "Bạn không thể quay lại và thay đổi khởi đầu, nhưng bạn có thể bắt đầu từ nơi bạn đang đứng và thay đổi kết thúc",
        56: "Cách tốt nhất để dự đoán tương lai là tạo ra nó",
        57: "Cuộc sống thực sự đơn giản, nhưng chúng ta cứ khăng khăng làm nó phức tạp",
        58: "Người khôn ngoan học từ mọi người. Người bình thường học từ kinh nghiệm của họ. Kẻ ngốc không học hỏi gì cả",
        59: "Thời gian bạn thích lãng phí không phải là thời gian lãng phí",
        60: "Tôi không thất bại. Tôi chỉ vừa tìm ra 10.000 cách không hoạt động",
        61: "Thiên tài là một phần trăm cảm hứng và chín mươi chín phần trăm mồ hôi",
        62: "Cơ hội thường được ngụy trang dưới dạng công việc khó khăn",
        63: "Tôi không thất bại. Tôi chỉ vừa tìm ra 10.000 cách không hoạt động",
        64: "Một người chưa bao giờ mắc lỗi thì chưa bao giờ thử làm điều gì mới",
        65: "Hãy cư xử như thể những gì bạn làm tạo ra sự khác biệt. Bởi vì nó thật sự tạo ra sự khác biệt",
        66: "Tình yêu không làm cho thế giới quay, nhưng nó làm cho cuộc hành trình trở nên đáng giá",
        67: "Cuộc sống không phải về việc tìm kiếm bản thân. Cuộc sống là về việc tạo ra bản thân",
        68: "Cách duy nhất để thực hiện công việc tuyệt vời là yêu thích những gì bạn làm",
        69: "Sự khác biệt giữa những người thành công và những người khác không phải là thiếu sức mạnh, thiếu kiến thức, mà là thiếu ý chí",
        70: "Đừng chờ đợi cơ hội. Hãy tạo ra chúng",
        71: "Tương lai thuộc về những ai chuẩn bị cho nó ngày hôm nay",
        72: "Thành công thường đến với những người quá bận rộn để tìm kiếm nó",
        73: "Đừng sợ từ bỏ điều tốt để theo đuổi điều tuyệt vời",
        74: "Cách duy nhất để làm điều bất khả thi là tin rằng nó có thể thực hiện được",
        75: "Cuộc sống không đo bằng số hơi thở bạn thở, mà bằng những khoảnh khắc khiến bạn nín thở",
        76: "Hạnh phúc không phải là đích đến, nó là cách thức di chuyển",
        77: "Bạn bỏ lỡ 100% những cú đánh bạn không thực hiện",
        78: "Tôi đã bỏ lỡ hơn 9000 cú đánh trong sự nghiệp. Tôi đã thua gần 300 trận đấu. 26 lần tôi được tin tưởng thực hiện cú đánh quyết định và đã bỏ lỡ. Tôi đã thất bại nhiều lần trong cuộc đời. Và đó chính là lý do tại sao tôi thành công",
        79: "Làm hoặc không làm, không có thử",
        80: "Nếu bạn làm những gì dễ dàng, cuộc sống của bạn sẽ khó khăn. Nhưng nếu bạn làm những gì khó khăn, cuộc sống của bạn sẽ dễ dàng",
        81: "Bạn không cần phải tuyệt vời để bắt đầu, nhưng bạn cần phải bắt đầu để trở nên tuyệt vời",
        82: "Chất lượng cuộc sống của bạn chính là chất lượng các mối quan hệ của bạn",
        83: "Bạn chỉ được trao cho một tia lửa điên rồ nhỏ. Bạn không được để mất nó",
        84: "Đừng lo lắng về bất cứ điều gì, mọi thứ nhỏ nhặt sẽ ổn thôi",
        85: "Một giấc mơ bạn mơ một mình chỉ là một giấc mơ. Một giấc mơ bạn mơ cùng người khác là hiện thực",
        86: "Không hoàn hảo là vẻ đẹp, điên rồ là thiên tài và tốt hơn là hoàn toàn nhàm chán",
        87: "Điều quan trọng nhất là tận hưởng cuộc sống của bạn - hạnh phúc - đó là tất cả những gì quan trọng",
        88: "Để trở nên không thể thay thế, người ta phải luôn khác biệt",
        89: "Ai đó đang ngồi trong bóng mát hôm nay vì ai đó đã trồng cây cách đây nhiều năm",
        90: "Những khách hàng không hài lòng nhất của bạn là nguồn học hỏi lớn nhất của bạn",
        91: "Khi một điều gì đó đủ quan trọng, bạn làm nó ngay cả khi tỷ lệ thành công không có lợi cho bạn",
        92: "Thật thú vị khi làm những điều bất khả thi",
        93: "Định kiến là gánh nặng làm rối loạn quá khứ, đe dọa tương lai và làm tê liệt hiện tại",
        94: "Hôm qua tôi thông minh, nên tôi muốn thay đổi thế giới. Hôm nay tôi khôn ngoan, nên tôi đang thay đổi bản thân mình",
        95: "Không phải tất cả chúng ta đều có thể làm những việc tuyệt vời. Nhưng chúng ta có thể làm những việc nhỏ với tình yêu tuyệt vời",
        96: "Hãy cho, nhưng cho đến khi nó đau đớn",
        97: "Hai con đường phân chia trong rừng, và tôi— tôi đã chọn con đường ít người đi, và điều đó đã tạo nên sự khác biệt",
        98: "Trong ba từ tôi có thể tóm tắt mọi thứ tôi đã học được về cuộc sống: nó tiếp tục",
        99: "Và, khi bạn muốn điều gì đó, toàn bộ vũ trụ sẽ đồng lòng giúp bạn đạt được nó",
        100: "Chỉ có một điều làm cho giấc mơ trở nên bất khả thi: nỗi sợ thất bại",
        101: "Hành trình nghìn dặm bắt đầu từ một bước chân",
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
        135: "Tôi không biết điều gì, nhưng tôi biết những điều tôi không biết",
        136: "Khoa học là một cách suy nghĩ hơn nhiều so với một kho kiến thức",
        137: "Nghiên cứu là những gì tôi đang làm khi tôi không biết mình đang làm gì",
        138: "Tôi thà có câu hỏi không thể trả lời còn hơn câu trả lời không thể đặt câu hỏi",
        139: "Tự nhiên không quan tâm đến những khó khăn toán học của chúng ta. Nó tích hợp một cách thực nghiệm",
        140: "Tôi có thể sống với sự nghi ngờ, và không chắc chắn, và không biết",
        141: "Học từ thực nghiệm, điều đó là tất cả",
        142: "Thật kỳ lạ khi càng biết nhiều, tôi càng chắc chắn về việc mình không biết gì",
        143: "Nếu bạn muốn học về tự nhiên, để đánh giá các ý tưởng như thế nào, điều quan trọng là phải học cách nghĩ",
        144: "Tôi nghĩ điều quan trọng là có một sự cân bằng giữa việc tôn trọng lửa và được làm quen với nó",
        145: "Giáo dục là điều còn lại sau khi một người đã quên tất cả những gì họ học được ở trường",
        146: "Nếu bạn nghĩ bạn hiểu cơ học lượng tử, bạn không hiểu cơ học lượng tử",
        147: "Việc phải tôn trọng những người khác bởi lý do họ giữ những chức vụ nhất định đối với tôi là vô nghĩa",
        148: "Tôi sẽ không làm gì hết nếu ai đó bảo tôi phải làm gì",
        149: "Tôi muốn biết cách Chúa tạo ra thế giới này",
        150: "Nghiên cứu là những gì tôi làm khi tôi chơi",
        151: "Vật lý không giống như toán học, và toán học không giống như vật lý",
        152: "Điều đó đâu có nghĩa là nó sai; điều đó có nghĩa là bạn chưa hiểu nó đủ tốt",
        153: "Tôi không có trách nhiệm phải sống theo kỳ vọng của người khác",
        154: "Thật vô nghĩa khi giả vờ bạn biết khi bạn không biết",
        155: "Nếu điều gì đó không đúng với bạn, đừng làm điều đó",
        156: "Có thể bạn không tin vào điều đó, nhưng tôi thật sự thích làm việc",
        157: "Tôi không quan tâm đến việc nổi tiếng. Tôi chỉ muốn được để yên",
        158: "Toán học không phải là khoa học thực",
        159: "Tôi không thể tạo ra những phát minh. Tôi không biết cách làm điều đó",
        160: "Vấn đề với tương lai là nó liên tục trở thành quá khứ",
        161: "Tôi biết mọi thứ trông như thế nào và tôi biết rằng có rất nhiều điều tôi không biết",
        162: "Tôi biết tôi không biết gì, nhưng ít nhất tôi biết điều đó"
    }
    
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        success_count = 0
        
        for quote_id, vietnamese_text in translations.items():
            cursor.execute(
                "UPDATE quotes SET vietnamese_translation = %s WHERE id = %s",
                (vietnamese_text, quote_id)
            )
            success_count += 1
            if success_count % 20 == 0:
                print(f"Applied {success_count} translations...")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✓ Successfully applied {success_count} Vietnamese translations")
        return True
        
    except Exception as e:
        print(f"Error applying translations: {e}")
        return False

def verify_completion():
    """Verify all quotes have Vietnamese translations"""
    conn = get_database_connection()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE vietnamese_translation IS NULL")
        missing = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM quotes")
        total = cursor.fetchone()[0]
        
        print(f"\nVerification Results:")
        print(f"Total quotes: {total}")
        print(f"Missing translations: {missing}")
        print(f"Complete translations: {total - missing}")
        
        if missing == 0:
            print("✅ ALL QUOTES NOW HAVE VIETNAMESE TRANSLATIONS!")
        else:
            print(f"⚠️ {missing} quotes still missing translations")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error during verification: {e}")

def main():
    print("🔄 APPLYING DIRECT VIETNAMESE TRANSLATIONS")
    print("==========================================")
    
    success = apply_direct_translations()
    if success:
        verify_completion()
    else:
        print("❌ Failed to apply translations")

if __name__ == "__main__":
    main()