import os
import json
from datetime import datetime
import numpy as np
import pandas as pd

class PortfolioManager:
    def __init__(self, initial_capital=10000, portfolio_file='data/portfolio.json'):
        self.initial_capital = float(initial_capital)
        self.cash = float(initial_capital)
        self.positions = {}
        self.history = []
        self.portfolio_file = portfolio_file
        
        # إنشاء المجلد إذا لم يكن موجوداً
        os.makedirs(os.path.dirname(self.portfolio_file) or 'data', exist_ok=True)
        self.load_portfolio()

    def load_portfolio(self):
        """تحميل المحفظة من ملف JSON بأمان"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cash = float(data.get('cash', self.initial_capital))
                    self.positions = data.get('positions', {})
                    self.history = data.get('history', [])
            except Exception as e:
                print(f"⚠️ Error loading portfolio: {e}")

    def save_portfolio(self):
        """حفظ المحفظة في ملف مع تحويل أنواع البيانات لضمان عدم حدوث خطأ JSON"""
        try:
            # تحويل البيانات إلى أنماط Python القياسية
            clean_positions = {}
            for sym, pos in self.positions.items():
                clean_positions[sym] = {
                    'quantity': int(pos['quantity']),
                    'avg_price': float(pos['avg_price'])
                }

            data_to_save = {
                'cash': float(self.cash),
                'positions': clean_positions,
                'history': self.history,
                'last_update': datetime.now().isoformat()
            }

            with open(self.portfolio_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving portfolio: {e}")

    def get_portfolio_value(self, current_prices):
        """حساب قيمة المحفظة الحالية بالكامل"""
        total_value = self.cash
        for symbol, position in self.positions.items():
            price = current_prices.get(symbol, position['avg_price'])
            total_value += position['quantity'] * price
        return float(total_value)

    def get_portfolio_status(self, current_prices):
        """الحصول على حالة المحفظة والتفاصيل الإحصائية"""
        status = {
            'cash': float(self.cash),
            'positions': {},
            'total_value': float(self.cash),
            'gain_loss': 0.0,
            'gain_loss_pct': 0.0
        }
        
        positions_value = 0.0
        
        for symbol, position in self.positions.items():
            qty = position['quantity']
            avg_price = position['avg_price']
            current_price = current_prices.get(symbol, avg_price)
            
            value = qty * current_price
            cost = qty * avg_price
            gain_loss = value - cost
            gain_loss_pct = ((value - cost) / cost * 100) if cost > 0 else 0.0
            
            status['positions'][symbol] = {
                'quantity': qty,
                'avg_price': float(avg_price),
                'current_price': float(current_price),
                'value': float(value),
                'gain_loss': float(gain_loss),
                'gain_loss_pct': float(gain_loss_pct)
            }
            
            positions_value += value
        
        status['total_value'] = float(self.cash + positions_value)
        if self.initial_capital > 0:
            status['gain_loss'] = float(status['total_value'] - self.initial_capital)
            status['gain_loss_pct'] = float((status['gain_loss'] / self.initial_capital) * 100)
        
        return status

    def add_position(self, symbol, quantity, price):
        """إضافة مركز جديد (شراء) مع التحقق من توفر السيادة النقدیة"""
        total_cost = quantity * price
        if total_cost > self.cash:
            return False  # رصيد غير كافٍ

        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': int(quantity),
                'avg_price': float(price)
            }
        else:
            # حساب متوسط السعر الترجيحي الجديد
            existing_qty = self.positions[symbol]['quantity']
            existing_cost = existing_qty * self.positions[symbol]['avg_price']
            total_quantity = existing_qty + quantity
            
            self.positions[symbol]['quantity'] = int(total_quantity)
            self.positions[symbol]['avg_price'] = float((existing_cost + total_cost) / total_quantity)
        
        self.cash -= total_cost
        
        # تسجيل العملية في السجل
        self.history.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'BUY',
            'symbol': symbol,
            'quantity': int(quantity),
            'price': float(price),
            'amount': float(total_cost),
            'cash_remaining': float(self.cash)
        })
        
        self.save_portfolio()
        return True

    def remove_position(self, symbol, quantity, price):
        """بيع جزء أو كل مركز متوفر"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        if position['quantity'] < quantity:
            return False
        
        position['quantity'] -= quantity
        total_proceeds = quantity * price
        self.cash += total_proceeds
        
        # إزالة المركز بالكامل إذا أصبحت الكمية صفراً
        if position['quantity'] <= 0:
            del self.positions[symbol]
        
        # تسجيل العملية
        self.history.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'SELL',
            'symbol': symbol,
            'quantity': int(quantity),
            'price': float(price),
            'amount': float(total_proceeds),
            'cash_remaining': float(self.cash)
        })
        
        self.save_portfolio()
        return True

    def reset_portfolio(self):
        """إعادة ضبط المحفظة للوضع الافتراضي"""
        self.cash = float(self.initial_capital)
        self.positions = {}
        self.history = []
        self.save_portfolio()

    def calculate_risk_metrics(self, returns):
        """حساب مقاييس المخاطر من سلسلة العوائد مع تنظيف البيانات"""
        if isinstance(returns, (list, pd.Series, np.ndarray)):
            returns = pd.Series(returns).dropna()
        
        if len(returns) < 2:
            return {
                'annual_returns': 0.0,
                'annual_volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0
            }
        
        annual_returns = float(np.mean(returns) * 252)
        annual_volatility = float(np.std(returns) * np.sqrt(252))
        
        # Sharpe Ratio (بافتراض معدل خالي من المخاطر Risk-Free Rate = 0)
        sharpe_ratio = float(annual_returns / annual_volatility) if annual_volatility > 0 else 0.0
        
        # Max Drawdown
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = float(np.min(drawdown)) if len(drawdown) > 0 else 0.0
        
        # Win Rate
        positive_returns = np.sum(returns > 0)
        win_rate = float(positive_returns / len(returns)) if len(returns) > 0 else 0.0
        
        return {
            'annual_returns': round(annual_returns, 4),
            'annual_volatility': round(annual_volatility, 4),
            'sharpe_ratio': round(sharpe_ratio, 2),
            'max_drawdown': round(max_drawdown, 4),
            'win_rate': round(win_rate, 4)
        }
