from django.core.management.base import BaseCommand, CommandError
from contentfetch.models import StockComment

class Command(BaseCommand):
    help = 'Deletes all comments for a specific stock. This is a destructive action.'

    def add_arguments(self, parser):
        parser.add_argument('stock_name', type=str, help='The name of the stock for which to delete comments.')

    def handle(self, *args, **options):
        stock_name_to_delete = options['stock_name']
        
        try:
            # Find all comments for the specified stock
            comments = StockComment.objects.filter(stock_name=stock_name_to_delete)
            
            # Get the count of comments to be deleted
            comment_count = comments.count()
            
            if comment_count == 0:
                self.stdout.write(self.style.SUCCESS(f"No comments found for stock: '{stock_name_to_delete}'"))
                return

            # Delete the comments
            comments.delete()
            
            self.stdout.write(self.style.SUCCESS(f"Successfully deleted {comment_count} comments for stock: '{stock_name_to_delete}'"))

        except Exception as e:
            raise CommandError(f'An error occurred: {e}')
