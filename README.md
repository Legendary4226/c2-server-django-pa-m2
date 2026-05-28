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

DNS server config

```
logging {
    channel query_log {
        file "/var/log/named/queries.log" versions 3 size 5m;
        severity debug 3;
        print-time yes;
        print-category yes;
        print-severity yes;
    };
    category queries { query_log; };
};

key "c2server" {
    algorithm hmac-sha256;
    secret "<replace by 'openssl rand -base64 16' output>";
};

zone "data.tm-it.fr" {
    type master;
    file "/etc/bind/db.data.tm-it.fr";
    allow-update { key "c2server"; };
};
```