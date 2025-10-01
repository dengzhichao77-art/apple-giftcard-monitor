import os
import requests
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# LINE Messaging API 配置 - 从环境变量读取
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')

# 全局变量用于跟踪上一次的折扣信息
last_discounts = []

def send_line_message(message):
    """发送LINE消息给自己"""
    try:
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
        }
        
        message_data = {
            "to": LINE_USER_ID,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=message_data)
        
        if response.status_code == 200:
            print("✅ LINE消息发送成功!")
            return True
        else:
            print(f"❌ LINE消息发送失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ LINE消息发送错误: {str(e)}")
        return False

def check_discounts():
    """检查折扣信息"""
    print("🎯 Appleギフトカード割引チェック開始...")
    
    try:
        with sync_playwright() as p:
            print("🌐 ブラウザ起動...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            print("📡 https://amaten.com/exhibitions/apple にアクセス...")
            page.goto('https://amaten.com/exhibitions/apple', wait_until='networkidle', timeout=60000)
            
            print("⏳ ページ読み込み待機...")
            page.wait_for_timeout(5000)
            
            content = page.content()
            print(f"📊 ページコンテンツ長: {len(content)} 文字")
            
            browser.close()
            return content
        
    except Exception as e:
        print(f"❌ 割引チェックエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def extract_discounts_from_html(html_content):
    """HTMLから割引情報を抽出"""
    print("🔍 BeautifulSoupでHTMLから割引情報を抽出...")
    
    discounts = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # js-rate要素を検索
        rate_elements = soup.find_all('span', class_='js-rate')
        print(f"📈 {len(rate_elements)} 個のjs-rate要素を発見")
        
        for element in rate_elements:
            try:
                discount_text = element.get_text().strip()
                discount = float(discount_text)
                
                # 80%以下の割引のみ対象（新需求）
                if discount < 80:
                    row = element.find_parent('tr')
                    if row:
                        face_value_elem = row.find('span', class_='js-face_value')
                        face_value = face_value_elem.get_text().strip() if face_value_elem else "不明"
                        
                        price_elem = row.find('span', class_='js-price')
                        price = price_elem.get_text().strip() if price_elem else "不明"
                        
                        discount_amount_elem = row.find('span', class_='js-discount')
                        discount_amount = discount_amount_elem.get_text().strip() if discount_amount_elem else "不明"
                        
                        discounts.append({
                            'discount': discount,
                            'face_value': face_value,
                            'price': price,
                            'discount_amount': discount_amount,
                            'source': 'js-rate element'
                        })
                        print(f"✅ 割引発見: {discount}% (額面: {face_value} → 価格: {price}, 節約: {discount_amount})")
            except ValueError:
                continue
        
        # 割引率でソート（低い順）
        discounts.sort(key=lambda x: x['discount'])
        
        print(f"📈 80%以下の割引合計: {len(discounts)} 件")
        return discounts
        
    except Exception as e:
        print(f"❌ 割引抽出エラー: {str(e)}")
        return []

def has_discounts_changed(new_discounts):
    """检查折扣信息是否有变化"""
    global last_discounts
    
    # 如果之前没有记录，直接返回True
    if not last_discounts:
        last_discounts = new_discounts
        return True
    
    # 比较折扣数量和最低折扣
    if len(new_discounts) != len(last_discounts):
        last_discounts = new_discounts
        return True
    
    # 比较每个折扣项
    for i, (new, old) in enumerate(zip(new_discounts, last_discounts)):
        if (new['discount'] != old['discount'] or 
            new['face_value'] != old['face_value'] or
            new['price'] != old['price']):
            last_discounts = new_discounts
            return True
    
    # 没有变化
    return False

def send_notification(discounts):
    """发送简洁的LINE通知"""
    if not discounts:
        print("📊 没有发现80%以下的折扣，不发送通知")
        return True
    
    # 检查折扣是否有变化
    if not has_discounts_changed(discounts):
        print("📊 折扣信息没有变化，不发送通知")
        return True
    
    try:
        print("📨 发送LINE通知...")
        
        # 构建简洁消息
        if discounts:
            # 只显示最低的几个折扣
            min_discounts = discounts[:3]  # 最多显示3个
            
            message = "🎯 Apple礼品卡优惠更新\n\n"
            
            for deal in min_discounts:
                message += f"• {deal['discount']}%优惠幅度出现\n"
            
            if len(discounts) > 3:
                message += f"• 还有{len(discounts)-3}个其他优惠\n"
            
            message += "\n🔗 查看详情: https://amaten.com/exhibitions/apple"
        else:
            message = "📊 当前无80%以下优惠"
        
        success = send_line_message(message)
        
        if success:
            print("✅ 通知发送成功!")
            return True
        else:
            print("❌ 通知发送失败")
            return False
            
    except Exception as e:
        print(f"❌ 发送通知时出错: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🔄 APPLE礼品卡监控启动")
    print("=" * 60)
    
    start_time = time.time()
    
    # 获取页面内容
    html_content = check_discounts()
    
    if html_content is None:
        print("❌ 页面内容获取失败")
        return
    
    # 提取折扣信息
    discounts = extract_discounts_from_html(html_content)
    
    # 发送通知（只在有变化时发送）
    send_notification(discounts)
    
    execution_time = time.time() - start_time
    print(f"⏱️ 总执行时间: {execution_time:.2f} 秒")
    print("=" * 60)
    print("✅ 监控完成")
    
    return discounts

if __name__ == "__main__":
    main()
