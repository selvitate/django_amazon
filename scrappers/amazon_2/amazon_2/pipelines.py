# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.pipelines.images import ImagesPipeline
import scrapy
import mysql.connector
import json
from datetime import datetime
from scrapy.utils.project import get_project_settings
import re
import ast


class AmazonSearchResultPipeline(ImagesPipeline):
    def process_item(self, item, spider):
        if item.get('price'):
            item['price'] = self.parse_price(item['price'])
        if item.get('title'):
            item['title'] = item.get('title').strip()
        if item.get('description'):
            item['description'] = self.parse_desc(item.get('description'))
        if item.get('rewiev_count'):
            item['rewiev_count'] = self.pase_rewiew(item.get('rewiev_count'))
        if item.get('product_rank'):
            item['product_rank'] = self.parse_product_rank(item.get('product_rank'))
        if item.get('image'):
            item['image'] = self.parse_image(item.get('image'))
        if item.get('top5_rewiews'):
            item['top5_rewiews'] = self.parse_top5(item.get('top5_rewiews'))
        if item.get('stars'):
            item['stars'] = self.parse_stars(item.get('stars'))
        if not item.get('free_delivery'):
            item['free_delivery'] = False
        if not item.get('is_amazonchoice'):
            item['is_amazonchoice'] = False
        if not item.get('prime'):
            item['prime'] = False
        if not item.get('sponsored'):
            item['sponsored'] = False
        if not item.get('sponsored_position'):
            item['sponsored_position'] = False
        if not item.get('sponsored_page'):
            item['sponsored_page'] = False
        # If you want add new function for data edding
        # Example:
        # if item.get('FIELD WHICH YOU NEED TO EDIT'):
        #   item['FIELD WHICH YOU NEED TO EDIT'] = self.CUSTOM_FUNCTION(...)
        return super(ImagesPipeline, self).process_item(item, spider)

    # def COSTOM_FUNC(self, ...):
    #   pass

    def pase_rewiew(self, item):
        item = item.replace(',', '')
        return int(item)

    def parse_stars(self, item):
        end = item.find('out')
        return float(item[:end].strip())

    def parse_price(self, item):
        item = item.replace(',', '')
        return float(item)

    def parse_top5(self, item):
        months = {
            'January': '01',
            'February': '02',
            'March': '03',
            'April': '04',
            'May': '05',
            'June': '06',
            'July': '07',
            'August': '08',
            'September': '09',
            'October': '10',
            'November': '11',
            'December': '12'
        }
        tmp = []
        for star_rew in item:
            star_rew = star_rew['data']
            for idx, rew in enumerate(star_rew):
                star_rew[idx]['text'] = rew['text'].replace('\n', ' ')
                for month in months.keys():
                    if month in rew['date']:
                        date = rew['date'].replace(month, months[month])
                        print(date)
                        star_rew[idx]['date'] = datetime.strptime(date, '%d %m %Y')
                        break
        return item

    def parse_image(self, item):
        start = item.find('[')
        end = item.find('colorToAsin')
        item = item[start:end - 1].strip()
        item = item[:-2].replace('null', ""'None'"")
        item = ast.literal_eval(item)
        image = []
        for elem in item:
            image.append(elem['hiRes'])
        return image

    def parse_desc(self, item):
        item = ''.join(item)
        item = item.replace('\t', '')
        item = item.replace('\n', ' ')
        item = item.strip()
        return item

    def parse_product_rank(self, item):
        # worst code ever
        tmp = []
        for idx, _ in enumerate(item):
            item[idx] = item[idx].replace('\n', '')
            item[idx] = item[idx].strip()
        item = ' '.join(item)
        item = item.split('#')
        for elem in item:
            numbers = re.search(r'[0-9]+', elem)
            if not numbers:
                continue
            d = {}
            d['rank'] = numbers.group(0)
            category = re.search(r"[a-zA-Z'& ]+", elem).group(0)
            category = category[category.find('in') + 3:]
            d['category'] = category.strip()
            tmp.append(d)
        return tmp

    def get_media_requests(self, item, info):
        if item['title'] and info.spider.image_manage != 'link':
            for idx, image_url in enumerate(item['image']):
                yield scrapy.Request(image_url, meta={'item': item, 'idx': idx})
        else:
            return item

    def image_downloaded(self, response, request, info):
        for path, image, buf in self.get_images(response, request, info):
            if not response.meta['item']['image']:
                return
            file_name = response.meta['item']['asin'].replace('/', '-')
            idx = response.meta.get('idx')
            path = '{}-{}.jpg'.format(file_name, idx)
            self.store.persist_file(
                path, buf, info,
                headers={'Content-Type': 'image/jpeg'})
        return response.meta['item']

