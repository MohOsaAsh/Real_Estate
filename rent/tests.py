from django.test import TestCase

# Create your tests here.
# rent/tests/test_contract_financial_service.py

from datetime import date
from decimal import Decimal
from django.test import TestCase
from rent.services.contract_financial_service import ContractFinancialService
from rent.models import Contract, Tenant

class ContractFinancialServiceTest(TestCase):
    
    def setUp(self):
        """إعداد بيانات الاختبار"""
        self.tenant = Tenant.objects.create(name='محمد أحمد')
        
        self.contract = Contract.objects.create(
            tenant=self.tenant,
            contract_number='C-2025-001',
            start_date=date(2025, 1, 1),
            end_date=date(2025, 12, 31),
            annual_rent=Decimal('120000.00'),
            payment_frequency='quarterly'
        )
    
    def test_calculate_periods(self):
        """اختبار حساب الفترات"""
        service = ContractFinancialService(self.contract)
        periods = service.calculate_periods_with_modifications()
        
        # يجب أن يكون هناك 4 فترات (ربع سنوية)
        self.assertEqual(len(periods), 4)
        
        # كل فترة = 120,000 / 4 = 30,000
        for period in periods:
            self.assertEqual(period['due_amount'], Decimal('30000.00'))
    
    def test_calculate_with_payments(self):
        """اختبار توزيع الدفعات"""
        # إضافة دفعة
        from rent.models import Receipt
        Receipt.objects.create(
            contract=self.contract,
            receipt_number='R-001',
            receipt_date=date(2025, 2, 1),
            amount=Decimal('30000.00'),
            status='posted'
        )
        
        service = ContractFinancialService(self.contract)
        data = service.calculate_periods_with_payments()
        
        # الفترة الأولى يجب أن تكون مدفوعة
        self.assertEqual(data['periods'][0]['status'], 'paid')
        self.assertEqual(data['totals']['total_paid'], Decimal('30000.00'))
    
    def test_generate_statement(self):
        """اختبار كشف الحساب"""
        service = ContractFinancialService(self.contract)
        statement = service.generate_statement()
        
        self.assertTrue(statement['success'])
        self.assertEqual(len(statement['lines']), 4)  # 4 فترات
        self.assertEqual(statement['summary']['total_periods'], 4)