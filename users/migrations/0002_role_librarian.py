from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            "UPDATE users_user SET role = 'LIBRARIAN' WHERE role = 'ADMIN'",
            reverse_sql=(
                "UPDATE users_user SET role = 'ADMIN' "
                "WHERE role = 'LIBRARIAN'"
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('LIBRARIAN', 'Librarian'),
                    ('MEMBER', 'Member'),
                ],
                default='MEMBER',
                max_length=20,
            ),
        ),
    ]
