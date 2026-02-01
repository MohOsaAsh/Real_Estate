# ========================================
# 2. models/report_models.py
# ========================================

from .common_imports_models import *


# ========================================
# 9. نماذج التقارير
# ========================================

class ReportTemplate(models.Model):
    """قوالب التقارير"""
    REPORT_TYPES = [
        ('tenants_due', 'المستأجرين المستحقين الدفع'),
        ('contracts_expiring', 'العقود المنتهية'),
        ('occupancy_rate', 'معدل الإشغال'),
        ('revenue', 'الإيرادات'),
        ('collection', 'التحصيل'),
        ('custom', 'مخصص'),
    ]
    
    name = models.CharField(_('اسم التقرير'), max_length=200)
    report_type = models.CharField(_('نوع التقرير'), max_length=50, choices=REPORT_TYPES)
    description = models.TextField(_('الوصف'), blank=True)
    
    # إعدادات التقرير
    filters = models.JSONField(_('الفلاتر'), default=dict, blank=True)
    columns = models.JSONField(_('الأعمدة'), default=list, blank=True)
    sort_by = models.CharField(_('ترتيب حسب'), max_length=100, blank=True)
    group_by = models.CharField(_('تجميع حسب'), max_length=100, blank=True)
    
    is_active = models.BooleanField(_('نشط'), default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_('تم الإنشاء بواسطة'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('قالب تقرير')
        verbose_name_plural = _('قوالب التقارير')
        ordering = ['name']
        permissions = [
            ('view_reports', 'عرض التقارير'),
            ('export_reports', 'تصدير التقارير'),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"
    
    def generate_report(self, start_date=None, end_date=None, **kwargs):
        """توليد التقرير"""
        if self.report_type == 'tenants_due':
            return self._generate_tenants_due_report(start_date, end_date)
        elif self.report_type == 'contracts_expiring':
            return self._generate_contracts_expiring_report(start_date, end_date)
        # ... باقي أنواع التقارير
    
    def _generate_tenants_due_report(self, start_date, end_date):
        """تقرير المستأجرين المستحقين الدفع (كما في الصورة)"""
        report_data = []
        
        # العقود النشطة + المنتهية + الملغاة (لظهور المستحقات المتبقية)
        contracts = Contract.objects.filter(
            status__in=['active', 'expired', 'terminated'],
            start_date__lte=end_date or date.today()
        ).select_related('tenant').prefetch_related('units')
        
        for contract in contracts:
            service = ContractFinancialService(contract, as_of_date=end_date)
            summary = service.get_contract_summary()
            
            if summary['outstanding'] > 0:
                # الحصول على الفترات المتأخرة
                overdue_periods = summary['overdue_periods']
                current_period = summary['current_period']
                
                # تحديد فترة الاستحقاق
                if overdue_periods:
                    period = overdue_periods[0]  # أول فترة متأخرة
                elif current_period:
                    period = current_period
                else:
                    continue
                
                report_data.append({
                    'tenant': contract.tenant,
                    'contract': contract,
                    'tenant_name': contract.tenant.name,
                    'contract_number': contract.contract_number,
                    'annual_rent': contract.annual_rent,
                    'payment_frequency': contract.get_payment_frequency_display(),
                    'period_start': period['start_date'],
                    'period_end': period['end_date'],
                    'due_amount': period['due_amount'],
                    'paid_amount': summary['total_paid'],
                    'outstanding': summary['outstanding'],
                    'units': ', '.join([u.unit_number for u in contract.units.all()]),
                    'tenant_phone': contract.tenant.phone,
                })
        
        return report_data
    
    def _generate_contracts_expiring_report(self, start_date, end_date):
        """تقرير العقود المنتهية"""
        today = date.today()
        if end_date:
            expiry_date = end_date
        else:
            expiry_date = today + timedelta(days=30)  # شهر من الآن
        
        expiring_contracts = Contract.objects.filter(
            status='active',
            end_date__lte=expiry_date,
            end_date__gte=today
        ).select_related('tenant').prefetch_related('units')
        
        report_data = []
        for contract in expiring_contracts:
            days_left = (contract.end_date - today).days
            
            report_data.append({
                'contract_number': contract.contract_number,
                'tenant_name': contract.tenant.name,
                'end_date': contract.end_date,
                'days_left': days_left,
                'units': ', '.join([u.unit_number for u in contract.units.all()]),
                'base_rent': contract.annual_rent,
                'payment_frequency': contract.get_payment_frequency_display(),
            })
        
        return report_data
