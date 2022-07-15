from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0003_group_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='group',
            name='slug',
            field=models.SlugField(),
        ),
    ]
