import requests
from lxml import html
import MySQLdb as mdb
from datetime import datetime
import time


TABLE_HISTORIC = 'historico_propiedades'
TABLE_DETAILS = 'detalles_propiedades'
C_DATE = datetime.now().strftime("%Y-%m-%d")
class RealEstate():

    def __init__(self, entry_html, property_type, city):
        self.html = entry_html

        self.properties = {}
        self.properties['type'] = property_type
        self.properties['city'] = city+'_aprox'

        self.get_data()

    def get_data(self):

        url = self.html.xpath('div/div[@class="content"]/div/a/@href')
        try:
            self.properties['url'] = url[0]
        except:
            self.properties['url'] = ''

        #id
        pos = self.properties['url'].rfind('/')+1
        try:
            self.properties['id'] = self.properties['url'][pos:]
        except:
            self.properties['id'] = ''


        # price
        #price = entry.xpath('div/div[@class="price_desc"]/p/span[@itemprop="price"]/text()')
        #try:
        #    self.properties['price'] = price[0]
        #except:
        #    self.properties['price'] = ''


        # area
        area = self.html.xpath('div/div[@class="price_desc"]/div/div[@class="m2"]/p/span[2]/text()')
        try:
            self.properties['area'] = area[0]
            self.properties['area'] = self.properties['area'].replace(' m2', '')
            self.properties['area'] = float(self.properties['area'])
        except:
            self.properties['area'] = 0

        # rooms
        rooms = self.html.xpath('div/div[@class="price_desc"]/div/div[@class="rooms"]/p/span[2]/text()')
        try:
            self.properties['rooms'] = int(rooms[0])
        except:
            self.properties['rooms'] = 0

        # bath
        baths = self.html.xpath('div/div[@class="price_desc"]/div/div[@class="bathrooms"]/p/span[2]/text()')
        try:
            self.properties['baths'] = float(baths[0])
        except:
            self.properties['baths'] = 0

        # garage
        garage = self.html.xpath('div/div[@class="price_desc"]/div/div[@class="bathrooms garages"]/p/span/text()')
        try:
            self.properties['garage'] = int(garage[0])
        except:
            self.properties['garage'] = 0

        # state
        stats = self.html.xpath('div[@class="tools"]/input[@name="data-stats"]')

        if len(stats) > 0:
            stats = stats[0]
            self.properties['state'] = stats.attrib['data-property-state']
            self.properties['stratum'] = int(stats.attrib['data-property-stratum'])
            self.properties['type'] = stats.attrib['data-property-business-type']
            self.properties['seller_type'] = stats.attrib['data-property-offerer']
            try:
                self.properties['seller'] = stats.attrib['data-property-enterprise-id']
            except:
                self.properties['seller'] = ''
            self.properties['id'] = stats.attrib['data-property-id']
            self.properties['price'] = float(stats.attrib['data-property-price'])
            self.properties['type_of_home'] = stats.attrib["data-property-type-id"]
            if self.properties['type_of_home'] == "1":
                self.properties['type_of_home'] = 'Apartamento'
            elif self.properties['type_of_home'] == "2":
                self.properties['type_of_home'] = 'Casa'
            elif self.properties['type_of_home'] == "6":
                self.properties['type_of_home'] = 'Local'
            elif self.properties['type_of_home'] == "3":
                self.properties['type_of_home'] = 'Oficina'
            elif self.properties['type_of_home'] == "8":
                self.properties['type_of_home'] = 'Bodega'
        else:
            self.properties['state'] = ''
            self.properties['stratum'] = 0
            self.properties['type'] = ''
            self.properties['seller_type'] = ''
            self.properties['seller'] = ''
            self.properties['price'] = 0
            self.properties['type_of_home'] = ''




        #city
        city = self.html.xpath('div[@class="tools"]/a[@class="show_tel"]/@data-property-city')
        if len(city) > 0:
            self.properties['city'] = city[0]

    def check_property(self):
        con.execute("SELECT * FROM `{}` WHERE `PROPERTY_ID` = '{}' ORDER BY `LAST_DATE` DESC LIMIT 1 ".format(TABLE_HISTORIC,self.properties['id']))
        row = con.fetchone()

        if not row:
            self.newProperty()
            return 0
        elif row[2] == self.properties['price']:
            self.updateDate(row[0])
            return 1
        else:
            self.newPrice()
            return 2

    def newProperty(self):
        #Add new row to historic table
        query = 'INSERT INTO `{table}`(`PROPERTY_ID`, `PRICE`, `INI_DATE`, `LAST_DATE`, `TYPE`) VALUES ("{p_id}",{price},"{ini_date}","{last_date}","{type}")'\
            .format(table=TABLE_HISTORIC,p_id=self.properties['id'], price=self.properties['price'], type=self.properties['type'], ini_date=C_DATE, last_date=C_DATE)
        con.execute(query)

        query = 'INSERT INTO `{table}`(`PROPERTY_ID`, `URL`, `SITE`, `CITY`, `TYPE`, `HOME`, `STATE`, `AREA`, `SELLER_TYPE`, `SELLER`, `STRATUM`, `ROOMS`, `BATHS`, `GARAGE`, `NEIGHBORHOOD`, `EXTRACTED`) VALUES ("{id}","{url}","{site}","{city}","{type}","{home}","{state}",{area},"{seller_type}","{seller}",{stratum},{rooms},{baths},{garage},"{neighborhood}",0)'\
            .format(table=TABLE_DETAILS,id=self.properties['id'], url=self.properties['url'], site='Metrocuadrado', city=self.properties['city'], type=self.properties['type'], home=self.properties['type_of_home'], state=self.properties['state'], area=self.properties['area'], seller_type=self.properties['seller_type'], seller=self.properties['seller'], stratum=self.properties['stratum'], rooms=self.properties['rooms'], baths=self.properties['baths'], garage=self.properties['garage'], neighborhood='' )
        con.execute(query)

    def newPrice(self):
        # Add new row to historic table
        query = 'INSERT INTO `{table}`(`PROPERTY_ID`, `PRICE`, `INI_DATE`, `LAST_DATE`, `TYPE`) VALUES ("{p_id}",{price},"{ini_date}","{last_date}","{type}")' \
            .format(table=TABLE_HISTORIC, p_id=self.properties['id'], price=self.properties['price'],
                    type=self.properties['type'], ini_date=C_DATE, last_date=C_DATE)
        con.execute(query)

    def updateDate(self, id):
        # Update last date
        query = 'UPDATE `{table}` SET `LAST_DATE`="{last_date}" WHERE `ENTRY_ID` = {id}' \
            .format(table=TABLE_HISTORIC,last_date=C_DATE, id=id)
        con.execute(query)

