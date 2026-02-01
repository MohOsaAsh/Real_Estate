# ====================================
# 2. audit_log/views.py
# ====================================

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .models import AuditLog

@login_required
def audit_dashboard(request):
    """لوحة التحكم الرئيسية"""
    stats = AuditLog.get_statistics(days=30)
    
    context = {
        'stats': stats,
        'page_title': 'لوحة التحكم - سجلات التدقيق',
    }
    return render(request, 'audit_log/dashboard.html', context)

@login_required
def audit_logs_list(request):
    """عرض قائمة السجلات مع الفلترة"""
    logs = AuditLog.objects.select_related('user').all()
    
    # الفلترة
    action = request.GET.get('action')
    user_name = request.GET.get('user')
    model_name = request.GET.get('model')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    
    if action:
        logs = logs.filter(action=action)
    if user_name:
        logs = logs.filter(user_name__icontains=user_name)
    if model_name:
        logs = logs.filter(model_name__icontains=model_name)
    if date_from:
        logs = logs.filter(created_at__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__lte=date_to)
    if search:
        logs = logs.filter(
            Q(user_name__icontains=search) |
            Q(object_repr__icontains=search) |
            Q(model_name__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    # الترتيب والصفحات
    logs = logs.order_by('-created_at')
    paginator = Paginator(logs, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # إذا كان HTMX request، نرجع فقط الجدول
    if request.headers.get('HX-Request'):
        return render(request, 'audit_log/partials/logs_table.html', {'page_obj': page_obj})
    
    context = {
        'page_obj': page_obj,
        'actions': AuditLog.ACTION_CHOICES,
        'page_title': 'سجلات التدقيق',
    }
    return render(request, 'audit_log/logs_list.html', context)

@login_required
def audit_log_detail(request, pk):
    """تفاصيل سجل معين"""
    log = AuditLog.objects.get(pk=pk)
    
    if request.headers.get('HX-Request'):
        return render(request, 'audit_log/partials/log_detail.html', {'log': log})
    
    context = {
        'log': log,
        'page_title': 'تفاصيل السجل',
    }
    return render(request, 'audit_log/log_detail.html', context)

@login_required
def audit_reports(request):
    """صفحة التقارير"""
    days = int(request.GET.get('days', 30))
    stats = AuditLog.get_statistics(days=days)
    
    context = {
        'stats': stats,
        'days': days,
        'page_title': 'تقارير التدقيق',
    }
    return render(request, 'audit_log/reports.html', context)

@login_required
def audit_api_stats(request):
    """API للإحصائيات (للرسوم البيانية)"""
    days = int(request.GET.get('days', 7))
    start_date = timezone.now() - timedelta(days=days)
    
    # إحصائيات يومية
    daily_stats = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        count = AuditLog.objects.filter(
            created_at__gte=date,
            created_at__lt=next_date
        ).count()
        daily_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # إحصائيات حسب النوع
    action_stats = list(AuditLog.objects.filter(
        created_at__gte=start_date
    ).values('action').annotate(count=Count('id')))
    
    return JsonResponse({
        'daily_stats': daily_stats,
        'action_stats': action_stats,
    })