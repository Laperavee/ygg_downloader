import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
from assets import headers, cookies

app = Flask(__name__)

def fetch_page_content(url):
    response = requests.get(url, headers=headers, cookies=cookies)
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
    response = requests.get(link, headers=headers, cookies=cookies)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        results_divs = soup.find_all("table", {"class": "infos-torrent"})

        if results_divs:
            download_link = None
            for table in results_divs:
                download_cell = table.find('a', class_='butt')
                if download_cell:
                    download_link = download_cell['href']
                    break
            if download_link:
                print("Lien de téléchargement:", download_link)
                return download_link
            else:
                print("Lien de téléchargement non trouvé.")
                return None
        else:
            print("Aucun tableau d'infos de torrent trouvé.")
            return None
    else:
        print(f"Erreur lors de la requête: {response.status_code}")
        return None

@app.route('/call_function/<path:link>', methods=['GET'])
def call_function(link):
    download_torrent(link)
    return jsonify({"message": f"Fonction exécutée pour: {link}"})

if __name__ == '__main__':
    app.run(debug=True)
