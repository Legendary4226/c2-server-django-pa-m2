# C2

Cron task

```
* * * * * python manage.py read_dns_logs
```

Dev

```
# Start tailwind + dev local server
python manage.py tailwind dev

# Only start Tailwind watch
python manage.py tailwind start

# Make sure NodeJS packages are installed:
cd theme/static_src/ && npm i && cd ../..
```