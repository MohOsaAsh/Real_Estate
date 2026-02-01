from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta

from .models import ContractModification, Contract
from .forms import (
    RentIncreaseForm, RentDecreaseForm, DiscountForm, 
    TaxForm, ExtendContractForm, TerminateContractForm,
    QuickModificationForm
)


# ==================== Class-Based Views ====================

class ModificationListView(LoginRequiredMixin, ListView):
    """عرض قائمة التسويات"""
    model = ContractModification
    template_name = 'modifications/modification_list.html'
    context_object_name = 'modifications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ContractModification.objects.select_related(
            'contract', 'created_by'
        ).order_by('-created_at')
        
        # فلترة حسب نوع التعديل
        modification_type = self.request.GET.get('type')
        if modification_type:
            queryset = queryset.filter(modification_type=modification_type)
        
        # فلترة حسب الحالة
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # فلترة حسب العقد
        contract_id = self.request.GET.get('contract')
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        # فلترة حسب التاريخ
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(effective_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(effective_date__lte=date_to)
        
        # بحث
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(contract__contract_number__icontains=search) |
                Q(reason__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات
        context['stats'] = {
            'total': ContractModification.objects.count(),
            'pending': ContractModification.objects.filter(status='pending').count(),
            'active': ContractModification.objects.filter(status='active').count(),
            'completed': ContractModification.objects.filter(status='completed').count(),
        }
        
        # عدد التسويات حسب النوع
        context['by_type'] = ContractModification.objects.values(
            'modification_type'
        ).annotate(count=Count('id'))
        
        # قائمة العقود للفلترة
        context['contracts'] = Contract.objects.filter(
            status='active'
        ).order_by('contract_number')
        
        return context


class ModificationDetailView(LoginRequiredMixin, DetailView):
    """عرض تفاصيل التسوية"""
    model = ContractModification
    template_name = 'modifications/modification_detail.html'
    context_object_name = 'modification'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # الأثر المالي
        context['financial_impact'] = self.object.get_financial_impact()
        
        # التسويات الأخرى على نفس العقد
        context['related_modifications'] = ContractModification.objects.filter(
            contract=self.object.contract
        ).exclude(id=self.object.id).order_by('-effective_date')[:5]
        
        return context


class RentIncreaseCreateView(LoginRequiredMixin, CreateView):
    """إنشاء تسوية زيادة إيجار"""
    model = ContractModification
    form_class = RentIncreaseForm
    template_name = 'modifications/rent_increase_form.html'
    success_url = reverse_lazy('modification_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modification_type = 'increase'
        messages.success(self.request, 'تم إنشاء تسوية زيادة الإيجار بنجاح')
        return super().form_valid(form)


class RentDecreaseCreateView(LoginRequiredMixin, CreateView):
    """إنشاء تسوية تخفيض إيجار"""
    model = ContractModification
    form_class = RentDecreaseForm
    template_name = 'modifications/rent_decrease_form.html'
    success_url = reverse_lazy('modification_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modification_type = 'decrease'
        messages.success(self.request, 'تم إنشاء تسوية تخفيض الإيجار بنجاح')
        return super().form_valid(form)


class DiscountCreateView(LoginRequiredMixin, CreateView):
    """إنشاء تسوية خصم"""
    model = ContractModification
    form_class = DiscountForm
    template_name = 'modifications/discount_form.html'
    success_url = reverse_lazy('modification_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modification_type = 'discount'
        messages.success(self.request, 'تم إنشاء تسوية الخصم بنجاح')
        return super().form_valid(form)


class TaxCreateView(LoginRequiredMixin, CreateView):
    """إنشاء تسوية ضريبة"""
    model = ContractModification
    form_class = TaxForm
    template_name = 'modifications/tax_form.html'
    success_url = reverse_lazy('modification_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modification_type = 'tax'
        messages.success(self.request, 'تم إنشاء تسوية الضريبة بنجاح')
        return super().form_valid(form)


class ExtendContractCreateView(LoginRequiredMixin, CreateView):
    """إنشاء تسوية تمديد عقد"""
    model = ContractModification
    form_class = ExtendContractForm
    template_name = 'modifications/extend_form.html'
    success_url = reverse_lazy('modification_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modification_type = 'extend'
        messages.success(self.request, 'تم إنشاء تسوية تمديد العقد بنجاح')
        return super().form_valid(form)


class TerminateContractCreateView(LoginRequiredMixin, CreateView):
    """إنشاء تسوية إنهاء عقد"""
    model = ContractModification
    form_class = TerminateContractForm
    template_name = 'modifications/terminate_form.html'
    success_url = reverse_lazy('modification_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.modification_type = 'terminate'
        messages.warning(self.request, 'تم إنشاء تسوية إنهاء العقد - يرجى المراجعة قبل التطبيق')
        return super().form_valid(form)


class ModificationUpdateView(LoginRequiredMixin, UpdateView):
    """تعديل تسوية"""
    model = ContractModification
    template_name = 'modifications/modification_update.html'
    success_url = reverse_lazy('modification_list')
    
    def get_form_class(self):
        """اختيار النموذج المناسب حسب نوع التسوية"""
        modification_type = self.object.modification_type
        
        form_mapping = {
            'increase': RentIncreaseForm,
            'decrease': RentDecreaseForm,
            'discount': DiscountForm,
            'tax': TaxForm,
            'extend': ExtendContractForm,
            'terminate': TerminateContractForm,
        }
        
        return form_mapping.get(modification_type, QuickModificationForm)
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث التسوية بنجاح')
        return super().form_valid(form)


class ModificationDeleteView(LoginRequiredMixin, DeleteView):
    """حذف تسوية"""
    model = ContractModification
    template_name = 'modifications/modification_confirm_delete.html'
    success_url = reverse_lazy('modification_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'تم حذف التسوية بنجاح')
        return super().form_valid(form)


# ==================== Function-Based Views ====================

@login_required
def modification_dashboard(request):
    """لوحة تحكم التسويات"""
    
    # إحصائيات عامة
    total_modifications = ContractModification.objects.count()
    pending_modifications = ContractModification.objects.filter(status='pending').count()
    active_modifications = ContractModification.objects.filter(status='active').count()
    
    # التسويات الأخيرة
    recent_modifications = ContractModification.objects.select_related(
        'contract', 'created_by'
    ).order_by('-created_at')[:10]
    
    # التسويات المعلقة
    pending_list = ContractModification.objects.filter(
        status='pending'
    ).select_related('contract').order_by('effective_date')[:5]
    
    # التسويات القادمة (التي لم يحن موعد تطبيقها)
    upcoming_modifications = ContractModification.objects.filter(
        status='pending',
        effective_date__gt=datetime.now().date()
    ).select_related('contract').order_by('effective_date')[:5]
    
    # إحصائيات حسب النوع
    modifications_by_type = ContractModification.objects.values(
        'modification_type'
    ).annotate(count=Count('id'))
    
    # الأثر المالي الإجمالي
    financial_impact = {
        'increases': ContractModification.objects.filter(
            modification_type='increase',
            status='active'
        ).aggregate(total=Sum('change_amount'))['total'] or 0,
        
        'decreases': ContractModification.objects.filter(
            modification_type='decrease',
            status='active'
        ).aggregate(total=Sum('change_amount'))['total'] or 0,
        
        'discounts': ContractModification.objects.filter(
            modification_type='discount',
            discount_applied=False
        ).aggregate(total=Sum('discount_amount'))['total'] or 0,
        
        'taxes': ContractModification.objects.filter(
            modification_type='tax',
            status='active'
        ).aggregate(total=Sum('tax_amount'))['total'] or 0,
    }
    
    context = {
        'total_modifications': total_modifications,
        'pending_modifications': pending_modifications,
        'active_modifications': active_modifications,
        'recent_modifications': recent_modifications,
        'pending_list': pending_list,
        'upcoming_modifications': upcoming_modifications,
        'modifications_by_type': modifications_by_type,
        'financial_impact': financial_impact,
    }
    
    return render(request, 'modifications/dashboard.html', context)


@login_required
def apply_modification(request, pk):
    """تطبيق التسوية على العقد"""
    modification = get_object_or_404(ContractModification, pk=pk)
    
    if modification.status != 'pending':
        messages.error(request, 'هذه التسوية تم تطبيقها مسبقاً أو ملغاة')
        return redirect('modification_detail', pk=pk)
    
    if request.method == 'POST':
        success = modification.apply_modification()
        
        if success:
            modification.approved_by = request.user
            modification.approved_at = datetime.now()
            modification.save()
            
            messages.success(request, f'تم تطبيق التسوية على العقد {modification.contract.contract_number} بنجاح')
        else:
            messages.error(request, 'حدث خطأ أثناء تطبيق التسوية')
        
        return redirect('modification_detail', pk=pk)
    
    return render(request, 'modifications/apply_confirm.html', {
        'modification': modification
    })


@login_required
def cancel_modification(request, pk):
    """إلغاء التسوية"""
    modification = get_object_or_404(ContractModification, pk=pk)
    
    if modification.status == 'completed':
        messages.error(request, 'لا يمكن إلغاء تسوية مكتملة')
        return redirect('modification_detail', pk=pk)
    
    if request.method == 'POST':
        success = modification.cancel_modification()
        
        if success:
            messages.warning(request, 'تم إلغاء التسوية')
        else:
            messages.error(request, 'حدث خطأ أثناء إلغاء التسوية')
        
        return redirect('modification_detail', pk=pk)
    
    return render(request, 'modifications/cancel_confirm.html', {
        'modification': modification
    })


@login_required
def get_contract_info(request, contract_id):
    """API: الحصول على معلومات العقد (AJAX)"""
    try:
        contract = Contract.objects.get(pk=contract_id)
        data = {
            'success': True,
            'contract_number': contract.contract_number,
            'rent_amount': float(contract.rent_amount),
            'start_date': contract.start_date.strftime('%Y-%m-%d'),
            'end_date': contract.end_date.strftime('%Y-%m-%d'),
            'tenant_name': contract.tenant.name if hasattr(contract, 'tenant') else '',
            'unit_name': contract.unit.name if hasattr(contract, 'unit') else '',
        }
    except Contract.DoesNotExist:
        data = {
            'success': False,
            'error': 'العقد غير موجود'
        }
    
    return JsonResponse(data)


@login_required
def quick_modification(request):
    """إنشاء تسوية سريعة"""
    if request.method == 'POST':
        form = QuickModificationForm(request.POST, request.FILES)
        if form.is_valid():
            modification = form.save(commit=False)
            modification.created_by = request.user
            modification.save()
            
            messages.success(request, 'تم إنشاء التسوية بنجاح')
            return redirect('modification_detail', pk=modification.pk)
    else:
        form = QuickModificationForm()
    
    return render(request, 'modifications/quick_form.html', {'form': form})


@login_required
def modification_report(request):
    """تقرير التسويات"""
    
    # الفترة الزمنية
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    modification_type = request.GET.get('type')
    
    queryset = ContractModification.objects.select_related('contract', 'created_by')
    
    if date_from:
        queryset = queryset.filter(effective_date__gte=date_from)
    if date_to:
        queryset = queryset.filter(effective_date__lte=date_to)
    if modification_type:
        queryset = queryset.filter(modification_type=modification_type)
    
    # إحصائيات التقرير
    report_stats = {
        'total_count': queryset.count(),
        'by_type': queryset.values('modification_type').annotate(count=Count('id')),
        'by_status': queryset.values('status').annotate(count=Count('id')),
        'total_increase': queryset.filter(
            modification_type='increase'
        ).aggregate(total=Sum('change_amount'))['total'] or 0,
        'total_decrease': queryset.filter(
            modification_type='decrease'
        ).aggregate(total=Sum('change_amount'))['total'] or 0,
        'total_discount': queryset.filter(
            modification_type='discount'
        ).aggregate(total=Sum('discount_amount'))['total'] or 0,
    }
    
    context = {
        'modifications': queryset.order_by('-effective_date'),
        'report_stats': report_stats,
        'date_from': date_from,
        'date_to': date_to,
        'modification_type': modification_type,
    }
    
    return render(request, 'modifications/report.html', context)