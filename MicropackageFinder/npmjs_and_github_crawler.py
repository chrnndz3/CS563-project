import bs4
import pandas
import requests

# Initialized variables
count = 1
username = "chrnndz3"
password = "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"

""" Returns the number of source code in a single js file
@code_rows: 
"""
def count_line_number(js_bs4tree):
    code_repo = js_bs4tree.find('table', {'class': 'js-file-line-container'})
    code_rows = code_repo.findAll('td', {'class':'js-file-line'})
    result = 0
    for i in code_rows:
        row_items = i.findChildren()
        if not row_items:
            continue
        result += 1 if row_items[0]["class"][0] != 'pl-c' else 0
    return result

# Crawler for npmjs
def crawler(package_name, npm_url):
    github_url = None
    npmjs_url = str(npm_url)

    try:
        npmjs_request = requests.get(npmjs_url, headers={'User-Agent': 'Chrome/35.0.1916.47'}).text
        npm_bs = bs4.BeautifulSoup(npmjs_request, 'html.parser')
        body = npm_bs.find('body')
        divs = body.find_all("div", {"class": "_702d723c dib w-50 bb b--black-10 pr2 w-100"})

        for div in divs:
            if div.find('h3', text='Repository'):
                a = div.find('a')
                github_url = str(a['href'])
                print("[Info] Github link: " + github_url)
    except:
        print('[Error] while crawling npmjs for package: ' + package_name + ' and url: ' + npmjs_url)
        return github_url

    return github_url


# Main method
def main(df):
    for index, row in df.iterrows():
        package_name = row['name']
        npmjs_url = row['npm-url']
        # Retrieve github url from npmjs url
        github_url = crawler(package_name, npmjs_url)
        github_url_request = requests.get(github_url)

        # Check the github link works and hasn't been deprecated
        if 200 == github_url_request.status_code:
            user_repo = github_url.replace('https://github.com/', '')
            github_url_repos = "https://api.github.com/repos/" + user_repo
            github_url_repos_data = requests.get(github_url_repos, auth=(username, password)).json()

            if "default_branch" not in github_url_repos_data:
                print("[Info] Default branch doesn't exist for: " + package_name)
                continue
            else:
                default_branch = github_url_repos_data["default_branch"]
                github_url_trees = "https://api.github.com/repos/" + user_repo + "/git/trees/" + default_branch + "?recursive=1"

                # retrieve the data in json
                github_url_trees_data = requests.get(github_url_trees, auth=(username, password)).json()
                tree_array = github_url_trees_data['tree'] if ("tree" in github_url_trees_data) else print(
                    "[Error] Tree array doesn't exist in: " + github_url_trees)

                # only retrieve the javascript files from a repo
                js_paths = []
                for object in tree_array:
                    path = object['path']
                    if path.endswith('.js'):
                        js_paths.append(path)

                for js_path in js_paths:
                    github_url_contents = "https://api.github.com/repos/" + user_repo + "/contents/" + js_path
                    data_contents = requests.get(github_url_contents, auth=(username, password)).json()
                    download_url = data_contents['download_url'] if ("download_url" in data_contents) else print(
                        "[Error] Download url doesn't exists for: " + github_url_contents)
                    download_url_request = requests.get(download_url, auth=(username, password))
                    js_file_content = download_url_request.text

                    js_file_bs4tree = bs4.BeautifulSoup(js_file_content, 'html.parser')
                    print(count_line_number(js_file_bs4tree))
                    # TODO: Parse the file content to get the number of lines
                    # print(file_content)
                    # break
        else:
            print("[Error] Github url " + github_url + " is not working, status code is: " + github_url_request.status_code)

        print("[Info] Done with package: " + package_name)
        break


if __name__ == "__main__":
    df = pandas.read_csv('package-names.csv', names=['name', 'npm-url'])
    main(df)
    print('[Info] Program has completed.')
