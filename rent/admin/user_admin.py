"""
User Admin
إدارة المستخدمين والملفات الشخصية
"""

from .common_imports_admin import (
    admin, UserAdmin, User,
    UserProfile,
    BaseStackedInline,
)


# ========================================
# UserProfile Inline
# ========================================

class UserProfileInline(BaseStackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'ملف المستخدم'
    fields = (
        'role', 'phone', 
        'can_manage_contracts', 'can_manage_tenants', 
        'can_manage_properties', 'can_process_payments', 
        'can_view_reports', 'can_manage_users', 
        'is_active'
    )


# ========================================
# Custom User Admin
# ========================================

class CustomUserAdmin(UserAdmin):
    """إدارة مخصصة للمستخدمين مع الملف الشخصي"""
    
    inlines = (UserProfileInline,)
    
    list_display = (
        'username', 'email', 'first_name', 'last_name', 
        'get_role', 'is_staff', 'is_active'
    )
    
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'profile__role'
    )
    
    search_fields = (
        'username', 'first_name', 'last_name', 
        'email', 'profile__phone'
    )
    
    def get_role(self, obj):
        """عرض دور المستخدم"""
        if hasattr(obj, 'profile'):
            return obj.profile.get_role_display()
        return "لا يوجد"
    get_role.short_description = 'الدور'


# ========================================
# التسجيل
# ========================================

def register_user_admin():
    """تسجيل إدارة المستخدمين"""
    # إلغاء التسجيل الافتراضي
    admin.site.unregister(User)
    # إعادة التسجيل بالإدارة المخصصة
    admin.site.register(User, CustomUserAdmin)