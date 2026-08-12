import pandas as pd
import json
import os
from datetime import datetime
import numpy as np

class PortfolioManager:
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}
        self.history = []
        self.portfolio_file = 'data/portfolio.json'
        os.makedirs('data', exist_ok=True)
        self.load_portfolio()
    
    def load_portfolio(self):
        """تحميل المحفظة من ملف"""
        if os.path.exists(self.portfolio_file):
            try:
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                    self.cash = data.get('cash', self.initial_capital)
                    self.positions = data.get('positions', {})
                    self.history = data.get('history', [])
            except Exception as e:
                print(f"Error loading portfolio: {e}")
    
    def save_portfolio(self):
        """حفظ المحفظة في ملف"""
        try:
            with open(self.portfolio_file, 'w') as f:
                json.dump({
                    'cash': self.cash,
                    'positions': self.positions,
                    'history': self.history,
                    'last_update': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving portfolio: {e}")
    
    def get_portfolio_value(self, current_prices):
        """حساب قيمة المحفظة الحالية"""
        total_value = self.cash
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                total_value += position['quantity'] * current_prices[symbol]
            else:
                total_value += position['quantity'] * position['avg_price']
        
        return total_value
    
    def get_portfolio_status(self, current_prices):
        """الحصول على حالة المحفظة"""
        status = {
            'cash': self.cash,
            'positions': {},
            'total_value': self.cash,
            'gain_loss': 0,
            'gain_loss_pct': 0
        }
        
        positions_value = 0
        total_cost = 0
        
        for symbol, position in self.positions.items():
            current_price = current_prices.get(symbol, position['avg_price'])
            value = position['quantity'] * current_price
            cost = position['quantity'] * position['avg_price']
            
            status['positions'][symbol] = {
                'quantity': position['quantity'],
                'avg_price': position['avg_price'],
                'current_price': current_price,
                'value': value,
                'gain_loss': value - cost,
                'gain_loss_pct': ((value - cost) / cost * 100) if cost > 0 else 0
            }
            
            positions_value += value
            total_cost += cost
        
        status['total_value'] = status['cash'] + positions_value
        if self.initial_capital > 0:
            status['gain_loss'] = status['total_value'] - self.initial_capital
            status['gain_loss_pct'] = (status['gain_loss'] / self.initial_capital * 100)
        
        return status
    
    def add_position(self, symbol, quantity, price):
        """إضافة مركز جديد"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'quantity': quantity,
                'avg_price': price
            }
        else:
            # تحديث المتوسط
            total_quantity = self.positions[symbol]['quantity'] + quantity
            total_cost = (self.positions[symbol]['quantity'] * self.positions[symbol]['avg_price']) + (quantity * price)
            self.positions[symbol]['quantity'] = total_quantity
            self.positions[symbol]['avg_price'] = total_cost / total_quantity
        
        self.cash -= quantity * price
        self.save_portfolio()
        
        # تسجيل العملية
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'BUY',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'amount': quantity * price,
            'cash_remaining': self.cash
        })
    
    def remove_position(self, symbol, quantity, price):
        """بيع جزء أو كل مركز"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        if position['quantity'] < quantity:
            return False
        
        position['quantity'] -= quantity
        self.cash += quantity * price
        
        # إزالة المركز بالكامل إذا كان الصفر
        if position['quantity'] == 0:
            del self.positions[symbol]
        
        self.save_portfolio()
        
        # تسجيل العملية
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'action': 'SELL',
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'amount': quantity * price,
            'cash_remaining': self.cash
        })
        
        return True
    
    def calculate_risk_metrics(self, returns):
        """حساب مقاييس المخاطر"""
        if len(returns) < 2:
            return {}
        
        metrics = {
            'annual_returns': np.mean(returns) * 252,
            'annual_volatility': np.std(returns) * np.sqrt(252),
            'sharpe_ratio': 0,
            'max_drawdown': 0,
            'win_rate': 0
        }
        
        # Sharpe Ratio
        if metrics['annual_volatility'] > 0:
            metrics['sharpe_ratio'] = metrics['annual_returns'] / metrics['annual_volatility']
        
        # Max Drawdown
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        metrics['max_drawdown'] = np.min(drawdown)
        
        # Win Rate
        positive_returns = np.sum(returns > 0)
        metrics['win_rate'] = positive_returns / len(returns) if len(returns) > 0 else 0
        
        return metrics
