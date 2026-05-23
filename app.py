import requests
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = 'manga-local-secret-2026' # Change this for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

ts = URLSafeTimedSerializer(app.config["SECRET_KEY"])

# --- DATABASE & LOGIN SETUP ---
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index' # Redirect to home if login is required

API_URL = "https://api.mangadex.org"

TAGS_MAP = {
    "Action": "391b0423-d847-456f-bbb0-8b094c10c1d1",
    "Adventure": "87dbfd80-3846-47ab-b541-9392228d7711",
    "Comedy": "4d32283e-9f8d-4aec-966a-2ee0af3f5a2d",
    "Drama": "b9afcb42-f2f6-4c4d-970f-2e17239777ee",
    "Fantasy": "cdc2aa2c-2820-413c-837c-ca6110915f81",
    "Horror": "cdad1168-1e45-4851-917c-444811a3cae3",
    "Mystery": "ee968100-4191-4968-93a3-2459c25143a4",
    "Psychological": "3b6051a0-8701-49df-9abf-142c1ccca3fa",
    "Romance": "423e2db2-915c-4ad0-9f4e-da01a02727d7",
    "Sci-Fi": "256c80d5-75f1-437c-ba37-ca6110915f81",
    "Slice of Life": "e5301a23-edd9-49dd-a0cb-2459c25143a4",
    "Sports": "69960289-76a0-471d-9e4a-59b581691c2f",
    "Supernatural": "e197df38-d0e7-43b5-9b09-2842d0c326dd",
    "Thriller": "07251805-9cb0-4c39-9ea0-40e962459d81",
    "Isekai": "ace04907-f6dd-477c-910d-405e3d0d30c1",
    "Historical": "3bbac9a5-6346-4abf-b4f4-fd9a269e901c"
}

# --- USER MODEL ---
# --- USER MODEL ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # NEW FIELDS:
    username = db.Column(db.String(50), nullable=True)
    profile_pic = db.Column(db.String(500), nullable=True, default='https://ui-avatars.com/api/?name=User&background=ea580c&color=fff')

class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.String(100), nullable=False)
    manga_title = db.Column(db.String(255), nullable=False)
    cover_url = db.Column(db.String(500), nullable=False) 

class History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    manga_id = db.Column(db.String(100), nullable=False)
    manga_title = db.Column(db.String(255), nullable=False)
    cover_url = db.Column(db.String(500), nullable=False)
    chapter_id = db.Column(db.String(100), nullable=False)
    chapter_num = db.Column(db.String(50), nullable=True)
    last_read = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- AUTHENTICATION ROUTES ---

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user:
        flash('Email already exists!')
        return redirect(url_for('index'))

    # Hash the password for security
    new_user = User(
        email=email, 
        password=generate_password_hash(password, method='pbkdf2:sha256')
    )
    db.session.add(new_user)
    db.session.commit()
    
    login_user(new_user)
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        flash('Please check your login details and try again.')
        return redirect(url_for('index'))

    login_user(user)
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()

    if user:
        # Create a secure token for this email
        token = ts.dumps(email, salt='recover-key')
        # Redirect straight to the reset page (Option 1)
        return redirect(url_for('reset_with_token', token=token))
    else:
        flash("Email not found.", "error")
        return redirect(url_for('index'))
    
