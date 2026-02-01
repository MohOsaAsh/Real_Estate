from .common_imports_view import *
# ========================================
# 8. التقارير
# ========================================

class ReportDashboardView(LoginRequiredMixin, PermissionCheckMixin, TemplateView):
    """لوحة التقارير"""
    template_name = 'reports/dashboard.html'
    required_permission = 'rent.view_reports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['report_templates'] = ReportTemplate.objects.filter(is_active=True)
        return context


class TenantsDueReportView(LoginRequiredMixin, PermissionCheckMixin, TemplateView):
    """تقرير المستأجرين المستحقين"""
    template_name = 'reports/tenants_due.html'
    required_permission = 'rent.view_reports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # الحصول على التواريخ من الفلتر
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to', date.today())
        
        # توليد التقرير
        report_template = ReportTemplate.objects.filter(
            report_type='tenants_due',
            is_active=True
        ).first()
        
        if report_template:
            report_data = report_template.generate_report(date_from, date_to)
            context['report_data'] = report_data
            # إجماليات للتقرير والجدول
            context['total_due'] = sum(item['due_amount'] for item in report_data)
            context['total_paid'] = sum(item['paid_amount'] for item in report_data)
            context['total_outstanding'] = sum(item['outstanding'] for item in report_data)
        
        context['date_from'] = date_from
        context['date_to'] = date_to
        return context



class ContractsExpiringReportView(LoginRequiredMixin, PermissionCheckMixin, TemplateView):
    """تقرير العقود المنتهية"""
    template_name = 'reports/contracts_expiring.html'
    required_permission = 'rent.view_reports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        
        # الفترة (افتراضياً 30 يوم)
        days = int(self.request.GET.get('days', 30))
        expiry_date = today + timedelta(days=days)
        
        expiring_contracts = Contract.objects.filter(
            status='active',
            end_date__lte=expiry_date,
            end_date__gte=today
        ).select_related('tenant').prefetch_related('units').order_by('end_date')
        
        report_data = []
        for contract in expiring_contracts:
            days_left = (contract.end_date - today).days
            
            report_data.append({
                'contract': contract,
                'contract_number': contract.contract_number,
                'tenant_name': contract.tenant.name,
                'tenant_phone': contract.tenant.phone,
                'start_date': contract.start_date,
                'end_date': contract.end_date,
                'days_left': days_left,
                'units': ', '.join([u.unit_number for u in contract.units.all()]),
                'base_rent': contract.annual_rent,
                'payment_frequency': contract.get_payment_frequency_display(),
            })
        
        context['expiring_contracts'] = report_data
        context['days'] = days
        context['expiry_date'] = expiry_date
        context['total_contracts'] = len(report_data)
        return context


class ActiveContractsReportView(LoginRequiredMixin, PermissionCheckMixin, TemplateView):
    """تقرير العقود النشطة مع إجراءات (سداد - تمديد - زيادة/تخفيض إيجار - قيمة مضافة - إنهاء)"""
    template_name = 'reports/active_contracts.html'
    required_permission = 'rent.view_reports'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contracts = Contract.objects.filter(
            status='active',
            is_deleted=False
        ).select_related('tenant').prefetch_related('units').order_by('-start_date')

        report_data = []
        for contract in contracts:
            report_data.append({
                'contract': contract,
                'contract_number': contract.contract_number,
                'tenant_name': contract.tenant.name,
                'tenant_phone': contract.tenant.phone or '',
                'annual_rent': contract.annual_rent,
                'start_date': contract.start_date,
                'end_date': contract.end_date,
                'payment_frequency': contract.get_payment_frequency_display(),
                'units': ', '.join(u.unit_number for u in contract.units.all()),
            })
        context['report_data'] = report_data
        context['total_contracts'] = len(report_data)
        context['report_date'] = date.today()
        return context


