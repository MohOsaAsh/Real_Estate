"""
User Profile Forms
نماذج المستخدمين والملفات الشخصية
"""

from .common_imports_forms import (
    forms, _, User, UserProfile,
    BaseModelForm
)


class UserProfileForm(BaseModelForm):
    """نموذج ملف المستخدم"""
    
    # حقول User
    username = forms.CharField(
        label=_('اسم المستخدم'),
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label=_('البريد الإلكتروني'),
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'example@email.com'})
    )
    first_name = forms.CharField(
        label=_('الاسم الأول'),
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label=_('اسم العائلة'),
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label=_('كلمة المرور'),
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text=_('اتركه فارغاً إذا كنت لا تريد تغيير كلمة المرور')
    )
    
    class Meta:
        model = UserProfile
        fields = ['role', 'phone', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '05xxxxxxxx'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # ملء البيانات من User إذا كان موجوداً
        if self.instance.pk and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        # إنشاء أو تحديث User
        if not profile.user_id:
            # إنشاء مستخدم جديد
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                email=self.cleaned_data.get('email', ''),
                password=self.cleaned_data.get('password', 'defaultpass123')
            )
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            user.save()
            profile.user = user
        else:
            # تحديث مستخدم موجود
            user = profile.user
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data.get('email', '')
            user.first_name = self.cleaned_data.get('first_name', '')
            user.last_name = self.cleaned_data.get('last_name', '')
            
            if self.cleaned_data.get('password'):
                user.set_password(self.cleaned_data['password'])
            
            user.save()
        
        if commit:
            profile.save()
        
        return profile