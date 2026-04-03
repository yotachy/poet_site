from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import os
import hashlib
import secrets
from datetime import datetime
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'poet-secret-key-change-in-production')

DB_PATH = 'poet.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin1234')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB


# ─── DB 초기화 ───────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                birth_year TEXT,
                tagline TEXT,
                bio TEXT,
                photo TEXT
            );

            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'history',
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subtitle TEXT,
                publisher TEXT,
                year TEXT,
                description TEXT,
                cover_image TEXT,
                sort_order INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS poems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                note TEXT,
                collection_id INTEGER,
                is_public INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(collection_id) REFERENCES collections(id)
            );

            CREATE TABLE IF NOT EXISTS guestbook (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT
            );
        ''')

        # 기본 프로필 데이터
        existing = conn.execute('SELECT id FROM profile WHERE id=1').fetchone()
        if not existing:
            conn.execute('''INSERT INTO profile (id, name, birth_year, tagline, bio, photo)
                VALUES (1, '시인의 이름', '1980', '詩는 삶의 가장 솔직한 언어입니다.',
                '이곳에 시인의 약력을 입력해 주세요.\n\n홍익대학교 국어국문학과를 졸업하고, 2005년 《현대시》로 등단하였습니다. 이후 꾸준히 시작 활동을 이어오며 세 권의 시집을 펴냈습니다. 일상의 작은 순간들에서 삶의 의미를 길어올리는 시를 써 왔습니다.',
                '')
            ''')

        # 기본 연혁 데이터
        cnt = conn.execute('SELECT COUNT(*) FROM history').fetchone()[0]
        if cnt == 0:
            histories = [
                ('2005', '《현대시》 등단', 'history', 1),
                ('2009', '첫 시집 《어느 봄날의 기억》 출간', 'history', 2),
                ('2011', '제15회 현대시 문학상 수상', 'award', 3),
                ('2015', '두 번째 시집 《빛의 목록》 출간', 'history', 4),
                ('2018', '제7회 오늘의 젊은 작가상 수상', 'award', 5),
                ('2022', '세 번째 시집 《고요한 시간들》 출간', 'history', 6),
            ]
            conn.executemany(
                'INSERT INTO history (year, content, category, sort_order) VALUES (?,?,?,?)',
                histories
            )

        # 기본 시집 데이터
        cnt = conn.execute('SELECT COUNT(*) FROM collections').fetchone()[0]
        if cnt == 0:
            cols = [
                ('어느 봄날의 기억', None, '문학과지성사', '2009',
                 '봄의 정경을 통해 소멸과 재생의 순환을 탐구한 첫 시집. 일상의 언어로 포착한 존재의 순간들이 담겨있습니다.', '', 1),
                ('빛의 목록', None, '창비', '2015',
                 '빛과 어둠이라는 대립항을 통해 삶의 다양한 결을 포착한 두 번째 시집. 더 깊어진 서정과 사유가 돋보입니다.', '', 2),
                ('고요한 시간들', None, '문학동네', '2022',
                 '고요함 속에서 발견한 삶의 진실들을 담은 세 번째 시집. 원숙해진 시인의 눈으로 바라본 세계가 펼쳐집니다.', '', 3),
            ]
            conn.executemany(
                'INSERT INTO collections (title, subtitle, publisher, year, description, cover_image, sort_order) VALUES (?,?,?,?,?,?,?)',
                cols
            )

        # 기본 시 데이터
        cnt = conn.execute('SELECT COUNT(*) FROM poems').fetchone()[0]
        if cnt == 0:
            now = datetime.now().isoformat()
            poems = [
                ('봄비', '''봄비가 내린다
창문에 기대어 바라보면
지붕 위의 빗소리가
오래된 노래처럼 들린다

잠시 나는 어디에도 없고
비만 내린다

그것으로 충분하다''', '《어느 봄날의 기억》 수록', 1, 1, now, now),
                ('빛의 목록', '''오늘 내가 본 빛들을 적어둔다

아침 여섯 시, 커튼 사이로 새어 들어온
금빛 한 줄기

지하철 유리창에 비친
낯선 얼굴의 눈빛

당신이 돌아서며 남긴
희고 조용한 등

—이것들이 하루를 만든다''', '《빛의 목록》 표제시', 2, 1, now, now),
                ('고요', '''말하지 않아도 되는 시간이 있다

차 한 잔이 식어가는 동안
창밖의 나무는 흔들리고

나는 그 흔들림을 오래 바라본다

