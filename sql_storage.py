import pymysql
import time
import os

class MySql:
    def __init__(self,host,user,password,port):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.file_path = 'exmanga'

    def init_database(self):
        host,user,password,port = (self.host,self.user,self.password,self.port)
        db = pymysql.connect(host = host,user = user,password = password,port = port)
        cursor = db.cursor()
        exist = 'show databases;'
        cursor.execute(exist)
        all_base = list(cursor.fetchall())
        if ('Exhentai',) in all_base:
            pass
        else:
            database = 'CREATE DATABASE Exhentai DEFAULT CHARACTER SET utf8'
            cursor.execute(database)
        db.close()
    
    def insert_data(self):
        host, user, password, port = (self.host, self.user, self.password, self.port)
        db = pymysql.connect(host=host, user=user, password=password,
                             port=port, db='Exhentai', use_unicode=True)
        cursor = db.cursor()
        exist = 'show tables;'
        cursor.execute(exist)
        all_table = list(cursor.fetchall())
        if ('picture',) in all_table:
            pass
        else:
            table = 'CREATE TABLE IF NOT EXISTS picture (en_name VARCHAR(255) NOT NULL,jp_name VARCHAR(255) NOT NULL,' \
                    'language VARCHAR(255) NOT NULL,size FLOAT NOT NULL,path VARCHAR(255) NOT NULL,pages INT NOT NULL,' \
                    'date DATE NOT NULL,download_time DATETIME NOT NULL,  PRIMARY KEY (en_name))'
            cursor.execute(table)
        file_list = os.listdir(self.file_path)
        dir_list = [os.path.join(self.file_path,file) for file in file_list]
        for manga_dir in dir_list:
            with open('{}/{}'.format(manga_dir,'information.txt'),'r') as info:
                information = info.readlines()
                en_name = information[0]
                jp_name = information[1]
                language = information[2]
                size = float(information[3].split(' ')[0])
                date = information[4].strip()
                pages = int(information[5].split('p')[0])
            with open('{}/{}'.format(manga_dir,'log.txt'),'r') as log:
                last_line = log.readlines()[-1].split(' ')
                download_time = last_line[0] + ' '+last_line[1]
            paths = os.path.abspath(manga_dir)
            data_format = 'INSERT INTO picture (en_name,jp_name,language,size,path,pages,date,download_time) ' \
                      'values (%s,%s,%s,%s,%s,%s,%s,%s)'
            try:
                cursor.execute(data_format,(en_name,jp_name,language,size,paths,pages,date,download_time))
                db.commit()
                now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                print('{} success saved ! {}'.format(now,en_name))
            except pymysql.Error as e:
                print('Error: {}'.format(e.args))
                db.roolback()
        db.close()

if __name__ == '__main__':
    mysql = MySql(host='localhost',user='root',password='123456',port=3306) #初始的默认参数
    mysql.insert_data()













