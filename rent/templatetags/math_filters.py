# rent/templatetags/math_filters.py

"""
Custom Template Filters for Mathematical Operations
فلاتر مخصصة للعمليات الحسابية
"""

from django import template
from django.contrib.humanize.templatetags.humanize import intcomma


register = template.Library()


@register.filter
def intcomma_int(value):
    try:
        return intcomma(int(round(value)))  # تحويل للـ int قبل intcomma
    except (ValueError, TypeError):
        return value

@register.filter
def intcomma_no_decimal(value):
    try:
        # تقريب وتحويل للعدد الصحيح ثم إضافة الفواصل
        return intcomma(int(round(value)))
    except:
        return value

@register.filter
def thousand_separator(value):
    try:
        return f"{value:,.2f}"
    except (ValueError, TypeError):
        return value


@register.filter(name='multiply')
def multiply(value, arg):
    """
    ضرب قيمتين
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='divide')
def divide(value, arg):
    """
    قسمة قيمتين
    Usage: {{ value|divide:arg }}
    """
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return 0


@register.filter(name='percentage')
def percentage(value, total):
    """
    حساب النسبة المئوية
    Usage: {{ value|percentage:total }}
    """
    try:
        total = float(total)
        if total == 0:
            return 0
        return (float(value) / total) * 100
    except (ValueError, TypeError):
        return 0


@register.filter(name='add_number')
def add_number(value, arg):
    """
    جمع رقمين
    Usage: {{ value|add_number:arg }}
    """
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='subtract')
def subtract(value, arg):
    """
    طرح رقمين
    Usage: {{ value|subtract:arg }}
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter(name='abs_value')
def abs_value(value):
    """
    القيمة المطلقة
    Usage: {{ value|abs_value }}
    """
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0


@register.filter(name='format_number')
def format_number(value, decimals=2):
    """
    تنسيق الأرقام
    Usage: {{ value|format_number:2 }}
    """
    try:
        return f"{float(value):.{int(decimals)}f}"
    except (ValueError, TypeError):
        return value


@register.simple_tag
def calculate_percentage(value, total):
    """
    حساب النسبة المئوية كـ tag
    Usage: {% calculate_percentage value total %}
    """
    try:
        total = float(total)
        if total == 0:
            return 0
        return (float(value) / total) * 100
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def multiply_values(value1, value2):
    """
    ضرب قيمتين كـ tag
    Usage: {% multiply_values value1 value2 %}
    """
    try:
        return float(value1) * float(value2)
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def divide_values(value1, value2):
    """
    قسمة قيمتين كـ tag
    Usage: {% divide_values value1 value2 %}
    """
    try:
        value2 = float(value2)
        if value2 == 0:
            return 0
        return float(value1) / value2
    except (ValueError, TypeError):
        return 0