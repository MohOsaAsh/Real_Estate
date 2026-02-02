# rent/views/contract_views.py

"""
Contract Views - Updated Version
✅ Updated to use ContractFinancialService
عروض العقود - محدث لاستخدام الخدمة الموحدة
"""

from .common_imports_view import *
from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.core.exceptions import ValidationError
from datetime import date

from rent.models.contract_models import Contract
from rent.forms import ContractForm

# ✅ NEW: استيراد الخدمة الموحدة
from rent.services.contract_financial_service import ContractFinancialService

from rent.views.common_imports_view import PermissionCheckMixin, AuditLogMixin


# ========================================
# Contract List View
# ========================================

class ContractListView(LoginRequiredMixin, PermissionCheckMixin, ListView):
    """قائمة العقود"""
    model = Contract
    template_name = 'contracts/contract_list.html'
    context_object_name = 'contracts'
    paginate_by = 20
    required_permission = 'rent.view_contract'
    
    def get_queryset(self):
        queryset = Contract.objects.select_related('tenant').prefetch_related('units')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(contract_number__icontains=search) |
                Q(tenant__name__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-start_date')


# ========================================
# Contract Detail View
# ========================================

class ContractDetailView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """
    تفاصيل العقد
    ✅ Updated to use ContractFinancialService
    """
    model = Contract
    template_name = 'contracts/contract_detail.html'
    context_object_name = 'contract'
    required_permission = 'rent.view_contract'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ✅ NEW: استخدام الخدمة الموحدة
        service = ContractFinancialService(self.object)
        
        # الملخص الشامل
        context['summary'] = service.get_contract_summary()
        
        # الفترات مع الدفعات
        periods_data = service.calculate_periods_with_payments()
        context['periods'] = periods_data['periods']
        context['totals'] = periods_data['totals']
        
        # التعديلات
        context['modifications'] = self.object.modifications.all().order_by('-effective_date')
        
        # السندات
        context['receipts'] = self.object.receipts.filter(
            is_deleted=False
        ).order_by('-receipt_date')
        
        return context


# ========================================
# Contract Create View
# ========================================

class ContractCreateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, CreateView):
    """إنشاء عقد جديد"""
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'
    success_url = reverse_lazy('rent:contract_list')
    required_permission = 'rent.add_contract'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        try:
            response = super().form_valid(form)
            self.log_action('create', self.object)
            messages.success(self.request, 'تم إنشاء العقد بنجاح')
            return response
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        # طباعة الأخطاء في console للتطوير
        print("Form is invalid. Errors:")
        print(form.errors.as_json())
        
        # إضافة رسائل لكل خطأ حقل
        for field, errors in form.errors.items():
            if field == '__all__':
                # أخطاء عامة ليست مرتبطة بحقل معين
                for error in errors:
                    messages.error(self.request, f"⚠️ {error}")
            else:
                for error in errors:
                    # رسائل محددة للحقل
                    messages.error(self.request, f"⚠️ الحقل '{field}': {error}")
        
        return super().form_invalid(form)


# ========================================
# Contract Update View
# ========================================

class ContractUpdateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, UpdateView):
    """تحديث بيانات العقد"""
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'
    success_url = reverse_lazy('rent:contract_list')
    required_permission = 'rent.change_contract'

    def form_valid(self, form):
        try:
            # حفظ البيانات القديمة قبل التحديث
            old_data = {field: getattr(self.object, field) for field in form.changed_data}

            response = super().form_valid(form)

            # حفظ البيانات الجديدة بعد التحديث
            new_data = {field: getattr(self.object, field) for field in form.changed_data}

            self.log_action('update', self.object, old_data=old_data, new_data=new_data)
            messages.success(self.request, 'تم تحديث بيانات العقد بنجاح')
            return response
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)


# ========================================
# Contract Activate View
# ========================================

class ContractActivateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, DetailView):
    """تفعيل العقد"""
    model = Contract
    required_permission = 'rent.activate_contract'
    
    def post(self, request, *args, **kwargs):
        contract = self.get_object()
        
        if contract.status != 'draft':
            messages.error(request, 'العقد ليس في حالة مسودة')
            return redirect('rent:contract_detail', pk=contract.pk)
        
        contract.status = 'active'
        contract.save()
        self.log_action('modify', contract, description='تفعيل العقد')
        messages.success(request, 'تم تفعيل العقد بنجاح')
        return redirect('rent:contract_detail', pk=contract.pk)


# ========================================
# Contract Terminate View
# ========================================

class ContractTerminateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, DetailView):
    """إنهاء العقد"""
    model = Contract
    template_name = 'contracts/contract_terminate.html'
    required_permission = 'rent.terminate_contract'
    
    def post(self, request, *args, **kwargs):
        contract = self.get_object()
        
        if contract.status != 'active':
            messages.error(request, 'العقد ليس نشطاً')
            return redirect('rent:contract_detail', pk=contract.pk)
        
        termination_reason = request.POST.get('termination_reason', '')
        actual_end_date = request.POST.get('actual_end_date', date.today())
        
        contract.status = 'terminated'
        contract.actual_end_date = actual_end_date
        contract.termination_reason = termination_reason
        contract.save()
        
        self.log_action('modify', contract, description='إنهاء العقد')
        messages.success(request, 'تم إنهاء العقد بنجاح')
        return redirect('rent:contract_detail', pk=contract.pk)


# ========================================
# Contract Statement View (Function-Based)
# ========================================

def contract_statement_view(request, contract_id):
    """
    عرض كشف حساب العقد - Function-based view
    ✅ Updated to use ContractFinancialService
    """
    contract = Contract.objects.get(id=contract_id)
    
    # ✅ NEW: استخدام الخدمة الموحدة
    service = ContractFinancialService(contract)
    statement = service.generate_statement()
    
    return render(request, 'contracts/statement.html', {'statement': statement})