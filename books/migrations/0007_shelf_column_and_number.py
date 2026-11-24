import re

from django.db import migrations, models


def normalize_shelf_names(apps, schema_editor):
    Shelf = apps.get_model('books', 'Shelf')
    Book = apps.get_model('books', 'Book')
    shelves = list(Shelf.objects.order_by('pk'))
    original_names = {shelf.pk: shelf.name for shelf in shelves}

    # Free the unique name constraint before assigning the standard names.
    for shelf in shelves:
        shelf.name = f'__shelf_migration_{shelf.pk}'
    Shelf.objects.bulk_update(shelves, ['name'])

    occupied = {}
    for shelf in shelves:
        match = re.fullmatch(r'([A-Za-z]+)-(\d+)', original_names[shelf.pk].strip())
        column = match.group(1).upper() if match else 'A'
        number = int(match.group(2)) if match else 0
        used = occupied.setdefault(column, set())
        if number < 1 or number in used:
            number = 1
            while number in used:
                number += 1
        used.add(number)
        shelf.column_name = column
        shelf.shelf_number = number
        shelf.name = f'{column}-{number:02d}'
    Shelf.objects.bulk_update(shelves, ['name', 'column_name', 'shelf_number'])

    names = {shelf.pk: shelf.name for shelf in shelves}
    batch = []
    for book in Book.objects.only('id', 'shelf_id').iterator(chunk_size=500):
        if book.shelf_id:
            book.shelf_location = names[book.shelf_id]
            batch.append(book)
        if len(batch) >= 500:
            Book.objects.bulk_update(batch, ['shelf_location'], batch_size=500)
            batch.clear()
    if batch:
        Book.objects.bulk_update(batch, ['shelf_location'], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [('books', '0006_book_shelf')]

    operations = [
        migrations.AddField(
            model_name='shelf',
            name='column_name',
            field=models.CharField(default='A', max_length=10),
        ),
        migrations.AddField(
            model_name='shelf',
            name='shelf_number',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='book',
            name='shelf_location',
            field=models.CharField(blank=True, default='', max_length=1000),
        ),
        migrations.RunPython(normalize_shelf_names, migrations.RunPython.noop),
    ]
