# rent/views/contract_statement_views.py

"""
Contract Statement Views - Updated Version
✅ Updated to use ContractFinancialService
عرض كشف حساب العقد - محدث لاستخدام الخدمة الموحدة
"""

import logging
from datetime import date, timedelta, datetime
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from django.http import JsonResponse

from rent.mixins import PermissionCheckMixin
from rent.models.contract_models import Contract

# ✅ NEW: استيراد الخدمة الموحدة
from rent.services.contract_financial_service import (
    ContractFinancialService,
    format_statement_report  # ✅ دالة التنسيق من الخدمة الموحدة
)

logger = logging.getLogger(__name__)


# ========================================
# Contract Statement View
# ========================================

class ContractStatementView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """
    عرض كشف حساب العقد
    ✅ Updated to use ContractFinancialService
    """
    model = Contract
    template_name = 'contracts/contract_statement.html'
    context_object_name = 'contract'
    required_permission = 'rent.view_contract_statement'
    
    def get_queryset(self):
        return Contract.objects.select_related('tenant')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # الحصول على التواريخ من الـ GET parameters
        end_date_str = self.request.GET.get('end_date')
        include_future = self.request.GET.get('include_future', 'false').lower() == 'true'
        
        # تحديد تاريخ النهاية
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except:
                end_date = date.today()
        else:
            end_date = date.today()
        
        # ✅ NEW: استخدام الخدمة الموحدة
        service = ContractFinancialService(self.object, as_of_date=end_date)
        statement = service.generate_statement(
            end_date=end_date,
            include_future=include_future
        )
        
        context['statement'] = statement
        context['end_date'] = end_date
        context['include_future'] = include_future
        
        # خيارات التواريخ السريعة
        today = date.today()
        context['date_options'] = {
            'today': today,
            'month_end': date(today.year, today.month, 1) + timedelta(days=32),
            'year_end': date(today.year, 12, 31),
            'contract_end': self.object.end_date,
        }
        
        logger.info(
            f'Statement generated for contract {self.object.id} '
            f'until {end_date} by {self.request.user.username}'
        )
        
        return context


# ========================================
# Contract Statement Print View
# ========================================

class ContractStatementPrintView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """
    طباعة كشف الحساب
    ✅ Updated to use ContractFinancialService
    """
    model = Contract
    required_permission = 'rent.view_contract_statement'
    template_name = 'contracts/contract_statement_print.html'
    context_object_name = 'contract'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # الحصول على التواريخ
        end_date_str = self.request.GET.get('end_date')
        include_future = self.request.GET.get('include_future', 'false').lower() == 'true'
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except:
                end_date = date.today()
        else:
            end_date = date.today()
        
        # ✅ NEW: استخدام الخدمة الموحدة
        service = ContractFinancialService(self.object, as_of_date=end_date)
        statement = service.generate_statement(
            end_date=end_date,
            include_future=include_future
        )
        
        context['statement'] = statement
        context['end_date'] = end_date
        context['print_date'] = date.today()
        
        # ✅ NEW: إضافة النص المنسق للطباعة
        if statement.get('success'):
            context['formatted_statement'] = format_statement_report(statement)
        
        return context


# ========================================
# Contract Statement API View (JSON)
# ========================================

class ContractStatementAPIView(LoginRequiredMixin, DetailView):
    """
    API لكشف الحساب (JSON)
    ✅ Updated to use ContractFinancialService
    """
    model = Contract
    
    def get(self, request, *args, **kwargs):
        contract = self.get_object()
        
        # الحصول على المعاملات
        end_date_str = request.GET.get('end_date')
        include_future = request.GET.get('include_future', 'false').lower() == 'true'
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except:
                end_date = date.today()
        else:
            end_date = date.today()
        
        # ✅ NEW: استخدام الخدمة الموحدة
        service = ContractFinancialService(contract, as_of_date=end_date)
        statement = service.generate_statement(
            end_date=end_date,
            include_future=include_future
        )
        
        if not statement.get('success'):
            return JsonResponse({
                'success': False,
                'error': statement.get('error')
            }, status=400)
        
        # تحويل الأسطر إلى dict
        lines_data = [line.to_dict() for line in statement['lines']]
        
        return JsonResponse({
            'success': True,
            'statement': {
                'lines': lines_data,
                'summary': statement['summary'],
            }
        })


# ========================================
# Contract Financial Summary API (Additional)
# ========================================

class ContractFinancialSummaryAPIView(LoginRequiredMixin, DetailView):
    """
    API لملخص مالي سريع
    ✅ NEW - يستخدم ContractFinancialService
    """
    model = Contract
    
    def get(self, request, *args, **kwargs):
        contract = self.get_object()
        
        # ✅ استخدام الخدمة الموحدة
        service = ContractFinancialService(contract)
        
        # الحصول على الملخص المالي
        summary = service.get_contract_summary()
        
        # الحصول على المبالغ المستحقة
        outstanding = service.get_outstanding_amount()
        outstanding_all = service.get_outstanding_amount(include_future=True)
        
        # نطاق الفترات غير المسددة
        unpaid_range = service.get_unpaid_periods_range()
        
        return JsonResponse({
            'success': True,
            'summary': {
                'total_periods': summary['total_periods'],
                'total_contract_value': float(summary['total_contract_value']),
                'total_paid': float(summary['total_paid']),
                'total_remaining': float(summary['total_remaining']),
                'outstanding': float(outstanding),
                'outstanding_all': float(outstanding_all),
                'paid_periods_count': len(summary['paid_periods']),
                'partial_periods_count': len(summary['partial_periods']),
                'overdue_periods_count': len(summary['overdue_periods']),
                'future_periods_count': len(summary['future_periods']),
            },
            'unpaid_range': {
                'text': service.get_unpaid_periods_date_range_text() if unpaid_range else None,
                'count': unpaid_range['unpaid_periods_count'] if unpaid_range else 0,
                'amount': float(unpaid_range['total_unpaid_amount']) if unpaid_range else 0,
            } if unpaid_range else None
        })