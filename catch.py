from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import requests
import time
import os
import sys
import random
import argparse
import pandas as pd
import multiprocessing
from urllib.parse import urlencode,quote
from bs4 import BeautifulSoup
from multiprocessing.pool import Pool

class Exhentai():
    category_dict = {'Manga': 1017, 'ArtistCG': 1015, 'GameCG': 1007, 'Western': 511,
                     'Non-h': 761, 'Imageset': 991, 'cosplay': 959, 'Misc': 1022}
    def __init__(self,category,save_path,url_file):
        self.headers = {'Host': 'e-hentai.org',
                        'Referer':'https://e-hentai.org/?page=1&f_cats=1017',
                        'Cookie': '__cfduid=d0bca687a1e225aaba9c210e542b0d79e1564320790',
                        'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'}
        self.base_url = 'http://e-hentai.org/?'
        self.lock = multiprocessing.Manager().Lock()
        self.category = category
        self.save_path = save_path
        self.url_file = url_file
        self.f_cats = self.category_dict[category]

    def get_picture_html(self,url):
        try:
            response = requests.get(url,headers = self.headers)
            time.sleep(random.random())
            if response.status_code == 200:
                res_text = response.text
                soup = BeautifulSoup(res_text,'lxml')
                return soup
        except requests.ConnectionError as e:
            print('Error',e.args)

    def get_url_info(self,soup):
        url_dict = {}
        name_dict = {}
        manga_urls = soup.find_all(attrs={'class': 'ido'})[0].find_all(attrs={'class': 'gl3c glname'})[1:]
        for index, j in enumerate(manga_urls):
            manga_url = j.a.attrs['href']
            manga_name = j.a.div.string
            url_dict[index] = manga_url
            name_dict[index] = manga_name
        for key,value in name_dict.items():
            print('{} {}'.format(key,value))
        return url_dict,name_dict

    def get_manga_urls(self,page):
        if page < 1:
            page = 1
        page -= 1
        self.params = {
            'page': page,
            'f_cats': self.f_cats}
        url = self.base_url + urlencode(self.params)
        soup = self.get_picture_html(url)
        url_dict,name_dict = self.get_url_info(soup)
        self.write_url_to_file(url_dict,name_dict)
        time.sleep(random.random())

    def write_url_to_file(self,url,name):
        if self.params['f_cats'] is not None:
            self.file_name = self.category + '.csv'
        else:
            self.file_name = 'url.csv'
        if os.path.exists(self.file_name):
            self.lock.acquire()
            url_df_0 = pd.read_csv(self.file_name,index_col=0)
            self.lock.release()
            url_df_1 = pd.DataFrame({'url':url,'name':name})
            new_df = pd.merge(url_df_0,url_df_1,how='outer')
            self.lock.acquire()
            new_df.to_csv(self.file_name)
            self.lock.release()
        else:
            url_df = pd.DataFrame({'url':url,'name':name})
            self.lock.acquire()
            url_df.to_csv(self.file_name)
            self.lock.release()

    def read_url_from_file(self,process_id):
        if os.path.exists(self.url_file):
            self.lock.acquire()
            url_df = pd.read_csv(self.url_file,index_col=0)
            self.lock.release()
            this_url =  url_df['url'].values[process_id]
            url_df = url_df[~url_df.url.isin([this_url])]
            url_df = url_df.reset_index(drop=True)
            self.lock.acquire()
            url_df.to_csv(self.url_file)
            self.lock.release()
            return this_url
        else:
            return None

    def search_keywords(self):
        while True:
            keyword = input("请输入你想搜索的漫画的关键字,包括漫画名、漫画语言、标签等：")
            keyword_search = quote(keyword)
            params = {
            'f_cats':self.f_cats,
            'f_search':keyword_search
            }
            url = self.base_url + urlencode(params)
            soup = self.get_picture_html(url)
            url_dict,_ = self.get_url_info(soup)
            loop = input("请问是否要重新搜索？输入q重新进入搜索。")
            if loop == 'q' or loop == 'Q':
                continue
            else:
                break
        number = input("请输入你想要下载的漫画序号(需要在显示的序号范围内。):")
        number = int(number)
        if number<0 or number>len(url_dict):
            number = 0
        return url_dict[number]

    def get_pictures(self,process_id):
        picture_list = []
        if process_id is None:
            one_manga = self.search_keywords()
        else:
            one_manga = self.read_url_from_file(process_id)
        soup = self.get_picture_html(one_manga)
        picture_html = soup.find_all(attrs={'class': 'gdtm'}, name='div')
        for html in picture_html:
            url = html.a.attrs['href']
            picture_list.append(url)
        manga_info = soup.find_all(name = 'td',attrs={'class':'gdt2'})
        manga_length = int(manga_info[5].string.split(' ')[0])
        manga_language = list(manga_info[3].strings)[0]
        manga_size = manga_info[4].string
        manga_date = manga_info[0].string.split(' ')[0]
        manga_en_name = soup.find(attrs={'id':'gn'}).string
        manga_jp_name = soup.find(attrs={'id':'gj'}).string
        if manga_jp_name is None or manga_jp_name == '':
            manga_jp_name = 'NULL'
        if manga_language is None or manga_language == '':
            manga_language = 'NULL'
        if manga_length>40:
            for i in range(manga_length//40):
                url = one_manga + '?p=%d' % (i + 1)
                soup_n = self.get_picture_html(url)
                picture_html_n = soup_n.find_all(attrs={'class':'gdtm'},name='div')
                for html_n in picture_html_n:
                    url = html_n.a.attrs['href']
                    picture_list.append(url)
        return {'en_name': manga_en_name, 'jp_name': manga_jp_name,
                'language':manga_language,'date':manga_date, 'size':manga_size,
                'length':str(manga_length)+'pages','urls': picture_list}

    def get_one_picture(self,url):
        try:
            response = requests.get(url,headers = self.headers)
            time.sleep(random.random())
            if response.status_code == 200:
                pic_text = response.text
                picture = BeautifulSoup(pic_text, 'lxml').find(attrs={'id':'img'}).attrs['src']
                pic_response = requests.get(picture)
                return pic_response.content
            else:
                print('picture download failed!')
                return response.status_code
        except requests.ConnectionError as e:
            return e.args

    def get_picture_contents(self,process_id):
        info = self.get_pictures(process_id)
        if not os.path.exists('exmanga'):
            os.mkdir('exmanga')
        manga_path = os.path.join('exmanga',info['en_name'])
        if not os.path.exists(manga_path):
            os.mkdir(manga_path)
        information = [info['en_name'],info['jp_name'],info['language'],
                       info['size'],info['date'],info['length']]
        log_file = open('{}/{}'.format(manga_path,'log.txt'),'a')
        with open ('{}/{}'.format(manga_path,'information.txt'),'w') as f:
            f.write('\n'.join(information))
        for picture_url in info['urls']:
            pic_content = self.get_one_picture(url = picture_url)
            pic_name = '{:0>4d}'.format(int(picture_url.split('-')[-1]))
            file_path = '{0}/{1}.{2}'.format(manga_path,pic_name,'jpg')
            with open (file_path,'wb') as f:
                f.write(pic_content)
            now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            save_log = '{} success saved {} {} ! \n'.format(now,info['en_name'],picture_url)
            if not isinstance(pic_content,bytes):
                save_log = '{} download failed {} {} ! because{} \n'.format\
                    (now,info['en_name'],picture_url,pic_content)
            print(save_log)
            log_file.write(save_log)
        log_file.close()

def main(args):
    ex = Exhentai(category=args.manga_category,save_path=args.save_path,url_file=args.choose_file)
    if args.mode == 'urls':
        pool_0 = Pool(processes=args.process)
        groups = [x for x in range(args.start_page, args.start_page + args.page_number)]
        pool_0.map(ex.get_manga_urls, groups)
        pool_0.close()
        pool_0.join()
    elif args.mode == 'search':
        while True:
            ex.get_picture_contents(process_id=None)
    else:
        url_df = pd.read_csv(ex.url_file, index_col=0)
        url_df = url_df.reset_index(drop=True)
        pool_1 = Pool(processes=args.process)
        groups = [x for x in range(url_df.shape[0])]
        pool_1.map(ex.get_picture_contents,groups)
        pool_1.close()
        pool_1.join()

def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('--start_page', type=int,
                        help='The start page which you want to crawl.', default=1)
    parser.add_argument('--page_number',type=int,
                        help='How many page do you want to crawl.',default=10)
    parser.add_argument('--manga_category', type=str,
                        help='What kind of pictures you want to download?'
                             'choose from Manga,ArtistCG,GameCG,Western,Non-h,Cosplay,Imageset,Misc',
                        default='Manga')
    parser.add_argument('--process',type=int,
                        help="How many process do you want to run?",default=2)
    parser.add_argument('--mode',type=str,
                        help="crawl mode, urls or mangas or search",default='mangas')
    parser.add_argument('--choose_file',type=str,
                        help='choose one url file to download.',default='Manga.csv')
    parser.add_argument('--save_path',type=str,
                        help="the path where you want to save the picture.",default='exmanga')
    return parser.parse_args(argv)


if __name__ == '__main__':
    main(parse_arguments(sys.argv[1:]))



