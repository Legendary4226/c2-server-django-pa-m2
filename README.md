# C2

Cron task

```
* * * * * python manage.py read_dns_logs
* * * * * python manage.py handle_finished_job
```

### Dev

```
# Start tailwind + dev local server
python manage.py tailwind dev

# Only start Tailwind watch
python manage.py tailwind start

# Make sure NodeJS packages are installed:
cd theme/static_src/ && npm i && cd ../..
```

### DNS server config

**/etc/bind/named.conf.local**

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
    allow-transfer { key "c2server"; };
};
```

**/var/lib/bind/db.data.tm-it.fr**

Set everything to a TTL of 5

```
$TTL 5
data.tm-it.fr.          IN SOA  ns1.data.tm-it.fr. admin.tm-it.fr. (
                                5         ; serial
                                5     ; refresh (1 week)
                                5      ; retry (1 day)
                                5    ; expire (4 weeks)
                                5     ; minimum (1 week)
                                )
                        NS      ns1.data.tm-it.fr.
                        <...>
```