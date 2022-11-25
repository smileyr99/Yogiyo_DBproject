from flask import Flask, render_template, session, url_for, request, redirect
import pymysql
import datetime

app = Flask(__name__)
app.secret_key = 'sample_secret'

menulist = list()

def connectsql():
    conn = pymysql.connect(host='127.0.0.1', user='root', passwd='didhd1', db='dbProject', charset='utf8')
    return conn


@app.route('/')
def main():
    return redirect(url_for('home_viewlist'))


@app.route('/home', methods=['GET', 'POST'])
def home_viewlist():
    # 검색했을경우
    if request.method == 'POST':
        search = request.form['search']
        search = '%' + search + '%'
        print(search)
        if 'userId' in session:
            userId = session['userId']
        else:
            userId = None
        conn = connectsql()
        cursor = conn.cursor()
        query = "select DISTINCT R.restaurant_name, R.score, R.thumbnail_picture, R.number_of_reviews, R.minimum_delivery_amount, R.location, R.thumbnail_picture_info from Restaurant as R natural join Menu as M where R.restaurant_name = M.restaurant_name and (M.menu_name like %s or R.restaurant_name like %s) "
        value = (search, search)
        cursor.execute(query, value)
        raw = cursor.fetchall()

        data_list = [list(row) for row in raw]
        print(data_list)

        cursor.close()
        conn.close()

        l = len(data_list)
        return render_template('home.html', logininfo=userId, datalist=data_list, l=l)

    # 검색안했을경우(default)
    else:
        if 'userId' in session:
            userId = session['userId']
        else:
            userId = None
        conn = connectsql()
        cursor = conn.cursor()
        query = "select  R.restaurant_name, R.score, R.thumbnail_picture, R.number_of_reviews, R.minimum_delivery_amount, R.location, R.thumbnail_picture_info from Restaurant as R order by score DESC"
        cursor.execute(query)
        raw = cursor.fetchall()

        data_list = [list(row) for row in raw]
        print(data_list)

        cursor.close()
        conn.close()

        return render_template('home.html', logininfo=userId, datalist=data_list)


@app.route('/login/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['id']
        userpw = request.form['pw']

        conn = connectsql()
        cursor = conn.cursor()
        query = "SELECT * FROM user_list WHERE ID = %s AND PW = %s"
        value = (userid, userpw)
        cursor.execute(query, value)
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        for row in data:
            data = row[0]

        if data:
            session['userId'] = request.form['id']
            session['userPw'] = request.form['pw']
            return redirect(url_for('home_viewlist'))
        else:
            return render_template('./login/loginError.html')
    else:
        return render_template('./login/login.html')


@app.route('/logout')
def logout():
    session.pop('userId', None)
    session.clear()
    return redirect(url_for('home_viewlist'))


@app.route('/regist/regist', methods=['GET', 'POST'])
def regist():
    if request.method == 'POST':
        userid = request.form['id']
        userpw = request.form['pw']
        username = request.form['user_name']
        userphone_number = request.form['phone_number']
        referrer_ID = request.form['referrer_ID']

        conn = connectsql()
        cursor = conn.cursor()
        query = "SELECT * FROM user_list WHERE ID = %s"
        value = userid
        cursor.execute(query, value)
        data = (cursor.fetchall())
        if data:
            conn.rollback()
            return render_template('./regist/registError.html')
        else:
            query = "INSERT INTO user_list (ID, PW, user_name, phone_number, referrer_ID ) values (%s, %s, %s, %s, %s)"
            value = (userid, userpw, username, userphone_number, referrer_ID)
            cursor.execute(query, value)
            conn.commit()
            return render_template('./regist/registSuccess.html')

        cursor.close()
        conn.close()

    else:
        return render_template('./regist/regist.html')


@app.route('/mypage', methods=['GET', 'POST'])
def mypage():
    if 'userId' in session:
        userId = session['userId']

        conn = connectsql()
        cursor = conn.cursor()
        query = "select U.ID, U.user_name, U.phone_number, U.user_point from user_list as U where U.ID = %s"
        cursor.execute(query, userId)
        data_list = cursor.fetchall()
        for row in data_list:
            data = row[1]

        query = "select address from address as A, user_list as U where U.ID = %s and U.ID=A.ID"
        cursor.execute(query, userId)
        address = cursor.fetchall()
        print(address)
        cursor.close()
        conn.close()
        return render_template('mypage.html', logininfo=data, datalist=data_list, addresslist=address)
    else:
        userId = None
        return render_template('mypageError.html', logininfo=userId)


@app.route('/registAddress', methods=['GET', 'POST'])
def registAddress():
    userId = session['userId']
    userAddress = request.form['address']
    conn = connectsql()
    cursor = conn.cursor()
    query = "INSERT INTO address (ID, address) values (%s, %s)"
    value = (userId, userAddress)
    cursor.execute(query, value)
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('mypage'))


