# Generated manually for adding termination_period_number field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rent', '0007_alter_contract_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='contractmodification',
            name='termination_period_number',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='رقم الفترة التي سيتم الإنهاء عندها - لا يتم احتساب إيجار بعدها',
                null=True,
                verbose_name='رقم فترة الإنهاء'
            ),
        ),
    ]
