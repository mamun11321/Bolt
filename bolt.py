#!/usr/bin/env python3
"""
Bolt SMS - সম্পূর্ণ অটোমেটিক OTP মনিটর বট
- 0.5 সেকেন্ড পরপর OTP চেক করে
- প্রতি 1.5 সেকেন্ড পরপর ব্রাউজার রিফ্রেশ করে
- চালু হওয়ার সাথে সাথে আজকের সব OTP ফরওয়ার্ড করে
- ডুপ্লিকেট OTP এড়ায়
"""

import os
import sys
import time
import json
import logging
import re
import asyncio
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

# ========== কনফিগারেশন ==========
TELEGRAM_BOT_TOKEN = "8618305528:AAF64PwFIlsw091Hbns8fGQqvwVSW6_4iCY"
GROUP_CHAT_ID = "-1001153782407"
USERNAME = "Sohaib12"
PASSWORD = "mamun1132"
BASE_URL = "http://93.190.143.35"
LOGIN_URL = f"{BASE_URL}/ints/Login"
SMS_PAGE_URL = f"{BASE_URL}/ints/agent/SMSCDRReports"

# ChromeDriver পাথ - Desktop এ রাখুন
CHROMEDRIVER_PATH = r"C:\Users\mamun\Desktop\chromedriver.exe"
# =================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('otp_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OTPBot:
    def __init__(self):
        self.driver = None
        self.logged_in = False
        self.processed_otps = self._load_processed_otps()
        self.total_otps_sent = 0
        self.is_monitoring = True
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.refresh_counter = 0
        
        patterns = [
            r'\b\d{4}\b', r'\b\d{5}\b', r'\b\d{6}\b',
            r'code[:\s]*\d+', r'OTP[:\s]*\d+',
            r'Telegram code[:\s]*\d+',
            r'WhatsApp code[:\s]*[\d-]+',
        ]
        self.otp_regex = re.compile('|'.join(patterns), re.IGNORECASE)
        
        logger.info("🤖 Bolt SMS OTP Monitor Bot Initialized")
    
    def _load_processed_otps(self):
        try:
            if os.path.exists('processed_otps.json'):
                with open('processed_otps.json', 'r') as f:
                    data = json.load(f)
                cutoff = datetime.now() - timedelta(hours=24)
                return {k for k, v in data.items() if datetime.fromisoformat(v) > cutoff}
        except:
            pass
        return set()
    
    def _save_processed_otps(self):
        try:
            data = {otp_id: datetime.now().isoformat() for otp_id in self.processed_otps}
            with open('processed_otps.json', 'w') as f:
                json.dump(data, f)
        except:
            pass
    
    def setup_browser(self):
        try:
            if not os.path.exists(CHROMEDRIVER_PATH):
                logger.error(f"❌ ChromeDriver not found at: {CHROMEDRIVER_PATH}")
                logger.info("💡 Please copy chromedriver.exe to Desktop")
                return False
            
            chrome_options = Options()
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            service = Service(CHROMEDRIVER_PATH)
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            logger.info("✅ Browser opened")
            return True
        except Exception as e:
            logger.error(f"Browser error: {e}")
            return False
    
    def solve_captcha(self):
        try:
            captcha_text = self.driver.find_element(By.XPATH, "//div[contains(text(), 'What is')]").text
            match = re.search(r'(\d+)\s*\+\s*(\d+)', captcha_text)
            if match:
                num1 = int(match.group(1))
                num2 = int(match.group(2))
                result = num1 + num2
                logger.info(f"🔍 Captcha: {num1} + {num2} = {result}")
                
                captcha_input = self.driver.find_element(By.NAME, "capt")
                captcha_input.clear()
                captcha_input.send_keys(str(result))
                return True
            return False
        except Exception as e:
            logger.error(f"Captcha error: {e}")
            return False
    
    def auto_login(self):
        try:
            logger.info("🔐 Logging in...")
            
            self.driver.get(LOGIN_URL)
            time.sleep(3)
            
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(USERNAME)
            logger.info(f"✅ Username: {USERNAME}")
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(PASSWORD)
            logger.info("✅ Password entered")
            
            time.sleep(1)
            self.solve_captcha()
            
            time.sleep(1)
            try:
                login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
                login_btn.click()
                logger.info("✅ Login button clicked")
            except:
                try:
                    login_btn = self.driver.find_element(By.XPATH, "//input[@type='submit']")
                    login_btn.click()
                    logger.info("✅ Login button clicked")
                except:
                    try:
                        login_btn = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Sign In')]")
                        login_btn.click()
                        logger.info("✅ Login button clicked")
                    except:
                        form = self.driver.find_element(By.TAG_NAME, "form")
                        form.submit()
                        logger.info("✅ Form submitted")
            
            time.sleep(5)
            
            current_url = self.driver.current_url
            logger.info(f"📍 URL: {current_url}")
            
            if 'agent' in current_url or 'Dashboard' in current_url:
                logger.info("✅✅✅ LOGIN SUCCESSFUL! ✅✅✅")
                self.logged_in = True
                
                self.driver.get(SMS_PAGE_URL)
                time.sleep(5)
                logger.info("📱 SMS page loaded")
                return True
            else:
                logger.error("❌ Login failed!")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def extract_otp(self, message):
        if not isinstance(message, str):
            message = str(message)
        
        patterns = [
            r'code[:\s]*(\d+)',
            r'OTP[:\s]*(\d+)',
            r'Telegram code[:\s]*(\d+)',
            r'\b(\d{4})\b',
            r'\b(\d{5})\b',
            r'\b(\d{6})\b',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def hide_phone(self, phone):
        phone_str = str(phone)
        if len(phone_str) >= 8:
            return phone_str[:4] + "****" + phone_str[-4:]
        elif len(phone_str) >= 4:
            return phone_str[:2] + "***" + phone_str[-2:]
        return phone_str
    
    def get_sms(self):
        try:
            rows = self.driver.find_elements(By.XPATH, "//table/tbody/tr")
            if not rows:
                return []
            
            sms_list = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 6:
                    sms_list.append({
                        'time': cols[0].text.strip(),
                        'phone': cols[2].text.strip(),
                        'client': cols[4].text.strip(),
                        'message': cols[5].text.strip()
                    })
            return sms_list
        except:
            return []
    
    async def send_telegram(self, msg):
        try:
            keyboard = [[
                InlineKeyboardButton("📢 Main Channel", url="https://t.me/updaterange"),
                InlineKeyboardButton("🤖 Number Bot", url="https://t.me/Updateotpnew_bot"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/rana1132")
            ]]
            await self.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=msg,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            return True
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return False
    
    async def send_all_today_otps(self):
        logger.info("📤 Sending today's OTPs...")
        
        sms_list = self.get_sms()
        if not sms_list:
            await self.send_telegram("📭 No OTPs found for today")
            return
        
        otp_count = 0
        for sms in sms_list:
            otp = self.extract_otp(sms['message'])
            if otp:
                sms_id = f"{sms['time']}_{sms['phone']}_{sms['message'][:50]}"
                if sms_id not in self.processed_otps:
                    phone = self.hide_phone(sms['phone'])
                    
                    msg = f"""
📜 **Previous OTP**
━━━━━━━━━━━━━━━━━━━━

📅 **Time:** `{sms['time']}`
📱 **Phone:** `{phone}`
👤 **Client:** `{sms['client']}`

🔐 **OTP Code:** `{otp}`

━━━━━━━━━━━━━━━━━━━━
🤖 @updaterange
"""
                    if await self.send_telegram(msg):
                        self.processed_otps.add(sms_id)
                        otp_count += 1
                        await asyncio.sleep(1)
        
        logger.info(f"✅ Sent {otp_count} OTPs")
        self._save_processed_otps()
        
        await self.send_telegram(
            f"✅ **Startup Complete!**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **Today's OTPs:** {otp_count}\n"
            f"⚡ **Check Interval:** 0.5 seconds\n"
            f"🔄 **Browser Refresh:** Every 1.5 seconds\n"
            f"🔄 **Status:** Monitoring\n"
            f"⏰ **Started:** {datetime.now().strftime('%H:%M:%S')}\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
    
    async def monitor(self):
        logger.info("🚀 Starting OTP monitor (0.5 sec interval)...")
        logger.info("🔄 Browser will refresh every 1.5 seconds")
        
        await self.send_telegram(f"✅ Bot Started!\nUser: {USERNAME}")
        
        while self.is_monitoring:
            try:
                start_time = time.time()
                
                sms_list = self.get_sms()
                
                if sms_list:
                    for sms in sms_list:
                        sms_id = f"{sms['time']}_{sms['phone']}_{sms['message'][:50]}"
                        
                        if sms_id not in self.processed_otps:
                            otp = self.extract_otp(sms['message'])
                            if otp:
                                logger.info(f"🆕 NEW OTP! {sms['time']} - {sms['phone']}")
                                
                                phone = self.hide_phone(sms['phone'])
                                
                                msg = f"""
🆕 **NEW OTP!**
━━━━━━━━━━━━━━━━━━━━

📅 **Time:** `{sms['time']}`
📱 **Phone:** `{phone}`
👤 **Client:** `{sms['client']}`

🔐 **OTP Code:** `{otp}`

📝 **Message:**
`{sms['message'][:300]}`

━━━━━━━━━━━━━━━━━━━━
🤖 @updaterange
"""
                                if await self.send_telegram(msg):
                                    self.processed_otps.add(sms_id)
                                    self.total_otps_sent += 1
                                    self._save_processed_otps()
                                    logger.info(f"✅ OTP #{self.total_otps_sent} sent")
                                    await asyncio.sleep(0.5)
                
                elapsed = time.time() - start_time
                wait_time = max(0, 0.5 - elapsed)
                await asyncio.sleep(wait_time)
                
                # প্রতি 1.5 সেকেন্ডে ব্রাউজার রিফ্রেশ
                self.refresh_counter += 1
                if self.refresh_counter >= 3:  # 0.5 * 3 = 1.5 সেকেন্ড
                    self.driver.refresh()
                    logger.debug("🔄 Browser refreshed (1.5 seconds)")
                    self.refresh_counter = 0
                    await asyncio.sleep(1.5)  # রিফ্রেশের পর 1.5 সেকেন্ড অপেক্ষা
                    
            except WebDriverException as e:
                logger.error(f"Driver error: {e}")
                logger.info("Reconnecting...")
                try:
                    self.driver.quit()
                    time.sleep(3)
                    self.setup_browser()
                    self.driver.get(SMS_PAGE_URL)
                    await asyncio.sleep(5)
                except:
                    pass
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(1)
    
    async def run(self):
        print("\n" + "="*60)
        print("🤖 BOLT SMS - OTP MONITOR BOT")
        print("="*60)
        print(f"📝 Username: {USERNAME}")
        print(f"📱 Telegram: {GROUP_CHAT_ID}")
        print(f"⚡ Check Interval: 0.5 seconds")
        print(f"🔄 Browser Refresh: Every 1.5 seconds")
        print("="*60)
        
        print("\n🔧 Setting up browser...")
        if not self.setup_browser():
            print("❌ Browser setup failed!")
            return
        
        print("\n🔐 Logging in...")
        if not self.auto_login():
            print("❌ Login failed!")
            await self.send_telegram("❌ **Login Failed!**")
            return
        
        print("\n✅ Login successful!")
        
        print("\n📤 Forwarding today's OTPs...")
        await self.send_all_today_otps()
        
        print("\n" + "="*60)
        print("🚀 Starting OTP Monitor...")
        print("="*60)
        print("⚡ Checking for new OTPs every 0.5 seconds")
        print("🔄 Browser refreshing every 1.5 seconds")
        print("📱 New OTPs will be forwarded immediately")
        print("🌐 Browser window will stay open")
        print("💾 Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        await self.monitor()


async def main():
    bot = OTPBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot stopped!")
        if bot.driver:
            bot.driver.quit()
        print(f"📊 Total OTPs sent: {bot.total_otps_sent}")
        print("👋 Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())