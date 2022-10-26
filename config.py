DB_HOST = 'localhost'
DB_PORT = 3306
DB_LOGIN = 'root'
DB_PASS = 'Neetqw2110'  # mac Neetqw2110 | Neetqw2110+++
DB_NAME = 'remanga'

from datetime import datetime

date1 = datetime.now()
date2 = datetime(day=1, month=7, year=2021)

timedelta = date1 - date2
print(timedelta)