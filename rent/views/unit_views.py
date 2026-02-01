from .common_imports_view import *
from django.db.models.functions import Cast
from django.db.models import IntegerField

# ========================================
# 4. إدارة الوحدات
# ========================================

class UnitListView(LoginRequiredMixin, PermissionCheckMixin, ListView):
    """قائمة الوحدات"""
    model = Unit
    template_name = 'units/unit_list.html'
    context_object_name = 'units'
    paginate_by = 30
    required_permission = 'rent.view_unit'
    
    def get_queryset(self):
        queryset = Unit.objects.filter(is_active=True).select_related('building__land')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(unit_number__icontains=search) |
                Q(building__name__icontains=search)
            )
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        building = self.request.GET.get('building')
        if building:
            queryset = queryset.filter(building_id=building)
        
        return queryset.annotate(
            unit_number_int=Cast('unit_number', IntegerField())
        ).order_by('building', 'floor', 'unit_number_int', 'unit_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buildings'] = Building.objects.filter(is_active=True).order_by('name')
        return context


class UnitDetailView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """تفاصيل الوحدة"""
    model = Unit
    template_name = 'units/unit_detail.html'
    context_object_name = 'unit'
    required_permission = 'rent.view_unit'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_contract'] = self.object.get_current_contract()
        context['contract_history'] = self.object.contracts.all().order_by('-start_date')
        return context


class UnitCreateView(LoginRequiredMixin, PermissionCheckMixin,  AuditLogMixin, CreateView):
    """إنشاء وحدة جديدة"""
    model = Unit
    form_class = UnitForm
    template_name = 'units/unit_form.html'
    success_url = reverse_lazy('rent:unit_list')
    required_permission = 'rent.add_unit'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.log_action('create', self.object)
        messages.success(self.request, 'تم إنشاء الوحدة بنجاح')
        return response


class UnitUpdateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, UpdateView):
    """تحديث بيانات الوحدة"""
    model = Unit
    form_class = UnitForm
    template_name = 'units/unit_form.html'
    success_url = reverse_lazy('rent:unit_list')
    required_permission = 'rent.change_unit'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action('update', self.object)
        messages.success(self.request, 'تم تحديث بيانات الوحدة بنجاح')
        return response



class UnitDeleteView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, DeleteView):
    """حذف الوحدة (حذف ناعم)"""
    model = Unit
    template_name = 'units/unit_confirm_delete.html'
    success_url = reverse_lazy('rent:unit_list')
    required_permission = 'rent.delete_unit'
    
    def form_valid(self, form):
        self.object = self.get_object()

        # التحقق من عدم وجود عقود نشطة
        if self.object.contracts.filter(status='active').exists():
            messages.error(self.request, 'لا يمكن حذف الوحدة - يوجد عقد نشط')
            return redirect('rent:unit_detail', pk=self.object.pk)

        self.object.is_active = False
        self.object.save()
        self.log_action('delete', self.object)
        messages.success(self.request, 'تم حذف الوحدة بنجاح')
        return redirect(self.success_url)

