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
    """تقرير معدل الإشغال - محسّن"""
    template_name = 'reports/occupancy.html'
    required_permission = 'rent.view_reports'

    def get_context_data(self, **kwargs):
        from django.db.models import Count, Q, Case, When, IntegerField

        context = super().get_context_data(**kwargs)

        # ✅ OPTIMIZED: إحصائيات عامة في query واحد
        unit_stats = Unit.objects.filter(is_active=True).aggregate(
            total=Count('id'),
            rented=Count('id', filter=Q(status='rented')),
            available=Count('id', filter=Q(status='available')),
            maintenance=Count('id', filter=Q(status='maintenance')),
            frozen=Count('id', filter=Q(status='frozen'))
        )

        total_units = unit_stats['total'] or 0
        rented_units = unit_stats['rented'] or 0
        available_units = unit_stats['available'] or 0
        maintenance_units = unit_stats['maintenance'] or 0
        frozen_units = unit_stats['frozen'] or 0

        context['total_units'] = total_units
        context['rented_units'] = rented_units
        context['available_units'] = available_units
        context['maintenance_units'] = maintenance_units
        context['frozen_units'] = frozen_units
        context['occupancy_rate'] = (rented_units / total_units * 100) if total_units > 0 else 0

        # ✅ OPTIMIZED: إحصائيات المباني في query واحد باستخدام annotate
        building_stats = Building.objects.filter(is_active=True).annotate(
            total=Count('units', filter=Q(units__is_active=True)),
            rented=Count('units', filter=Q(units__status='rented', units__is_active=True)),
            available=Count('units', filter=Q(units__status='available', units__is_active=True))
        ).values('id', 'name', 'total', 'rented', 'available')

        # تحويل النتائج لقائمة مع حساب rate
        building_stats_list = []
        for stat in building_stats:
            total = stat['total'] or 0
            rented = stat['rented'] or 0
            rate = (rented / total * 100) if total > 0 else 0
            building_stats_list.append({
                'building_name': stat['name'],
                'total': total,
                'rented': rented,
                'available': stat['available'] or 0,
                'rate': round(rate, 1)
            })

        context['building_stats'] = building_stats_list

        # بيانات للرسم البياني
        context['chart_data'] = {
            'labels': ['مؤجرة', 'متاحة', 'صيانة', 'مجمدة'],
            'values': [rented_units, available_units, maintenance_units, frozen_units]
        }

        return context


class RevenueReportView(LoginRequiredMixin, PermissionCheckMixin, TemplateView):
    """تقرير الإيرادات - محسّن"""
    template_name = 'reports/revenue.html'
    required_permission = 'rent.view_reports'

    def get_context_data(self, **kwargs):
        from django.db.models.functions import TruncMonth
        from django.db.models import Count

        context = super().get_context_data(**kwargs)
        today = date.today()

        # الفترة (افتراضياً آخر 12 شهر)
        months = int(self.request.GET.get('months', 12))
        start_date = today - timedelta(days=30 * months)
        month_start_current = today.replace(day=1)

        # ✅ OPTIMIZED: جلب كل الإحصائيات في query واحد
        base_qs = Receipt.objects.filter(
            status='posted',
            receipt_date__gte=start_date
        )

        # إجمالي الإيرادات + عدد السندات في query واحد
        totals = base_qs.aggregate(
            total_revenue=Sum('amount'),
            total_receipts=Count('id')
        )
        total_revenue = totals['total_revenue'] or Decimal('0')
        total_receipts = totals['total_receipts'] or 0

        # ✅ OPTIMIZED: الإيرادات الشهرية في query واحد باستخدام TruncMonth
        monthly_data = base_qs.annotate(
            month=TruncMonth('receipt_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')

        # تحويل النتائج لقوائم
        monthly_dict = {item['month']: item['total'] for item in monthly_data}

        monthly_revenue = []
        monthly_labels = []
        monthly_values = []

        # إنشاء قائمة بكل الشهور (حتى الفارغة)
        from dateutil.relativedelta import relativedelta
        current_month = start_date.replace(day=1)
        while current_month <= today:
            month_label = current_month.strftime('%Y-%m')
            month_total = monthly_dict.get(current_month, Decimal('0'))

            monthly_labels.append(month_label)
            monthly_values.append(float(month_total or 0))
            monthly_revenue.append({
                'month': month_label,
                'total': month_total or Decimal('0')
            })

            current_month = current_month + relativedelta(months=1)

        # ✅ OPTIMIZED: الإيرادات حسب طريقة الدفع (query موجود بالفعل - جيد)
        payment_methods = base_qs.values('payment_method').annotate(
            total=Sum('amount')
        ).order_by('-total')

        payment_methods_data = []
        for method in payment_methods:
            payment_methods_data.append({
                'method': method.get('payment_method', 'غير محدد'),
                'method_code': method['payment_method'],
                'total': method['total']
            })

        # ✅ OPTIMIZED: الإيرادات اليوم والشهر الحالي في query واحد
        today_and_month = Receipt.objects.filter(
            status='posted',
            receipt_date__gte=month_start_current
        ).aggregate(
            month_revenue=Sum('amount'),
            today_revenue=Sum('amount', filter=Q(receipt_date=today))
        )

        today_revenue = today_and_month['today_revenue'] or Decimal('0')
        month_revenue = today_and_month['month_revenue'] or Decimal('0')

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


