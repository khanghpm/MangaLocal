import requests
from itsdangerous import URLSafeTimedSerializer
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
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

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

    return render_template('index.html', manga_list=manga_data, rec_list=rec_data)

@app.route('/manga/<id>')
def manga_details(id):
    # 1. Get the target language from the URL query parameters (default to 'en')
    target_lang = request.args.get('lang', 'en')

    # Fetch Manga Data
    m_resp = requests.get(f"{API_URL}/manga/{id}", params={"includes[]": ["cover_art", "author"]}).json()
    m_data = m_resp.get('data', {})
    attr = m_data.get('attributes', {})
    links = attr.get('links', {})
    
    # 2. Extract available languages for the switcher menu
    available_langs = attr.get('availableTranslatedLanguages', [])
    # Sort them alphabetically for the dropdown
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

    # 3. Fetch Chapters using the DYNAMIC target_lang
    c_params = {
        "limit": 500, 
        "translatedLanguage[]": [target_lang], 
        "order[chapter]": "desc",
        #"includeExternalUrl": "1",
        "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"] # <--- ADD THIS LINE
    }
    c_resp = requests.get(f"{API_URL}/manga/{id}/feed", params=c_params).json()

   # --- THE DEBUG TRIPLE-CHECK ---
    req = requests.Request('GET', f"{API_URL}/manga/{id}/feed", params=c_params).prepare()
    print(f"--- DEBUG: FULL API URL: {req.url} ---")
    
    c_resp = requests.get(f"{API_URL}/manga/{id}/feed", params=c_params).json()
    raw_chapters = c_resp.get('data', [])
    print(f"--- DEBUG: API found {len(raw_chapters)} chapters for lang: {target_lang} ---")
    
    raw_chapters = c_resp.get('data', [])
    unique_chapters = []
    seen_numbers = set()

    for chap in raw_chapters:
        num = chap['attributes'].get('chapter')
        if num not in seen_numbers:
            # Add a helper for the template to show "Oneshot" if the number is null
            chap['display_num'] = num if num else "Oneshot"
            unique_chapters.append(chap)
            seen_numbers.add(num)

    # Recommendations Logic
    rec_params = {"limit": 7, "includes[]": ["cover_art"], "contentRating[]": ["safe", "suggestive"]}
    if tag_ids:
        rec_params["includedTags[]"] = tag_ids[:3]
    
    rec_resp = requests.get(f"{API_URL}/manga", params=rec_params).json()
    recs_data = rec_resp.get('data', [])

    if not recs_data:
        if "includedTags[]" in rec_params: del rec_params["includedTags[]"]
        rec_resp = requests.get(f"{API_URL}/manga", params=rec_params).json()
        recs_data = rec_resp.get('data', [])

    recommendations = []
    for r in recs_data:
        if r['id'] == id: continue
        if len(recommendations) >= 6: break
        
        r_title = r['attributes']['title'].get('en') or next(iter(r['attributes']['title'].values()), "Untitled")
        r_cover_file = next((rel['attributes'].get('fileName') for rel in r.get('relationships', []) 
                           if rel['type'] == 'cover_art' and 'attributes' in rel), "")
        r_cover = f"https://uploads.mangadex.org/covers/{r['id']}/{r_cover_file}.256.jpg" if r_cover_file else ""
        
        recommendations.append({"id": r['id'], "title": r_title, "cover": r_cover})

    manga_info = {
        "id": id, "title": title, "desc": description, "cover": cover_url,
        "status": status, "author": author_name, "tags": tags,
        "year": year, "type": m_type, "official": official_eng,
        "adult": adult_content, "mal": mal_id, "al": al_id
    }
    
    return render_template('manga.html', 
        manga=manga_info, 
        chapters=unique_chapters, 
        available_langs=available_langs, # New variable for HTML
        current_lang=target_lang,        # New variable for HTML
        recs=recommendations
    )

@app.route('/search')
def search():
    # 1. Capture user inputs
    query = request.args.get('q', '').strip()
    statuses = request.args.getlist('status')
    types = request.args.getlist('type')
    tags = request.args.getlist('tags')
    demographics = request.args.getlist('demographic')
    ratings = request.args.getlist('rating') or ["safe", "suggestive"]
    sort_by = request.args.get('sort', 'relevance')
    order_dir = request.args.get('order', 'desc')

    # --- PAGINATION LOGIC ---
    offset = int(request.args.get('offset', 0))
    limit = 36 # Your updated limit

    is_discovery = not any([query, statuses, types, tags, demographics])

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
        if tags: params['includedTags[]'] = tags
        if demographics: params['publicationDemographic[]'] = demographics

    manga_data = []
    try:
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
                           selected_tags=tags,
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
        new_email = request.form.get('email')
        new_password = request.form.get('password')
        
        # Email Update
        if new_email and new_email != current_user.email:
            current_user.email = new_email
            
        # Password Update
        if new_password:
            current_user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
            
        db.session.commit()
        flash("Settings updated successfully!", "success")
        return redirect(url_for('setting'))
        
    # --- CRITICAL MISSING LINE FROM YOUR SCREENSHOT ---
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

        # 2. Get Manga Title
        m_resp = requests.get(f"{API_URL}/manga/{manga_id}").json()
        m_title = m_resp['data']['attributes']['title'].get('en') or next(iter(m_resp['data']['attributes']['title'].values()), "Untitled")

        # 3. Fetch all chapters for the nav bar (Language Synchronized)
        # Using the detected 'chapter_lang' instead of hardcoded 'en'
        feed_params = {
            "limit": 500, 
            "translatedLanguage[]": [chapter_lang], 
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
        
    except Exception as e:
        print(f"CRITICAL ERROR IN READER: {e}")
        return redirect('/')
    
    return render_template('reader.html', 
        images=image_urls, 
        manga_title=m_title,
        manga_id=manga_id,
        current_num=current_num,
        current_display=current_display,
        all_chapters=unique_chaps,
        prev_id=prev_id,
        next_id=next_id
    )

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

# --- STARTUP ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Automatically creates the database file
    app.run(debug=True, port=5000)
