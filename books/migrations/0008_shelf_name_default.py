from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('books', '0007_shelf_column_and_number')]

    operations = [
        migrations.AlterField(
            model_name='shelf',
            name='name',
            field=models.CharField(blank=True, default='', max_length=100, unique=True),
        ),
    ]
