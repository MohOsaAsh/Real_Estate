from django.test import TestCase, Client
from django.contrib.auth.models import User, Group, Permission
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType


class UserRegistrationTests(TestCase):
    """
    اختبارات تسجيل المستخدمين الجدد
    """
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('register')
    
    def test_registration_page_loads(self):
        """اختبار تحميل صفحة التسجيل"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/register.html')
    
    def test_user_registration_success(self):
        """اختبار تسجيل مستخدم جديد بنجاح"""
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#'
        }
        response = self.client.post(self.register_url, data)
        
        # التحقق من إعادة التوجيه بعد التسجيل الناجح
        self.assertEqual(response.status_code, 302)
        
        # التحقق من إنشاء المستخدم
        self.assertTrue(User.objects.filter(username='testuser').exists())
        
        # التحقق من البيانات
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
    
    def test_registration_with_duplicate_username(self):
        """اختبار منع التسجيل باسم مستخدم موجود"""
        # إنشاء مستخدم
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        # محاولة التسجيل بنفس الاسم
        data = {
            'username': 'existinguser',
            'first_name': 'New',
            'last_name': 'User',
            'email': 'new@example.com',
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#'
        }
        response = self.client.post(self.register_url, data)
        
        # يجب أن يبقى في نفس الصفحة مع أخطاء
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'username', 
                           'يوجد مستخدم بهذا الاسم فعلا.')
    
    def test_registration_with_duplicate_email(self):
        """اختبار منع التسجيل ببريد إلكتروني موجود"""
        # إنشاء مستخدم
        User.objects.create_user(
            username='user1',
            email='duplicate@example.com',
            password='password123'
        )
        
        # محاولة التسجيل بنفس البريد
        data = {
            'username': 'user2',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'duplicate@example.com',
            'password1': 'TestPass123!@#',
            'password2': 'TestPass123!@#'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'email', 
                           'هذا البريد الإلكتروني مستخدم بالفعل.')
    
    def test_registration_password_mismatch(self):
        """اختبار عدم تطابق كلمات المرور"""
        data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'password1': 'TestPass123!@#',
            'password2': 'DifferentPass123!@#'
        }
        response = self.client.post(self.register_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password2', 
                           'كلمتي المرور لا تتطابق.')
    
    def test_authenticated_user_redirect(self):
        """اختبار إعادة توجيه المستخدم المسجل دخوله"""
        # إنشاء وتسجيل دخول مستخدم
        user = User.objects.create_user('testuser', 'test@example.com', 'password123')
        self.client.login(username='testuser', password='password123')
        
        # محاولة الوصول لصفحة التسجيل
        response = self.client.get(self.register_url)
        
        # يجب إعادة التوجيه
        self.assertEqual(response.status_code, 302)


class UserLoginTests(TestCase):
    """
    اختبارات تسجيل الدخول
    """
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!@#'
        )
    
    def test_login_page_loads(self):
        """اختبار تحميل صفحة تسجيل الدخول"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')
    
    def test_login_success(self):
        """اختبار تسجيل دخول ناجح"""
        data = {
            'username': 'testuser',
            'password': 'TestPass123!@#'
        }
        response = self.client.post(self.login_url, data)
        
        # التحقق من إعادة التوجيه
        self.assertEqual(response.status_code, 302)
        
        # التحقق من تسجيل الدخول
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_invalid_credentials(self):
        """اختبار تسجيل دخول ببيانات خاطئة"""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)
        
        # يجب البقاء في نفس الصفحة
        self.assertEqual(response.status_code, 200)
        
        # التحقق من عدم تسجيل الدخول
        self.assertFalse(response.wsgi_request.user.is_authenticated)
    
    def test_login_nonexistent_user(self):
        """اختبار تسجيل دخول بمستخدم غير موجود"""
        data = {
            'username': 'nonexistent',
            'password': 'somepassword'
        }
        response = self.client.post(self.login_url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class UserLogoutTests(TestCase):
    """
    اختبارات تسجيل الخروج
    """
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('logout')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
    
    def test_logout_success(self):
        """اختبار تسجيل خروج ناجح"""
        # تسجيل الدخول أولاً
        self.client.login(username='testuser', password='password123')
        
        # تسجيل الخروج
        response = self.client.post(self.logout_url)
        
        # التحقق من إعادة التوجيه
        self.assertEqual(response.status_code, 302)
        
        # التحقق من تسجيل الخروج
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # إعادة توجيه لتسجيل الدخول


class DashboardTests(TestCase):
    """
    اختبارات لوحة التحكم
    """
    def setUp(self):
        self.client = Client()
        self.dashboard_url = reverse('dashboard')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
    
    def test_dashboard_requires_login(self):
        """اختبار أن لوحة التحكم تتطلب تسجيل الدخول"""
        response = self.client.get(self.dashboard_url)
        
        # إعادة توجيه لصفحة تسجيل الدخول
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('login')}?next={self.dashboard_url}")
    
    def test_dashboard_access_for_authenticated_user(self):
        """اختبار وصول المستخدم المصادق"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/dashboard.html')
    
    def test_dashboard_shows_only_current_user_for_normal_users(self):
        """اختبار أن المستخدم العادي يرى نفسه فقط"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(len(response.context['users']), 1)
        self.assertEqual(response.context['users'][0], self.user)
    
    def test_dashboard_shows_all_users_for_superuser(self):
        """اختبار أن المشرف يرى جميع المستخدمين"""
        self.client.login(username='admin', password='admin123')
        response = self.client.get(self.dashboard_url)
        
        self.assertEqual(len(response.context['users']), 2)


