from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def home_redirect(request):
    """إعادة توجيه ذكية حسب حالة المستخدم"""
    if request.user.is_authenticated:
        return redirect('rent:report_rep')
    return redirect('auth_app:login')

urlpatterns = [
    path('admin/', admin.site.urls),

    # توجيه ذكي للصفحة الرئيسية → تقرير المستأجرين
    path('', home_redirect, name='home'),

    # تطبيق الإيجارات
    path('dashboard/', include('rent.urls')),

    # تطبيق المصادقة
    path('auth/', include('authentication_app.urls')),

    # سجل التدقيق
    path('audit/', include('audit_log.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)