@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    try:
        # Check if the token is valid (expires in 30 mins)
        email = ts.loads(token, salt="recover-key", max_age=1800)
    except:
        flash("The reset link is invalid or has expired.", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        new_password = request.form.get('password')
        
        # Hash and Save
        user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
        db.session.commit()
        
        flash("Password updated successfully!", "success")
        return redirect(url_for('index'))

    return render_template('reset_password.html', token=token)

# --- MANGADEX ROUTES ---

@app.route('/bookmarks')
@login_required
def bookmarks():
    # Notice how these next two lines are pushed in!
    user_bookmarks = Bookmark.query.filter_by(user_id=current_user.id).all()
    return render_template('bookmarks.html', bookmarks=user_bookmarks)

@app.route('/api/bookmark', methods=['POST'])
# Notice we removed @login_required here!
def toggle_bookmark():
    # 1. Manually check if the user is logged in first
    if not current_user.is_authenticated:
        return jsonify({"error": "unauthorized"}), 401

    data = request.json
    manga_id = data.get('manga_id')
    manga_title = data.get('manga_title')
    cover_url = data.get('cover_url', '')

    if not manga_id:
        return jsonify({"error": "Missing manga ID"}), 400

    existing_bookmark = Bookmark.query.filter_by(user_id=current_user.id, manga_id=manga_id).first()

    if existing_bookmark:
        db.session.delete(existing_bookmark)
        db.session.commit()
        return jsonify({"status": "removed"})
    else:
        new_bookmark = Bookmark(
            user_id=current_user.id, 
            manga_id=manga_id, 
            manga_title=manga_title, 
            cover_url=cover_url
        )
        db.session.add(new_bookmark)
        db.session.commit()
        return jsonify({"status": "added"})
    
@app.route('/history')
@login_required
def history():
    # Fetch history and order it so the most recently read is at the top
    user_history = History.query.filter_by(user_id=current_user.id).order_by(History.last_read.desc()).all()
    return render_template('history.html', history=user_history)
    
@app.route('/')
def index():
    # 1. Fetch "Hot Updates" (Aligned to your new 36-card grid)
    params = {
        "limit": 20, 
        "includes[]": ["cover_art"],
        "contentRating[]": ["safe", "suggestive"] 
    }
    resp = requests.get(f"{API_URL}/manga", params=params).json()
    
    manga_data = []
    for m in resp.get('data', []):
        attrs = m['attributes']
        # Unified Title logic
        t_attr = attrs['title']
        title = t_attr.get('en') or next(iter(t_attr.values()), "Untitled")
        
        # Unified Cover logic (matches your search route)
        cover_file = next((r['attributes']['fileName'] for r in m.get('relationships', []) 
                         if r['type'] == 'cover_art' and 'attributes' in r), None)
        cover = f"https://uploads.mangadex.org/covers/{m['id']}/{cover_file}.256.jpg" if cover_file else ""

        # SYNCED DATA: Adding status and type for the card badges
        manga_data.append({
            "id": m['id'], 
            "title": title, 
            "cover": cover,
            "status": attrs.get('status', '').capitalize(),
            "type": "Manga" if attrs.get('originalLanguage') == 'ja' else "Manhwa/Manhua"
        })

    # 2. Fetch "Recommendations"
    rec_params = {
        "limit": 6, 
        "offset": 40,
        "includes[]": ["cover_art"],
        "contentRating[]": ["safe", "suggestive"]
    }
    rec_resp = requests.get(f"{API_URL}/manga", params=rec_params).json()
    
    rec_data = []
    for m in rec_resp.get('data', []):
        attrs = m['attributes']
        t_attr = attrs['title']
        title = t_attr.get('en') or next(iter(t_attr.values()), "Untitled")
        
        cover_file = next((r['attributes']['fileName'] for r in m.get('relationships', []) 
                         if r['type'] == 'cover_art' and 'attributes' in r), None)
        cover = f"https://uploads.mangadex.org/covers/{m['id']}/{cover_file}.256.jpg" if cover_file else ""

        rec_data.append({
            "id": m['id'], 
            "title": title, 
            "cover": cover,
            "status": attrs.get('status', '').capitalize(),
            "type": "Manga" if attrs.get('originalLanguage') == 'ja' else "Manhwa/Manhua"
        })

    return render_template('index.html', manga_list=manga_data, rec_list=rec_data, next_offset=20)

@app.route('/api/load-more-hot')
def load_more_hot():
    offset = request.args.get('offset', default=20, type=int)
    limit = 20
    
    # Call the MangaDex API with the dynamic offset
    params = {
        "limit": limit,
        "offset": offset,
        "includes[]": ["cover_art"],
        "contentRating[]": ["safe", "suggestive"]
    }
    
    try:
        resp = requests.get(f"{API_URL}/manga", params=params).json()
        
        manga_data = []
        for m in resp.get('data', []):
            attrs = m['attributes']
            t_attr = attrs['title']
            title = t_attr.get('en') or next(iter(t_attr.values()), "Untitled")
            
            cover_file = next((r['attributes']['fileName'] for r in m.get('relationships', []) 
                             if r['type'] == 'cover_art' and 'attributes' in r), None)
            cover = f"https://uploads.mangadex.org/covers/{m['id']}/{cover_file}.256.jpg" if cover_file else ""

            manga_data.append({
                "id": m['id'], 
                "title": title, 
                "cover": cover,
                "status": attrs.get('status', '').capitalize(),
                "type": "Manga" if attrs.get('originalLanguage') == 'ja' else "Manhwa/Manhua"
            })
            
        if not manga_data:
            return ""
            
        # Match your exact template file name and your 'manga_list' variable name
        return render_template('manga grid partial.html', manga_list=manga_data)
        
    except Exception as e:
        print(f"Database/API Error: {e}")
        return "", 500
    

@app.route('/manga/<id>')
def manga_details(id):
    # 1. Get the target language from the URL query parameters (default to 'en')
    target_lang = request.args.get('lang', 'en')

    try:
        # Fetch Manga Data SAFELY
        m_req = requests.get(f"{API_URL}/manga/{id}", params={"includes[]": ["cover_art", "author"]})
        if not m_req.ok:
            print(f"API Error fetching Manga {id}: {m_req.status_code}")
            return redirect('/')
            
        m_resp = m_req.json()
        m_data = m_resp.get('data', {})
        attr = m_data.get('attributes', {})
        links = attr.get('links', {})
        
        # 2. Extract available languages for the switcher menu
        available_langs = attr.get('availableTranslatedLanguages', [])
        if available_langs:
            available_langs.sort()
        
        # Safely get title and description
        title = attr.get('title', {}).get('en') or next(iter(attr.get('title', {}).values()), "Untitled")
        description = attr.get('description', {}).get('en', "No description available.")
        status = attr.get('status', 'Ongoing').capitalize()
        year = attr.get('year', 'Unknown')
        m_type = m_data.get('type', 'manga').capitalize()
        
        official_eng = "Yes" if links.get('eng') else "No"
        adult_content = "Yes" if attr.get('contentRating') in ['erotica', 'pornographic'] else "No"
        
        mal_id = links.get('mal')
        al_id = links.get('al')

        tags = [t['attributes']['name']['en'] for t in attr.get('tags', [])]
        tag_ids = [t['id'] for t in attr.get('tags', [])]

        # Handle Relationships (Cover and Author)
        cover_file = ""
        author_name = "Unknown"
        for rel in m_data.get('relationships', []):
            if rel['type'] == 'cover_art' and 'attributes' in rel:
                cover_file = rel['attributes'].get('fileName', "")
            if rel['type'] == 'author' and 'attributes' in rel:
                author_name = rel['attributes'].get('name', "Unknown")
        
        # Using the 512px version for a balance of quality and speed on the info page
        cover_url = f"https://uploads.mangadex.org/covers/{id}/{cover_file}.512.jpg" if cover_file else ""

        # 3. Fetch Chapters using the DYNAMIC target_lang (BULLETPROOF)
        c_params = {
            "limit": 500, 
            "translatedLanguage[]": [target_lang, "no"], 
            "order[chapter]": "desc",
            "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"]
        }
        
        c_request = requests.get(f"{API_URL}/manga/{id}/feed", params=c_params)
        raw_chapters = []
        
        if c_request.ok:
            c_resp = c_request.json()
            raw_chapters = c_resp.get('data', [])
        
        unique_chapters = []
        for chap in raw_chapters:
            num = chap['attributes'].get('chapter')
            chap['display_num'] = num if num else "Oneshot"
            unique_chapters.append(chap)

        # 4. Recommendations Logic (BULLETPROOF)
        rec_params = {"limit": 7, "includes[]": ["cover_art"], "contentRating[]": ["safe", "suggestive"]}
        if tag_ids:
            rec_params["includedTags[]"] = tag_ids[:3]
        
        recs_data = []
        rec_req = requests.get(f"{API_URL}/manga", params=rec_params)
        
        if rec_req.ok:
            recs_data = rec_req.json().get('data', [])

        # Fallback if no recommendations found with tags
        if not recs_data:
            if "includedTags[]" in rec_params: 
                del rec_params["includedTags[]"]
            rec_req2 = requests.get(f"{API_URL}/manga", params=rec_params)
            if rec_req2.ok:
                recs_data = rec_req2.json().get('data', [])

        recommendations = []
        for r in recs_data:
            if r['id'] == id: continue
            if len(recommendations) >= 6: break
            
            r_title = r['attributes']['title'].get('en') or next(iter(r['attributes']['title'].values()), "Untitled")
            r_cover_file = next((rel['attributes'].get('fileName') for rel in r.get('relationships', []) 
                               if rel['type'] == 'cover_art' and 'attributes' in rel), "")
            r_cover = f"https://uploads.mangadex.org/covers/{r['id']}/{r_cover_file}.256.jpg" if r_cover_file else ""
            
            # These fields are required for the new recommendation UI badges
            r_status = r['attributes'].get('status', '').capitalize()
            r_type = "Manga" if r['attributes'].get('originalLanguage') == 'ja' else "Manhwa/Manhua"
            
            recommendations.append({
                "id": r['id'], 
                "title": r_title, 
                "cover": r_cover, 
                "status": r_status, 
                "type": r_type
            })

        manga_info = {
            "id": id, "title": title, "desc": description, "cover": cover_url,
            "status": status, "author": author_name, "tags": tags,
            "year": year, "type": m_type, "official": official_eng,
            "adult": adult_content, "mal": mal_id, "al": al_id
        }
        
        is_bookmarked = False
        if current_user.is_authenticated:
            existing = Bookmark.query.filter_by(user_id=current_user.id, manga_id=id).first()
            if existing:
                is_bookmarked = True
        
        return render_template('manga.html', 
            manga=manga_info, 
            chapters=unique_chapters, 
            available_langs=available_langs,
            current_lang=target_lang,
            recs=recommendations,
            is_bookmarked=is_bookmarked
        )

    except Exception as e:
        print(f"CRITICAL ERROR IN MANGA DETAILS: {e}")
        return redirect('/')