class UserDetailTests(TestCase):
    """
    اختبارات عرض تفاصيل المستخدم
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.detail_url = reverse('user-detail', kwargs={'pk': self.user.pk})
    
    def test_user_detail_requires_login(self):
        """اختبار أن صفحة التفاصيل تتطلب تسجيل الدخول"""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 302)
    
    def test_user_can_view_own_details(self):
        """اختبار أن المستخدم يمكنه رؤية تفاصيله"""
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.detail_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user_profile'], self.user)


class UserUpdateTests(TestCase):
    """
    اختبارات تحديث بيانات المستخدم
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        self.update_url = reverse('user-update', kwargs={'pk': self.user.pk})
    
    def test_user_can_update_own_profile(self):
        """اختبار أن المستخدم يمكنه تحديث ملفه الشخصي"""
        self.client.login(username='testuser', password='password123')
        
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        response = self.client.post(self.update_url, data)
        
        # التحقق من التحديث
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
    
    def test_user_cannot_update_other_user_profile(self):
        """اختبار أن المستخدم لا يمكنه تحديث ملف مستخدم آخر"""
        self.client.login(username='otheruser', password='password123')
        
        data = {
            'first_name': 'Hacker',
            'last_name': 'Attempt',
            'email': 'hacker@example.com'
        }
        response = self.client.post(self.update_url, data)
        
        # يجب إعادة التوجيه
        self.assertEqual(response.status_code, 302)
        
        # التحقق من عدم التحديث
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Test')


class UserDeleteTests(TestCase):
    """
    اختبارات حذف المستخدمين
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.delete_url = reverse('user-delete', kwargs={'pk': self.user.pk})
        
        # إعطاء صلاحية الحذف للـ admin
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.get(
            codename='delete_user',
            content_type=content_type
        )
        self.admin.user_permissions.add(permission)
    
    def test_user_cannot_delete_themselves(self):
        """اختبار أن المستخدم لا يمكنه حذف نفسه"""
        self.client.login(username='admin', password='admin123')
        
        admin_delete_url = reverse('user-delete', kwargs={'pk': self.admin.pk})
        response = self.client.post(admin_delete_url)
        
        # يجب إعادة التوجيه
        self.assertEqual(response.status_code, 302)
        
        # التحقق من عدم الحذف
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())
    
    def test_admin_can_delete_user(self):
        """اختبار أن المشرف يمكنه حذف مستخدم"""
        self.client.login(username='admin', password='admin123')
        
        response = self.client.post(self.delete_url)
        
        # التحقق من الحذف
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())
    
    def test_user_without_permission_cannot_delete(self):
        """اختبار أن المستخدم بدون صلاحية لا يمكنه الحذف"""
        normal_user = User.objects.create_user(
            username='normal',
            email='normal@example.com',
            password='password123'
        )
        self.client.login(username='normal', password='password123')
        
        response = self.client.post(self.delete_url)
        
        # يجب إعادة التوجيه (ممنوع)
        self.assertEqual(response.status_code, 302)
        
        # التحقق من عدم الحذف
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())


class PermissionManagementTests(TestCase):
    """
    اختبارات إدارة الصلاحيات
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        self.permission_url = reverse('permission-management', kwargs={'pk': self.user.pk})
    
    def test_only_superuser_can_access_permission_management(self):
        """اختبار أن المشرف فقط يمكنه الوصول لإدارة الصلاحيات"""
        # مستخدم عادي
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.permission_url)
        self.assertEqual(response.status_code, 302)
        
        # مشرف
        self.client.login(username='admin', password='admin123')
        response = self.client.get(self.permission_url)
        self.assertEqual(response.status_code, 200)
    
    def test_superuser_can_assign_permissions(self):
        """اختبار أن المشرف يمكنه تعيين الصلاحيات"""
        self.client.login(username='admin', password='admin123')
        
        # الحصول على صلاحية
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.get(
            codename='add_user',
            content_type=content_type
        )
        
        data = {
            'user_permissions': [permission.pk],
            'groups': [],
            'is_staff': True,
            'is_superuser': False,
            'is_active': True
        }
        response = self.client.post(self.permission_url, data)
        
        # التحقق من التعيين
        self.user.refresh_from_db()
        self.assertTrue(self.user.user_permissions.filter(pk=permission.pk).exists())
        self.assertTrue(self.user.is_staff)


class UserListTests(TestCase):
    """
    اختبارات قائمة المستخدمين
    """
    def setUp(self):
        self.client = Client()
        self.user_list_url = reverse('user-list')
        
        # إنشاء مستخدم عادي
        self.normal_user = User.objects.create_user(
            username='normal',
            email='normal@example.com',
            password='password123'
        )
        
        # إنشاء مستخدم مع صلاحية العرض
        self.viewer = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='password123'
        )
        content_type = ContentType.objects.get_for_model(User)
        permission = Permission.objects.get(
            codename='view_user',
            content_type=content_type
        )
        self.viewer.user_permissions.add(permission)
    
    def test_user_list_requires_permission(self):
        """اختبار أن قائمة المستخدمين تتطلب صلاحية"""
        # مستخدم بدون صلاحية
        self.client.login(username='normal', password='password123')
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, 302)
        
        # مستخدم بصلاحية
        self.client.login(username='viewer', password='password123')
        response = self.client.get(self.user_list_url)
        self.assertEqual(response.status_code, 200)