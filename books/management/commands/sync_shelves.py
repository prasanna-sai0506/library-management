from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from books.models import Book, Shelf


class Command(BaseCommand):
    help = 'Resolve legacy shelf names/IDs in batches, optionally creating overflow shelves.'

    def add_arguments(self, parser):
        parser.add_argument('--capacity', type=int, default=70)
        parser.add_argument('--create-missing', action='store_true')
        parser.add_argument('--overflow', action='store_true')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--batch-size', type=int, default=2000)

    @transaction.atomic
    def handle(self, *args, **options):
        capacity, size = options['capacity'], options['batch_size']
        if capacity < 1 or size < 1:
            raise CommandError('Capacity and batch size must be positive.')
        shelves = list(Shelf.objects.select_for_update().order_by('pk'))
        by_name = {s.name: s for s in shelves}
        by_id = {s.pk: s for s in shelves}
        used = defaultdict(int)
        # One scan; no per-book queries or writes. Lock against concurrent edits.
        books = list(Book.objects.select_for_update().only(
            'id', 'shelf_id', 'shelf_location', 'total_copies').order_by('pk'))
        legacy = defaultdict(list)
        for shelf in shelves:
            for book_id in shelf.placements:
                legacy[int(book_id)].append(shelf)
        pending, created, moved = [], 0, 0
        groups = defaultdict(list)
        for book in books:
            if book.shelf_id:
                used[book.shelf_id] += book.total_copies
                continue
            label = book.shelf_location.strip()
            if not label and legacy[book.pk]:
                if len(legacy[book.pk]) != 1:
                    raise CommandError(f'Book {book.pk} has placements on multiple shelves; resolve it first.')
                label = legacy[book.pk][0].name
            if label:
                groups[label].append(book)
        for shelf in shelves:
            if used[shelf.pk] > shelf.capacity:
                raise CommandError(f'Shelf {shelf.name} already exceeds its capacity.')
        for label, members in groups.items():
            shelf = by_name.get(label)
            if shelf is None and label.isdecimal():
                shelf = by_id.get(int(label))
            if shelf is None:
                if not options['create_missing']:
                    raise CommandError(f'Unknown shelf {label!r}; use --create-missing or create it first.')
                shelf = Shelf.objects.create(name=label, capacity=capacity)
                by_name[label] = shelf
                created += 1
            base, sequence = shelf.name, 1
            for book in members:
                if book.total_copies > max(shelf.capacity, capacity):
                    raise CommandError(f'Book {book.pk} has too many copies for one shelf.')
                while used[shelf.pk] + book.total_copies > shelf.capacity:
                    if not options['overflow']:
                        raise CommandError(f'Shelf {shelf.name} is full; use --overflow or increase its capacity.')
                    sequence += 1
                    name = f'{base} / {sequence}'
                    if len(name) > 100:
                        raise CommandError(f'Overflow name exceeds 100 characters: {name}')
                    shelf = by_name.get(name)
                    if shelf is None:
                        shelf = Shelf.objects.create(name=name, capacity=capacity)
                        by_name[name] = shelf
                        created += 1
                used[shelf.pk] += book.total_copies
                book.shelf_id, book.shelf_location = shelf.pk, shelf.name
                pending.append(book)
                moved += 1
                if len(pending) >= size:
                    Book.objects.bulk_update(pending, ['shelf', 'shelf_location'], batch_size=size)
                    pending.clear()
        if pending:
            Book.objects.bulk_update(pending, ['shelf', 'shelf_location'], batch_size=size)
        if options['dry_run']:
            transaction.set_rollback(True)
        prefix = 'Dry run: ' if options['dry_run'] else ''
        self.stdout.write(self.style.SUCCESS(f'{prefix}{moved:,} books synchronized; {created:,} shelves created.'))
