import bs4
import pandas
import requests

# Initialized variables
count = 1
token = "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"

""" Returns the number of source code in a single js file
@code_rows: 
"""


def count_line_number(js_bs4tree):
    code_repo = js_bs4tree.find('table', {'class': 'js-file-line-container'})
    code_rows = code_repo.findAll('td', {'class': 'js-file-line'})
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


def check_github_url(package_name, github_url):
    try:
        if (github_url is not None) and ("github.com" in github_url):
            return True
    except:
        print("[Info] Issue with " + package_name + " github url: " + str(github_url))

    return False


# Main method
def main(df):
    for index, row in df.iterrows():
        package_name = row['name']
        npmjs_url = row['npm-url']

        # Retrieve github url from npmjs url
        github_url = crawler(package_name, npmjs_url)
        github_url_exists = check_github_url(package_name, github_url)

        # Check the github link works and hasn't been deprecated
        if github_url_exists:
            user_repo = github_url.replace('https://github.com/', '')
            github_url_repos = "https://api.github.com/repos/" + user_repo
            headers = {'Authorization': 'access_token %s' % token}
            github_url_repos_request = requests.get(github_url_repos, headers=headers)

            try:
                if "200" != str(github_url_repos_request.status_code):
                    print("[Info] Github API is not 200 for: " + package_name + " " + str(github_url_repos_request.status_code))
                    print("[Info] " + github_url_repos_request.text)
                    continue
                else:
                    github_url_repos_data = requests.get(github_url_repos, headers=headers).json()
                    default_branch = github_url_repos_data["default_branch"] if (
                            "default_branch" in github_url_repos_data) else print(
                        "[Error] Default branch doesn't exist for: " + package_name)
                    github_url_trees = "https://api.github.com/repos/" + user_repo + "/git/trees/" + default_branch + "?recursive=1"

                    # retrieve the data in json
                    github_url_trees_data = requests.get(github_url_trees, headers=headers).json()
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
                        data_contents = requests.get(github_url_contents, headers=headers).json()
                        download_url = data_contents['download_url'] if ("download_url" in data_contents) else print(
                            "[Error] Download url doesn't exists for: " + github_url_contents)
                        download_url_request = requests.get(download_url, headers=headers)
                        js_file_content = download_url_request.text

                        # js_file_bs4tree = bs4.BeautifulSoup(js_file_content, 'html.parser')
                        # print(count_line_number(js_file_bs4tree))
            except:
                print("[Error] Issue with the following package: " + package_name)
                continue
            break
            # print("[Info] Done with package: " + package_name)
            # break
        else:
            print("[Skip] Github link doesn't exist for: " + package_name)
            break


if __name__ == "__main__":
    df = pandas.read_csv('package-names.csv', names=['name', 'npm-url'])
    main(df)
    print('[Info] ----- Program has completed -----')
