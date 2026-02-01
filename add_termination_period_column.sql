-- Manual SQL Migration for termination_period_number field
-- تطبيق يدوي للـ Migration

-- Add termination_period_number column to contract_modifications table
ALTER TABLE contract_modifications 
ADD COLUMN termination_period_number INTEGER NULL;

-- Add comment to the column (optional)
COMMENT ON COLUMN contract_modifications.termination_period_number 
IS 'رقم الفترة التي سيتم الإنهاء عندها - لا يتم احتساب إيجار بعدها';
