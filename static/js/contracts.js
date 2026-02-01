document.addEventListener("DOMContentLoaded", function() {
    let currentStep = 1;
    const totalSteps = 3;

    const nextBtn = document.querySelector(".btn-next");
    const prevBtn = document.querySelector(".btn-prev");
    const submitBtn = document.querySelector(".btn-submit");
   

    // -----------------------------
    // Show step function
    // -----------------------------
    function showStep(step) {
        console.log("Showing step:", step);
        document.querySelectorAll(".form-step").forEach(el => el.style.display = "none");
        const stepDiv = document.querySelector(`.form-step[data-step="${step}"]`);
        if (stepDiv) stepDiv.style.display = "block";

        // Update step indicators
        document.querySelectorAll(".step").forEach(el => el.classList.remove("active", "completed"));
        for (let i = 1; i < step; i++) {
            const completedStep = document.querySelector(`.step[data-step="${i}"]`);
            if (completedStep) completedStep.classList.add("completed");
        }
        const activeStep = document.querySelector(`.step[data-step="${step}"]`);
        if (activeStep) activeStep.classList.add("active");

        // Update buttons
        if(prevBtn) prevBtn.style.display = step === 1 ? "none" : "inline-block";
        if(nextBtn) nextBtn.style.display = step === totalSteps ? "none" : "inline-block";
        if(submitBtn) submitBtn.style.display = step === totalSteps ? "inline-block" : "none";

        // Update summary if last step
        if (step === totalSteps) updateSummary();
    }

    // -----------------------------
    // Step validation
    // -----------------------------
    function validateStep(step) {
        console.log("Validating step:", step);
        let valid = true;
        const requiredFields = document.querySelectorAll(`.form-step[data-step="${step}"] [required]`);
        requiredFields.forEach(field => {
            if (!field.checkValidity()) {
                valid = false;
                field.classList.add("is-invalid");
            } else {
                field.classList.remove("is-invalid");
            }
        });
        return valid;
    }

    // -----------------------------
    // Navigation buttons
    // -----------------------------
    if(nextBtn){
        nextBtn.addEventListener("click", function() {
            console.log("Next button clicked on step:", currentStep);
            if (validateStep(currentStep)) {
                if (currentStep < totalSteps) {
                    currentStep++;
                    showStep(currentStep);
                }
            }
        });
    }

    if(prevBtn){
        prevBtn.addEventListener("click", function() {
            if (currentStep > 1) {
                currentStep--;
                showStep(currentStep);
            } else {
                console.log("Cannot go back from step 1");
            }
        });
    }

    // -----------------------------
    // Duration calculation
    // -----------------------------
    const startDateInput = document.getElementById("id_start_date");
    const endDateInput = document.getElementById("id_end_date");
    const durationInput = document.getElementById("id_contract_duration_months");
    const durationText = document.getElementById("duration-text");

    // حساب تاريخ النهاية تلقائياً عند تغيير تاريخ البداية أو مدة العقد
    function calculateEndDate() {
        if (startDateInput && durationInput && endDateInput) {
            const startDate = startDateInput.value;
            const duration = parseInt(durationInput.value);

            if (startDate && duration > 0) {
                const start = new Date(startDate);
                const end = new Date(start);
                end.setMonth(end.getMonth() + duration);

                // تنسيق التاريخ بصيغة YYYY-MM-DD
                const year = end.getFullYear();
                const month = String(end.getMonth() + 1).padStart(2, '0');
                const day = String(end.getDate()).padStart(2, '0');
                endDateInput.value = `${year}-${month}-${day}`;

                // تحديث عرض المدة إذا وجد
                if (durationText) {
                    durationText.textContent = `${duration} شهر`;
                }
            } else {
                endDateInput.value = '';
                if (durationText) {
                    durationText.textContent = '';
                }
            }
        }
    }

    // عند تغيير تاريخ البداية أو مدة العقد، احسب تاريخ النهاية تلقائياً
    if (startDateInput) {
        startDateInput.addEventListener("change", calculateEndDate);
    }
    if (durationInput) {
        durationInput.addEventListener("change", calculateEndDate);
        durationInput.addEventListener("input", calculateEndDate);
    }

    // جعل حقل تاريخ النهاية للقراءة فقط في JavaScript أيضاً
    if (endDateInput) {
        endDateInput.setAttribute('readonly', 'readonly');
        endDateInput.style.backgroundColor = '#e9ecef';
        endDateInput.style.cursor = 'not-allowed';
    }

    // -----------------------------
    // Rent calculation
    // -----------------------------
    const rentAmountInput = document.getElementById("id_annual_rent");
    const paymentFrequencyInput = document.getElementById("id_payment_frequency");
    const annualRentDisplay = document.getElementById("annual-rent");
    const paymentCountDisplay = document.getElementById("payment-count");
    const paymentAmountDisplay = document.getElementById("payment-amount");

    function calculateRent() {
        const amount = parseFloat(rentAmountInput.value) || 0;
        const frequency = paymentFrequencyInput.value;
        const periods = { monthly: 12, quarterly: 4, semi_annual: 2, annual: 1 };
        const count = periods[frequency] || 12;
        const annual = amount / count;

        if (annualRentDisplay) annualRentDisplay.textContent = annual.toLocaleString('ar-SA') + ' ريال';
        if (paymentCountDisplay) paymentCountDisplay.textContent = count;
        if (paymentAmountDisplay) paymentAmountDisplay.textContent = amount.toLocaleString('ar-SA') + ' ريال';
    }

    [rentAmountInput, paymentFrequencyInput].forEach(el => {
        if(el){
            el.addEventListener("change", calculateRent);
            el.addEventListener("input", calculateRent);
        }
    });

    // -----------------------------
    // Show selected units (checkboxes)
    // -----------------------------
    const selectedUnitsDiv = document.getElementById("selected-units");
    function updateSelectedUnits() {
        if (!selectedUnitsDiv) return;

        const checkedUnits = document.querySelectorAll('input[name="units"]:checked');
        let html = '';
        checkedUnits.forEach(chk => {
            const label = document.querySelector(`label[for="${chk.id}"]`);
            const text = label ? label.textContent.trim() : chk.value;
            html += `<div class="unit-badge">
                        <i class="fas fa-home"></i>
                        ${text}
                        <span class="remove-unit" data-id="${chk.value}">×</span>
                    </div>`;
        });

        selectedUnitsDiv.innerHTML = html;
    }

    document.querySelectorAll('input[name="units"]').forEach(chk => {
        chk.addEventListener('change', updateSelectedUnits);
    });

    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-unit')) {
            const id = e.target.getAttribute('data-id');
            const checkbox = document.querySelector(`input[name="units"][value="${id}"]`);
            if (checkbox) {
                checkbox.checked = false;
                updateSelectedUnits();
            }
        }
    });

    // -----------------------------
    // Update contract summary
    // -----------------------------
    function updateSummary() {
        const tenantSelect = document.getElementById("id_tenant");
        const checkedUnits = document.querySelectorAll('input[name="units"]:checked');

        const tenant = tenantSelect ? tenantSelect.options[tenantSelect.selectedIndex]?.text : '';
        const units = Array.from(checkedUnits).map(chk => {
            const label = document.querySelector(`label[for="${chk.id}"]`);
            return label ? label.textContent.trim() : chk.value;
        }).join(", ");

        const startDate = startDateInput ? startDateInput.value : '';
        const endDate = endDateInput ? endDateInput.value : '';
        const amount = rentAmountInput ? rentAmountInput.value : '';
        const frequency = paymentFrequencyInput ? paymentFrequencyInput.options[paymentFrequencyInput.selectedIndex]?.text : '';

        const summaryDiv = document.getElementById("contract-summary");
        if (summaryDiv) {
            summaryDiv.innerHTML = `
                <div class="row g-3">
                    <div class="col-md-6"><strong>المستأجر:</strong> ${tenant}</div>
                    <div class="col-md-6"><strong>الوحدات:</strong> ${units}</div>
                    <div class="col-md-6"><strong>الفترة:</strong> ${startDate} - ${endDate}</div>
                    <div class="col-md-6"><strong>قيمة الإيجار:</strong> ${amount} ريال</div>
                    <div class="col-md-6"><strong>دورية السداد:</strong> ${frequency}</div>
                </div>
            `;
        }
    }

    // -----------------------------
    // Load tenant info
    // -----------------------------
    const tenantSelect = document.getElementById("id_tenant");
    const tenantInfoDiv = document.getElementById("tenant-info");

    if (tenantSelect && tenantInfoDiv) {
        tenantSelect.addEventListener("change", function() {
            const tenantId = tenantSelect.value;
            if (tenantId) {
                tenantInfoDiv.innerHTML = '<small class="text-muted">جاري التحميل...</small>';
                // يمكن إضافة AJAX هنا إذا لزم
            } else {
                tenantInfoDiv.innerHTML = '';
            }
        });
    }

    // -----------------------------
    // Initialize
    // -----------------------------
    showStep(currentStep);
    updateSelectedUnits();

    // حساب تاريخ النهاية عند تحميل الصفحة في حالة التعديل
    if (startDateInput && durationInput && startDateInput.value && durationInput.value) {
        calculateEndDate();
    }
});
