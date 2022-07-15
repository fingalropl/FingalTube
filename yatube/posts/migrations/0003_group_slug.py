from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0002_auto_20220526_1816'),
    ]

    operations = [
        migrations.AddField(
            model_name='group',
            name='slug',
            field=models.URLField(blank=True),
        ),
    ]
