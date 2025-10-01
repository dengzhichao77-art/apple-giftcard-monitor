import os
import requests
import re
import time
import sys
from playwright.sync_api import sync_playwright

def check_discounts():
    print("🎯 Starting Apple gift card discount check...")
    
    try:
        with sync_playwright() as p:
            print("🌐 Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # 设置用户代理
            page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            print("📡 Navigating to https://amaten.com/exhibitions/apple...")
            page.goto('https://amaten.com/exhibitions/apple', wait_until='networkidle', timeout=60000)
            
            print("⏳ Waiting for page to load (10 seconds)...")
            page.wait_for_timeout(10000)
            
            # 获取页面信息用于调试
            title = page.title()
            print(f"📄 Page title: {title}")
            
            # 获取页面内容
            content = page.content()
            print(f"📊 Page content length: {len(content)} characters")
            
            # 保存页面内容到文件用于调试（可选）
            with open('page_content.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("💾 Page content saved to page_content.html")
            
            browser.close()
        
        print("🔍 Searching for discounts in page content...")
        discounts = []
        
        # 折扣匹配模式
        patterns = [
            r'(\d+\.?\d*)%\s*OFF',
            r'(\d+\.?\d*)%\s*off',
            r'(\d+\.?\d*)%\s*オフ',
            r'(\d+\.?\d*)%\s*割引',
            r'OFF\s*(\d+\.?\d*)%',
            r'off\s*(\d+\.?\d*)%',
        ]
        
        found_count = 0
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            print(f"🔎 Pattern '{pattern}' found {len(matches)} matches")
            
            for match in matches:
                try:
                    discount = float(match)
                    found_count += 1
                    print(f"   - Found: {discount}%")
                    
                    # 只关注正常的折扣范围
                    if 70 <= discount <= 95:
                        # 去重检查
                        is_duplicate = any(abs(existing - discount) < 0.1 for existing in discounts)
                        if not is_duplicate:
                            discounts.append(discount)
                            print(f"✅ VALID DISCOUNT: {discount}% OFF")
                except ValueError:
                    continue
        
        print(f"📈 Search summary: {found_count} total matches, {len(discounts)} valid discounts")
        
        if discounts:
            print(f"🎯 Final valid discounts: {discounts}")
        else:
            print("❌ No valid discounts found in the 70-95% range")
            
        return sorted(discounts)
        
    except Exception as e:
        print(f"❌ Error during discount check: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

def send_notification(discounts):
    sckey = os.environ.get('SCKEY')
    if not sckey:
        print("❌ SCKEY environment variable not set")
        return False
    
    try:
        if discounts:
            title = f"🎉 Found {len(discounts)} Apple Gift Card Deals!"
            content = "## 🍎 Apple Gift Card Discount Alert!\\n\\n"
            
            for i, discount in enumerate(discounts, 1):
                content += f"{i}. **{discount}% OFF**\\n"
            
            content += "\\n---\\n"
            content += "💡 Lower percentage = Better deal!\\n"
            content += "\\n🔗 [View on Amaten](https://amaten.com/exhibitions/apple)"
            
            print(f"📨 Sending notification with {len(discounts)} discounts")
        else:
            title = "📊 Apple Gift Card Monitor Report"
            content = "## 🍎 No Discounts Found\\n\\n"
            content += "Currently no Apple gift card discounts below 85% were found.\\n"
            content += "The monitoring system is running normally.\\n\\n"
            content += "Next check in 2 hours. ⏰"
            
            print("📨 Sending 'no discounts' notification")
        
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
    
    # 检查折扣
    discounts = check_discounts()
    
    # 发送通知
    send_notification(discounts)
    
    execution_time = time.time() - start_time
    print(f"⏱️ Total execution time: {execution_time:.2f} seconds")
    print("=" * 60)
    print("✅ MONITORING COMPLETE")
    
    return discounts

if __name__ == "__main__":
    main()
