cd /home/frappe/frappe-bench/apps/mietrecht_ch/
git pull
cd /home/frappe/frappe-bench/
bench --site mp-test.libracore.ch migrate && bench restart
