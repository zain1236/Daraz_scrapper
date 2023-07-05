from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager
from flask import Flask, jsonify
import mysql.connector

cnx = mysql.connector.connect(
    host='db4free.net',
    user='test_user_zain',
    password='test@123',
    database='test_zain_db'
)

def get_product(element):
    img = element.find_element(By.CLASS_NAME, "image--WOyuZ").get_attribute('src')
    title = element.find_element(By.CLASS_NAME, "title--wFj93").text
    price = element.find_element(By.CLASS_NAME, "price--NVB62").text
    price = price[4:]
    try:
        price = price.replace(",", "")
        price = int(price)
    except:
        pass

    product = {'title': title,
               'image': img,
               'price': price
               }
    return product

def scrap(name):
    print("scrapping")
    url = 'https://www.daraz.pk/catalog/?q={}'.format(name)


    # print('url', url)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)

    # driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    results = driver.find_elements(By.CLASS_NAME, "gridItem--Yd0sa")

    counter = 0
    products = []
    for result in results:
        prod = get_product(result)
        products.append(prod)
        counter += 1
        if counter == 10:
            break

    print(products)
    return products




app = Flask(__name__)

@app.route('/api/q/<name>', methods=['GET'])
def get_items(name):
    # Connect to the MySQL server

    cursor = cnx.cursor()
    query = "INSERT INTO `test_zain_db`.`search` (`query`,`created_At`) VALUES ('{}',NOW())".format(name)
    cursor.execute(query)

    rowid = cursor.lastrowid

    items = scrap(name)

    data = [(item['title'], item['price'], item['image'], rowid) for item in items]
    query = "INSERT INTO `test_zain_db`.`product` (`title`, `price`, `image`, `query`) VALUES (%s, %s, %s, %s)"
    cursor.executemany(query, data)

    cnx.commit()
    cursor.close()
    return jsonify(items)

@app.route('/api/history', methods=['GET'])
def get_history():
    cursor = cnx.cursor()

    query = "SELECT `id`, `query`, `created_At` FROM `search` ORDER BY `created_At` DESC"
    cursor.execute(query)
    search_history = cursor.fetchall()

    cursor.close()

    s_list = []
    for search in search_history:
        row_id = search[0]
        keyword = search[1]
        created_at = search[2]
        s_list.append({"id":row_id,"keyword": keyword, "created_at": created_at})

    # Return the search history list
    return jsonify(s_list)

@app.route('/api/products/<queryId>', methods=['GET'])
def get_history_products(queryId):
    cursor = cnx.cursor()

    # Retrieve the products from the specified search history row
    query = "SELECT `title`, `price`, `image` FROM `product` WHERE `query` = %s LIMIT 10"
    cursor.execute(query, (queryId,))
    prods = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()

    products = []
    # # Process the products
    for product in prods:
        title = product[0]
        price = product[1]
        image = product[2]
        products.append({"title": title, "price": price, "image": image})

    # Return the products as JSON
    return jsonify(products)



if __name__ == '__main__':
    app.run(debug=True)
