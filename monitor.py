import os
import requests
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# LINE Messaging API 配置 - 使用您提供的凭证
LINE_ACCESS_TOKEN = "IvrlgZ9u0izzW2C3Eb0xyHvprQHH0x70DMf99E4itGBe0HsqYX8JE4MTdzCpSm9e2VmqhoNPCWgIk6LVeAHrXiQCmTBcoZ6ag6KPiI8BIntkrUlXfORESUWdlO60BgwE0PJ9XFIbO37ugR+eo4B5swdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "U7278cf6212a50c40127da84e3c5e2f27"

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
        elif response.status_code == 401:
            print("❌ Access Token无效")
            return False
        elif response.status_code == 403:
            print("❌ 权限不足，请检查Channel设置")
            return False
        else:
            print(f"❌ LINE消息发送失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ LINE消息发送错误: {str(e)}")
        return False

def send_line_flex_message(discounts):
    """发送更美观的LINE Flex Message"""
    try:
        url = "https://api.line.me/v2/bot/message/push"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
        }
        
        if discounts:
            # 创建折扣信息的Flex Message
            bubbles = []
            
            for i, deal in enumerate(discounts[:5]):  # 最多显示5个
                bubble = {
                    "type": "bubble",
                    "size": "micro",
                    "body": {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"{deal['discount']}% OFF",
                                "weight": "bold",
                                "size": "lg",
                                "color": "#1DB446"
                            },
                            {
                                "type": "separator",
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "margin": "lg",
                                "spacing": "sm",
                                "contents": [
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "額面",
                                                "color": "#aaaaaa",
                                                "size": "sm",
                                                "flex": 2
                                            },
                                            {
                                                "type": "text",
                                                "text": deal['face_value'],
                                                "wrap": True,
                                                "color": "#666666",
                                                "size": "sm",
                                                "flex": 4
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "価格",
                                                "color": "#aaaaaa",
                                                "size": "sm",
                                                "flex": 2
                                            },
                                            {
                                                "type": "text",
                                                "text": deal['price'],
                                                "wrap": True,
                                                "color": "#666666",
                                                "size": "sm",
                                                "flex": 4
                                            }
                                        ]
                                    },
                                    {
                                        "type": "box",
                                        "layout": "baseline",
                                        "contents": [
                                            {
                                                "type": "text",
                                                "text": "節約",
                                                "color": "#aaaaaa",
                                                "size": "sm",
                                                "flex": 2
                                            },
                                            {
                                                "type": "text",
                                                "text": deal['discount_amount'],
                                                "wrap": True,
                                                "color": "#FF0000",
                                                "size": "sm",
                                                "flex": 4,
                                                "weight": "bold"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    "footer": {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "sm",
                        "contents": [
                            {
                                "type": "button",
                                "style": "primary",
                                "height": "sm",
                                "action": {
                                    "type": "uri",
                                    "label": "購入ページへ",
                                    "uri": "https://amaten.com/exhibitions/apple"
                                }
                            }
                        ]
                    }
                }
                bubbles.append(bubble)
            
            # 添加总结bubble
            summary_bubble = {
                "type": "bubble",
                "size": "micro",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📊 サマリー",
                            "weight": "bold",
                            "size": "lg",
                            "color": "#000000"
                        },
                        {
                            "type": "separator",
                            "margin": "md"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "見つけた割引",
                                            "color": "#aaaaaa",
                                            "size": "sm",
                                            "flex": 3
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{len(discounts)}件",
                                            "wrap": True,
                                            "color": "#1DB446",
                                            "size": "sm",
                                            "flex": 2,
                                            "weight": "bold"
                                        }
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "baseline",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "最低割引",
                                            "color": "#aaaaaa",
                                            "size": "sm",
                                            "flex": 3
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{discounts[0]['discount']}%",
                                            "wrap": True,
                                            "color": "#FF0000",
                                            "size": "sm",
                                            "flex": 2,
                                            "weight": "bold"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
            bubbles.append(summary_bubble)
            
            message_data = {
                "to": LINE_USER_ID,
                "messages": [
                    {
                        "type": "flex",
                        "altText": f"Appleギフトカード割引 {len(discounts)}件見つかりました",
                        "contents": {
                            "type": "carousel",
                            "contents": bubbles
                        }
                    }
                ]
            }
        else:
            # 没有折扣时的简单消息
            message_data = {
                "to": LINE_USER_ID,
                "messages": [
                    {
                        "type": "text",
                        "text": "📊 Appleギフトカード監視レポート\n\n現在、85%以下の割引商品は見つかりませんでした。\n\n次のチェックは2時間後です。⏰"
                    }
                ]
            }
        
        response = requests.post(url, headers=headers, json=message_data)
        
        if response.status_code == 200:
            print("✅ LINE Flex Message送信成功!")
            return True
        else:
            print(f"❌ LINE Flex Message送信失敗: {response.status_code}")
            # 失败时回退到普通文本消息
            if discounts:
                message = f"🎉 Appleギフトカード割引情報\n\n{len(discounts)}件の割引商品が見つかりました！\n\n"
                for deal in discounts[:3]:
                    message += f"• {deal['discount']}% OFF (額面: {deal['face_value']} → 価格: {deal['price']})\n"
                message += "\n🔗 https://amaten.com/exhibitions/apple"
            else:
                message = "📊 現在、85%以下の割引商品は見つかりませんでした。"
            
            return send_line_message(message)
            
    except Exception as e:
        print(f"❌ LINE Flex Message送信エラー: {str(e)}")
        return False

def check_discounts():
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
                
                # 85%以下の割引のみ対象
                if discount < 85:
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
        
        print(f"📈 有効な割引合計: {len(discounts)} 件")
        return discounts
        
    except Exception as e:
        print(f"❌ 割引抽出エラー: {str(e)}")
        return []

def send_notification(discounts):
    """LINEに通知を送信"""
    try:
        print("📨 LINE通知を送信...")
        
        # Flex Messageで送信
        success = send_line_flex_message(discounts)
        
        if success:
            print("✅ LINE通知送信成功!")
            return True
        else:
            print("❌ LINE通知送信失敗")
            return False
            
    except Exception as e:
        print(f"❌ LINE通知送信エラー: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🔄 APPLEギフトカードモニター起動")
    print("=" * 60)
    
    start_time = time.time()
    
    # ページコンテンツを取得
    html_content = check_discounts()
    
    if html_content is None:
        print("❌ ページコンテンツの取得に失敗")
        return
    
    # 割引情報を抽出
    discounts = extract_discounts_from_html(html_content)
    
    # LINE通知を送信
    send_notification(discounts)
    
    execution_time = time.time() - start_time
    print(f"⏱️ 総実行時間: {execution_time:.2f} 秒")
    print("=" * 60)
    print("✅ モニタリング完了")
    
    return discounts

if __name__ == "__main__":
    main()
