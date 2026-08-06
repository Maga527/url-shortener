from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
import random
import string
import urllib.parse
app = Flask(__name__)

password = "sV0fKRWjZrqT1T@n"
encoded_password = urllib.parse.quote_plus(password)
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://postgres:{encoded_password}@78.40.194.10:5432/my_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 #указываем какая база данных
db = SQLAlchemy(app)

class URLMap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.Text, nullable=False)  # Длинная ссылка (Text, так как URL бывают длинными)
    short_code = db.Column(db.String(10), unique=True, nullable=False)  # Короткий код, обязательно уникальный
    clicks = db.Column(db.Integer, default=0, nullable=False)

@app.route("/", methods=['POST', 'GET'])
def home():
    if request.method == "POST":
        original_url = request.form.get('title')

        urlmap = URLMap(original_url=original_url, short_code=generate_short_code(6))
        try:
            db.session.add(urlmap)  # добавляем в базу данных
            db.session.commit()  # сохраняем

            all_urls = URLMap.query.order_by(URLMap.id.desc()).all()
            return render_template("main.html", short_url=urlmap.short_code, urls=all_urls)
  # куда перенаправляем после заполнения всех полей
        except Exception as e:
            db.session.rollback()  # Обязательно для PostgreSQL!
            return f"произошла ошибка: {e}"
    else:
        # Когда пользователь просто зашел на сайт (GET), берем из базы все ссылки
        # order_by(URLMap.id.desc()) отсортирует их так, чтобы новые были вверху
        all_urls = URLMap.query.order_by(URLMap.id.desc()).all()
        return render_template("main.html", urls=all_urls)

def generate_short_code(length=6):
    # Берем все английские буквы (маленькие и большие) и цифры
    chars = string.ascii_letters + string.digits
    # Собираем случайную строчку нужной длины
    return ''.join(random.choice(chars) for _ in range(length))

@app.route("/delete/<int:id>", methods=['POST', 'GET'])
def url_delete(id):
    # Находим ссылку в базе по id, если её нет — вернёт 404 ошибку
    url_record = URLMap.query.get_or_404(id)
    try:
        db.session.delete(url_record)  # Удаляем из сессии
        db.session.commit()            # Сохраняем изменения в PostgreSQL
        return redirect('/')           # Перенаправляем на главную страницу
    except Exception as e:
        db.session.rollback()          # Важно для Postgres: откатываем сессию при ошибке
        return f"При удалении ссылки произошла ошибка: {e}"

@app.route("/<string:short_code>")
def redirect_to_url(short_code):
    db_record = URLMap.query.filter_by(short_code=short_code).first()
    if db_record:
        # Прибавляем 1 при каждом переходе
        db_record.clicks += 1
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        return redirect(db_record.original_url)
    return "Ссылка не найдена", 404
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)

