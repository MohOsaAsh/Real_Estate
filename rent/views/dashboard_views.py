# rent/views/dashboard_views.py

"""
Dashboard Views - Updated Version
✅ Updated to use ContractFinancialService
لوحة التحكم - محدث لاستخدام الخدمة الموحدة
"""

from .common_imports_view import *
from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Count, Sum, Q
from django.contrib import messages
from django.views import View
from django.http import JsonResponse
# # ✅ إضافة الـ Choices
# from rent.models import (
#      Land, Building, Unit, Contract
# )
from rent.services.unit_availability_service import UnitAvailabilityService


# ✅ NEW: استيراد الخدمة الموحدة
from rent.services.contract_financial_service import ContractFinancialService


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    الصفحة الرئيسية - لوحة التحكم
    ✅ Updated to use ContractFinancialService
    متاحة لجميع المستخدمين المسجلين
    """
    template_name = 'dashboard.html'
    login_url = '/auth/login/'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        
        try:
            # ========================================
            # 1. إحصائيات العقود
            # ========================================
            context['total_contracts'] = Contract.objects.filter(
                status='active',
                is_deleted=False
            ).count()
            
            context['expiring_contracts'] = Contract.objects.filter(
                status='active',
                is_deleted=False,
                end_date__lte=today + timedelta(days=30),
                end_date__gte=today
            ).count()
            
            # ========================================
            # 2. إحصائيات الوحدات
            # ========================================
            units_stats = Unit.objects.filter(is_active=True).aggregate(
                total=Count('id'),
                rented=Count('id', filter=Q(status='rented'))
            )
            
            context['total_units'] = units_stats['total'] or 0
            context['rented_units'] = units_stats['rented'] or 0
            context['available_units'] = context['total_units'] - context['rented_units']
            context['occupancy_rate'] = round(
                (context['rented_units'] / context['total_units'] * 100) 
                if context['total_units'] > 0 else 0,
                2
            )
            
            # ========================================
            # 3. إحصائيات المستأجرين
            # ========================================
            context['total_tenants'] = Tenant.objects.filter(
                is_active=True
            ).count()
            
            # ========================================
            # 4. إحصائيات الدفعات
            # ========================================
            context['total_receipts_today'] = Receipt.objects.filter(
                status='posted',
                receipt_date=today
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            context['total_receipts_month'] = Receipt.objects.filter(
                status='posted',
                receipt_date__year=today.year,
                receipt_date__month=today.month
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # ========================================
            # 5. الإشعارات غير المقروءة
            # ========================================
            context['unread_notifications'] = Notification.objects.filter(
                is_read=False,
                user=self.request.user
            ).count()
            
            # ========================================
            # 6. العقود المنتهية قريباً
            # ========================================
            context['expiring_contracts_list'] = Contract.objects.filter(
                status='active',
                is_deleted=False,
                end_date__lte=today + timedelta(days=30),
                end_date__gte=today
            ).select_related('tenant').prefetch_related(
                'units__building__land'
            ).order_by('end_date')[:5]
            
            # ========================================
            # 7. المدفوعات المتأخرة
            # ========================================
            context['overdue_contracts'] = self._get_overdue_contracts()
            
            # ✅ NEW: إحصائيات المستحقات
            context['total_outstanding'] = self._calculate_total_outstanding()
            
            # ========================================
            # 8. إحصائيات إضافية (اختياري)
            # ========================================
            context['total_lands'] = Land.objects.filter(is_active=True).count()
            context['total_buildings'] = Building.objects.filter(is_active=True).count()


            #===============================================
            #تحديث  الوحدات   
            #===============================================
             # تنفيذ المهمة
            service = UnitAvailabilityService(
                contract_model=Contract,
                unit_model=Unit,
                active_status_value='active',      # ✅ القيمة مباشرة
                available_status_value='available', # ✅ القيمة مباشرة
                rented_status_value='rented' # ✅ من الـ Choices
            )
            service.update_all_units_availability()
            


            #===============================================
            
        except Exception as e:
            # في حالة حدوث خطأ، سجله واستمر
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Dashboard error: {e}", exc_info=True)
            messages.warning(
                self.request,
                'حدث خطأ أثناء تحميل بعض البيانات. جارٍ المحاولة مرة أخرى...'
            )
        
        return context
    
    def _get_overdue_contracts(self):
        """
        الحصول على العقود المتأخرة في الدفع
        ✅ Updated to use ContractFinancialService
        """
        overdue_contracts = []
        
        try:
            active_contracts = Contract.objects.filter(
                status__in=['active', 'expired', 'suspended'],
                is_deleted=False
            ).select_related('tenant').prefetch_related(
                'units__building__land'
            )[:50]  # حد أقصى 50 عقد لتحسين الأداء
            
            for contract in active_contracts:
                try:
                    # ✅ NEW: استخدام الخدمة الموحدة
                    service = ContractFinancialService(contract)
                    outstanding = service.get_outstanding_amount()
                    
                    if outstanding > 0:
                        # الحصول على الفترات المتأخرة
                        overdue_periods = [
                            p for p in service.get_unpaid_periods()
                            if p['status'] == 'overdue'
                        ]
                        
                        overdue_contracts.append({
                            'contract': contract,
                            'outstanding': outstanding,
                            'status': contract.status,
                            'overdue_periods_count': len(overdue_periods),
                            'days_overdue': self._calculate_days_overdue(contract, overdue_periods),
                        })
                except Exception as e:
                    # تسجيل الخطأ واستمر
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error calculating for contract {contract.id}: {e}")
                    continue
            
            # ترتيب حسب المبلغ المتأخر (من الأكبر للأصغر)
            overdue_contracts.sort(key=lambda x: x['outstanding'], reverse=True)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting overdue contracts: {e}")
        
        return overdue_contracts[:5]  # أول 5 فقط
    
    def _calculate_days_overdue(self, contract, overdue_periods):
        """
        حساب عدد الأيام المتأخرة
        ✅ Updated - يستخدم الفترات المتأخرة
        """
        try:
            if not overdue_periods:
                return 0
            
            # أقدم فترة متأخرة
            oldest_period = min(overdue_periods, key=lambda p: p['start_date'])
            today = date.today()
            
            if oldest_period['start_date'] < today:
                return (today - oldest_period['start_date']).days
            
            return 0
        except Exception:
            return 0
    
    def _calculate_total_outstanding(self):
        """
        ✅ NEW: حساب إجمالي المستحقات لجميع العقود النشطة
        """
        try:
            active_contracts = Contract.objects.filter(
                status='active',
                is_deleted=False
            )[:100]  # حد أقصى 100 عقد
            
            total = Decimal('0')
            
            for contract in active_contracts:
                try:
                    service = ContractFinancialService(contract)
                    outstanding = service.get_outstanding_amount()
                    total += outstanding
                except Exception:
                    continue
            
            return total
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating total outstanding: {e}")
            return Decimal('0')


# ========================================
# View إضافي: API للإحصائيات (اختياري)
# ========================================

class DashboardStatsAPIView(LoginRequiredMixin, View):
    """
    ✅ NEW: API لجلب إحصائيات Dashboard بصيغة JSON
    مفيد للتحديث الديناميكي بدون إعادة تحميل الصفحة
    """
    
    def get(self, request, *args, **kwargs):
        from django.http import JsonResponse
        
        try:
            today = date.today()
            
            # العقود المتأخرة
            active_contracts = Contract.objects.filter(
                status='active',
                is_deleted=False
            )[:50]
            
            overdue_count = 0
            total_outstanding = Decimal('0')
            
            for contract in active_contracts:
                try:
                    service = ContractFinancialService(contract)
                    outstanding = service.get_outstanding_amount()
                    
                    if outstanding > 0:
                        overdue_count += 1
                        total_outstanding += outstanding
                except Exception:
                    continue
            
            # الدفعات اليوم
            receipts_today = Receipt.objects.filter(
                status='posted',
                receipt_date=today
            ).aggregate(
                total=Sum('amount'),
                count=Count('id')
            )
            
            return JsonResponse({
                'success': True,
                'stats': {
                    'overdue_contracts': overdue_count,
                    'total_outstanding': float(total_outstanding),
                    'receipts_today': {
                        'count': receipts_today['count'] or 0,
                        'total': float(receipts_today['total'] or 0)
                    }
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)