@app.route('/search')
def search():
    # 1. Capture user inputs
    query = request.args.get('q', '').strip()
    statuses = request.args.getlist('status')
    types = request.args.getlist('type')
    
    # --- FIX: Convert tag names to UUIDs ---
    tag_names = request.args.getlist('tags')
    tag_ids = [TAGS_MAP[t] for t in tag_names if t in TAGS_MAP]
    # ---------------------------------------
    
    demographics = request.args.getlist('demographic')
    ratings = request.args.getlist('rating') or ["safe", "suggestive"]
    sort_by = request.args.get('sort', 'relevance')
    order_dir = request.args.get('order', 'desc')

    # --- PAGINATION LOGIC ---
    offset = int(request.args.get('offset', 0))
    limit = 36 # Your updated limit

    # Update discovery check to use our new tag_ids variable
    is_discovery = not any([query, statuses, types, tag_ids, demographics])

    # 2. Build params as a Dictionary
    params = {
        'limit': limit,
        'offset': offset,
        'includes[]': ['cover_art'],
        'contentRating[]': ratings,
        'includedTagsMode': 'OR'
    }

    if is_discovery:
        params['order[followedCount]'] = 'desc'
    else:
        actual_sort = sort_by
        if not query and sort_by == 'relevance':
            actual_sort = 'followedCount'
        
        params[f'order[{actual_sort}]'] = order_dir
        
        if query: params['title'] = query
        if statuses: params['status[]'] = statuses
        if types: params['originalLanguage[]'] = types
        # --- FIX: Use mapped IDs here ---
        if tag_ids: params['includedTags[]'] = tag_ids
        # --------------------------------
        if demographics: params['publicationDemographic[]'] = demographics

    manga_data = []
    try:
        # Debugging: this will print the clean URL with UUIDs so you can verify it works
        debug_url = requests.Request('GET', f"{API_URL}/manga", params=params).prepare().url
        print(f"--- ACTIVE SEARCH SIGNAL ---\nURL: {debug_url}\n------------------------")
        
        resp = requests.get(f"{API_URL}/manga", params=params).json()
        
        for m in resp.get('data', []):
            attrs = m['attributes']
            title = attrs['title'].get('en') or next(iter(attrs['title'].values()), "Untitled")
            
            cover_file = next((r['attributes']['fileName'] for r in m.get('relationships', []) 
                             if r['type'] == 'cover_art' and 'attributes' in r), None)
            cover = f"https://uploads.mangadex.org/covers/{m['id']}/{cover_file}.256.jpg" if cover_file else ""

            manga_data.append({
                "id": m['id'], 
                "title": title, 
                "cover": cover,
                "status": attrs.get('status', '').capitalize(),
                "type": "Manga" if attrs.get('originalLanguage') == 'ja' else "Manhwa/Manhua"
            })
    except Exception as e:
        print(f"Search API Error: {e}")

    # --- THE AJAX FIX ---
    # If the request comes from the "View More" button, only return the cards
    if request.args.get('ajax'):
        return render_template('manga grid partial.html', manga_list=manga_data)

    # Otherwise, return the full page as usual
    return render_template('search.html', 
                           manga_list=manga_data, 
                           all_tags=TAGS_MAP,
                           is_discovery=is_discovery,
                           selected_statuses=statuses,
                           selected_types=types,
                           selected_tags=tag_names, # Keep names for the checkboxes
                           selected_demographics=demographics,
                           selected_ratings=ratings,
                           current_sort=sort_by,
                           current_order=order_dir,
                           query=query,
                           next_offset=offset + limit)


