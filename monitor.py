import os
import requests
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# LINE Messaging API 配置 - 从环境变量读取
LINE_ACCESS_TOKEN = os.environ.get('LINE_ACCESS_TOKEN')
LINE_USER_ID = os.environ.get('LINE_USER_ID')

def send_line_message(message):
    """发送LINE消息给自己"""
    if not LINE_ACCESS_TOKEN or not LINE_USER_ID:
        print("❌ LINE配置信息缺失")
        return False
    
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

def should_run_check():
    """根据当前时间决定是否执行检查"""
    import datetime
    
    # 获取当前日本时间
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    weekday = now.weekday()  # 0=周一, 6=周日
    hour = now.hour
    minute = now.minute
    
    print(f"🕐 当前时间: {now.strftime('%Y-%m-%d %H:%M JST')}, 星期{['一','二','三','四','五','六','日'][weekday]}")
    
    # 0-6点之间：只在0分和30分运行
    if 0 <= hour < 6:
        if minute in [0, 30]:
            print("✅ 0-6点时段，在30分钟间隔时间，执行检查")
            return True
        else:
            print("💤 0-6点时段，非30分钟间隔时间，跳过")
            return False
    
    # 其他时间：每次都执行（因为GitHub调度可能不稳定）
    print("✅ 活跃时段，执行检查")
    return True

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
                
                # 80%以下の割引のみ対象
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

def get_discounts_fingerprint(discounts):
    """生成折扣信息的指纹，用于比较变化"""
    if not discounts:
        return "no_discounts"
    
    # 只取前3个最佳折扣生成指纹
    fingerprint_parts = []
    for deal in discounts[:3]:
        fingerprint_parts.append(f"{deal['discount']}:{deal['face_value']}:{deal['price']}")
    
    return "|".join(fingerprint_parts)

def send_notification(discounts):
    """发送简洁的LINE通知 - 只显示最大的优惠"""
    if not discounts:
        print("📊 没有发现80%以下的折扣，不发送通知")
        return True
    
    try:
        print("📨 发送LINE通知...")
        
        # 只取最大的优惠（折扣率最低的）
        best_deal = discounts[0]
        
        # 构建简洁消息 - 格式: 「79％、10000円→7900円」
        message = f"🎯 {best_deal['discount']}％、{best_deal['face_value']}→{best_deal['price']}"
        
        # 如果有多个优惠，在消息末尾添加数量提示
        if len(discounts) > 1:
            message += f" (他{len(discounts)-1}件)"
        
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
    import datetime
    
    # 获取日本时间
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(jst)
    
    print("=" * 60)
    print(f"🔄 APPLE礼品卡监控启动 - {now.strftime('%Y-%m-%d %H:%M:%S JST')}")
    print("=" * 60)
    
    # 检查是否应该执行
    if not should_run_check():
        print("🎯 本次检查已跳过")
        return
    
    # 原有的监控逻辑...
    start_time = time.time()
    
    # 获取页面内容
    html_content = check_discounts()
    
    if html_content is None:
        print("❌ 页面内容获取失败")
        return
    
    # 提取折扣信息
    discounts = extract_discounts_from_html(html_content)
    
    # 发送通知（暂时每次都发送，因为状态无法持久化）
    send_notification(discounts)
    
    execution_time = time.time() - start_time
    print(f"⏱️ 总执行时间: {execution_time:.2f} 秒")
    print("=" * 60)
    print("✅ 监控完成")
    
    return discounts

if __name__ == "__main__":
    main()
