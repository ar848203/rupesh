from flask import Flask, render_template, request
import requests
import time

app = Flask(__name__)

API_BASE = "https://api.khanglobalstudies.com"

# Function to get fresh auth token
def get_auth_token():
    login_url = f"{API_BASE}/cms/login"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "okhttp/3.9.1"
    }
    data = {
        "phone": "9661880780",
        "password": "rupesh@123"
    }

    response = requests.post(login_url, headers=headers, data=data)

    if response.status_code == 200:
        token = response.json().get('token')
        return f"Bearer {token}"
    else:
        print("Failed to get token:", response.text)
        return None

# Get lessons using fresh token
def get_lessons(course_id):
    token = get_auth_token()
    if not token:
        return []

    url = f"{API_BASE}/cms/user/courses/{course_id}/v2-lessons"
    headers = {"Authorization": token}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()
    else:
        return []

# Home page: Show all courses
# Home page: Show all courses
@app.route('/')
def home():
    import json
    with open('course.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    courses = []
    for item in data['data']:
        courses.append({
            "id": item['id'],
            "title": item['title'],
            "image": item['image']['large'] if 'image' in item and item['image'] else ''
        })

    return render_template('home.html', courses=courses)

@app.route('/view-pdf')
def view_pdf():
    pdf_url = request.args.get('url')
    return render_template('pdfview.html', pdf_url=pdf_url)

# When user clicks on a course
@app.route('/course/<int:course_id>')
def course(course_id):
    lessons = get_lessons(course_id)
    return render_template('lessons.html', lessons=lessons)

# Lesson details
@app.route('/lesson/<int:lesson_id>')
def lesson_details(lesson_id):
    token = get_auth_token()
    if not token:
        return "Failed to get token", 500

    # Remove Bearer from token
    clean_token = token.replace('Bearer ', '')
    api_url = f"https://madxabhi-4dfdf4ed1663.herokuapp.com/lesson_id?cid={lesson_id}&token={clean_token}"

    response = requests.get(api_url, timeout=10)
    data = response.json()

    def fix_url(url):
        if not url:
            return ""

        capital_mapping = {
            'A': 'P', 'B': 'Q', 'C': 'R', 'D': 'y', 'E': 'z', 'F': 'U', 'G': 'V', 'H': 'W',
            'I': 'd', 'J': 'e', 'K': 'f', 'L': 'X', 'M': 'Y', 'N': 'Z', 'O': 'D', 'P': 'E',
            'Q': 'F', 'R': 'G', 'S': 'H', 'T': 'L', 'U': 's', 'V': 't', 'W': 'u', 'X': 'v',
            'Y': 'w', 'Z': 'x'
        }
        small_mapping = {
            'a': 'M', 'b': 'N', 'c': 'O', 'd': 'S', 'e': 'T', 'f': 'a', 'g': 'b', 'h': 'c',
            'i': 'A', 'j': 'B', 'k': 'C', 'l': 'g', 'm': 'h', 'n': 'i', 'o': 'j', 'p': 'k',
            'q': 'I', 'r': 'J', 's': 'K', 't': 'l', 'u': 'm', 'v': 'n', 'w': 'o', 'x': 'p',
            'y': 'q', 'z': 'r'
        }

        translated = ''
        for ch in url:
            if ch in capital_mapping:
                translated += capital_mapping[ch]
            elif ch in small_mapping:
                translated += small_mapping[ch]
            else:
                translated += ch
        return translated

    # PDFs
    pdfs = []
    for item in data['notes']:
        if item['type'] == 'pdf':
            pdfs.append({
                'name': item['name'],
                'published_at': item['published_at'],
                'pdf_url': fix_url(item['video_url'])  # Ensure the pdf_url is processed correctly
            })

    # Videos
    videos = []
    for item in data['videos']:
        if item['type'] in ['yt', 'kgs']:
            video_pdfs = []
            # Safely handle None value for 'pdfs'
            pdfs_data = item.get('pdfs', [])
            if pdfs_data:
                for pdf_item in pdfs_data:
                    video_pdfs.append({
                        'url': pdf_item.get('url') # Ensure the URL for PDFs is processed correctly
                    })
            videos.append({
                'name': item['name'],
                'published_at': item['published_at'],
                'video_url': fix_url(item['video_url']),  # Ensure the video URL is processed correctly
                'thumb': item.get('thumb', ''),
                'pdfs': video_pdfs,  # Added PDFs related to each video
                'type': item.get('type', '')
            })

    return render_template('lesson_detail.html', lesson=data, pdfs=pdfs, videos=videos)

# Player
@app.route('/player/<path:video_id>')
def player(video_id):
    video = video_id
    if not video:
        return "Video not found", 404
    return render_template('player.html', video=video)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
