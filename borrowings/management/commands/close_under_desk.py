from django.core.management.base import BaseCommand

from borrowings.models import UnderDeskBook


class Command(BaseCommand):
    help = 'Move all under-desk book copies to the shelf at end of day'

    def handle(self, *args, **options):
        count = UnderDeskBook.objects.count()
        UnderDeskBook.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            f'Moved {count} under-desk book copy/copies to the shelf.'
        ))
