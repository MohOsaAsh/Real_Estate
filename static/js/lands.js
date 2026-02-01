// static/js/lands_form.js

// console.log("lands_form.js loaded");
// alert("lands_form.js loaded");

document.addEventListener('DOMContentLoaded', function () {

    // عناصر النموذج
    const ownershipField = document.getElementById('id_ownership_type');
    const rentInfo = document.getElementById('rent-info');
    const rentStartDate = document.getElementById('id_rent_start_date');
    const rentDuration = document.getElementById('id_rent_duration_years');
    const rentEndDate = document.getElementById('id_rent_end_date');

    // --- دالة لإظهار/إخفاء معلومات الإيجار ---
    function toggleRentalInfo() {
        if (!ownershipField || !rentInfo) return;

        if (ownershipField.value === 'rented') {
            rentInfo.style.display = 'block';
        } else {
            rentInfo.style.display = 'none';
        }
    }

    // --- عند تغيير نوع الملكية ---
    if (ownershipField) {
        ownershipField.addEventListener('change', toggleRentalInfo);
    }

    // --- تحقق عند تحميل الصفحة (مهم في التعديل) ---
    toggleRentalInfo();

    // --- حساب تاريخ نهاية الإيجار تلقائيًا ---
    function calculateEndDate() {
        if (!rentStartDate || !rentDuration || !rentEndDate) return;

        const startDateValue = rentStartDate.value;
        const durationValue = parseInt(rentDuration.value);

        if (startDateValue && durationValue) {
            const startDate = new Date(startDateValue);
            const endDate = new Date(startDate);
            endDate.setFullYear(endDate.getFullYear() + durationValue);

            rentEndDate.value = endDate.toISOString().split('T')[0];
        }
    }

    if (rentStartDate) rentStartDate.addEventListener('change', calculateEndDate);
    if (rentDuration) rentDuration.addEventListener('change', calculateEndDate);
   

});