@app.route('/mypage_order_list')
def mypage_order_list():
    if 'userId' in session:
        conn = connectsql()
        cursor = conn.cursor()
        userId = session['userId']
        query = "select distinct L.restaurant_name, O.order_date, O.total_price, O.method_of_payment, O.delivery_address, O.requests, O.order_number from Order_ as O, Order_list as L where O.order_number=L.order_number and L.ID=%s;"
        cursor.execute(query, userId)
        tmp = cursor.fetchall()
        order_list = [list(row) for row in tmp]
        cursor.execute(query, userId)
        print(order_list)

        menu_list=[]
        tmp1_list=[]
        tmp2_list = []
        for row in order_list:
            order_number = row[6]
            query = "select menu_name, count from Order_list where order_number=%s"
            cursor.execute(query, order_number)
            tmp = cursor.fetchall()
            for row in tmp:
                tmp1_list.append(row[0]+" "+str(row[1])+"개")
                print(tmp1_list)
            tmp2_list.append(tmp1_list)
            tmp1_list=[]
        print(tmp2_list)

        for row in tmp2_list:
            s = '/  '.join(row)
            menu_list.append(s)
            print(menu_list)

        for i in range(len(order_list)):
            order_list[i].append(menu_list[i])

        print(menu_list)

        query = "select user_name from user_list where ID=%s"
        cursor.execute(query, userId)
        data = cursor.fetchall()
        print(order_list)
        for row in data:
            nickname = row[0]

        cursor.close()
        conn.close()

        return render_template('mypage_order_list.html', logininfo=nickname, orderlist=order_list, menulist = menu_list)


@app.route('/detail/<restaurant_name>', methods=['GET', 'POST'])
def detail(restaurant_name):
    if 'userId' in session:
        userId = session['userId']

        conn = connectsql()
        cursor = conn.cursor()
        query = "select * from menu where restaurant_name = %s"
        value = restaurant_name
        cursor.execute(query, value)
        data_list = cursor.fetchall()
        print(data_list)
        cursor.close()
        conn.close()

        return render_template('detail.html', logininfo=userId, restaurantName=restaurant_name, datalist=data_list)


@app.route('/order/<restaurant_name>', methods=['GET', 'POST'])
def order(restaurant_name):
    if 'userId' in session:
        userId = session['userId']
        if request.method == 'POST':
            menuCnt = request.form.getlist('menuCnt')
            print(menuCnt)

            conn = connectsql()
            cursor = conn.cursor()
            query = "select menu_name from Menu where restaurant_name=%s"
            cursor.execute(query, restaurant_name)
            menu_list = cursor.fetchall()
            query = "select price from Menu where restaurant_name=%s"
            cursor.execute(query, restaurant_name)
            price_list = cursor.fetchall()
            cursor.close()
            conn.close()

            menuList = []
            for menu in menu_list:
                menuList.append(menu[0])
            print(menuList[0])


            priceList = []
            for price in price_list:
                priceList.append(price[0])
            print(priceList[0])
            total_price = []

            for i in range(len(menu_list)):
                total_price.append(priceList[i] * int(menuCnt[i]))
            print(total_price)

            dic = dict(zip(menuList, total_price))

            now = datetime.datetime.now()
            now_date = now.strftime("%Y{} %m{} %d{} %H{}%M{}%S")
            now_date = now_date.format('년', '월', '일', ':', ':')
            order_number = now.strftime("%Y%m%d%H%M%S")
            conn = connectsql()
            cursor = conn.cursor()
            query = "INSERT INTO Order_ (order_number,ID, order_date , total_price) values (%s, %s, %s, %s)"
            value = (order_number, userId, now_date, sum(total_price))
            cursor.execute(query, value)
            lst = cursor.fetchall()
            print(lst)
            conn.commit()
            cursor.close()
            conn.close()

            for i in range(len(menuCnt)):
                if menuCnt[i] == '0':
                    continue
                conn = connectsql()
                cursor = conn.cursor()
                query = "INSERT INTO Order_list (order_number, restaurant_name, menu_name, ID, count) values ( %s, %s, %s, %s, %s)"
                value = (order_number, restaurant_name, menu_list[i], userId, menuCnt[i])
                cursor.execute(query, value)
                conn.commit()
                cursor.close()
                conn.close()

            return render_template('./order/order.html', logininfo=userId, ordernumber=order_number, totalprice=sum(total_price), dic=dic)
        else:
            return render_template('./login/login.html')
    else:
        return render_template('./login/login.html')


@app.route('/payment/<order_number>', methods=['GET', 'POST'])
def payment(order_number):
    if 'userId' in session:
        userId = session['userId']
        conn = connectsql()
        cursor = conn.cursor()
        query = "select total_price from Order_ where order_number=%s"
        value = (order_number)
        cursor.execute(query, value)
        data = cursor.fetchall()
        for row in data:
            totalprice = row[0]
        print(totalprice)
        cursor.close()
        conn.close()

        if request.method == 'POST':
            address = request.form['address']
            require = request.form['require']
            paymentMethod = request.form['paymentMethod']

            conn = connectsql()
            cursor = conn.cursor()
            query = "UPDATE  Order_ SET method_of_payment = %s, requests = %s, delivery_address= %s where order_number = %s;"
            value = (paymentMethod, require, address, order_number)
            cursor.execute(query, value)
            conn.commit()


            return render_template('./order/orderComplete.html')
        else:
            return render_template('./order/order.html', logininfo=userId, totalPrice=totalprice)
    else:
        return render_template('./login/login.html')


if __name__ == '__main__':
    app.run()
