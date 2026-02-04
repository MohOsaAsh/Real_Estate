# views/contract_modification_views.py

import logging
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import (
    ListView, DetailView, CreateView, 
    UpdateView, DeleteView
)
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count
from django.core.exceptions import PermissionDenied

# استيراد من الموديلات الموجودة
from rent.models.contract_models import Contract ,ContractStatus, PropertyStatus
from rent.models.contractmodify_models import ContractModification, ModificationType

# استيراد النماذج الموجودة
from rent.forms.contract_modification_forms import (
    ExtensionForm, 
    RentIncreaseForm, 
    RentDecreaseForm,
    DiscountForm, 
    VATForm, 
    TerminationForm, 
    get_modification_form
)


# استيراد الدوال المشتركة
from rent.utils.contract_utils import calculate_contract_due_dates

logger = logging.getLogger(__name__)


# ========================================
# List View
# ========================================

class ModificationListView(LoginRequiredMixin, ListView):
    """عرض قائمة تعديلات العقود"""
    model = ContractModification
    template_name = 'contract_modifications/modification_list.html'
    context_object_name = 'modifications'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ContractModification.objects.select_related(
            'contract', 
            'contract__tenant', 
            'created_by', 
            'applied_by'
        ).order_by('-created_at')
        
        # Filters
        contract_id = self.request.GET.get('contract')
        mod_type = self.request.GET.get('type')
        status = self.request.GET.get('status')
        search = self.request.GET.get('search')
        
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)
        
        if mod_type:
            queryset = queryset.filter(modification_type=mod_type)
        
        if status == 'applied':
            queryset = queryset.filter(is_applied=True)
        elif status == 'pending':
            queryset = queryset.filter(is_applied=False)
        
        if search:
            queryset = queryset.filter(
                Q(contract__contract_number__icontains=search) |
                Q(contract__tenant__name__icontains=search) |
                Q(description__icontains=search)
            )
        
        logger.info(
            f'Modification list accessed by {self.request.user.username}, '
            f'filters: contract={contract_id}, type={mod_type}, status={status}, search={search}'
        )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # إحصائيات بسيطة
        all_mods = ContractModification.objects.all()
        context['stats'] = {
            'total': all_mods.count(),
            'applied': all_mods.filter(is_applied=True).count(),
            'pending': all_mods.filter(is_applied=False).count(),
        }
        
        # إحصائيات حسب النوع
        type_stats = all_mods.values('modification_type').annotate(
            count=Count('id')
        ).order_by('-count')
        context['type_stats'] = type_stats
        
        # قيم الفلاتر
        context['modification_types'] = ModificationType.choices
        context['selected_contract'] = self.request.GET.get('contract', '')
        context['selected_type'] = self.request.GET.get('type', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        
        return context


# ========================================
# Detail View
# ========================================

class ModificationDetailView(LoginRequiredMixin, DetailView):
    """عرض تفاصيل التعديل"""
    model = ContractModification
    template_name = 'contract_modifications/modification_detail.html'
    context_object_name = 'modification'
    
    def get_queryset(self):
        return ContractModification.objects.select_related(
            'contract', 
            'contract__tenant', 
            'created_by', 
            'applied_by'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_apply'] = (
            not self.object.is_applied and 
            self.request.user.has_perm('rent.change_contractmodification')
        )
        context['can_edit'] = (
            not self.object.is_applied and 
            self.request.user.has_perm('rent.change_contractmodification')
        )
        context['can_delete'] = (
            not self.object.is_applied and 
            self.request.user.has_perm('rent.delete_contractmodification')
        )
        
        logger.info(
            f'Modification {self.object.id} viewed by {self.request.user.username}'
        )
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle apply modification action"""
        self.object = self.get_object()
        
        if 'apply' in request.POST:
            # التحقق من الصلاحيات
            if not request.user.has_perm('rent.change_contractmodification'):
                messages.error(request, 'ليس لديك صلاحية لتطبيق التعديلات')
                return redirect('rent:modification_detail', pk=self.object.pk)
            
            if not self.object.is_applied:
                logger.info(
                    f'Applying modification {self.object.id} by {request.user.username}'
                )
                
                success, message = self.object.apply_modification(request.user)
                
                if success:
                    messages.success(request, message)
                    logger.info(
                        f'Modification {self.object.id} applied successfully'
                    )
                else:
                    messages.error(request, message)
                    logger.error(
                        f'Failed to apply modification {self.object.id}: {message}'
                    )
            else:
                messages.warning(request, 'التعديل مُطبّق مسبقاً')
                logger.warning(
                    f'Attempted to apply already applied modification {self.object.id}'
                )
        
        return redirect('rent:modification_detail', pk=self.object.pk)


# ========================================
# Create Views - Base
# ========================================

class ModificationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Base create view for modifications"""
    template_name = 'contract_modifications/modification_form.html'
    permission_required = 'rent.add_contractmodification'
    
    def handle_no_permission(self):
        """معالجة عدم وجود صلاحيات"""
        messages.error(self.request, 'ليس لديك صلاحية لإنشاء تعديلات العقود')
        logger.warning(
            f'Permission denied for {self.request.user.username} '
            f'to create modification'
        )
        return redirect('rent:modification_list')
    
    def get_initial(self):
        initial = super().get_initial()
        contract_id = self.request.GET.get('contract')
        if contract_id:
            initial['contract'] = contract_id
        return initial
    
    def form_valid(self, form):
        try:
            form.instance.created_by = self.request.user
            response = super().form_valid(form)
            
            messages.success(
                self.request, 
                f'تم إنشاء {form.instance.get_modification_type_display()} بنجاح'
            )
            
            logger.info(
                f'Modification created: ID={self.object.id}, '
                f'Type={self.object.modification_type}, '
                f'Contract={self.object.contract.contract_number}, '
                f'User={self.request.user.username}'
            )
            
            return response
        
        except Exception as e:
            logger.error(
                f'Error creating modification: User={self.request.user.username}, '
                f'Error={str(e)}',
                exc_info=True
            )
            messages.error(self.request, f'خطأ في إنشاء التعديل: {str(e)}')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('rent:modification_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.get_title()
        context['modification_type'] = self.get_modification_type()

        # ✅ إرسال قائمة العقود للـ dropdown (Tom Select)
        context['contracts_list'] = Contract.objects.filter(
            status__in=['draft', 'active'],
            is_deleted=False
        ).select_related('tenant').order_by('contract_number')

        # تمرير بيانات جميع العقود للـ JavaScript
        try:
            contracts_data = {}
            for contract in Contract.objects.filter(
                status__in=['draft', 'active'],
                is_deleted=False
            ).select_related('tenant'):
                try:
                    contracts_data[contract.id] = {
                        'tenant_name': contract.tenant.name,
                        'rent_amount': str(contract.annual_rent),
                        'start_date': contract.start_date.strftime('%Y-%m-%d'),
                        'end_date': contract.end_date.strftime('%Y-%m-%d'),
                        'payment_frequency': contract.payment_frequency,
                        'due_dates': [
                            d.strftime('%Y-%m-%d') 
                            for d in calculate_contract_due_dates(contract)
                        ]
                    }
                except Exception as e:
                    logger.error(
                        f'Error processing contract {contract.id}: {str(e)}'
                    )
                    continue
            
            context['contracts_data'] = contracts_data
        
        except Exception as e:
            logger.error(f'Error preparing contracts data: {str(e)}')
            context['contracts_data'] = {}
        
        # معلومات العقد المحدد مسبقاً
        contract_id = self.request.GET.get('contract')
        if contract_id:
            try:
                contract = Contract.objects.select_related('tenant').get(id=contract_id)
                context['selected_contract'] = contract
                context['due_dates'] = calculate_contract_due_dates(contract)
            except Contract.DoesNotExist:
                logger.warning(f'Contract {contract_id} not found')
                pass
            except Exception as e:
                logger.error(f'Error getting selected contract: {str(e)}')
                pass
        
        return context
    
    def get_title(self):
        return "تعديل عقد"
    
    def get_modification_type(self):
        return None


# ========================================
# Create Views - Specific Types
# ========================================

class ExtensionCreateView(ModificationCreateView):
    """إنشاء تمديد عقد"""
    form_class = ExtensionForm
    
    def get_title(self):
        return "تمديد عقد"
    
    def get_modification_type(self):
        return ModificationType.EXTENSION


class RentIncreaseCreateView(ModificationCreateView):
    """إنشاء زيادة إيجار"""
    form_class = RentIncreaseForm
    
    def get_title(self):
        return "زيادة إيجار"
    
    def get_modification_type(self):
        return ModificationType.RENT_INCREASE


class RentDecreaseCreateView(ModificationCreateView):
    """إنشاء تخفيض إيجار"""
    form_class = RentDecreaseForm
    
    def get_title(self):
        return "تخفيض إيجار"
    
    def get_modification_type(self):
        return ModificationType.RENT_DECREASE


class DiscountCreateView(ModificationCreateView):
    """إنشاء خصم"""
    form_class = DiscountForm
    
    def get_title(self):
        return "خصم"
    
    def get_modification_type(self):
        return ModificationType.DISCOUNT


class VATCreateView(ModificationCreateView):
    """إنشاء قيمة مضافة"""
    form_class = VATForm
    
    def get_title(self):
        return "قيمة مضافة"
    
    def get_modification_type(self):
        return ModificationType.VAT


class TerminationCreateView(ModificationCreateView):
    """إنشاء إنهاء عقد"""
    form_class = TerminationForm
    
    def get_title(self):
        return "إنهاء عقد"
    
    def get_modification_type(self):
        return ModificationType.TERMINATION


# ========================================
# Update View
# ========================================

class ModificationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """تعديل التعديل (فقط إذا لم يتم تطبيقه)"""
    model = ContractModification
    template_name = 'contract_modifications/modification_form.html'
    permission_required = 'rent.change_contractmodification'
    
    def handle_no_permission(self):
        """معالجة عدم وجود صلاحيات"""
        messages.error(self.request, 'ليس لديك صلاحية لتعديل التعديلات')
        logger.warning(
            f'Permission denied for {self.request.user.username} '
            f'to update modification'
        )
        return redirect('rent:modification_list')
    
    def get_form_class(self):
        return get_modification_form(self.object.modification_type)
    
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if self.object.is_applied:
            messages.error(request, 'لا يمكن تعديل تعديل مُطبّق')
            logger.warning(
                f'Attempted to edit applied modification {self.object.id} '
                f'by {request.user.username}'
            )
            return redirect('rent:modification_detail', pk=self.object.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, 'تم تحديث التعديل بنجاح')
            
            logger.info(
                f'Modification {self.object.id} updated by {self.request.user.username}'
            )
            
            return response
        
        except Exception as e:
            logger.error(
                f'Error updating modification {self.object.id}: {str(e)}',
                exc_info=True
            )
            messages.error(self.request, f'خطأ في تحديث التعديل: {str(e)}')
            return self.form_invalid(form)
    
    def get_success_url(self):
        return reverse('rent:modification_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        context['title'] = f'تعديل {self.object.get_modification_type_display()}'
        context['modification_type'] = self.object.modification_type

        # ✅ إرسال قائمة العقود للـ dropdown (Tom Select)
        context['contracts_list'] = Contract.objects.filter(
            status__in=['draft', 'active'],
            is_deleted=False
        ).select_related('tenant').order_by('contract_number')

        # إضافة بيانات العقود
        try:
            contracts_data = {}
            for contract in Contract.objects.filter(
                status__in=['draft', 'active'],
                is_deleted=False
            ).select_related('tenant'):
                try:
                    contracts_data[contract.id] = {
                        'tenant_name': contract.tenant.name,
                        'rent_amount': str(contract.annual_rent),
                        'start_date': contract.start_date.strftime('%Y-%m-%d'),
                        'end_date': contract.end_date.strftime('%Y-%m-%d'),
                        'payment_frequency': contract.payment_frequency,
                        'due_dates': [
                            d.strftime('%Y-%m-%d') 
                            for d in calculate_contract_due_dates(contract)
                        ]
                    }
                except Exception as e:
                    logger.error(
                        f'Error processing contract {contract.id}: {str(e)}'
                    )
                    continue
            
            context['contracts_data'] = contracts_data
        
        except Exception as e:
            logger.error(f'Error preparing contracts data: {str(e)}')
            context['contracts_data'] = {}
        
        return context


# ========================================
# Delete View
# ========================================

class ModificationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف التعديل (فقط إذا لم يتم تطبيقه)"""
    model = ContractModification
    template_name = 'contract_modifications/modification_confirm_delete.html'
    success_url = reverse_lazy('rent:modification_list')
    permission_required = 'rent.delete_contractmodification'
    
    def handle_no_permission(self):
        """معالجة عدم وجود صلاحيات"""
        messages.error(self.request, 'ليس لديك صلاحية لحذف التعديلات')
        logger.warning(
            f'Permission denied for {self.request.user.username} '
            f'to delete modification'
        )
        return redirect('rent:modification_list')
    
    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if self.object.is_applied:
            messages.error(request, 'لا يمكن حذف تعديل مُطبّق')
            logger.warning(
                f'Attempted to delete applied modification {self.object.id} '
                f'by {request.user.username}'
            )
            return redirect('rent:modification_detail', pk=self.object.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        modification_id = self.object.id
        modification_type = self.object.get_modification_type_display()

        try:
            response = super().form_valid(form)
            messages.success(self.request, f'تم حذف {modification_type} بنجاح')

            logger.info(
                f'Modification {modification_id} deleted by {self.request.user.username}'
            )

            return response

        except Exception as e:
            logger.error(
                f'Error deleting modification {modification_id}: {str(e)}',
                exc_info=True
            )
            messages.error(self.request, f'خطأ في حذف التعديل: {str(e)}')
            return redirect('rent:modification_detail', pk=modification_id)


# ========================================
# Contract Modifications View
# ========================================

class ContractModificationsView(LoginRequiredMixin, ListView):
    """عرض جميع تعديلات عقد معين"""
    model = ContractModification
    template_name = 'contract_modifications/contract_modifications.html'
    context_object_name = 'modifications'
    paginate_by = 10
    
    def get_queryset(self):
        self.contract = get_object_or_404(Contract, pk=self.kwargs['contract_id'])
        return ContractModification.objects.filter(
            contract=self.contract
        ).select_related('created_by', 'applied_by').order_by('-effective_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract'] = self.contract
        
        # إحصائيات خاصة بالعقد
        mods = self.get_queryset()
        context['stats'] = {
            'total': mods.count(),
            'applied': mods.filter(is_applied=True).count(),
            'pending': mods.filter(is_applied=False).count(),
        }
        
        # إحصائيات حسب النوع
        type_stats = mods.values('modification_type').annotate(
            count=Count('id')
        )
        context['type_stats'] = type_stats
        
        context['can_modify'] = (
            self.contract.status in ['draft', 'active'] and 
            self.request.user.has_perm('rent.add_contractmodification')
        )
        
        logger.info(
            f'Contract {self.contract.id} modifications viewed by {self.request.user.username}'
        )
        
        return context


# ========================================
# Apply Modification View
# ========================================

class ApplyModificationView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """تطبيق التعديل على العقد"""
    model = ContractModification
    permission_required = 'rent.change_contractmodification'
    
    def handle_no_permission(self):
        """معالجة عدم وجود صلاحيات"""
        messages.error(self.request, 'ليس لديك صلاحية لتطبيق التعديلات')
        logger.warning(
            f'Permission denied for {self.request.user.username} '
            f'to apply modification'
        )
        return redirect('rent:modification_list')
    
    def post(self, request, *args, **kwargs):
        modification = self.get_object()
        
        if modification.is_applied:
            messages.warning(request, 'التعديل مُطبّق مسبقاً')
            logger.warning(
                f'Attempted to apply already applied modification {modification.id} '
                f'by {request.user.username}'
            )
        else:
            logger.info(
                f'Applying modification {modification.id} '
                f'(Type: {modification.modification_type}) '
                f'by {request.user.username}'
            )
            
            success, message = modification.apply_modification(request.user)
            
            if success:
                messages.success(request, message)
                logger.info(
                    f'Modification {modification.id} applied successfully'
                )
            else:
                messages.error(request, message)
                logger.error(
                    f'Failed to apply modification {modification.id}: {message}'
                )
        
        return redirect('rent:modification_detail', pk=modification.pk)
    
    def get(self, request, *args, **kwargs):
        """إعادة توجيه GET إلى صفحة التفاصيل"""
        return redirect('rent:modification_detail', pk=self.kwargs['pk'])