cities = ['Medellin','Bogota', 'Cali', 'Ibague', 'Barranquilla']

real_estate_types = ['apartamento', 'casa'] #Define types

page = 0
for city in cities:
    if city == 'Bogota':
        ages = ['Más de 20 años', 'Entre 10 y 20 años', 'Entre 5 y 10 años', 'Entre 0 y 5 años', 'para-estrenar', 'en-construccion'] #Define property age
    else:
        ages = ['']

    for type_val in real_estate_types:
        for age in ages:

             stop = False
             first = True
             last_n_results = 0
             while stop==False and page<200:
                page += 1
                url = 'http://www.metrocuadrado.com/search/list/ajax?&mnrogarajes=&mnrobanos=&mnrocuartos=&mtiempoconstruido='+age+'&marea=&mvalorarriendo=&mvalorventa=&mciudad='+city+'&mubicacion=&mtiponegocio=&mtipoinmueble='+type_val+'&mzona=&msector=&mbarrio=&selectedLocationCategory=1&selectedLocationFilter=mciudad&mestadoinmueble=&madicionales=&orderBy=&sortType=&companyType=&companyName=&midempresa=&mgrupo=&mgrupoid=&mbasico=&currentPage='+str(page)+'&totalPropertiesCount=12528&totalUsedPropertiesCount=12524&totalNewPropertiesCount=4&sfh=1'
                results = requests.post(url)
                #with open('test_file.html', 'w') as fl:
                #    fl.write(results.text)
                results = html.fromstring(results.text)

                counters = [0, 0, 0]
                if first:
                    n_results = results.xpath('//span[@class="save-search-title"]/text()')
                    if len(n_results) > 0:
                        try:
                            n_results = n_results[0].strip()
                            pos = n_results.find(' ')
                            n_results = int(n_results[:pos])
                            n_results = round(n_results/50)

                            if n_results != last_n_results:
                                print(url)
                                if n_results > 1000:
                                    stop = True
                                last_n_results = n_results
                        except:
                            n_results = 'NN'


                entries = results.xpath('//div[@class="m_rs_list_item_main"]')

                with mdb.connect('localhost', 'root', '', '') as con:

                    for entry in entries:

                        try:
                            res = RealEstate(entry, 'SIN TIPO', city)

                            #Compare if there is another property with that id
                            property_state = res.check_property()

                            #Update counters
                            counters[property_state] += 1
                        except Exception as e:
                            print("Error with ", url)
                            print(str(e))

                next_page = results.xpath('//div[@class="pager"]/a[@class="next list"]/text()')
                if len(next_page) == 0:
                    stop = True


                print(city, type_val,age, page,n_results, "Counters:",', '.join(str(e) for e in counters))

                time.sleep(1)

             page = 0
