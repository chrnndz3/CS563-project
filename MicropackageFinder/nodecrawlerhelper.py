from urllib.request import urlopen, Request
import time, re

# Just checking if dependencies are already installed
def install_and_import(package):
    import importlib
    try:
        importlib.import_module(package)
    except ImportError:
        import pip
        pip.main(['install', package])
    finally:
        globals()[package] = importlib.import_module(package)

def count_line_number(code_rows):
    result = 0
    for i in code_rows:
        row_items = i.findChildren()
        if not row_items:
            continue
        result += 1 if row_items[0]["class"][0] != 'pl-c' else 0
    return result


# Install dependencies if necessary
install_and_import("bs4")
install_and_import("pandas")

LINE_THRESHOLD = 50

df = pandas.read_csv('package-names.csv', names=['name', 'npm-url'])

for index, row in df.iterrows():
    try:
        npm_html = urlopen(Request(row['npm-url'], headers={'User-Agent': 'Chrome/35.0.1916.47'}))
        npm_bs4tree = bs4.BeautifulSoup(npm_html, 'html.parser')
        github_link = npm_bs4tree.find('a', {'target': '_blank'}).findChildren()[-1].text
    except: 
        print('Error at npm parsing')
        continue

    if not github_link:
        continue

    try:
        github_url = "https://www." + github_link
        github_html = urlopen(Request(github_url, headers={'User-Agent': 'Chrome/35.0.1916.47'}))
        github_bs4tree = bs4.BeautifulSoup(github_html, 'html.parser')
        line_count = 0
        for link in github_bs4tree.findAll('a', {'class': 'js-navigation-open'}):
            file_url = "https://www.github.com" + link['href']
            if not re.search("\.js$",file_url):
                continue
            file_html = urlopen(Request(file_url, headers={'User-Agent': 'Chrome/35.0.1916.47'}))
            file_bs4tree = bs4.BeautifulSoup(file_html, 'html.parser')
            code_repo = file_bs4tree.find('table', {'class': 'js-file-line-container'})
            line_count += count_line_number(code_repo.findAll('td', {'class':'js-file-line'}))
            if line_count >= LINE_THRESHOLD:
                print("This is NOT a Micropackage " + github_url)
                break
        if line_count < LINE_THRESHOLD:
            print("This is a Micropackage " + github_url)
    except:
        print('Error at Github parsing')
        continue