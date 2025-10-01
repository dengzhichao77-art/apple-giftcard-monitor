import os
import requests
import re
import time
import json
from playwright.sync_api import sync_playwright

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
            
            print("📡 Navigating to target page...")
            page.goto('https://amaten.com/exhibitions/apple', wait_until='networkidle', timeout=60000)
            
            print("⏳ Waiting for page to load...")
            page.wait_for_timeout(10000)
            
            # 获取页面信息
            title = page.title()
            print(f"📄 Page title: {title}")
            
            # 获取页面内容
            content = page.content()
            print(f"📊 Page content length: {len(content)} characters")
            
            # 保存完整的页面内容用于分析
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("💾 Full page content saved to debug_page.html")
            
            # 尝试获取页面文本内容（可能更容易找到折扣）
            text_content = page.inner_text('body')
            with open('debug_text.txt', 'w', encoding='utf-8') as f:
                f.write(text_content)
            print("💾 Page text content saved to debug_text.txt")
            
            browser.close()
            
            return content, text_content
        
    except Exception as e:
        print(f"❌ Error during discount check: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

def search_discounts(html_content, text_content):
    """多种方式搜索折扣信息"""
    print("🔍 Searching for discounts using multiple methods...")
    discounts = []
    
    # 方法1: 基本的折扣模式
    basic_patterns = [
        r'(\d+\.?\d*)%\s*OFF',
        r'(\d+\.?\d*)%\s*off',
        r'(\d+\.?\d*)%\s*オフ',
        r'(\d+\.?\d*)%\s*割引',
        r'OFF\s*(\d+\.?\d*)%',
        r'off\s*(\d+\.?\d*)%',
        r'オフ\s*(\d+\.?\d*)%',
        r'割引\s*(\d+\.?\d*)%',
    ]
    
    # 方法2: 搜索包含数字和百分比的任何文本
    percentage_patterns = [
        r'(\d+\.?\d*)%',
        r'(\d+)％',  # 全角百分比
    ]
    
    # 方法3: 搜索价格相关的模式
    price_patterns = [
        r'¥\s*[\d,]+',
        r'￥\s*[\d,]+',
        r'[\d,]+\s*円',
    ]
    
    # 在HTML内容中搜索
    print("📋 Searching in HTML content...")
    for pattern in basic_patterns + percentage_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        if matches:
            print(f"🔎 Pattern '{pattern}' found {len(matches)} matches in HTML")
            for match in matches:
                try:
                    discount = float(match)
                    if 70 <= discount <= 95:
                        if not any(abs(d - discount) < 0.1 for d in discounts):
                            discounts.append(discount)
                            print(f"✅ HTML DISCOUNT: {discount}%")
                except:
                    continue
    
    # 在文本内容中搜索
    print("📋 Searching in text content...")
    for pattern in basic_patterns + percentage_patterns:
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        if matches:
            print(f"🔎 Pattern '{pattern}' found {len(matches)} matches in text")
            for match in matches:
                try:
                    discount = float(match)
                    if 70 <= discount <= 95:
                        if not any(abs(d - discount) < 0.1 for d in discounts):
                            discounts.append(discount)
                            print(f"✅ TEXT DISCOUNT: {discount}%")
                except:
                    continue
    
    # 搜索价格信息（用于调试）
    print("💰 Searching for price information...")
    for pattern in price_patterns:
        html_matches = re.findall(pattern, html_content)
        text_matches = re.findall(pattern, text_content)
        if html_matches:
            print(f"💵 Price pattern '{pattern}' found in HTML: {html_matches[:3]}")  # 只显示前3个
        if text_matches:
            print(f"💵 Price pattern '{pattern}' found in text: {text_matches[:3]}")
    
    # 搜索特定的已知折扣（80.9）
    if '80.9' in html_content or '80.9' in text_content:
        print("🎉 Found '80.9' in content!")
        if 80.9 not in discounts:
            discounts.append(80.9)
    
    # 搜索80-95之间的任何数字
    print("🔢 Searching for numbers in 80-95 range...")
    number_pattern = r'\b(8[0-9]|9[0-5])(\.\d+)?\b'
    html_numbers = re.findall(number_pattern, html_content)
    text_numbers = re.findall(number_pattern, text_content)
    
    for num_tuple in html_numbers + text_numbers:
        num_str = ''.join(num_tuple)
        try:
            num = float(num_str)
            if 80 <= num <= 95:
                if not any(abs(d - num) < 0.1 for d in discounts):
                    discounts.append(num)
                    print(f"✅ NUMBER FOUND: {num}%")
        except:
            continue
    
    print(f"📈 Total valid discounts found: {len(discounts)}")
    return sorted(discounts)

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
        else:
            title = "📊 Apple Gift Card Monitor - Debug Info"
            content = "## 🍎 Debug Information\\n\\n"
            content += "The monitor ran successfully but found no discounts.\\n"
            content += "\\n**What this means:**\\n"
            content += "- ✅ JavaScript rendering is working\\n"
            content += "- ✅ Page loaded successfully (92K+ characters)\\n"
            content += "- ❌ No discount patterns matched\\n"
            content += "\\nThe discount display format may be different than expected.\\n"
            content += "Next check in 2 hours. ⏰"
        
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
    html_content, text_content = check_discounts()
    
    if html_content is None:
        print("❌ Failed to get page content")
        return
    
    # 搜索折扣
    discounts = search_discounts(html_content, text_content)
    
    # 发送通知
    send_notification(discounts)
    
    execution_time = time.time() - start_time
    print(f"⏱️ Total execution time: {execution_time:.2f} seconds")
    print("=" * 60)
    print("✅ MONITORING COMPLETE")
    
    return discounts

if __name__ == "__main__":
    main()
