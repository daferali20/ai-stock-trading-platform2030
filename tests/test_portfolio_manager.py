import unittest
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.portfolio_manager import PortfolioManager

class TestPortfolioManager(unittest.TestCase):
    """اختبارات إدارة المحفظة"""
    
    def setUp(self):
        self.manager = PortfolioManager(initial_capital=10000)
    
    def test_initialization(self):
        """اختبار التهيئة"""
        self.assertEqual(self.manager.initial_capital, 10000)
        self.assertEqual(self.manager.cash, 10000)
        self.assertEqual(len(self.manager.positions), 0)
    
    def test_add_position(self):
        """اختبار إضافة مركز"""
        self.manager.add_position('AAPL', 10, 150)
        
        self.assertIn('AAPL', self.manager.positions)
        self.assertEqual(self.manager.positions['AAPL']['quantity'], 10)
        self.assertEqual(self.manager.positions['AAPL']['avg_price'], 150)
        self.assertEqual(self.manager.cash, 10000 - 10 * 150)
        
        # إضافة إلى مركز موجود
        self.manager.add_position('AAPL', 5, 155)
        self.assertEqual(self.manager.positions['AAPL']['quantity'], 15)
        self.assertEqual(self.manager.positions['AAPL']['avg_price'], (10*150 + 5*155) / 15)
    
    def test_remove_position(self):
        """اختبار إزالة مركز"""
        self.manager.add_position('AAPL', 10, 150)
        
        # بيع جزء
        success = self.manager.remove_position('AAPL', 5, 160)
        self.assertTrue(success)
        self.assertEqual(self.manager.positions['AAPL']['quantity'], 5)
        self.assertEqual(self.manager.cash, 10000 - 10*150 + 5*160)
        
        # بيع الكل
        success = self.manager.remove_position('AAPL', 5, 165)
        self.assertTrue(success)
        self.assertNotIn('AAPL', self.manager.positions)
    
    def test_get_portfolio_value(self):
        """اختبار حساب قيمة المحفظة"""
        self.manager.add_position('AAPL', 10, 150)
        self.manager.add_position('GOOGL', 5, 100)
        
        prices = {'AAPL': 160, 'GOOGL': 110}
        value = self.manager.get_portfolio_value(prices)
        expected = self.manager.cash + 10*160 + 5*110
        self.assertEqual(value, expected)
    
    def test_get_portfolio_status(self):
        """اختبار الحصول على حالة المحفظة"""
        self.manager.add_position('AAPL', 10, 150)
        prices = {'AAPL': 160}
        
        status = self.manager.get_portfolio_status(prices)
        
        self.assertIn('cash', status)
        self.assertIn('positions', status)
        self.assertIn('total_value', status)
        self.assertIn('gain_loss', status)
        self.assertIn('gain_loss_pct', status)
        
        self.assertIn('AAPL', status['positions'])
        self.assertEqual(status['positions']['AAPL']['quantity'], 10)

if __name__ == '__main__':
    unittest.main()
