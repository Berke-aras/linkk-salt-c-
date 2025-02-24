import os
import sqlite3
import random
import string
import datetime
import json
import logging
import requests
from flask import Flask, request, redirect, render_template, session, url_for, flash, g, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter.util import get_remote_address

# Uygulama ve log ayarları
app = Flask(__name__)
app.secret_key = 'degistirin_bunu_gercek_ortam_icin'
DATABASE = 'database.db'

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    format="%(asctime)s %(levelname)s: %(message)s"
)

# Rate Limiter (varsayılan: gün başına 200, saat başına 50 istek)


# Papara API ayarları (demo/sandbox amaçlı)
PAPARA_API_KEY = "YOUR_PAPARA_API_KEY"
PAPARA_SECRET = "YOUR_PAPARA_SECRET"
PAPARA_BASE_URL = "https://sandbox-api.papara.com"  # Gerçek ortamda uygun URL'yi kullanın

# Veritabanı bağlantısı
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    with app.app_context():
        db = get_db()
        db.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'free'
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_url TEXT NOT NULL,
            short_code TEXT UNIQUE NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )''')
        db.commit()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# Rastgele kısaltılmış kod üretimi
def generate_short_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Non-üye linklerinin 24 saat sonra silinmesi
def cleanup_expired_links():
    db = get_db()
    now = datetime.datetime.now()
    db.execute("DELETE FROM links WHERE expires_at IS NOT NULL AND expires_at <= ?", (now,))
    db.commit()

@app.before_request
def before_request():
    cleanup_expired_links()

# Papara ödeme simülasyonu
def papara_initiate_payment(user_id, amount, callback_url):
    """
    Gerçek entegrasyon için Papara API dokümantasyonuna göre gerekli istekler yapılmalıdır.
    Bu örnekte, ödeme isteği simüle edilip, dummy token ve redirect URL üretiliyor.
    """
    payment_token = "papara_token_" + str(random.randint(1000, 9999))
    redirect_url = "https://sandbox.papara.com/checkout?token=" + payment_token
    logging.info(f"Papara payment initiated for user {user_id}, amount {amount}, token {payment_token}")
    return payment_token, redirect_url

# Anasayfa
@app.route('/')
def index():
    user = None
    if 'user_id' in session:
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    return render_template('index.html', user=user)

# Hakkında sayfası
@app.route('/about')
def about():
    return render_template('about.html')

# Üyelik yükseltme (Papara ödeme entegrasyonu ile)
@app.route('/upgrade')
def upgrade():
    if 'user_id' not in session:
        flash("Önce giriş yapmalısınız.", "error")
        return redirect(url_for('login'))
    return render_template('upgrade.html')

# Papara ödeme başlatma (Rate limit: 5 istek/dakika)
@app.route('/upgrade/initiate', methods=['POST'])
def upgrade_initiate():
    if 'user_id' not in session:
        flash("Önce giriş yapmalısınız.", "error")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    amount = "1"  # Ödeme miktarı (örneğin: 1 TL)
    callback_url = request.host_url.rstrip("/") + url_for('payment_callback')
    
    token, redirect_url = papara_initiate_payment(user_id, amount, callback_url)
    # Ödeme başlatıldığını logla
    logging.info(f"User {user_id} initiated Papara payment. Redirecting to: {redirect_url}")
    return redirect(redirect_url)

# Papara ödeme callback'i (ödeme sonucu)
@app.route('/payment/callback', methods=['GET', 'POST'])
def payment_callback():
    token = request.args.get("token")
    if not token:
        flash("Ödeme işlemi iptal edildi.", "error")
        logging.warning("Payment callback called without token")
        return redirect(url_for('upgrade'))
    
    # Simüle: Eğer token "papara_token_" ile başlıyorsa ödeme başarılı kabul edilsin.
    if token.startswith("papara_token_"):
        db = get_db()
        db.execute("UPDATE users SET role = 'premium' WHERE id = ?", (session['user_id'],))
        db.commit()
        flash("Ödeme başarılı! Hesabınız premium'a yükseltildi.", "success")
        logging.info(f"User {session['user_id']} upgraded to premium via Papara, token: {token}")
    else:
        flash("Ödeme başarısız.", "error")
        logging.error(f"Payment verification failed for token: {token}")
    return redirect(url_for('index'))

# Hesap oluşturma (Rate limit: 5 istek/dakika)
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Ek kontrol: kullanıcı adı alfanümerik ve 3-20 karakter arası olmalı
        if not username.isalnum() or not (3 <= len(username) <= 20):
            flash("Kullanıcı adı sadece harf ve rakam içermeli ve 3 ile 20 karakter arasında olmalı.", "error")
            logging.warning(f"Invalid signup attempt with username: {username}")
            return redirect(url_for('signup'))
        db = get_db()
        hashed = generate_password_hash(password)
        try:
            db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            db.commit()
            flash("Kayıt başarılı. Lütfen giriş yapın.", "success")
            logging.info(f"New user signed up: {username}")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Bu kullanıcı adı zaten mevcut.", "error")
            logging.warning(f"Signup failed, username already exists: {username}")
    return render_template('signup.html')

# Kullanıcı girişi (Rate limit: 10 istek/dakika)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash("Giriş başarılı.", "success")
            logging.info(f"User logged in: {username}")
            return redirect(url_for('index'))
        else:
            flash("Giriş başarısız. Bilgilerinizi kontrol ediniz.", "error")
            logging.warning(f"Failed login attempt for username: {username}")
    return render_template('login.html')

# Kullanıcı çıkışı
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Çıkış yapıldı.", "success")
    logging.info("User logged out")
    return redirect(url_for('index'))

# Link kısaltma işlemi (Rate limit: 20 istek/dakika)
@app.route('/shorten', methods=['POST'])
def shorten():
    original_url = request.form['url']
    if not (original_url.startswith('http://') or original_url.startswith('https://')):
        flash("Lütfen geçerli bir URL girin (http:// veya https:// ile başlamalı).", "error")
        return redirect(url_for('index'))
    db = get_db()
    user_id = session.get('user_id')
    now = datetime.datetime.now()
    expires_at = None
    if user_id:
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        # Ücretsiz üye için link sınırı 5 adet
        if user['role'] == 'free':
            count = db.execute("SELECT COUNT(*) as count FROM links WHERE user_id = ? AND expires_at IS NULL", (user_id,)).fetchone()['count']
            if count >= 5:
                flash("Ücretsiz üye olarak sadece 5 adet sınırsız link oluşturabilirsiniz. Premium yükseltmeye göz atın!", "error")
                return redirect(url_for('index'))
    else:
        expires_at = now + datetime.timedelta(hours=24)
    short_code = generate_short_code()
    while db.execute("SELECT * FROM links WHERE short_code = ?", (short_code,)).fetchone():
        short_code = generate_short_code()
    db.execute("INSERT INTO links (original_url, short_code, user_id, expires_at) VALUES (?, ?, ?, ?)",
               (original_url, short_code, user_id, expires_at))
    db.commit()
    logging.info(f"Link created: {original_url} -> {short_code} by user: {user_id if user_id else 'non-member'}")
    
    # Üye olmayan kullanıcılar için cookie'ye link bilgisini ekle
    if not user_id:
        links = []
        links_cookie = request.cookies.get("links")
        if links_cookie:
            try:
                links = json.loads(links_cookie)
            except Exception:
                links = []
        links.append({
            "short_code": short_code,
            "original_url": original_url,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S")
        })
        response = make_response(redirect(url_for('index')))
        response.set_cookie("links", json.dumps(links), max_age=30*24*60*60)  # 30 gün geçerli
        flash(f"Kısaltılmış link: {request.host_url}{short_code}", "success")
        return response
    else:
        flash(f"Kısaltılmış link: {request.host_url}{short_code}", "success")
        return redirect(url_for('index'))

# Kısaltılmış linke yönlendirme
@app.route('/<short_code>')
def redirect_short(short_code):
    db = get_db()
    link = db.execute("SELECT * FROM links WHERE short_code = ?", (short_code,)).fetchone()
    if link:
        logging.info(f"Redirecting short link {short_code} to {link['original_url']}")
        return redirect(link['original_url'])
    else:
        flash("Aradığınız link bulunamadı.", "error")
        logging.warning(f"Short link not found: {short_code}")
        return redirect(url_for('index'))

# Link geçmişi sayfası (üye olanlar kendi linklerini, üye olmayanlar cookie tabanlı)
@app.route('/my_links')
def my_links():
    if 'user_id' in session:
        db = get_db()
        user_id = session['user_id']
        links = db.execute("SELECT * FROM links WHERE user_id = ?", (user_id,)).fetchall()
        return render_template('my_links.html', links=links, user_type="member")
    else:
        links = []
        links_cookie = request.cookies.get("links")
        if links_cookie:
            try:
                links = json.loads(links_cookie)
            except Exception:
                links = []
        return render_template('my_links.html', links=links, user_type="non-member")

# Link silme (sadece üye kullanıcılar için)
@app.route('/delete/<int:link_id>')
def delete_link(link_id):
    if 'user_id' not in session:
        flash("Bu işlem için giriş yapmalısınız.", "error")
        return redirect(url_for('login'))
    db = get_db()
    link = db.execute("SELECT * FROM links WHERE id = ? AND user_id = ?", (link_id, session['user_id'])).fetchone()
    if not link:
        flash("Link bulunamadı veya yetkisiz işlem.", "error")
        logging.warning(f"Unauthorized delete attempt for link ID: {link_id}")
        return redirect(url_for('my_links'))
    db.execute("DELETE FROM links WHERE id = ?", (link_id,))
    db.commit()
    flash("Link silindi.", "success")
    logging.info(f"Link ID {link_id} deleted by user {session['user_id']}")
    return redirect(url_for('my_links'))

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
