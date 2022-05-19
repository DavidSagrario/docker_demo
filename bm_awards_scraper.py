import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import time
from time import sleep, strftime
from datetime import date
import random
from random import randint
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import mysql.connector
from mysql.connector import Error
from mysql.connector import errorcode

class oscars_scraper:
    def __init__(self, host='db',db='oscars_db',tableName="best_movie_oscars", url = 'https://www.filmaffinity.com/es/award_data.php?award_id=academy_awards'):
        self.url = url
        self.host= host
        self.db = db
        self.tableName = tableName

    def create_db_table(self):
        """ Connect to MySQL database """
        sleep(20)
        conn = None
        try:
            conn = mysql.connector.connect(host=self.host,
                                        database=self.db,
                                        user="root",
                                        password="mysql_pwd-demo@1.")
            if conn.is_connected():
                print('Connected to MySQL database')
                cursor = conn.cursor()

                try:
                    cursor.execute("USE {}".format(self.db))
                except mysql.connector.Error as err:
                    print("Database {} does not exists.".format(self.db))
                    if err.errno == errorcode.ER_BAD_DB_ERROR:
                        self.create_database(cursor)
                        print("Database {} created successfully.".format(self.db))
                        conn.database = self.db
                    else:
                        print(err)
                        exit(1)

                try:
                    print("Creating table {}: ".format(self.tableName), end='')
                    sql = '''CREATE TABLE `{}` (
                            `title` varchar(100) NOT NULL,
                            `oscars_year` int(4) NOT NULL,
                            `num_nominations` int(2) NOT NULL,
                            `num_awards` int(2) NOT NULL,
                            `link` varchar(100) NOT NULL,
                            `tag` varchar(10) NOT NULL,
                            `scrape_date` date NOT NULL
                            )'''.format(self.tableName)
                    cursor.execute(sql)
                except mysql.connector.Error as err:
                    if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                        print("already exists.")
                    else:
                        print(err.msg)
                else:
                    print("OK")
                
        except Error as e:
            print(e)

        finally:
            if conn is not None and conn.is_connected():
                conn.close()

    def insert_into_db(self, new_row):
        conn = None
        
        conn = mysql.connector.connect(host=self.host,
                                    database=self.db,
                                    user="root",
                                    password="mysql_pwd-demo@1.")
        if conn.is_connected():
            cursor = conn.cursor()

        placeholders = ', '.join(['%s'] * len(new_row))
        columns = ', '.join(new_row.keys())
        sql = "INSERT INTO %s ( %s ) VALUES ( %s )" % (self.tableName, columns, placeholders)
        
        cursor.execute(sql, list(new_row.values()))
        conn.commit()
        print('ROW INSERTED:','\n',new_row)

        if conn is not None and conn.is_connected():
                conn.close()

    def ff_scraper(self):
        self.create_db_table()

        driver = webdriver.Remote(
            'http://firefox:4444/wd/hub',
            desired_capabilities=webdriver.DesiredCapabilities.FIREFOX
        )

        driver.maximize_window()

        driver.get(self.url)

        sleep(10)

        try:
            #accept = driver.find_element_by_xpath('//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]')
            accept = driver.find_element(by=By.XPATH, value='//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]')
            accept.click()

        except:
            pass

        sleep(randint(1,20))

        source = driver.page_source
        soup = BeautifulSoup(source,features="html.parser")

        raw_links = soup.find('table', {'id':'all-winners'}).find_all('a')
        links = []
        for link in raw_links:
            if 'decade' in str(link):
                pass
            else:
                links.append(str(link).split('href="')[1].split('"')[0])

        for link in links[:5]:
            driver.get(link)

            sleep(randint(5,40))

            source = driver.page_source
            soup = BeautifulSoup(source,features="html.parser")
            
            year = int(link.split('_')[-1])
            
            winner = [x.strip() for x in soup.find('div',{'class':'wrapper'}).find_all('ul')[0].text.split('\n') if x]
            w_title = winner[2]
            w_nom = int(winner[-3].split()[0])
            w_aw = int(winner[-1].split()[0])
            w_link = 'https://www.filmaffinity.com/es/film{}.html'.format(str(soup.find('div',{'class':'wrapper'}).find_all('ul')[0].find('a')).split('href="')[1].split('"')[0].split('=')[-1])
            w_tag = 'winner'
            
            new_row = {'title':w_title,
                    'oscars_year':year,
                    'num_nominations':w_nom,
                    'num_awards':w_aw,
                    'link':w_link,
                    'tag':w_tag,
                    'scrape_date':date.today()}
            self.insert_into_db(new_row)
            #db = db.append(new_row, ignore_index=True)
            
            candidates = [x.strip() for x in soup.find('div',{'class':'wrapper'}).find_all('ul')[1].text.split('\n') if x]
            can_title = [candidates[i-1] for i in range(len(candidates)) if 'nominaci' in candidates[i]]
            can_nom = [int(candidates[i].split()[0]) for i in range(len(candidates)) if 'nominaci' in candidates[i]]
            can_aw = []
            for i in range(len(candidates)):
                if candidates[i] in can_title:
                    try:
                        if 'premio' in candidates[i+3]:
                            can_aw.append(int(candidates[i+3].split()[0]))
                        elif 'premio' not in candidates[i+3]:
                            can_aw.append(0)
                        else:
                            pass
                    except:
                        can_aw.append(0)
                        
            can_raw_links = soup.find('div',{'class':'wrapper'}).find_all('ul')[1].find_all('a')
            can_links = ['https://www.filmaffinity.com/es/film{}.html'.format(str(can_raw_links[i]).split('href="')[1].split('"')[0].split('=')[-1]) for i in range(len(can_raw_links))]
            can_links = list(set(can_links))
            can_tag = ['candidate' for i in range(len(can_links))]
            
            for i in range(len(can_links)): 
                new_row = {'title':can_title[i],
                        'oscars_year':year,
                        'num_nominations':can_nom[i],
                        'num_awards':can_aw[i],
                        'link':can_links[i],
                        'tag':can_tag[i],
                        'scrape_date':date.today()}
                #db = db.append(new_row, ignore_index=True)
                #db.to_csv('{}/MyCollection_{}.csv'.format(os.getcwd(), date.today()))
                self.insert_into_db(new_row)
        driver.quit()

if __name__ == '__main__':
    test = oscars_scraper()
    print("initialized class to test")
    test.ff_scraper()
     # function test