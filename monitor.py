import os
import requests
import re
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def check_discounts():
    print("🎯 Starting Apple gift card discount check...")
    
    try:
        with sync_playwright() as p:
            print("🌐 Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            print("📡 Navigating to https://amaten.com/exhibitions/apple...")
            page.goto('https://amaten.com/exhibitions/apple', wait_until='networkidle', timeout=60000)
            
            print("⏳ Waiting for page to load...")
            page.wait_for_timeout(5000)
            
            # 获取页面内容
            content = page.content()
            print(f"📊 Page content length: {len(content)} characters")
            
            browser.close()
            
            return content
        
    except Exception as e:
        print(f"❌ Error during discount check: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def extract_discounts_from_html(html_content):
    """从HTML中提取折扣信息"""
    print("🔍 Extracting discounts from HTML using BeautifulSoup...")
    
    discounts = []
    
    try:
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 方法1: 查找所有js-rate元素（主要方法）
        rate_elements = soup.find_all('span', class_='js-rate')
        print(f"📈 Found {len(rate_elements)} js-rate elements")
        
        for element in rate_elements:
            try:
                discount_text = element.get_text().strip()
                discount = float(discount_text)
                
                # 只关注低于85%的折扣
                if discount < 85:
                    # 获取父级行信息用于上下文
                    row = element.find_parent('tr')
                    if row:
                        # 获取面值
                        face_value_elem = row.find('span', class_='js-face_value')
                        face_value = face_value_elem.get_text().strip() if face_value_elem else "Unknown"
                        
                        # 获取价格
                        price_elem = row.find('span', class_='js-price')
                        price = price_elem.get_text().strip() if price_elem else "Unknown"
                        
                        # 获取折扣金额
                        discount_amount_elem = row.find('span', class_='js-discount')
                        discount_amount = discount_amount_elem.get_text().strip() if discount_amount_elem else "Unknown"
                        
                        discounts.append({
                            'discount': discount,
                            'face_value': face_value,
                            'price': price,
                            'discount_amount': discount_amount,
                            'source': 'js-rate element'
                        })
                        print(f"✅ Found discount: {discount}% (面值: {face_value}円 → 价格: {price}円, 节省: {discount_amount}円)")
            except ValueError:
                continue
        
        # 方法2: 在表格行中搜索折扣（备用方法）
        if not discounts:
            print("🔍 Trying alternative search method...")
            rows = soup.find_all('tr', class_='js-gift-row')
            print(f"📊 Found {len(rows)} gift card rows")
            
            for row in rows:
                try:
                    # 在行文本中搜索百分比
                    row_text = row.get_text()
                    percentage_matches = re.findall(r'(\d+\.?\d*)%', row_text)
                    
                    for match in percentage_matches:
                        discount = float(match)
                        if discount < 85:
                            # 检查是否已经添加过这个折扣
                            if not any(abs(d['discount'] - discount) < 0.1 for d in discounts):
                                discounts.append({
                                    'discount': discount,
                                    'face_value': "Unknown",
                                    'price': "Unknown", 
                                    'discount_amount': "Unknown",
                                    'source': 'row text search'
                                })
                                print(f"✅ Found discount in row: {discount}%")
                except:
                    continue
        
        # 按折扣排序（从低到高）
        discounts.sort(key=lambda x: x['discount'])
        
        print(f"📈 Total valid discounts found: {len(discounts)}")
        return discounts
        
    except Exception as e:
        print(f"❌ Error extracting discounts: {str(e)}")
        return []

def send_notification(discounts):
    sckey = os.environ.get('SCKEY')
    if not sckey:
        print("❌ SCKEY environment variable not set")
        return False
    
    try:
        if discounts:
            # 只取最低的3个折扣，避免通知太长
            top_discounts = discounts[:3]
            
            title = f"🎉 发现 {len(discounts)} 个Apple礼品卡优惠!"
            content = "## 🍎 Apple礼品卡优惠提醒\\n\\n"
            content += f"共找到 **{len(discounts)}** 个折扣低于85%的优惠！\\n\\n"
            
            for i, deal in enumerate(top_discounts, 1):
                content += f"{i}. **{deal['discount']}% OFF**\\n"
                content += f"   - 面值: {deal['face_value']}円 → 价格: {deal['price']}円\\n"
                content += f"   - 节省: {deal['discount_amount']}円\\n\\n"
            
            if len(discounts) > 3:
                content += f"... 还有 {len(discounts) - 3} 个其他优惠\\n\\n"
            
            content += "💡 **折扣越低越划算！**\\n"
            content += "\\n🔗 [立即查看](https://amaten.com/exhibitions/apple)"
        else:
            title = "📊 Apple礼品卡监控报告"
            content = "## 🍎 当前无优惠\\n\\n"
            content += "目前没有发现折扣低于85%的Apple礼品卡。\\n"
            content += "\\n监控系统运行正常，下次检查在2小时后。⏰"
        
        print("📨 Sending notification...")
        response = requests.post(
            f"https://sctapi.ftqq.com/{sckey}.send",
            data={
                "title": title,
                "desp": content
            },
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ Notification sent successfully!")
            return True
        else:
            print(f"❌ Notification failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending notification: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🔄 APPLE GIFT CARD MONITOR STARTING")
    print("=" * 60)
    
    start_time = time.time()
    
    # 获取页面内容
    html_content = check_discounts()
    
    if html_content is None:
        print("❌ Failed to get page content")
        return
    
    # 提取折扣信息
    discounts = extract_discounts_from_html(html_content)
    
    # 发送通知
    send_notification(discounts)
    
    execution_time = time.time() - start_time
    print(f"⏱️ Total execution time: {execution_time:.2f} seconds")
    print("=" * 60)
    print("✅ MONITORING COMPLETE")
    
    return discounts

if __name__ == "__main__":
    main()