class AmazonProductDump(object):
    """
    Class for connect to DB.
    Change settings for you in "create_connection" func

    """

    def __init__(self):
        self.create_connection()
        self.create_table()

    def create_connection(self):
        db_settings = get_project_settings().get('DB_SETTINGS')
        self.conn = mysql.connector.connect(
            host=db_settings.get('host'),
            user=db_settings.get('user'),
            passwd=db_settings.get('passwd'),
            database=db_settings.get('database')
        )
        self.curr = self.conn.cursor()

    def create_table(self):
        """
        Here i create the table
        and dump the data into base
        """
        self.curr.execute(
            """
            CREATE TABLE IF NOT EXISTS product(
                product_id int unsigned not null auto_increment,
                asin VARCHAR(20),
                title text,
                descriprion text,
                url text,
                price float,
                image_url text,
                stars float,
                seller text,
                rewiev_count int,
                prime bool,
                is_amazonchoice bool,
                free_delivery bool,
                sponsored bool,
                sponsored_position int,
                sponsored_page int,
                keyword text,
                top_100 text,
                adding_date timestamp,
                status text,
                PRIMARY KEY(product_id)
            );
            """
        )

        self.curr.execute(
            """
            CREATE TABLE IF NOT EXISTS ranks(
                rank_id int unsigned not null auto_increment,
                product_id int unsigned not null,
                category text,
                rank int,
                foreign key (product_id) references product(product_id) on delete cascade,
                PRIMARY KEY(rank_id)
            );
            """
        )

        self.curr.execute(
            """
            CREATE TABLE IF NOT EXISTS rewiews(
                rewiew_id int unsigned not null auto_increment,
                product_id int unsigned not null,
                rewiew_text text,
                rewiew_date timestamp,
                rewiew_star int,
                foreign key (product_id) references product(product_id) on delete cascade,
                primary key(rewiew_id)
            );
            """
        )



    def process_item(self, item, spider):
        if item.get('image'):
            images = json.dumps(item['image'])
            patterns = '[]"'
            for pattern in patterns:
                images = images.replace(pattern, '')
            item['image'] = images
        self.store_db(item)
        return item

    def store_db(self, item):
        # get the row from db
        self.curr.execute(
            """SELECT * FROM product
                WHERE asin = (%s) LIMIT 1""", (
                item['asin'],
            ))
        row = self.curr.fetchall()
        if row:
            row = row[0]
        # if it exist and we use product_page scrapper - update product db, and insert to the ranks and rewiews db's
        if row and item['scrapper'] == 'product_page':
            self.curr.execute(
                """
                UPDATE product set descriprion=%s, image_url=%s, seller=%s, top_100=%s, status='updated'
                WHERE asin=(%s)
                """, (item.get('description'), item.get('image'), item.get('seller'), item.get('top_100'), item['asin'])
            )
            self.conn.commit()
            for elem in item['product_rank']:
                self.curr.execute(
                    """
                    INSERT INTO ranks(product_id,category,rank)
                    VALUES (%s, %s, %s)""",
                    (
                        row[0],
                        elem['category'],
                        elem['rank']
                    ))
                self.conn.commit()

            for elem in item['top5_rewiews']:
                star = elem['star']
                for rewiev in elem['data']:
                    self.curr.execute(
                        """
                        INSERT INTO rewiews(product_id,rewiew_text,rewiew_date,rewiew_star)
                        VALUES (%s, %s, %s, %s)""",
                        (
                            row[0],
                            rewiev['text'],
                            rewiev['date'],
                            star
                        ))
                    self.conn.commit()

        # if exist and use amazon_search_result scrapper - update row
        elif row and item['scrapper'] == 'amazon_search_result':
            keywords = json.loads(row[16])
            # item['keyword'] = 'test'
            if item['keyword'] not in keywords:
                keywords.append(item['keywords'])
                keywords = json.dumps(keywords)
                patterns = '[]"'
                for pattern in patterns:
                    keywords = keywords.replace(pattern, '')
            else:
                keywords = json.dumps([item['keyword']])
            self.curr.execute(
                """
                UPDATE product set title=%s, url=%s, price=%s, stars=%s, rewiev_count=%s, prime=%s,
                                   is_amazonchoice=%s, free_delivery=%s, sponsored=%s, sponsored_position=%s,
                                   sponsored_page=%s, keyword=%s, adding_date=%s, status=%s
                WHERE asin=(%s)
                """, (item.get('title'), item.get('url'), item.get('price'), item.get('stars'), item.get('rewiev_count'),
                      item.get('prime'), item.get('is_amazonchoice'), item.get('free_delivery'), item.get('sponsored'),
                      item.get('sponsored_position'), item.get('sponsored_page'), keywords,
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'new', item['asin']))
        # if not exist and use amazon_search_result scrapper - create row
        elif not row and item['scrapper'] == 'amazon_search_result':
            keywords = json.dumps([item['keyword']])
            patterns = '[]"'
            for pattern in patterns:
                keywords = keywords.replace(pattern, '')
            self.curr.execute(
                """
                INSERT INTO product(asin,title,url,price,stars,
                                rewiev_count,prime,is_amazonchoice,free_delivery,sponsored,
                                sponsored_position,sponsored_page,keyword,adding_date,status)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    item.get('asin'),
                    item.get('title'),
                    item.get('url'),
                    item.get('price'),
                    item.get('stars'),
                    item.get('rewiev_count'),
                    item.get('prime'),
                    item.get('is_amazonchoice'),
                    item.get('free_delivery'),
                    item.get('sponsored'),
                    item.get('sponsored_position'),
                    item.get('sponsored_page'),
                    keywords,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'new'
                ))
        self.conn.commit()
