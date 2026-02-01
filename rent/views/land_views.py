from .common_imports_view import *

# ========================================
# 2. إدارة الأراضي
# ========================================

class LandListView(LoginRequiredMixin, PermissionCheckMixin, ListView):
    """قائمة الأراضي"""
    model = Land
    template_name = 'lands/land_list.html'
    context_object_name = 'lands'
    paginate_by = 20
    required_permission = 'rent.view_land'  # ✅ استخدام الصلاحية الصحيحة
    
    def get_queryset(self):
        queryset = Land.objects.filter(is_active=True)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(deed_number__icontains=search) |
                Q(owner_name__icontains=search)
            )
        
        ownership = self.request.GET.get('ownership')
        if ownership:
            queryset = queryset.filter(ownership_type=ownership)
        
        return queryset.order_by('-created_at')


class LandDetailView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """تفاصيل الأرض"""
    model = Land
    template_name = 'lands/land_detail.html'
    context_object_name = 'land'
    required_permission = 'rent.view_land'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['buildings'] = self.object.get_active_buildings()
        context['total_units'] = Unit.objects.filter(
            building__land=self.object,
            is_active=True
        ).count()
        return context


class LandCreateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, CreateView):
    """إنشاء أرض جديدة"""
    model = Land
    form_class = LandForm
    template_name = 'lands/land_form.html'
    success_url = reverse_lazy('rent:land_list')
    required_permission = 'rent.add_land'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.log_action('create', self.object)  # ✅ يعمل الآن
        messages.success(self.request, 'تم إنشاء الأرض بنجاح')
        return response


class LandUpdateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, UpdateView):
    """تحديث بيانات الأرض"""
    model = Land
    form_class = LandForm
    template_name = 'lands/land_form.html'
    success_url = reverse_lazy('rent:land_list')
    required_permission = 'rent.change_land'
    
    def form_valid(self, form):
        # حفظ البيانات القديمة
        old_data = {field: getattr(self.object, field) for field in form.changed_data}
        
        response = super().form_valid(form)
        
        # حفظ البيانات الجديدة
        new_data = {field: getattr(self.object, field) for field in form.changed_data}
        
        self.log_action('update', self.object, old_data=old_data, new_data=new_data)
        messages.success(self.request, 'تم تحديث بيانات الأرض بنجاح')
        return response


class LandDeleteView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, DeleteView):
    """حذف الأرض (حذف ناعم)"""
    model = Land
    template_name = 'lands/land_confirm_delete.html'
    success_url = reverse_lazy('rent:land_list')
    required_permission = 'rent.delete_land'

    def form_valid(self, form):
        self.object = self.get_object()
        try:
            self.object.is_active = False
            self.object.save()
            self.log_action('delete', self.object)
            messages.success(self.request, 'تم حذف الأرض بنجاح')
        except Exception:
            messages.error(self.request, 'لا يمكن حذف الأرض - توجد مباني مرتبطة بها')
            return redirect('rent:land_detail', pk=self.object.pk)
        return redirect(self.success_url)