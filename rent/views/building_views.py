
from .common_imports_view import *

# ========================================
# 3. إدارة المباني
# ========================================

class BuildingListView(LoginRequiredMixin, PermissionCheckMixin, ListView):
    """قائمة المباني"""
    model = Building
    template_name = 'buildings/building_list.html'
    context_object_name = 'buildings'
    paginate_by = 20
    required_permission = 'rent.view_building'
    
    def get_queryset(self):
        queryset = Building.objects.filter(is_active=True).select_related('land')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(land__name__icontains=search)
            )
        
        building_type = self.request.GET.get('type')
        if building_type:
            queryset = queryset.filter(building_type=building_type)
        
        return queryset.order_by('-created_at')


class BuildingDetailView(LoginRequiredMixin, PermissionCheckMixin, DetailView):
    """تفاصيل المبنى"""
    model = Building
    template_name = 'buildings/building_detail.html'
    context_object_name = 'building'
    required_permission = 'rent.view_building'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['units'] = self.object.units.filter(is_active=True)
        context['occupancy_rate'] = self.object.get_occupancy_rate()
        return context


class BuildingCreateView(LoginRequiredMixin, PermissionCheckMixin, AuditLogMixin, CreateView):
    """إنشاء مبنى جديد"""
    model = Building
    form_class = BuildingForm
    template_name = 'buildings/building_form.html'
    success_url = reverse_lazy('rent:building_list')
    required_permission = 'rent.add_building'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.log_action('create', self.object)
        messages.success(self.request, 'تم إنشاء المبنى بنجاح')
        return response


class BuildingUpdateView(LoginRequiredMixin, PermissionCheckMixin,  UpdateView):
    """تحديث بيانات المبنى"""
    model = Building
    form_class = BuildingForm
    template_name = 'buildings/building_form.html'
    success_url = reverse_lazy('rent:building_list')
    required_permission = 'rent.change_building'

    def form_valid(self, form):
        response = super().form_valid(form)
        self.log_action('update', self.object)
        messages.success(self.request, 'تم تحديث بيانات المبنى بنجاح')
        return response




class BuildingDeleteView(LoginRequiredMixin, PermissionCheckMixin,  DeleteView):
    """حذف المبنى (حذف ناعم)"""
    model = Building
    template_name = 'buildings/building_confirm_delete.html'
    success_url = reverse_lazy('rent:building_list')
    required_permission = 'rent.delete_building'

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.is_active = False
        self.object.save()
        self.log_action('delete', self.object)
        messages.success(self.request, 'تم حذف المبنى بنجاح')
        return redirect(self.success_url)


