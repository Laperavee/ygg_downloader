from flask import Flask, render_template, request, jsonify, Response
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from assets import headers, cookies, proxy

app = Flask(__name__)

def fetch_page_content(url):
    response = requests.get(url, headers=headers, cookies=cookies, proxies=proxy)
    if response.status_code == 200:
        return response.content
    else:
        print(f"Erreur lors de la requête: {response.status_code}")
        return None

def parse_torrent_info(soup):
    results_divs = soup.find_all("div", {"class": "table-responsive results"})
    all_info = []
    for div in results_divs:
        tr_elements = div.find_all("tr")
        for tr in tr_elements:
            title_element = tr.find("a", id="torrent_name")
            if title_element:
                link = quote(title_element["href"], safe=":/+")
                title = title_element.text.strip()
                comments = tr.find_all("td")[3].text.strip()
                age = tr.find_all("td")[4].text.strip()
                size = tr.find_all("td")[5].text.strip()
                completed = tr.find_all("td")[6].text.strip()
                seeders = tr.find_all("td")[7].text.strip()
                leechers = tr.find_all("td")[8].text.strip()

                all_info.append({
                    "title": title,
                    "link": link,
                    "comments": comments,
                    "age": age,
                    "size": size,
                    "seeders": seeders,
                    "leechers": leechers,
                    "completed": completed
                })
    return all_info

def define_type_id(index):
    if index == 0:
        return None
    elif index == 1:
        return 2178
    elif index == 2:
        return 2179

@app.route('/')
def index():
    return render_template('form.html')

@app.route('/search', methods=['POST'])
def search():
    title = request.json.get('title')
    type = int(request.json.get('type'))
    type_id = define_type_id(type)
    if type_id is None:
        url = f"https://www.ygg.re/engine/search?name={title}&category=2145&do=search"
    else:
        url = f"https://www.ygg.re/engine/search?name={title}&category=2145&sub_category={type_id}&do=search"
    content = fetch_page_content(url)
    if content:
        soup = BeautifulSoup(content, "html.parser")
        all_info = parse_torrent_info(soup)
        sorted_info = sorted(all_info, key=lambda x: int(x['completed']), reverse=True)[:5]
        return jsonify({"results": sorted_info})
    return jsonify({"error": "Aucun résultat trouvé"})

def download_torrent(link):
    response = requests.get(link, headers=headers, cookies=cookies, proxies=proxy)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        download_link = soup.find("a", class_="butt")["href"] if soup.find("a", class_="butt") else None
        title_element = soup.find("h1")
        title = title_element.text.strip() if title_element else "torrent"
        print(f"Titre obtenu: {title}")
        if download_link:
            full_download_link = f"https://www.ygg.re{download_link}" if not download_link.startswith(
                "http") else download_link
            return full_download_link, title
        else:
            print("Lien de téléchargement non trouvé.")
            return None, title
    else:
        print(f"Erreur lors de la requête: {response.status_code}")
        return None, "torrent"

@app.route('/get_torrent_link', methods=['GET'])
def get_torrent_link():
    url = request.args.get('url')
    if url:
        download_link, title = download_torrent(url)
        if download_link:
            print("Before sending : ",{"download_link": download_link, "title": title})
            return jsonify({"download_link": download_link, "title": title})
        else:
            return jsonify({"error": "Erreur lors de l'obtention du lien de téléchargement."}), 500
    else:
        return jsonify({"error": "URL non spécifiée."}), 400

@app.route('/proxy')
@app.route('/proxy')
def proxy_request():
    target_url = request.args.get('url')
    title = request.args.get('title')
    if not target_url:
        return "URL non spécifiée", 400
    if not title:
        return "Titre non spécifié", 400
    try:
        response = requests.get(target_url, headers=headers, cookies=cookies, proxies=proxy)
        if response.status_code == 200:
            filename = f"{title}.torrent"
            return Response(
                response.content,
                headers={
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'application/x-bittorrent'
                }
            )
        else:
            return f"Erreur lors de la connexion au proxy: {response.status_code}", 500
    except Exception as e:
        return str(e), 500
@app.route('/call_function/<path:link>', methods=['GET'])
def call_function(link):
    download_torrent(link)
    return jsonify({"message": f"Fonction exécutée pour: {link}"})

if __name__ == '__main__':
    app.run(debug=True)
