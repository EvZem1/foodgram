import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from api.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает ингредиенты из CSV файла в базу данных'

    def handle(self, *args, **options):
        csv_file_path = settings.BASE_DIR / 'data' / 'ingredients.csv'

        try:
            with open(csv_file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                self.stdout.write(self.style.SUCCESS(
                    'Начинаю загрузку ингредиентов...'
                ))

                count = 0
                for row in reader:
                    name, measurement_unit = row
                    _, created = Ingredient.objects.get_or_create(
                        name=name,
                        measurement_unit=measurement_unit
                    )
                    if created:
                        count += 1

                self.stdout.write(self.style.SUCCESS(
                    f'Загрузка завершена. '
                    f'Добавлено {count} новых ингредиентов.'
                ))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'ОШИБКА: Файл не найден по пути: {csv_file_path}'
            ))
