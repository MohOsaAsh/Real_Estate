from .common_imports_view import *

# ========================================
# 5. إدارة المستأجرين
# ========================================

class TenantListView(LoginRequiredMixin, PermissionCheckMixin, ListView):
    """قائمة المستأجرين"""
    model = Tenant
    template_name = 'tenants/tenant_list.html'
    context_object_name = 'tenants'
    paginate_by = 20
    required_permission = 'rent.view_tenant'
    
    def get_queryset(self):
        queryset = Tenant.objects.filter(is_active=True)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(id_number__icontains=search)
            )
        
        tenant_type = self.request.GET.get('type')
        if tenant_type:
            queryset = queryset.filter(tenant_type=tenant_type)
        
        return queryset.order_by('name')


class TenantDetailView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """تفاصيل المستأجر"""
    model = Tenant
    template_name = 'tenants/tenant_detail.html'
    context_object_name = 'tenant'
    required_permission = 'rent.view_tenant'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_contracts'] = self.object.get_active_contracts()
        context['all_contracts'] = self.object.contracts.all().order_by('-start_date')
        context['documents'] = self.object.documents.all()
        context['outstanding_balance'] = self.object.get_outstanding_balance()
        return context


class TenantCreateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, CreateView):
    """إنشاء مستأجر جديد"""
    model = Tenant
    form_class = TenantForm
    template_name = 'tenants/tenant_form.html'
    success_url = reverse_lazy('rent:tenant_list')
    required_permission = 'rent.add_tenant'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.log_action('create', self.object)
        messages.success(self.request, 'تم إنشاء المستأجر بنجاح')
        return response
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field}: {error}")
        return super().form_invalid(form)


class TenantUpdateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, UpdateView):
    """تحديث بيانات المستأجر"""
    model = Tenant
    form_class = TenantForm
    template_name = 'tenants/tenant_form.html'
    success_url = reverse_lazy('tenant_list')
    required_permission = 'rent.change_tenant'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action('update', self.object)
        messages.success(self.request, 'تم تحديث بيانات المستأجر بنجاح')
        return response




class TenantDeleteView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, DeleteView):
    """حذف المستأجر (حذف ناعم)"""
    model = Tenant
    template_name = 'tenants/tenant_confirm_delete.html'
    success_url = reverse_lazy('rental:tenant_list')
    required_permission = 'rent.delete_tenant'


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # تمرير العقود النشطة للتمبلت
        context['active_contracts'] = self.object.contracts.filter(status='active')
        return context
    



    def form_valid(self, form):
        self.object = self.get_object()

        # التحقق من عدم وجود عقود نشطة
        if self.object.contracts.filter(status='active').exists():
            messages.error(self.request, 'لا يمكن حذف المستأجر - يوجد عقود نشطة')
            return redirect('rental:tenant_detail', pk=self.object.pk)

        self.object.is_active = False
        self.object.save()
        self.log_action('delete', self.object)
        messages.success(self.request, 'تم حذف المستأجر بنجاح')
        return redirect(self.success_url)


