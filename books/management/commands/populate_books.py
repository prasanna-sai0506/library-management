from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from books.models import AVAILABLE, Book


class Command(BaseCommand):
    help = 'Populate the books table with generated records.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100000,
            help='Target total number of books (default: 100000).',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=2000,
            help='Number of records inserted per bulk operation (default: 2000).',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Delete existing books before populating.',
        )

    def handle(self, *args, **options):
        target = options['count']
        batch_size = options['batch_size']

        if target < 0:
            raise CommandError('--count must be zero or greater.')
        if batch_size < 1:
            raise CommandError('--batch-size must be greater than zero.')

        with transaction.atomic():
            if options['clear']:
                Book.objects.all().delete()

            existing_count = Book.objects.count()
            to_create = max(target - existing_count, 0)
            if not to_create:
                self.stdout.write(self.style.SUCCESS(
                    f'Book table already contains at least {target:,} records '
                    f'({existing_count:,} present).'
                ))
                return

            existing_isbns = set(
                Book.objects.exclude(isbn='').values_list('isbn', flat=True)
            )
            categories = [
                'Fiction', 'Science', 'History', 'Biography', 'Technology',
                'Mathematics', 'Literature', 'Mystery', 'Fantasy', 'Romance',
                'Travel', 'Cooking', 'Art', 'Music', 'Business',
                'Health', 'Education', 'Philosophy', 'Religion', 'Children',
            ]

            created = 0
            candidate = 1
            batch = []

            while created < to_create:
                isbn = f'978{candidate:010d}'
                candidate += 1
                if isbn in existing_isbns:
                    continue

                index = existing_count + created
                category = categories[index % len(categories)]
                total_copies = (index % 8) + 1
                shelf_letter = chr(ord('A') + (index % 26))
                shelf_number = (index // 26) % 50 + 1
                borrowing_cost = Decimal('5.00') + Decimal(index % 20)

                batch.append(Book(
                    title=f'The Library Collection Volume {index + 1:06d}',
                    author=f'Author {((index % 500) + 1):04d}',
                    isbn=isbn,
                    category=category,
                    shelf_location=f'{shelf_letter}-{shelf_number:02d}',
                    total_copies=total_copies,
                    available_copies=total_copies,
                    availability=AVAILABLE,
                    borrowing_cost=borrowing_cost,
                    borrowing_period=7 + (index % 21),
                ))
                existing_isbns.add(isbn)
                created += 1

                if len(batch) == batch_size:
                    Book.objects.bulk_create(batch)
                    batch = []

                    if created % 10000 == 0 or created == to_create:
                        self.stdout.write(f'Inserted {created:,} of {to_create:,}...')

            if batch:
                Book.objects.bulk_create(batch)

        final_count = Book.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'Populated books table: added {created:,}; '
            f'{final_count:,} records now present.'
        ))
