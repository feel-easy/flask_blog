import datetime
from dateutil.relativedelta import relativedelta
d1 = datetime.datetime.today()
print(d1)
d2 = d1 + relativedelta(months=+20)

print(d2)

import requests
url = 'http://www.baidu.com'

requests.get(url=url)