from django import forms
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError


# ============ نموذج تسجيل مستخدم جديد ============
class UserRegistrationForm(UserCreationForm):
    """
    نموذج تسجيل مستخدم جديد مع حقول إضافية
    """
    email = forms.EmailField(
        required=True,
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل البريد الإلكتروني'
        })
    )
    
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label='الاسم الأول',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل الاسم الأول'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label='اسم العائلة',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل اسم العائلة'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        labels = {
            'username': 'اسم المستخدم',
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم المستخدم'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تخصيص حقول كلمة المرور
        self.fields['password1'].label = 'كلمة المرور'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور'
        })
        self.fields['password2'].label = 'تأكيد كلمة المرور'
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'أعد إدخال كلمة المرور'
        })
    
    def clean_email(self):
        """
        التحقق من أن البريد الإلكتروني غير مستخدم
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('هذا البريد الإلكتروني مستخدم بالفعل.')
        return email
    
    def clean_username(self):
        """
        التحقق من اسم المستخدم
        """
        username = self.cleaned_data.get('username')
        if len(username) < 3:
            raise ValidationError('اسم المستخدم يجب أن يكون 3 أحرف على الأقل.')
        return username
    
    def save(self, commit=True):
        """
        حفظ المستخدم مع البيانات الإضافية
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


# ============ نموذج تحديث بيانات المستخدم ============
class UserUpdateForm(forms.ModelForm):
    """
    نموذج تحديث معلومات المستخدم
    """
    email = forms.EmailField(
        required=True,
        label='البريد الإلكتروني',
        widget=forms.EmailInput(attrs={
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'اسم العائلة',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_email(self):
        """
        التحقق من أن البريد الإلكتروني غير مستخدم من قبل مستخدم آخر
        """
        email = self.cleaned_data.get('email')
        user_id = self.instance.id
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            raise ValidationError('هذا البريد الإلكتروني مستخدم بالفعل.')
        return email


# ============ نموذج تسجيل الدخول مخصص ============
class CustomLoginForm(AuthenticationForm):
    """
    نموذج تسجيل دخول مخصص مع تنسيق Bootstrap
    """
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل اسم المستخدم',
            'autofocus': True
        })
    )
    
    password = forms.CharField(
        label='كلمة المرور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'أدخل كلمة المرور'
        })
    )


# ============ نموذج إدارة الصلاحيات ============
class PermissionAssignmentForm(forms.ModelForm):
    """
    نموذج لإدارة صلاحيات ومجموعات المستخدمين
    """
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label='المجموعات',
        widget=forms.CheckboxSelectMultiple,
        help_text='اختر المجموعات التي ينتمي إليها المستخدم'
    )
    
    user_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        label='الصلاحيات الخاصة',
        widget=forms.CheckboxSelectMultiple,
        help_text='اختر الصلاحيات الخاصة بالمستخدم'
    )
    
    is_staff = forms.BooleanField(
        required=False,
        label='موظف (يمكنه الدخول للوحة الإدارة)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_superuser = forms.BooleanField(
        required=False,
        label='مشرف عام (جميع الصلاحيات)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_active = forms.BooleanField(
        required=False,
        label='حساب نشط',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ('groups', 'user_permissions', 'is_staff', 'is_superuser', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # فقط صلاحيات تطبيق rent
        self.fields['user_permissions'].queryset = Permission.objects.filter(
            content_type__app_label='rent'
        ).select_related('content_type').order_by('content_type__model', 'codename')


# ============ نموذج البحث عن المستخدمين ============
class UserSearchForm(forms.Form):
    """
    نموذج للبحث عن المستخدمين
    """
    search = forms.CharField(
        required=False,
        label='بحث',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'ابحث عن مستخدم...'
        })
    )
    
    is_active = forms.NullBooleanField(
        required=False,
        label='الحالة',
        widget=forms.Select(
            choices=[
                ('', 'الكل'),
                ('true', 'نشط'),
                ('false', 'غير نشط')
            ],
            attrs={'class': 'form-control'}
        )
    )
    
    is_staff = forms.NullBooleanField(
        required=False,
        label='نوع المستخدم',
        widget=forms.Select(
            choices=[
                ('', 'الكل'),
                ('true', 'موظف'),
                ('false', 'مستخدم عادي')
            ],
            attrs={'class': 'form-control'}
        )
    )


# ============ نموذج إنشاء مجموعة جديدة ============
class GroupCreationForm(forms.ModelForm):
    """
    نموذج لإنشاء مجموعة جديدة مع الصلاحيات
    """
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        label='الصلاحيات',
        widget=forms.CheckboxSelectMultiple,
        help_text='اختر الصلاحيات لهذه المجموعة'
    )
    
    class Meta:
        model = Group
        fields = ('name', 'permissions')
        labels = {
            'name': 'اسم المجموعة',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'أدخل اسم المجموعة'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تنظيم الصلاحيات حسب النموذج
        self.fields['permissions'].queryset = Permission.objects.select_related(
            'content_type'
        ).order_by('content_type__app_label', 'content_type__model', 'codename')