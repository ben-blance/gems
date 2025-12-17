#!/bin/bash

echo "Setting up Quant Trading Platform..."

pip install -r requirements.txt

createdb quant_db || echo "Database already exists"

python manage.py makemigrations
python manage.py migrate

python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results

mkdir -p media/uploads

echo "Setup complete!"
echo ""
echo "To start the application:"
echo "1. Terminal 1: redis-server"
echo "2. Terminal 2: celery -A config worker -l info"
echo "3. Terminal 3: celery -A config beat -l info"
echo "4. Terminal 4: python manage.py django_producer --symbols=btcusdt,ethusdt"
echo "5. Terminal 5: python manage.py runserver"