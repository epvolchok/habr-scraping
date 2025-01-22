import requests
import pandas as pd
from bs4 import BeautifulSoup
import time


def page_number(query):
    """Функция возвращает количество страниц выдачи для запроса query"""
    URL = 'https://habr.com/ru/search/'
    params = {
        'q': query
    }
    req = requests.get(URL, params=params)
    soup = BeautifulSoup(req.text)
    pages = soup.find_all('a', class_='tm-pagination__page')
    return pages[-1].text.strip()

def page_url(page):
    """Поисковая ссылка для страницы под номером page"""
    return f'https://habr.com/ru/search/page{page}/'

def create_fullink(link):
    """На основе окончания ссылки (link) достраивается
    полный адрес страницы с результатами"""
    return 'https://habr.com'+link

#в зависимости от типа поста

def article(article):
    """Функция извлекает заголовок, ссылку и дату
    из описания простого поста"""
    title = article.find('a', 'tm-title__link').text
    link = article.find('a', 'tm-title__link').get('href')
    date = pd.to_datetime(article.find('span', 'tm-article-datetime-published').find('time').get('datetime'))
    return date, title, link

def megapost(article):
    """Функция извлекает заголовок, ссылку и дату
    из описания мегапоста"""
    title = article.find('h2', 'tm-megapost-snippet__title').text
    link = article.find('a', 'tm-megapost-snippet__link tm-megapost-snippet__card').get('href')
    date = pd.to_datetime(article.find('time', 'tm-megapost-snippet__datetime-published').get('datetime'))
    return date, title, link

posts_type = {'article': article, 'megapost': megapost}



def get_text(link):
    """Получает текст и рейтинг статьи по ссылке"""
    req = requests.get(link)
    soup = BeautifulSoup(req.text)
    article_body = soup.find('div', 'tm-article-body')
    if article_body is not None:
        text = article_body.text.strip()
        rating = soup.find('span', 'tm-votes-meter__value').text
    else:
        text = 'Страница не найдена'
        rating = None
    return text, rating

def get_articles(url, query):
    """Возвращает результаты по запросу query
    со страницы url"""
    df = pd.DataFrame()
    params = {
        'q': query
    }
    req = requests.get(url, params=params)
    time.sleep(0.3)
    soup = BeautifulSoup(req.text)
    #формируем строку с результатами
    articles = soup.find_all('article', class_='tm-articles-list__item')
    for el in articles:
        #в зависимости от типа поста
        for ts in posts_type:
            tag = f'tm-{ts}-snippet'
            if el.find('div', tag):
                date, title, link = posts_type[ts](el)
        #полная ссылка на статью
        fullink = create_fullink(link)
        #полный текст статьи и рейтинг 
        #(ищутся единообразно для постов всех типов)
        text, rating = get_text(fullink)

        #результаты    
        row = {'date': date, 'title': title, 'link': fullink, 'text': text, 'rating': rating}
        df = pd.concat([df, pd.DataFrame([row])])
        df.reset_index(drop=True, inplace=True)    
    return df

def get_habr_articles(query, pages):
    """Возвращает датафрейм с результатами поиска в виде
    date - title - link - text - rating
    по списку запросов query с (pages)-количества страниц поисковой выдачи"""
    habr_articles = pd.DataFrame()

    #для каждого запроса из списка
    for q in query:
        #если запрашиваемое число страниц не превышает
        #общее количество страниц выдачи
        if 0 < pages <= int(page_number(q)):
            time.sleep(0.3)

            for page in range(1, pages+1):
                #формируем ссылку для каждой страницы
                url = page_url(page)
                #получаем данные с этой страницы
                df = get_articles(url, q)
                #добавляем к уже найденным
                habr_articles = pd.concat([habr_articles, df])
                habr_articles.reset_index(drop=True, inplace=True) 
    return habr_articles.drop_duplicates(subset='link')

res = get_habr_articles(query=['python', 'анализ данных'], pages=2)
res