class OccupancyReportView(LoginRequiredMixin, PermissionCheckMixin, TemplateView):
    """تقرير معدل الإشغال"""
    template_name = 'reports/occupancy.html'
    required_permission = 'rent.view_reports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات عامة
        total_units = Unit.objects.filter(is_active=True).count()
        rented_units = Unit.objects.filter(status='rented', is_active=True).count()
        available_units = Unit.objects.filter(status='available', is_active=True).count()
        maintenance_units = Unit.objects.filter(status='maintenance', is_active=True).count()
        frozen_units = Unit.objects.filter(status='frozen', is_active=True).count()
        
        context['total_units'] = total_units
        context['rented_units'] = rented_units
        context['available_units'] = available_units
        context['maintenance_units'] = maintenance_units
        context['frozen_units'] = frozen_units
        context['occupancy_rate'] = (rented_units / total_units * 100) if total_units > 0 else 0
        
        # إحصائيات حسب المبنى
        buildings = Building.objects.filter(is_active=True)
        building_stats = []
        
        for building in buildings:
            total = building.units.filter(is_active=True).count()
            rented = building.units.filter(status='rented', is_active=True).count()
            available = building.units.filter(status='available', is_active=True).count()
            rate = (rented / total * 100) if total > 0 else 0
            
            building_stats.append({
                'building': building,
                'building_name': building.name,
                'total': total,
                'rented': rented,
                'available': available,
                'rate': rate
            })
        
        context['building_stats'] = building_stats
        
        # بيانات للرسم البياني
        context['chart_data'] = {
            'labels': ['مؤجرة', 'متاحة', 'صيانة', 'مجمدة'],
            'values': [rented_units, available_units, maintenance_units, frozen_units]
        }
        
        return context


class RevenueReportView(LoginRequiredMixin, PermissionCheckMixin, TemplateView):
    """تقرير الإيرادات"""
    template_name = 'reports/revenue.html'
    required_permission = 'rent.view_reports'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        
        # الفترة (افتراضياً آخر 12 شهر)
        months = int(self.request.GET.get('months', 12))
        start_date = today - timedelta(days=30 * months)
        
        # إجمالي الإيرادات
        total_revenue = Receipt.objects.filter(
            status='posted',
            receipt_date__gte=start_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # الإيرادات الشهرية
        monthly_revenue = []
        monthly_labels = []
        monthly_values = []
        
        for i in range(months):
            month_start = today - timedelta(days=30 * (months - i))
            month_end = month_start + timedelta(days=30)
            
            month_total = Receipt.objects.filter(
                status='posted',
                receipt_date__gte=month_start,
                receipt_date__lt=month_end
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            month_label = month_start.strftime('%Y-%m')
            monthly_labels.append(month_label)
            monthly_values.append(float(month_total))
            
            monthly_revenue.append({
                'month': month_label,
                'total': month_total
            })
        
        # الإيرادات حسب طريقة الدفع
        payment_methods = Receipt.objects.filter(
            status='posted',
            receipt_date__gte=start_date
        ).values('payment_method').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        payment_methods_data = []
        for method in payment_methods:
            payment_methods_data.append({
                'method': method.get('payment_method', 'غير محدد'),
                'method_code': method['payment_method'],
                'total': method['total']
            })
        
        # الإيرادات اليوم
        today_revenue = Receipt.objects.filter(
            status='posted',
            receipt_date=today
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # الإيرادات الشهر الحالي
        month_start = today.replace(day=1)
        month_revenue = Receipt.objects.filter(
            status='posted',
            receipt_date__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # عدد السندات
        total_receipts = Receipt.objects.filter(
            status='posted',
            receipt_date__gte=start_date
        ).count()
        
        context['total_revenue'] = total_revenue
        context['today_revenue'] = today_revenue
        context['month_revenue'] = month_revenue
        context['total_receipts'] = total_receipts
        context['monthly_revenue'] = monthly_revenue
        context['payment_methods'] = payment_methods_data
        context['months'] = months
        context['start_date'] = start_date
        
        # بيانات للرسم البياني
        context['chart_data'] = {
            'labels': monthly_labels,
            'values': monthly_values
        }
        
        return context


