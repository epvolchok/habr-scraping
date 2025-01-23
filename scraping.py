import pandas as pd
from librequest import GetArticles

pages = 2
habr_connection = GetArticles(pages)
queries = ['анализ данных']
res = habr_connection.get(*queries)
print(res.tail(10))
print(res.dtypes)