
"""
Simple Arabic Tafqeet Utility
تحويل الأرقام إلى كلمات عربية
"""
from decimal import Decimal

def tafqeet(number):
    """
    Convert number to Arabic text
    تحويل الرقم إلى نص عربي
    """
    if number == 0:
        return "صفر"

    number = Decimal(str(number))
    
    # Split integer and decimal parts
    integer_part = int(number)
    decimal_part = int((number - Decimal(integer_part)) * 100)
    
    text = ""
    
    if integer_part > 0:
        text += convert_number(integer_part)
        text += " ريال سعودي"
        
    if decimal_part > 0:
        if text:
            text += " و "
        text += convert_number(decimal_part)
        text += " هللة"
        
    if not text:
        return "صفر ريال"
        
    return text + " فقط لا غير"

def convert_number(n):
    """
    Recursive function to convert integers to Arabic words
    """
    if n < 0:
        return "سالب " + convert_number(-n)
    if n == 0:
        return ""

    if n < 10:
        return ["", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"][n]
    
    if n < 20:
        return ["عشرة", "أحد عشر", "اثنا عشر", "ثلاثة عشر", "أربعة عشر", "خمسة عشر", "ستة عشر", "سبعة عشر", "ثمانية عشر", "تسعة عشر"][n - 10]
    
    if n < 100:
        unit = n % 10
        ten = n // 10
        text = ["", "", "عشرون", "ثلاثون", "أربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"][ten]
        if unit > 0:
            text = convert_number(unit) + " و" + text
        return text
    
    if n < 200:
        return "مائة" + (" و" + convert_number(n - 100) if n > 100 else "")
    
    if n < 300:
        return "مائتان" + (" و" + convert_number(n - 200) if n > 200 else "")
        
    if n < 1000:
        hundred = n // 100
        text = convert_number(hundred) + " مائة"
        if n % 100 > 0:
            text += " و" + convert_number(n % 100)
        return text
    
    if n < 2000:
        return "ألف" + (" و" + convert_number(n - 1000) if n > 1000 else "")
        
    if n < 3000:
        return "ألفان" + (" و" + convert_number(n - 2000) if n > 2000 else "")
        
    if n < 10000: # 3000 - 9999
        thousand = n // 1000
        text = convert_number(thousand) + " آلاف"
        if n % 1000 > 0:
            text += " و" + convert_number(n % 1000)
        return text
        
    if n < 11000: # 10000 - 10999
        return "عشرة آلاف" + (" و" + convert_number(n - 10000) if n > 10000 else "")
        
    if n < 1000000:
        thousand = n // 1000
        text = convert_number(thousand) + " ألف"
        if n % 1000 > 0:
            text += " و" + convert_number(n % 1000)
        return text
        
    if n < 2000000:
        return "مليون" + (" و" + convert_number(n - 1000000) if n > 1000000 else "")
        
    if n < 1000000000:
        million = n // 1000000
        text = convert_number(million) + " مليون"
        if n % 1000000 > 0:
            text += " و" + convert_number(n % 1000000)
        return text
        
    return str(n)
