# MangaLocal Reader

A high-performance manga reader built with **Flask** and the **MangaDex API**.

## Features
* **Language Switcher**: Dynamically switch between English, Vietnamese, and other available translations.
* **Double-Fetch Logic**: Optimized to fetch both the latest and earliest chapters for long-running series.
* **Live Search**: Real-time manga suggestions as you type.
* **Stable Image Hosting**: Configured with stable host overrides for reliable loading in Vietnam.

## Local Setup
1. Clone the repo: `git clone https://github.com/khanghpm/MangaLocal.git`
2. Install dependencies: `pip install -r requirements.txt`
3. Initialize Database: `python app.py` (Creates `users.db` automatically)
4. Open `http://127.0.0.1:5000`