@app.route('/setting', methods=['GET', 'POST'])
@login_required 
def setting():
    if request.method == 'POST':
        action = request.form.get('action')

        # --- GENERAL TAB SUBMISSION ---
        if action == 'update_general':
            new_email = request.form.get('email')
            new_username = request.form.get('username')
            new_pic = request.form.get('profile_pic')
            
            # Check if email is being changed to one that already exists
            if new_email and new_email != current_user.email:
                existing = User.query.filter_by(email=new_email).first()
                if existing:
                    flash("That email is already in use.", "error")
                    return redirect(url_for('setting'))
                current_user.email = new_email
                
            if new_username:
                current_user.username = new_username
            if new_pic:
                current_user.profile_pic = new_pic
                
            db.session.commit()
            flash("General settings updated successfully!", "success")

        # --- SECURITY TAB SUBMISSION ---
        elif action == 'update_security':
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            
            # Verify the old password first
            if not check_password_hash(current_user.password, old_password):
                flash("Incorrect old password. Changes denied.", "error")
            elif new_password:
                # If verified, hash and save the new password
                current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
                db.session.commit()
                flash("Password updated successfully!", "success")
            else:
                flash("Please enter a new password.", "error")

        return redirect(url_for('setting'))
        
    return render_template('setting.html')

