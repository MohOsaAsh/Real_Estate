from django.urls import path
from .views import (
    UserRegistrationView,
    UserLoginView,
    UserLogoutView,
    #DashboardView,
    UserDetailView,
    UserUpdateView,
    UserDeleteView,
    PermissionManagementView,
    UserListView,
    AccessDeniedView,
)

app_name = 'auth_app'

urlpatterns = [
    # ============ المصادقة الأساسية ============
    # التسجيل
    path('register/', UserRegistrationView.as_view(), name='register'),
    
    # تسجيل الدخول
    path('login/', UserLoginView.as_view(), name='login'),
    
    # تسجيل الخروج
    path('logout/', UserLogoutView.as_view(), name='logout'),
    
    # ============ لوحة التحكم والمستخدمين ============
    # لوحة التحكم الرئيسية
    #path('user_dashboard/', DashboardView.as_view(), name='user_dashboard'),
    
    # قائمة المستخدمين
    path('users/', UserListView.as_view(), name='user-list'),
    
    # عرض تفاصيل مستخدم
    path('user/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    
    # تعديل بيانات مستخدم
    path('user/<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    
    # حذف مستخدم
    path('user/<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),
    
    # ============ إدارة الصلاحيات ============
    # إدارة صلاحيات مستخدم
    path('user/<int:pk>/permissions/', PermissionManagementView.as_view(), name='permission-management'),
    
    # ============ صفحات الأخطاء ============
    # صفحة ممنوع الوصول
    path('access-denied/', AccessDeniedView.as_view(), name='access-denied'),
]