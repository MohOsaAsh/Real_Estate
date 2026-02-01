from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.contrib.auth.models import User, Group, Permission
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import login
from .forms import UserRegistrationForm, UserUpdateForm, PermissionAssignmentForm


# ============ التسجيل وإنشاء مستخدم جديد ============
class UserRegistrationView(CreateView):
    """عرض تسجيل مستخدم جديد"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'authentication/register.html'
    success_url = reverse_lazy('auth_app:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.')
        return response
    
    def dispatch(self, request, *args, **kwargs):
        # إذا كان المستخدم مسجل دخول بالفعل، إعادة توجيهه للداشبورد
        if request.user.is_authenticated:
            return redirect('rent:dashboard')  # ✅ تعديل هنا
        return super().dispatch(request, *args, **kwargs)


# ============ تسجيل الدخول ============
class UserLoginView(LoginView):
    """عرض تسجيل الدخول"""
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """تحديد الصفحة بعد تسجيل الدخول الناجح"""
        # 1. تحقق من معامل 'next' في URL
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        
        # 2. التوجيه إلى الداشبورد الرئيسي
        return reverse_lazy('rent:dashboard')  # ✅ تعديل هنا
    
    def form_valid(self, form):
        messages.success(self.request, f'مرحباً {form.get_user().username}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'اسم المستخدم أو كلمة المرور غير صحيحة.')
        return super().form_invalid(form)


# ============ تسجيل الخروج ============
class UserLogoutView(LogoutView):
    """عرض تسجيل الخروج"""
    http_method_names = ['post', 'get']  # ✅ إضافة GET للسماح بالوصول المباشر
    
    def get_next_page(self):
        """تحديد الصفحة بعد تسجيل الخروج"""
        return reverse_lazy('auth_app:login')  # ✅ تعديل هنا
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'تم تسجيل الخروج بنجاح.')
        return super().dispatch(request, *args, **kwargs)


# ============ لوحة التحكم الرئيسية (للمستخدمين) ============
class DashboardView(LoginRequiredMixin, ListView):
    """
    لوحة التحكم للمستخدمين - تتطلب تسجيل الدخول
    ملاحظة: هذه لوحة تحكم المستخدمين، وليست الداشبورد الرئيسي
    """
    model = User
    template_name = 'authentication/user_dashboard.html'
    context_object_name = 'users'
    login_url = '/auth/login/'  # ✅ تعديل هنا
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all().order_by('-date_joined')
        return User.objects.filter(id=self.request.user.id)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_users'] = User.objects.count()
        context['active_users'] = User.objects.filter(is_active=True).count()
        return context


# ============ عرض تفاصيل المستخدم ============
class UserDetailView(LoginRequiredMixin, DetailView):
    """عرض تفاصيل مستخدم معين"""
    model = User
    template_name = 'authentication/user_detail.html'
    context_object_name = 'user_profile'
    login_url = '/auth/login/'  # ✅ تعديل هنا
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['user_groups'] = user.groups.all()
        context['user_permissions'] = user.user_permissions.all()
        context['all_permissions'] = user.get_all_permissions()
        return context


# ============ تعديل بيانات المستخدم ============
class UserUpdateView(LoginRequiredMixin, UpdateView):
    """تعديل بيانات المستخدم"""
    model = User
    form_class = UserUpdateForm
    template_name = 'authentication/user_update.html'
    login_url = '/auth/login/'  # ✅ تعديل هنا
    
    def get_success_url(self):
        return reverse_lazy('auth_app:user-detail', kwargs={'pk': self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj != request.user and not request.user.is_superuser:
            messages.error(request, 'ليس لديك صلاحية تعديل هذا المستخدم.')
            return redirect('rent:dashboard')  # ✅ تعديل هنا
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث البيانات بنجاح!')
        return super().form_valid(form)


# ============ حذف مستخدم ============
class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """حذف مستخدم - يتطلب صلاحية delete_user"""
    model = User
    template_name = 'authentication/user_confirm_delete.html'
    success_url = reverse_lazy('rent:dashboard')  # ✅ تعديل هنا
    permission_required = 'auth.delete_user'
    login_url = '/auth/login/'  # ✅ تعديل هنا
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj == request.user:
            messages.error(request, 'لا يمكنك حذف حسابك الخاص.')
            return redirect('rent:dashboard')  # ✅ تعديل هنا
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف المستخدم بنجاح!')
        return super().delete(request, *args, **kwargs)


# ============ إدارة الصلاحيات ============
class PermissionManagementView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """إدارة صلاحيات المستخدمين - يتطلب أن يكون superuser"""
    model = User
    form_class = PermissionAssignmentForm
    template_name = 'authentication/permission_management.html'
    permission_required = 'auth.change_user'
    login_url = '/auth/login/'  # ✅ تعديل هنا
    
    def get_success_url(self):
        return reverse_lazy('auth_app:permission-management', kwargs={'pk': self.object.pk})
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'هذه الصفحة متاحة للمشرفين فقط.')
            return redirect('rent:dashboard')  # ✅ تعديل هنا
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث الصلاحيات بنجاح!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_groups'] = Group.objects.prefetch_related('permissions').all()
        # Only rent app permissions
        context['available_permissions'] = Permission.objects.filter(
            content_type__app_label='rent'
        ).select_related('content_type').order_by('content_type__model', 'codename')

        # Group descriptions for display
        context['group_descriptions'] = {
            'مدير النظام': 'جميع الصلاحيات في النظام',
            'محاسب': 'سندات القبض كاملة + عرض العقود + التقارير',
            'مدير إيجار': 'العقود + المستأجرين + عرض العقارات والسندات',
            'موظف استقبال': 'إضافة سندات + عرض العقود والمستأجرين',
            'مشاهد فقط': 'عرض فقط لجميع البيانات',
        }

        # Permission categories for organized display
        context['permission_categories'] = {
            'receipt': {'label': 'سندات القبض', 'icon': 'fa-receipt'},
            'contract': {'label': 'العقود', 'icon': 'fa-file-contract'},
            'contractmodification': {'label': 'تعديلات العقود', 'icon': 'fa-edit'},
            'tenant': {'label': 'المستأجرين', 'icon': 'fa-users'},
            'tenantdocument': {'label': 'مستندات المستأجرين', 'icon': 'fa-folder-open'},
            'building': {'label': 'المباني', 'icon': 'fa-building'},
            'unit': {'label': 'الوحدات', 'icon': 'fa-door-open'},
            'land': {'label': 'الأراضي', 'icon': 'fa-map'},
            'reporttemplate': {'label': 'التقارير', 'icon': 'fa-chart-bar'},
            'notification': {'label': 'الإشعارات', 'icon': 'fa-bell'},
            'backup': {'label': 'النسخ الاحتياطي', 'icon': 'fa-database'},
            'backupschedule': {'label': 'جدول النسخ الاحتياطي', 'icon': 'fa-calendar-alt'},
            'scheduledtask': {'label': 'المهام المجدولة', 'icon': 'fa-clock'},
            'taskexecution': {'label': 'تنفيذ المهام', 'icon': 'fa-cogs'},
            'tasklog': {'label': 'سجل المهام', 'icon': 'fa-list-alt'},
            'userprofile': {'label': 'ملفات المستخدمين', 'icon': 'fa-id-card'},
        }
        return context


# ============ قائمة المستخدمين ============
class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """قائمة جميع المستخدمين - يتطلب صلاحية view_user"""
    model = User
    template_name = 'authentication/user_list.html'
    context_object_name = 'users'
    permission_required = 'auth.view_user'
    login_url = '/auth/login/'  # ✅ تعديل هنا
    paginate_by = 10
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(username__icontains=search_query)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


# ============ صفحة ممنوع الوصول ============
class AccessDeniedView(LoginRequiredMixin, DetailView):
    """صفحة تظهر عند عدم وجود صلاحيات كافية"""
    template_name = 'authentication/access_denied.html'
    
    def get(self, request, *args, **kwargs):
        return self.render_to_response({})