이것이 내가 아는
가장 충만한 고요''', '《고요한 시간들》 수록', 3, 1, now, now),
            ]
            conn.executemany(
                'INSERT INTO poems (title, content, note, collection_id, is_public, created_at, updated_at) VALUES (?,?,?,?,?,?,?)',
                poems
            )
    print("DB 초기화 완료")


# ─── 유틸 ────────────────────────────────────────────────────
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ─── 공개 라우트 ─────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    profile = db.execute('SELECT * FROM profile WHERE id=1').fetchone()
    recent_poems = db.execute(
        'SELECT * FROM poems WHERE is_public=1 ORDER BY created_at DESC LIMIT 3'
    ).fetchall()
    collections = db.execute(
        'SELECT * FROM collections ORDER BY sort_order'
    ).fetchall()
    histories = db.execute(
        'SELECT * FROM history ORDER BY sort_order'
    ).fetchall()
    return render_template('index.html', profile=profile, recent_poems=recent_poems,
                           collections=collections, histories=histories)


@app.route('/poems')
def poems():
    db = get_db()
    collection_id = request.args.get('collection', type=int)
    query = 'SELECT p.*, c.title as col_title FROM poems p LEFT JOIN collections c ON p.collection_id=c.id WHERE p.is_public=1'
    params = []
    if collection_id:
        query += ' AND p.collection_id=?'
        params.append(collection_id)
    query += ' ORDER BY p.created_at DESC'
    poems_list = db.execute(query, params).fetchall()
    collections = db.execute('SELECT * FROM collections ORDER BY sort_order').fetchall()
    return render_template('poems.html', poems=poems_list, collections=collections,
                           selected_collection=collection_id)


@app.route('/poem/<int:poem_id>')
def poem_detail(poem_id):
    db = get_db()
    poem = db.execute(
        'SELECT p.*, c.title as col_title FROM poems p LEFT JOIN collections c ON p.collection_id=c.id WHERE p.id=? AND p.is_public=1',
        (poem_id,)
    ).fetchone()
    if not poem:
        flash('존재하지 않는 시입니다.')
        return redirect(url_for('poems'))
    prev_poem = db.execute(
        'SELECT id, title FROM poems WHERE is_public=1 AND id < ? ORDER BY id DESC LIMIT 1', (poem_id,)
    ).fetchone()
    next_poem = db.execute(
        'SELECT id, title FROM poems WHERE is_public=1 AND id > ? ORDER BY id ASC LIMIT 1', (poem_id,)
    ).fetchone()
    return render_template('poem_detail.html', poem=poem, prev_poem=prev_poem, next_poem=next_poem)


@app.route('/works')
def works():
    db = get_db()
    profile = db.execute('SELECT * FROM profile WHERE id=1').fetchone()
    collections = db.execute('SELECT * FROM collections ORDER BY sort_order').fetchall()
    histories = db.execute('SELECT * FROM history ORDER BY sort_order').fetchall()
    return render_template('works.html', profile=profile, collections=collections, histories=histories)


# ─── 방명록 ──────────────────────────────────────────────────
@app.route('/guestbook')
def guestbook():
    db = get_db()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    total = db.execute('SELECT COUNT(*) FROM guestbook').fetchone()[0]
    entries = db.execute(
        'SELECT id, nickname, content, created_at, updated_at FROM guestbook ORDER BY created_at DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    total_pages = (total + per_page - 1) // per_page
    return render_template('guestbook.html', entries=entries, page=page,
                           total_pages=total_pages, total=total)


@app.route('/guestbook/write', methods=['POST'])
def guestbook_write():
    nickname = request.form.get('nickname', '').strip()
    password = request.form.get('password', '').strip()
    content = request.form.get('content', '').strip()
    if not nickname or not password or not content:
        flash('모든 항목을 입력해주세요.')
        return redirect(url_for('guestbook'))
    if len(content) > 500:
        flash('내용은 500자 이내로 입력해주세요.')
        return redirect(url_for('guestbook'))
    db = get_db()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.execute(
        'INSERT INTO guestbook (nickname, password_hash, content, created_at) VALUES (?,?,?,?)',
        (nickname, hash_password(password), content, now)
    )
    db.commit()
    flash('방명록이 등록되었습니다.')
    return redirect(url_for('guestbook'))


@app.route('/guestbook/edit/<int:entry_id>', methods=['POST'])
def guestbook_edit(entry_id):
    password = request.form.get('password', '')
    content = request.form.get('content', '').strip()
    db = get_db()
    entry = db.execute('SELECT * FROM guestbook WHERE id=?', (entry_id,)).fetchone()
    if not entry:
        return jsonify({'success': False, 'message': '존재하지 않는 글입니다.'})
    if entry['password_hash'] != hash_password(password):
        return jsonify({'success': False, 'message': '비밀번호가 틀렸습니다.'})
    if not content:
        return jsonify({'success': False, 'message': '내용을 입력해주세요.'})
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.execute('UPDATE guestbook SET content=?, updated_at=? WHERE id=?', (content, now, entry_id))
    db.commit()
    return jsonify({'success': True, 'content': content, 'updated_at': now})


@app.route('/guestbook/delete/<int:entry_id>', methods=['POST'])
def guestbook_delete(entry_id):
    password = request.form.get('password', '')
    db = get_db()
    entry = db.execute('SELECT * FROM guestbook WHERE id=?', (entry_id,)).fetchone()
    if not entry:
        return jsonify({'success': False, 'message': '존재하지 않는 글입니다.'})
    if entry['password_hash'] != hash_password(password):
        return jsonify({'success': False, 'message': '비밀번호가 틀렸습니다.'})
    db.execute('DELETE FROM guestbook WHERE id=?', (entry_id,))
    db.commit()
    return jsonify({'success': True})


# ─── 관리자 ──────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        flash('비밀번호가 틀렸습니다.')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin_dashboard():
    db = get_db()
    poem_count = db.execute('SELECT COUNT(*) FROM poems').fetchone()[0]
    public_count = db.execute('SELECT COUNT(*) FROM poems WHERE is_public=1').fetchone()[0]
    guest_count = db.execute('SELECT COUNT(*) FROM guestbook').fetchone()[0]
    col_count = db.execute('SELECT COUNT(*) FROM collections').fetchone()[0]
    recent_guests = db.execute(
        'SELECT nickname, content, created_at FROM guestbook ORDER BY created_at DESC LIMIT 5'
    ).fetchall()
    return render_template('admin/dashboard.html',
                           poem_count=poem_count, public_count=public_count,
                           guest_count=guest_count, col_count=col_count,
                           recent_guests=recent_guests)


@app.route('/admin/poems')
@login_required
def admin_poems():
    db = get_db()
    poems_list = db.execute(
        'SELECT p.*, c.title as col_title FROM poems p LEFT JOIN collections c ON p.collection_id=c.id ORDER BY p.created_at DESC'
    ).fetchall()
    collections = db.execute('SELECT * FROM collections ORDER BY sort_order').fetchall()
    return render_template('admin/poems.html', poems=poems_list, collections=collections)


@app.route('/admin/poem/new', methods=['GET', 'POST'])
@login_required
def admin_poem_new():
    db = get_db()
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        note = request.form.get('note', '').strip()
        collection_id = request.form.get('collection_id') or None
        is_public = 1 if request.form.get('is_public') == '1' else 0
        now = datetime.now().isoformat()
        db.execute(
            'INSERT INTO poems (title, content, note, collection_id, is_public, created_at, updated_at) VALUES (?,?,?,?,?,?,?)',
            (title, content, note, collection_id, is_public, now, now)
        )
        db.commit()
        flash('시가 등록되었습니다.')
        return redirect(url_for('admin_poems'))
    collections = db.execute('SELECT * FROM collections ORDER BY sort_order').fetchall()
    return render_template('admin/poem_form.html', poem=None, collections=collections)


@app.route('/admin/poem/<int:poem_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_poem_edit(poem_id):
    db = get_db()
    poem = db.execute('SELECT * FROM poems WHERE id=?', (poem_id,)).fetchone()
    if not poem:
        flash('존재하지 않는 시입니다.')
        return redirect(url_for('admin_poems'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        note = request.form.get('note', '').strip()
        collection_id = request.form.get('collection_id') or None
        is_public = 1 if request.form.get('is_public') == '1' else 0
        now = datetime.now().isoformat()
        db.execute(
            'UPDATE poems SET title=?, content=?, note=?, collection_id=?, is_public=?, updated_at=? WHERE id=?',
            (title, content, note, collection_id, is_public, now, poem_id)
        )
        db.commit()
        flash('수정되었습니다.')
        return redirect(url_for('admin_poems'))
    collections = db.execute('SELECT * FROM collections ORDER BY sort_order').fetchall()
    return render_template('admin/poem_form.html', poem=poem, collections=collections)


@app.route('/admin/poem/<int:poem_id>/delete', methods=['POST'])
@login_required
def admin_poem_delete(poem_id):
    db = get_db()
    db.execute('DELETE FROM poems WHERE id=?', (poem_id,))
    db.commit()
    flash('삭제되었습니다.')
    return redirect(url_for('admin_poems'))


@app.route('/admin/poem/<int:poem_id>/toggle', methods=['POST'])
@login_required
def admin_poem_toggle(poem_id):
    db = get_db()
    poem = db.execute('SELECT is_public FROM poems WHERE id=?', (poem_id,)).fetchone()
    new_status = 0 if poem['is_public'] else 1
    db.execute('UPDATE poems SET is_public=? WHERE id=?', (new_status, poem_id))
    db.commit()
    return jsonify({'success': True, 'is_public': new_status})


@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    db = get_db()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        birth_year = request.form.get('birth_year', '').strip()
        tagline = request.form.get('tagline', '').strip()
        bio = request.form.get('bio', '').strip()
        photo = request.form.get('current_photo', '')

        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photo = filename

        db.execute(
            'UPDATE profile SET name=?, birth_year=?, tagline=?, bio=?, photo=? WHERE id=1',
            (name, birth_year, tagline, bio, photo)
        )
        db.commit()
        flash('프로필이 저장되었습니다.')
        return redirect(url_for('admin_profile'))
    profile = db.execute('SELECT * FROM profile WHERE id=1').fetchone()
    return render_template('admin/profile.html', profile=profile)


@app.route('/admin/history')
@login_required
def admin_history():
    db = get_db()
    histories = db.execute('SELECT * FROM history ORDER BY sort_order').fetchall()
    return render_template('admin/history.html', histories=histories)


@app.route('/admin/history/add', methods=['POST'])
@login_required
def admin_history_add():
    db = get_db()
    year = request.form.get('year', '').strip()
    content = request.form.get('content', '').strip()
    category = request.form.get('category', 'history')
    max_order = db.execute('SELECT MAX(sort_order) FROM history').fetchone()[0] or 0
    db.execute('INSERT INTO history (year, content, category, sort_order) VALUES (?,?,?,?)',
               (year, content, category, max_order + 1))
    db.commit()
    flash('추가되었습니다.')
    return redirect(url_for('admin_history'))


@app.route('/admin/history/delete/<int:hid>', methods=['POST'])
@login_required
def admin_history_delete(hid):
    db = get_db()
    db.execute('DELETE FROM history WHERE id=?', (hid,))
    db.commit()
    return jsonify({'success': True})



# --- 시집 관리 ---
@app.route('/admin/collections')
@login_required
def admin_collections():
    db = get_db()
    cols = db.execute('SELECT * FROM collections ORDER BY sort_order').fetchall()
    return render_template('admin/collections.html', collections=cols)

@app.route('/admin/collection/add', methods=['POST'])
@login_required
def admin_collection_add():
    db = get_db()
    title = request.form.get('title', '').strip()
    publisher = request.form.get('publisher', '').strip()
    year = request.form.get('year', '').strip()
    description = request.form.get('description', '').strip()
    cover_image = ''
    if 'cover_image' in request.files:
        file = request.files['cover_image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cover_image = filename
    max_order = db.execute('SELECT MAX(sort_order) FROM collections').fetchone()[0] or 0
    db.execute('INSERT INTO collections (title, publisher, year, description, cover_image, sort_order) VALUES (?,?,?,?,?,?)',
        (title, publisher, year, description, cover_image, max_order + 1))
    db.commit()
    flash('시집이 추가되었습니다.')
    return redirect(url_for('admin_collections'))

@app.route('/admin/collection/<int:col_id>/delete', methods=['POST'])
@login_required
def admin_collection_delete(col_id):
    db = get_db()
    db.execute('DELETE FROM collections WHERE id=?', (col_id,))
    db.commit()
    return jsonify({'success': True})

# ─── 템플릿 컨텍스트 자동 주입 ───────────────────────────────
@app.context_processor
def inject_globals():
    db = get_db()
    profile = db.execute('SELECT * FROM profile WHERE id=1').fetchone()
    return {
        'now': datetime.now(),
        'profile': profile,
    }


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)


# ─── 검색 ────────────────────────────────────────────────────
@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    results = []
    if q and len(q) >= 2:
        db = get_db()
        results = db.execute(
            '''SELECT id, title, content, created_at FROM poems
               WHERE is_public=1 AND (title LIKE ? OR content LIKE ?)
               ORDER BY created_at DESC LIMIT 20''',
            (f'%{q}%', f'%{q}%')
        ).fetchall()
    return render_template('search.html', q=q, results=results)


# ─── 에러 핸들러 ──────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
