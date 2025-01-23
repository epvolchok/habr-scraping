import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

class GetArticles():
    def __init__(self, num_pages=1):
        self.link = 'https://habr.com'
        self.num_pages = num_pages
        self.df_articles = pd.DataFrame()
        self.posts_types = {'article': GetArticles.article, 'megapost': GetArticles.megapost}

    def page_number(self, query):
        """Returns the number pages of search results"""
        URL = self.link + '/ru/search/'
        params = {
            'q': query
        }
        req = requests.get(URL, params=params)
        soup = BeautifulSoup(req.text, features="lxml")
        pages = soup.find_all('a', class_='tm-pagination__page')
        return pages[-1].text.strip()
    
    def page_url(self, page):
        """Search link for the page number n"""
        return self.link + f'/ru/search/page{page}/'
    
    def create_fullink(self, link):
        """ Creates a full link for a specific request"""
        return self.link+link
    
    @staticmethod
    def article(article):
        """Get title, link and date for a simple post"""
        title = article.find('a', 'tm-title__link').text
        link = article.find('a', 'tm-title__link').get('href')
        date = pd.to_datetime(article.find('a', 'tm-article-datetime-published').find('time').get('datetime'))
        return date, title, link
    
    @staticmethod
    def megapost(article):
        """Get title, link and date for  a megapost"""
        title = article.find('h2', 'tm-megapost-snippet__title').text
        link = article.find('a', 'tm-megapost-snippet__link tm-megapost-snippet__card').get('href')
        date = pd.to_datetime(article.find('time', 'tm-megapost-snippet__datetime-published').get('datetime'))
        return date, title, link

    def get_article_data(self, post_type, article):
        func = self.posts_types[post_type]
        
        if func:
            results = func(article)
            return results
        else: 
            print("Error in article type")
            return -100, -100, -100
        
    @staticmethod
    def get_fulltext(link):
        """Get full text of the article from the {link}"""
        req = requests.get(link)
        soup = BeautifulSoup(req.text, features="lxml")
        article_body = soup.find('div', 'article-formatted-body')
        if article_body is not None:
            text_blocks = article_body.find_all('p')
            text_blocks = list(map(lambda el: el.text.strip(), text_blocks))
            text = ' '.join(text_blocks)
            rating = soup.find('span', 'tm-votes-lever__score-counter').text
        else:
            text = 'Page not found'
            rating = None
        return text, rating

    def get_data(self, url, query):
        """Resurns results on a query
        from url-page"""
        df = pd.DataFrame()
        params = {
            'q': query
                }
        req = requests.get(url, params=params)
        time.sleep(0.3)
        soup = BeautifulSoup(req.text, features="lxml")
        articles = soup.find_all('article', class_='tm-articles-list__item')
        print(f'{len(articles)} articles on the page')
        print(f'Collecting data for query {{\x1B[3m{query}\x1B[0m}}... \nPlease wait...')
        for article in articles:
            for post_type in self.posts_types:
                tag = f'tm-{post_type}-snippet'
                if article.find('div', tag):
                    date, title, link = self.get_article_data(post_type, article)
            if link:
                fullink = self.create_fullink(link)
                
                text, rating = GetArticles.get_fulltext(fullink)

                row = {'date': date, 'title': title, 'link': fullink, 'text': text, 'rating': rating}
                df = pd.concat([df, pd.DataFrame([row])])
                df.reset_index(drop=True, inplace=True)
        return df

    def get(self, *queries):
        """Returns a dataframe with structure:
        date - title - link - text - rating
        """
        if queries:
            for query in queries:
                
                if 0 < self.num_pages <= int(self.page_number(query)):
                    time.sleep(0.3)

                    for page in range(1, self.num_pages+1):
                        url = self.page_url(page)
                        print(f'Page number {page}')

                        df = self.get_data(url, query)
                        
                        self.df_articles = pd.concat([self.df_articles, df])
                        self.df_articles.reset_index(drop=True, inplace=True)
            print(f'Recieved {len(self.df_articles.drop_duplicates(subset='link'))} rows of data')
            return self.df_articles.drop_duplicates(subset='link')