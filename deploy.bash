#!/bin/bash

chmod u+x venv/bin/activate
source venv/bin/activate

pip install -r requirements.txt

cd theme/static_src && npm i && cd ../..

python manage.py tailwind build

systemctl restart django.service