from django.db import migrations, models


def consolidate_assignments(apps, schema_editor):
    Shelf = apps.get_model('books', 'Shelf')
    ShelfAssignment = apps.get_model('books', 'ShelfAssignment')

    for assignment in ShelfAssignment.objects.select_related('shelf').all():
        shelf = assignment.shelf
        placements = dict(shelf.placements)
        book_key = str(assignment.book_id)
        placements[book_key] = placements.get(book_key, 0) + assignment.copies
        shelf.placements = placements
        shelf.save(update_fields=['placements'])


class Migration(migrations.Migration):
    dependencies = [
        ('books', '0004_shelf_shelfassignment'),
    ]

    operations = [
        migrations.AddField(
            model_name='shelf',
            name='placements',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.RunPython(consolidate_assignments, migrations.RunPython.noop),
        migrations.DeleteModel(
            name='ShelfAssignment',
        ),
    ]
