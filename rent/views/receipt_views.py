# rent/views/receipt_views.py

"""
Receipt Views - Updated Version
✅ Updated to use ContractFinancialService
عروض سندات القبض - محدث لاستخدام الخدمة الموحدة
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
from django.db.models import Q, Sum, Count

from rent.models import Receipt, Contract
from rent.forms import ReceiptForm

# ✅ NEW: استيراد الخدمة الموحدة
from rent.services.contract_financial_service import ContractFinancialService

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
    required_permission = 'rent.view_receipt'
    
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
    required_permission = 'rent.view_receipt'
    
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

class ReceiptCreateView(LoginRequiredMixin, PermissionCheckMixin, CreateView):
    """
    إنشاء سند قبض جديد - Dynamic Version
    ✅ Updated to use ContractFinancialService

    الآلية:
    1. GET بدون params → عرض Form فارغ
    2. GET مع contract & amount → عرض معاينة التوزيع مع تعبئة الفورم
    3. POST → حفظ السند
    """
    model = Receipt
    form_class = ReceiptForm
    template_name = 'receipts/receipt_form_preview.html'
    required_permission = 'rent.add_receipt'

    def get_success_url(self):
        return reverse_lazy('rent:receipt_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ✅ إرسال قائمة العقود النشطة للـ dropdown
        context['contracts_list'] = Contract.objects.filter(
            status='active',
            is_deleted=False
        ).select_related('tenant').order_by('contract_number')

        # إذا كان GET يحتوي على بيانات معاينة
        if self.request.method == 'GET' and 'contract' in self.request.GET:
            # بناء الفورم مع بيانات GET للحفاظ على القيم
            context['form'] = ReceiptForm(self.request.GET)

            contract_id = self.request.GET.get('contract')
            amount_str = self.request.GET.get('amount')

            if contract_id and amount_str:
                context.update(self._generate_preview(contract_id, amount_str))
        else:
            # الفورم العادي (GET بدون params أو POST)
            context['form'] = self.get_form()

        return context

    def get_form_kwargs(self):
        """
        نترك kwargs كما هي، لأننا نبني الفورم مع GET في get_context_data
        """
        return super().get_form_kwargs()

    def _generate_preview(self, contract_id, amount_str):
        """
        حساب توزيع المبلغ على الفترات غير المسددة
        ✅ Updated to use ContractFinancialService
        """
        try:
            contract = Contract.objects.get(pk=contract_id)
        except Contract.DoesNotExist:
            return {'preview_error': 'العقد غير موجود'}

        try:
            amount = Decimal(amount_str)
        except:
            return {'preview_error': 'المبلغ غير صالح'}

        # ✅ NEW: استخدام الخدمة الموحدة
        service = ContractFinancialService(contract)
        data = service.calculate_periods_with_payments()

        if amount > data['totals']['total_remaining']:
            return {'preview_error': 'المبلغ أكبر من المتبقي'}

        # كل شيء جاهز
        return {
            'preview_mode': True,
            'selected_contract': contract,
            'input_amount': amount,

            'total_contract_value': data['totals']['total_due'],
            'total_paid': data['totals']['total_paid'],
            'total_remaining': data['totals']['total_remaining'],

            'all_periods': data['periods'],
            'unpaid_periods': service.get_unpaid_periods(),
            'distribution': service.calculate_payment_distribution(amount),
        }

    def form_valid(self, form):
        """
        حفظ السند
        """
        form.instance.created_by = self.request.user

        try:
            # التحقق النهائي من إمكانية القبول
            can_pay, message = form.instance.contract.can_accept_payment(form.instance.amount)
            if not can_pay:
                form.add_error('amount', message)
                return self.form_invalid(form)

            # حفظ السند
            response = super().form_valid(form)

            # Log action
            if hasattr(self, 'log_action') and callable(self.log_action):
                self.log_action(
                    'create',
                    self.object,
                    description=f'إنشاء سند قبض {self.object.receipt_number} بمبلغ {self.object.amount}'
                )

            messages.success(
                self.request,
                f'تم إنشاء سند القبض {self.object.receipt_number} بنجاح'
            )

            return response

        except ValidationError as e:
            if hasattr(e, 'messages'):
                for message in e.messages:
                    form.add_error(None, message)
            else:
                form.add_error(None, str(e))
            return self.form_invalid(form)


# ========================================
# Receipt Update View
# ========================================

class ReceiptUpdateView(LoginRequiredMixin, PermissionCheckMixin, UpdateView):
    """
    تعديل سند قبض - Dynamic Version
    ✅ Updated to use ContractFinancialService
    """
    model = Receipt
    form_class = ReceiptForm
    template_name = 'receipts/receipt_form.html'
    required_permission = 'rent.change_receipt'
    
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
            # التحقق من إمكانية القبول
            can_pay, message = form.instance.contract.can_accept_payment(form.instance.amount)
            if not can_pay:
                form.add_error('amount', message)
                return self.form_invalid(form)
            
            response = super().form_valid(form)
            
            # Log action
            if hasattr(self, 'log_action') and callable(self.log_action):
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

class ReceiptDeleteView(LoginRequiredMixin, PermissionCheckMixin, DeleteView):
    """حذف سند قبض"""
    model = Receipt
    template_name = 'receipts/receipt_delete.html'
    context_object_name = 'receipt'
    required_permission = 'rent.delete_receipt'
    
    def get_success_url(self):
        return reverse_lazy('rent:receipt_list')
    
    def get_queryset(self):
        # Only allow deleting draft receipts
        return Receipt.objects.filter(
            is_deleted=False,
            status='draft'
        )
    
    def form_valid(self, form):
        self.object = self.get_object()
        success_url = self.get_success_url()

        # Get delete reason if provided
        delete_reason = self.request.POST.get('delete_reason', '')

        # Soft delete
        self.object.is_deleted = True
        self.object.deleted_by = self.request.user
        self.object.save()

        # Log action
        if hasattr(self, 'log_action') and callable(self.log_action):
            self.log_action(
                'delete',
                self.object,
                description=f'حذف سند قبض {self.object.receipt_number}. السبب: {delete_reason}'
            )

        messages.success(
            self.request,
            f'تم حذف سند القبض {self.object.receipt_number} بنجاح'
        )

        return redirect(success_url)


# ========================================
# Receipt Post View (Finalize)
# ========================================

class ReceiptPostView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """ترحيل سند القبض"""
    model = Receipt
    required_permission = 'rent.post_receipt'
    
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

class ReceiptCancelView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """إلغاء سند القبض"""
    model = Receipt
    required_permission = 'rent.cancel_receipt'
    
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
            if hasattr(self, 'log_action') and callable(self.log_action):
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
    """
    طباعة سند القبض - Updated
    ✅ Updated to use ContractFinancialService
    """
    model = Receipt
    template_name = 'receipts/receipt_print.html'
    context_object_name = 'receipt'
    required_permission = 'rent.print_receipt'
    
    def get_queryset(self):
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
        
        # ✅ NEW: استخدام الخدمة الموحدة للحصول على الفترات المغطاة
        receipt = self.object
        if receipt.contract:
            service = ContractFinancialService(receipt.contract)
            
            # الحصول على الفترات المغطاة بهذا السند
            # (هذه الدالة يجب إضافتها للـ Service إذا لم تكن موجودة)
            context['covered_periods'] = self._get_covered_periods(service, receipt)
        
        # Add unit and building info safely
        if receipt.contract:
            context['unit'] = getattr(receipt.contract, 'unit', None)
            if context.get('unit'):
                context['building'] = getattr(context['unit'], 'building', None)
        
        return context
    
    def _get_covered_periods(self, service, receipt):
        """
        حساب الفترات التي غطاها هذا السند
        ✅ يستخدم منطق الخدمة الموحدة
        """
        try:
            # الحصول على المدفوع قبل هذا السند
            paid_before = receipt.contract.receipts.filter(
                receipt_date__lt=receipt.receipt_date,
                status='posted',
                is_deleted=False
            ).exclude(
                pk=receipt.pk
            ).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            paid_with = paid_before + receipt.amount
            
            # الحصول على الفترات
            periods = service.calculate_periods_with_modifications()
            covered_periods = []
            
            cumulative = Decimal('0')
            
            for period in periods:
                period_start = cumulative
                period_end = cumulative + period['due_amount']
                
                if paid_with > period_start and paid_before < period_end:
                    start_in_period = max(paid_before, period_start)
                    end_in_period = min(paid_with, period_end)
                    allocated = end_in_period - start_in_period
                    
                    if allocated > 0:
                        covered_periods.append({
                            'period_number': period['period_number'],
                            'start_date': period['start_date'],
                            'end_date': period.get('end_date'),
                            'due_amount': period['due_amount'],
                            'allocated_amount': allocated,
                            'description': f'سداد دفعة من إيجار الفترة'
                        })
                
                cumulative = period_end
                
                if paid_with <= cumulative:
                    break
            
            return covered_periods
            
        except Exception as e:
            # في حالة حدوث خطأ، نرجع قائمة فارغة
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error calculating covered periods: {e}')
            return []


# ========================================
# Receipt PDF Export View
# ========================================

class ReceiptPDFView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """
    تصدير سند القبض كـ PDF
    ✅ يستخدم xhtml2pdf
    """
    model = Receipt
    template_name = 'receipts/receipt_pdf.html'
    context_object_name = 'receipt'
    required_permission = 'rent.export_receipt_pdf'

    def get_queryset(self):
        return Receipt.objects.select_related(
            'contract__tenant',
            'created_by',
            'posted_by'
        ).filter(is_deleted=False)

    def get(self, request, *args, **kwargs):
        from django.template.loader import get_template
        from django.http import HttpResponse
        from io import BytesIO
        from django.utils import timezone

        try:
            from xhtml2pdf import pisa
            HAS_XHTML2PDF = True
        except ImportError:
            HAS_XHTML2PDF = False

        self.object = self.get_object()
        receipt = self.object

        # جلب الفترات المغطاة
        covered_periods = []
        unit_numbers = "غير محدد"
        location = "غير محدد"

        if receipt.contract:
            service = ContractFinancialService(receipt.contract)
            covered_periods = self._get_covered_periods_with_status(service, receipt)

            # جلب أرقام الوحدات والموقع
            unit_numbers = service.all_unit_numbers_str
            location = service.location

        import os
        from django.conf import settings as django_settings

        base_dir = str(django_settings.BASE_DIR)

        context = {
            'receipt': receipt,
            'covered_periods': covered_periods,
            'unit_numbers': unit_numbers,
            'location': location,
            'now': timezone.now(),
            'site_url': request.build_absolute_uri('/').rstrip('/'),
        }

        # Check directly from request GET parameters
        is_download = request.GET.get('download') == 'true'
        context['is_download'] = is_download

        if is_download:
            bg_rel_path = os.path.join('static', 'images', 'receipt_bg.jpg')
            #bg_rel_path = os.path.join('static', 'images', 'receipt_bg.png')


            background_path = os.path.join(base_dir, bg_rel_path)
            if os.name == 'nt':
                background_path = background_path.replace('\\', '/')
            context['background_path'] = background_path

        if HAS_XHTML2PDF:
            # تسجيل خط عربي مع reportlab و xhtml2pdf
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from xhtml2pdf.default import DEFAULT_FONT

            font_dir = os.path.join(base_dir, 'static', 'fonts')

            if 'Arabic' not in pdfmetrics.getRegisteredFontNames():
                font_path = os.path.join(font_dir, 'arial.ttf')
                font_bold_path = os.path.join(font_dir, 'arialbd.ttf')

                # تسجيل مع reportlab
                pdfmetrics.registerFont(TTFont('Arabic', font_path))
                pdfmetrics.registerFont(TTFont('Arabic-Bold', font_bold_path))
                from reportlab.lib.fonts import addMapping
                addMapping('Arabic', 0, 0, 'Arabic')
                addMapping('Arabic', 1, 0, 'Arabic-Bold')

                # تسجيل في قاموس xhtml2pdf لربط اسم CSS بالخط
                DEFAULT_FONT['arabic'] = 'Arabic'
                DEFAULT_FONT['arabic-bold'] = 'Arabic-Bold'

            # استخدام xhtml2pdf لإنشاء PDF
            template = get_template('receipts/receipt_pdf.html')
            html_string = template.render(context)

            # معالجة النص العربي لتصحيح الحروف والاتجاه
            try:
                import arabic_reshaper
                from bidi.algorithm import get_display
                import re

                def reshape_arabic_in_html(html):
                    """إعادة تشكيل النص العربي داخل HTML مع الحفاظ على الوسوم"""
                    parts = re.split(r'(<[^>]+>)', html)
                    result_parts = []
                    for part in parts:
                        if part.startswith('<'):
                            result_parts.append(part)
                        else:
                            if any('\u0600' <= c <= '\u06FF' or '\u0750' <= c <= '\u077F' for c in part):
                                reshaped = arabic_reshaper.reshape(part)
                                bidi_text = get_display(reshaped)
                                result_parts.append(bidi_text)
                            else:
                                result_parts.append(part)
                    return ''.join(result_parts)

                html_string = reshape_arabic_in_html(html_string)
            except ImportError:
                pass

            # إنشاء PDF
            result = BytesIO()
            pdf = pisa.pisaDocument(
                BytesIO(html_string.encode('utf-8')),
                result,
                encoding='utf-8',
            )

            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf')
                
                # Custom filename: Number - Tenant - Date
                filename = f"{receipt.receipt_number} - {receipt.contract.tenant.name} - {receipt.receipt_date}"
                
                # Check directly from request GET parameters
                # Use string 'true' to match URL query param
                is_download = request.GET.get('download') == 'true'
                disposition_type = 'attachment' if is_download else 'inline'

                response['Content-Disposition'] = (
                    f'{disposition_type}; filename="{filename}.pdf"'
                )
                return response

        # Fallback: عرض HTML
        return render(request, 'receipts/receipt_pdf.html', context)

    def _get_covered_periods_with_status(self, service, receipt):
        """
        حساب الفترات التي غطاها هذا السند مع حالة كل فترة (كامل/جزئي)
        """
        try:
            # الحصول على المدفوع قبل هذا السند
            paid_before = receipt.contract.receipts.filter(
                receipt_date__lt=receipt.receipt_date,
                status='posted',
                is_deleted=False
            ).exclude(
                pk=receipt.pk
            ).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')

            paid_with = paid_before + receipt.amount

            # الحصول على الفترات
            periods = service.calculate_periods_with_modifications()
            covered_periods = []

            cumulative = Decimal('0')

            for period in periods:
                period_start = cumulative
                period_end = cumulative + period['due_amount']

                if paid_with > period_start and paid_before < period_end:
                    start_in_period = max(paid_before, period_start)
                    end_in_period = min(paid_with, period_end)
                    allocated = end_in_period - start_in_period

                    if allocated > 0:
                        # حساب المتبقي بعد هذه الدفعة
                        remaining_after = period['due_amount'] - (end_in_period - period_start)

                        covered_periods.append({
                            'period_number': period['period_number'],
                            'start_date': period['start_date'],
                            'end_date': period.get('end_date'),
                            'due_amount': period['due_amount'],
                            'allocated_amount': allocated,
                            'remaining_after': max(Decimal('0'), remaining_after),
                            'description': f'إيجار الفترة {period["period_number"]}'
                        })

                cumulative = period_end

                if paid_with <= cumulative:
                    break

            return covered_periods

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error calculating covered periods: {e}')
            return []