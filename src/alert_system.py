import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import telegram
from src.config import Config
import logging

class AlertSystem:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.email_sender = Config.EMAIL_SENDER
        self.email_password = Config.EMAIL_PASSWORD
        self.email_receiver = Config.EMAIL_RECEIVER
        
        self.bot = None
        if self.bot_token:
            self.bot = telegram.Bot(token=self.bot_token)
    
    def send_telegram(self, message):
        """إرسال تنبيه عبر Telegram"""
        try:
            if self.bot and self.chat_id:
                self.bot.send_message(chat_id=self.chat_id, text=message)
                return True
        except Exception as e:
            logging.error(f"Telegram error: {e}")
        return False
    
    def send_email(self, subject, message):
        """إرسال تنبيه عبر البريد الإلكتروني"""
        try:
            if not all([self.email_sender, self.email_password, self.email_receiver]):
                return False
            
            msg = MIMEMultipart()
            msg['From'] = self.email_sender
            msg['To'] = self.email_receiver
            msg['Subject'] = subject
            
            msg.attach(MIMEText(message, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email_sender, self.email_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logging.error(f"Email error: {e}")
        return False
    
    def console_alert(self, message):
        """تنبيه في وحدة التحكم"""
        print(f"🔔 ALERT: {message}")
        return True
    
    def send_alert(self, message, method='console'):
        """إرسال تنبيه عبر الطريقة المحددة"""
        methods = {
            'console': self.console_alert,
            'telegram': self.send_telegram,
            'email': lambda m: self.send_email("Stock Alert", m)
        }
        
        method_func = methods.get(method, self.console_alert)
        return method_func(message)
    
    def send_signal_alert(self, signal_data, symbol):
        """إرسال تنبيه مخصص لإشارات التداول"""
        message = f"""
📊 *Stock Alert: {symbol}*
━━━━━━━━━━━━━━━━━
🟢 *Signal:* {signal_data['signal']}
📈 *Confidence:* {signal_data['confidence']:.1f}%
🎯 *Score:* {signal_data['score']:.2f}

📋 *Details:*
• Technical: {signal_data['details'].get('technical', 0):.2f}
• Sentiment: {signal_data['details'].get('sentiment', 0):.2f}
• Prediction: {signal_data['details'].get('prediction', 0):.2f}
• Market: {signal_data['details'].get('market', 0):.2f}
━━━━━━━━━━━━━━━━━
"""
        # إرسال التنبيه عبر جميع الطرق
        self.console_alert(message)
        self.send_telegram(message)
        self.send_email(f"Signal Alert - {symbol}", message)