@app.route('/random')
def random_manga():
    response = requests.get(f"{API_URL}/manga/random").json()
    manga_id = response['data']['id']
    return redirect(f"/manga/{manga_id}")

@app.route('/api/search_suggestions')
def search_suggestions():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])

    try:
        # 1. Fetch from MangaDex
        resp = requests.get(f"{API_URL}/manga", params={
            "title": query,
            "limit": 5,
            "includes[]": ["cover_art"]
        }).json()
        
        data = resp.get('data', [])
        results = [] # Defining 'results' here fixes the error!
        
        for manga in data:
            m_id = manga.get('id')
            attrs = manga.get('attributes', {})
            title = attrs.get('title', {}).get('en', '') or list(attrs.get('title', {}).values())[0]
            
            # Extract cover[cite: 2]
            cover_file = ""
            for rel in manga.get('relationships', []):
                if rel.get('type') == 'cover_art':
                    cover_file = rel.get('attributes', {}).get('fileName', '')
            
            cover_url = f"https://uploads.mangadex.org/covers/{m_id}/{cover_file}.256.jpg" if cover_file else ""
            
            results.append({
                "id": m_id,
                "title": title,
                "cover": cover_url
            })
        
        return jsonify(results)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify([])

@app.route('/reader/<chapter_id>')
def reader(chapter_id):
    try:
        # 1. Get current chapter info
        params = {"includes[]": ["manga"]}
        c_resp = requests.get(f"{API_URL}/chapter/{chapter_id}", params=params).json()
        c_data = c_resp.get('data', {})
        
        if not c_data:
            return redirect('/')

        # SYNC FIX: Detect the language of this specific chapter
        # This ensures the nav bar shows chapters in the same language
        chapter_lang = c_data.get('attributes', {}).get('translatedLanguage', 'en')
        
        manga_id = next((r['id'] for r in c_data.get('relationships', []) if r['type'] == 'manga'), None)
        attrs = c_data.get('attributes', {})
        current_num = attrs.get('chapter', '?')
        
        # Define current_display for your reader.html title tag
        current_display = attrs.get('title') or f"Episode {current_num}"

        # 2. Get Manga Title AND Cover Art
        m_resp = requests.get(f"{API_URL}/manga/{manga_id}", params={"includes[]": ["cover_art"]}).json()
        m_title = m_resp['data']['attributes']['title'].get('en') or next(iter(m_resp['data']['attributes']['title'].values()), "Untitled")

        # Extract the cover file
        cover_file = next((r['attributes']['fileName'] for r in m_resp['data'].get('relationships', []) if r['type'] == 'cover_art' and 'attributes' in r), None)
        manga_cover = f"https://uploads.mangadex.org/covers/{manga_id}/{cover_file}.256.jpg" if cover_file else ""

        # 3. Fetch all chapters for the nav bar (Language Synchronized)
        # Using the detected 'chapter_lang' instead of hardcoded 'en'
        feed_params = {
            "limit": 500, 
            "translatedLanguage[]": [chapter_lang, "no"], 
            "order[chapter]": "desc" 
        }
        f_resp = requests.get(f"{API_URL}/manga/{manga_id}/feed", params=feed_params).json()
        
        unique_chaps = []
        seen = set()
        for chap in f_resp.get('data', []):
            num = chap['attributes'].get('chapter')
            if num and num not in seen:
                unique_chaps.append({"id": chap['id'], "num": num, "display": f"Episode {num}"})
                seen.add(num)

        # Sort chapters back to ascending order for the dropdown UI
        unique_chaps.sort(key=lambda x: float(x['num']) if x['num'] and x['num'].replace('.','',1).isdigit() else 0)
        
        # 4. Calculate Prev and Next IDs
        prev_id = next_id = None
        for i, c in enumerate(unique_chaps):
            if c['id'] == chapter_id:
                if i > 0: prev_id = unique_chaps[i-1]['id']
                if i < len(unique_chaps) - 1: next_id = unique_chaps[i+1]['id']
                break

        # 5. Get images with Stable Host Override
        server_resp = requests.get(f"{API_URL}/at-home/server/{chapter_id}").json()
        chapter_info = server_resp.get('chapter', {})
        chapter_hash = chapter_info.get('hash')
        
        # Stable host for reliability in Vietnam
        base_url = "https://uploads.mangadex.org" 

        # Select path type: dataSaver vs original data
        filenames = chapter_info.get('dataSaver')
        if filenames:
            path_type = 'data-saver'
        else:
            filenames = chapter_info.get('data', [])
            path_type = 'data'
        
        if not chapter_hash or not filenames:
            return redirect(f"/manga/{manga_id}")

        # Construct Final URLs using the STABLE host
        image_urls = [f"{base_url}/{path_type}/{chapter_hash}/{f}" for f in filenames]
    
    # --- NEW: Check if it's already bookmarked ---
        is_bookmarked = False
        if current_user.is_authenticated:
            existing = Bookmark.query.filter_by(user_id=current_user.id, manga_id=manga_id).first()
            if existing:
                is_bookmarked = True

                # --- NEW: UPDATE READING HISTORY ---
            history_record = History.query.filter_by(user_id=current_user.id, manga_id=manga_id).first()
            if history_record:
                # If they already read this manga, just update to the latest chapter
                history_record.chapter_id = chapter_id
                history_record.chapter_num = current_num
            else:
                # If this is their first time reading this manga, create a new record
                new_history = History(
                    user_id=current_user.id,
                    manga_id=manga_id,
                    manga_title=m_title,
                    cover_url=manga_cover,
                    chapter_id=chapter_id,
                    chapter_num=current_num
                )
                db.session.add(new_history)
            
            db.session.commit()
            # -----------------------------------

    except Exception as e:
        print(f"CRITICAL ERROR IN READER: {e}")
        return redirect('/')
    
    return render_template('reader.html', 
        images=image_urls, 
        manga_title=m_title,
        manga_id=manga_id,
        manga_cover=manga_cover,
        current_num=current_num,
        current_display=current_display,
        all_chapters=unique_chaps,
        prev_id=prev_id,
        next_id=next_id,
        is_bookmarked=is_bookmarked
    )

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# --- STARTUP ---
# 1. Place this AFTER all your models and routes are defined!
with app.app_context():
    db.create_all()

# 2. This remains at the very end
if __name__ == '__main__':
    app.run(debug=True)