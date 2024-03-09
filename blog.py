from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
from datetime import datetime


# Kullanıcı Kayıt Formu
class ReqisterForm(Form):
    name = StringField("İsim Soyisim", validators= [validators.length(min =4, max =25 )])
    username = StringField("Kullanıcı Adı", validators= [validators.length(min =5, max =35 )])
    email = StringField("Email Adresi", validators= [validators.Email(message = "Lütfen Geçerli Bir Email Adresi Giriniz... ")])
    password = PasswordField("Parola", validators=[validators.DataRequired(message = "Lütfen Bir Parola Belirleyiniz..."),validators.EqualTo(fieldname= "confirm", message = "Parolanız Uyuşmuyor...")])
    confirm = PasswordField("Parola Doğrula")

# Kullanıcı Giriş Formu
class LoginForm(Form):
    username = StringField("Kullanıcı Adı", validators= [validators.length(min =5, max =35 )])
    password = PasswordField("Parola", validators=[validators.DataRequired(message = "Lütfen Geçerli Parola Giriniz...")])

# Makale Form
class ArticleForm(Form):
    title = StringField("Makale Başlığı", validators=[validators.length(min =5 , max = 100)])
    content = TextAreaField("Makale İçeriği", validators=[validators.length(min =10)])

# Yorum Form
class CommentForm(Form):
    content = TextAreaField("",validators=[validators.length(min =10)])



# Kullanıcı Giriş Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:       
            return f(*args, **kwargs)
        else:
            flash("Bu sayfayı görüntülemek için lütfen giriş yapınız...", "danger")
            return redirect(url_for("login"))
    return decorated_function




app = Flask(__name__)

app.secret_key = "ybblog"  #flash mesajları için gerekli

app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)



@app.route("/")
def index():

    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")


# Kontrol Paneli
@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where author = %s "
    result = cursor.execute(sorgu,(session["username"],))
    
    if result > 0:
        data = cursor.fetchall()
        return render_template("dashboard.html", articles = data)
    else:
        flash("Henüz hiç makaleniz bulunmuyor...","danger")
        return render_template("dashboard.html")


# Makale Ekleme İşlemi
@app.route("/addarticle", methods = ["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)

    if request.method == "POST" and form.validate():

        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()

        flash("Makale başarıyla eklendi...", "success")
        return redirect(url_for("dashboard"))

    return render_template("addarticle.html", form = form)



# Makale Güncelleme İşlemi
@app.route("/edit/<string:id>", methods = ["GET", "POST"])
@login_required
def update(id):

    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sorgu = "select * from  articles where id = %s and author = %s"
        result = cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle bir makale yok veya buna yetkiniz bulunmuyor...", "danger")
            return redirect(url_for("index"))
        
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            
            return render_template("update.html", form = form)

    else : # POST REQUESTS

        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data
        update_date = datetime.now()

        cursor = mysql.connection.cursor()
        sorgu = "update articles set title = %s, content = %s , update_date = %s where id = %s"
        cursor.execute(sorgu,(newTitle,newContent,update_date,id))
        mysql.connection.commit()
        cursor.close()
        
        flash("Makalen Başarıyla Güncellendi...", "success")
        return redirect(url_for("dashboard"))


# Makale Arama İşlemi
@app.route("/search", methods = ["GET", "POST"])
def search():
    if request.form == "GET":
        return redirect(url_for("index"))
    
    else:
        keyword = request.form.get("keyword") 

        cursor = mysql.connection.cursor()
        sorgu = "select * from articles where title like '%" + keyword + "%' "
        result = cursor.execute(sorgu)

        if result == 0:
            flash("Bu metni içeren bir makale bulunmuyor...", "warning")
            return redirect(url_for("articles"))
        
        else:
            
            data = cursor.fetchall()
            return render_template("articles.html", articles = data)

 # Yorum işlemi
@app.route("/comment/<string:id>" , methods = ["GET", "POST"])
@login_required
def comment(id):
    form = CommentForm(request.form)

    if request.method == "POST":
        content = form.content.data

        cursor = mysql.connection.cursor()
        sorgu = " insert into comments(author,article,content) values(%s,%s,%s)"
        cursor.execute(sorgu,(session["username"],id,content))
        mysql.connection.commit()
        cursor.close()
        return redirect(url_for("articles"))


    else:
        return render_template("comment.html" , form = form)



# Makale Silme İşlemi
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where author = %s and id = %s"
    result = cursor.execute(sorgu,(session["username"],id))
    
    if result > 0:

        sorgu_Del = "delete from articles where id = %s"
        cursor.execute(sorgu_Del,(id,))
        mysql.connection.commit()
        cursor.close()
        
        flash("Silme işlemi başarıyla gerçekleşti", "success")
        return redirect(url_for("dashboard"))

    else:
        flash("Böyle bir makale yok veya bu işleme yetkiniz yok...", "danger")
        return redirect(url_for("index"))



#Kayıt Olma
@app.route("/register", methods = [ "GET", "POST" ])
def reqister():
    form = ReqisterForm(request.form)

    if request.method == "POST" and form.validate():

        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sorgu = "INSERT INTO users(name,username,email,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,username,email,password))
        mysql.connection.commit()
        cursor.close()
        
        flash("Başarıyla Kayıt Oldunuz...", "success")
        return redirect(url_for("login"))
    
    else:
        return render_template("register.html", form = form)


# Makale Detay Sayfası
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where id = %s"
    result = cursor.execute(sorgu,(id,))

    cursor2 = mysql.connection.cursor()
    sorgu2 = "select * from comments where article = %s"
    cursor2.execute(sorgu2,(id))


    if result > 0:
        data = cursor.fetchone()
        data2 = cursor2.fetchall()
        return render_template("article.html", article = data, comments = data2)
        
    else:
        return render_template("article.html")



#Login İşlemi
@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm(request.form)
    
    if request.method == "POST":

        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sorgu = "select * from users where username = %s"
        
        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarıyla giriş yaptınız...", "success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash("Parolanızı yanlış girdiniz...", "danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle bir kullanıcı bulunmamaktadır...", "danger")
            return redirect(url_for("login"))
    
    return render_template("login.html",form = form)


#Logout işlemi
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# Makaleler Bölümü
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles"
    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")




if __name__ == "__main__":
    app.run(debug=True)