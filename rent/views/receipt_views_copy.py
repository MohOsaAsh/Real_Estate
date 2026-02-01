"""
Receipt Views - Fixed Version
عروض سندات القبض - نسخة محدثة
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Q, Sum, Count

from rent.models import Receipt, Contract
from rent.forms import ReceiptForm
from rent.views.common_imports_view import PermissionCheckMixin


# ========================================
# Receipt List View
# ========================================

class ReceiptListView(LoginRequiredMixin, PermissionCheckMixin, ListView):
    """قائمة سندات القبض"""
    model = Receipt
    template_name = 'receipts/receipt_list.html'
    context_object_name = 'receipts'
    paginate_by = 30
    required_permission = 'can_process_payments'
    
    def get_queryset(self):
        queryset = Receipt.objects.select_related(
            'contract__tenant',
            'created_by'
        ).filter(is_deleted=False)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(receipt_number__icontains=search) |
                Q(contract__contract_number__icontains=search) |
                Q(contract__tenant__name__icontains=search)
            )
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Date filters
        date_from = self.request.GET.get('date_from')
        if date_from:
            queryset = queryset.filter(receipt_date__gte=date_from)
        
        date_to = self.request.GET.get('date_to')
        if date_to:
            queryset = queryset.filter(receipt_date__lte=date_to)
        
        return queryset.order_by('-receipt_date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        queryset = self.get_queryset()
        
        # Add statistics
        context['total_amount'] = queryset.filter(
            status='posted'
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        context['posted_count'] = queryset.filter(status='posted').count()
        context['draft_count'] = queryset.filter(status='draft').count()
        context['cancelled_count'] = queryset.filter(status='cancelled').count()
        
        return context


# ========================================
# Receipt Detail View
# ========================================

class ReceiptDetailView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """تفاصيل سند القبض"""
    model = Receipt
    template_name = 'receipts/receipt_detail.html'
    context_object_name = 'receipt'
    required_permission = 'can_process_payments'
    
    def get_queryset(self):
        return Receipt.objects.select_related(
            'contract__tenant',
            'created_by',
            'posted_by',
            'cancelled_by'
        ).filter(is_deleted=False)


# ========================================
# Receipt Create View
# ========================================

class ReceiptCreateView(LoginRequiredMixin, PermissionCheckMixin,  CreateView):
    """إنشاء سند قبض جديد"""
    model = Receipt
    form_class = ReceiptForm
    template_name = 'receipts/receipt_form.html'
    required_permission = 'can_process_payments'
    
    def get_success_url(self):
        """استخدام اسم URL الصحيح"""
        return reverse_lazy('rent:receipt_detail', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pre-fill contract if provided in URL
        contract_id = self.request.GET.get('contract')
        if contract_id:
            try:
                contract = Contract.objects.get(pk=contract_id)
                kwargs['initial'] = {'contract': contract}
            except Contract.DoesNotExist:
                pass
        return kwargs
    
    def form_valid(self, form):
        # Set created_by
        form.instance.created_by = self.request.user
        
        try:
            response = super().form_valid(form)
            
            # Log action
            self.log_action(
                'create',
                self.object,
                description=f'إنشاء سند قبض {self.object.receipt_number}'
            )
            
            messages.success(
                self.request,
                f'تم إنشاء سند القبض {self.object.receipt_number} بنجاح'
            )
            
            return response
            
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)
        except Exception as e:
            messages.error(self.request, f'حدث خطأ: {str(e)}')
            return self.form_invalid(form)


# ========================================
# Receipt Update View
# ========================================

class ReceiptUpdateView(LoginRequiredMixin, PermissionCheckMixin, UpdateView):
    """تعديل سند قبض"""
    model = Receipt
    form_class = ReceiptForm
    template_name = 'receipts/receipt_form.html'
    required_permission = 'can_process_payments'
    
    def get_success_url(self):
        return reverse_lazy('rent:receipt_detail', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        # Only allow editing draft receipts
        return Receipt.objects.filter(
            is_deleted=False,
            status='draft'
        )
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            
            # Log action
            self.log_action(
                'update',
                self.object,
                description=f'تعديل سند قبض {self.object.receipt_number}'
            )
            
            messages.success(
                self.request,
                f'تم تعديل سند القبض {self.object.receipt_number} بنجاح'
            )
            
            return response
            
        except ValidationError as e:
            form.add_error(None, e)
            return self.form_invalid(form)


# ========================================
# Receipt Delete View
# ========================================

class ReceiptDeleteView(LoginRequiredMixin, PermissionCheckMixin,  DeleteView):
    """حذف سند قبض"""
    model = Receipt
    template_name = 'receipts/receipt_delete.html'
    context_object_name = 'receipt'
    required_permission = 'can_process_payments'
    
    def get_success_url(self):
        return reverse_lazy('rent:receipt_list')
    
    def get_queryset(self):
        # Only allow deleting draft receipts
        return Receipt.objects.filter(
            is_deleted=False,
            status='draft'
        )
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Get delete reason if provided
        delete_reason = request.POST.get('delete_reason', '')
        
        # Soft delete
        self.object.is_deleted = True
        self.object.deleted_by = request.user
        self.object.save()
        
        # Log action
        self.log_action(
            'delete',
            self.object,
            description=f'حذف سند قبض {self.object.receipt_number}. السبب: {delete_reason}'
        )
        
        messages.success(
            request,
            f'تم حذف سند القبض {self.object.receipt_number} بنجاح'
        )
        
        return redirect(success_url)


# ========================================
# Receipt Post View (Finalize)
# ========================================

class ReceiptPostView(LoginRequiredMixin, PermissionCheckMixin,  DetailView):
    """ترحيل سند القبض"""
    model = Receipt
    required_permission = 'can_process_payments'
    
    def post(self, request, *args, **kwargs):
        receipt = self.get_object()
        
        # Post the receipt
        success, message = receipt.post_receipt(user=request.user)
        
        if success:
            if hasattr(self, 'log_action') and callable(self.log_action):
            # Log action
                self.log_action(
                    'payment',
                    receipt,
                    description=f'ترحيل سند القبض {receipt.receipt_number}'
                )
            
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('rent:receipt_detail', pk=receipt.pk)


# ========================================
# Receipt Cancel View
# ========================================

class ReceiptCancelView(LoginRequiredMixin, PermissionCheckMixin,  DetailView):
    """إلغاء سند القبض"""
    model = Receipt
    required_permission = 'can_process_payments'
    
    def post(self, request, *args, **kwargs):
        receipt = self.get_object()
        
        # Get cancellation reason
        reason = request.POST.get('reason', '')
        
        if not reason:
            messages.error(request, 'يجب إدخال سبب الإلغاء')
            return redirect('rent:receipt_detail', pk=receipt.pk)
        
        # Cancel the receipt
        success, message = receipt.cancel_receipt(reason=reason, user=request.user)
        
        if success:
            # Log action
            self.log_action(
                'cancel',
                receipt,
                description=f'إلغاء سند القبض {receipt.receipt_number}. السبب: {reason}'
            )
            
            messages.success(request, message)
        else:
            messages.error(request, message)
        
        return redirect('rent:receipt_detail', pk=receipt.pk)


# ========================================
# Receipt Print View
# ========================================

class ReceiptPrintView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """طباعة سند القبض"""
    model = Receipt
    template_name = 'receipts/receipt_print.html'
    context_object_name = 'receipt'
    required_permission = 'can_process_payments'
    
    def get_queryset(self):
        # استخدام select_related فقط للعلاقات المباشرة
        return Receipt.objects.select_related(
            'contract__tenant',
            'created_by',
            'posted_by'
        ).filter(is_deleted=False)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add current date/time for print
        from django.utils import timezone
        context['now'] = timezone.now()
        
        # Add QR code if needed (you can implement this later)
        context['qr_code'] = None
        
        # Add unit and building info safely
        receipt = self.object
        if receipt.contract:
            context['unit'] = getattr(receipt.contract, 'unit', None)
            if context['unit']:
                context['building'] = getattr(context['unit'], 'building', None)
        
        return context