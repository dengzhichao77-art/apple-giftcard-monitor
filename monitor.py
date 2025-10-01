import os
import requests
import re
import time
from playwright.sync_api import sync_playwright

def check_discounts():
    print("🎯 Checking Apple gift card discounts...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            page.goto('https://amaten.com/exhibitions/apple', timeout=30000)
            page.wait_for_timeout(5000)
            
            content = page.content()
            browser.close()
        
        discounts = []
        patterns = [
            r'(\d+\.?\d*)%\s*OFF',
            r'(\d+\.?\d*)%\s*off',
            r'(\d+\.?\d*)%\s*オフ',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    discount = float(match)
                    if 70 <= discount <= 95:
                        if not any(abs(d - discount) < 0.1 for d in discounts):
                            discounts.append(discount)
                            print(f"✅ Found: {discount}% OFF")
                except:
                    continue
        
        return sorted(discounts)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def send_notification(discounts):
    sckey = os.environ.get('SCKEY')
    if not sckey:
        print("❌ No SCKEY set")
        return
    
    try:
        if discounts:
            title = f"🎉 Found {len(discounts)} Apple Gift Card Deals!"
            content = "## Apple Gift Card Discounts\\n\\n"
            for i, discount in enumerate(discounts, 1):
                content += f"{i}. **{discount}% OFF**\\n"
            content += "\\n👉 [View Now](https://amaten.com/exhibitions/apple)"
        else:
            title = "📊 Apple Gift Card Monitor"
            content = "No discounts found. Monitor is running normally."
        
        response = requests.post(
            f"https://sctapi.ftqq.com/{sckey}.send",
            data={"title": title, "desp": content},
            timeout=10
        )
        
        print(f"📨 Notification sent: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Notification failed: {e}")

if __name__ == "__main__":
    print("🔄 Starting monitor...")
    discounts = check_discounts()
    send_notification(discounts)
    print("✅ Done!")
