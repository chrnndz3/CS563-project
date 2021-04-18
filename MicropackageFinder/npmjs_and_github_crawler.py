import json
import os
import traceback

import bs4
import pandas
import requests

# Initialized variables
count = 1
username = 'chrnndz3'
token = "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"

""" Returns the number of source code in a single js file
@code_rows: 
"""
MICROPACKAGE_LINE_THRESHOLD = 50


def count_line_number(js_file):
    # TODO Exclude comments
    result = 0
    line_length = 0
    for i in range(len(js_file)):
        line_length += 1
        if (js_file[i] == '\\' and js_file[i + 1] == '\\') or (js_file[i] == '\n' and line_length == 1):
            while js_file[i] != '\n':
                i += 1
            line_length = 0
        if js_file[i] == '\n' and line_length > 2:
            result += 1
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
        traceback.print_exc()
        return github_url

    return github_url


def check_github_url(package_name, github_url):
    try:
        if (github_url is not None) and ("github.com" in github_url):
            return True
    except:
        print("[Error] Issue with " + package_name + " github url: " + str(github_url))
        traceback.print_exc()

    return False


# Main method
def main(df):
    for index, row in df.iterrows():
        package_name = row['name']
        npmjs_url = row['npm-url']
        line_count = 0

        # Retrieve github url from npmjs url
        github_url = crawler(package_name, npmjs_url)
        github_url_exists = check_github_url(package_name, github_url)

        # Check the github link works and hasn't been deprecated
        if github_url_exists:
            user_repo = github_url.replace('https://github.com/', '')
            github_url_user_repo = "https://api.github.com/repos/" + user_repo
            headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
            github_url_repos_request = requests.get(github_url_user_repo, headers=headers)

            try:
                if "200" != str(github_url_repos_request.status_code):
                    print("[Info] Github API is not 200 for: " + package_name + " " + str(
                        github_url_repos_request.status_code))
                    print("[Info] " + github_url_repos_request.text)
                    continue
                else:
                    github_url_repos_data = requests.get(github_url_user_repo, headers=headers).json()
                    default_branch = github_url_repos_data["default_branch"] if (
                            "default_branch" in github_url_repos_data) else print(
                        "[Error] Default branch doesn't exist for: " + package_name)
                    github_url_trees = github_url_user_repo + "/git/trees/" + default_branch + "?recursive=1"

                    # retrieve the data in json
                    github_url_trees_data = requests.get(github_url_trees, headers=headers).json()
                    tree_array = github_url_trees_data['tree'] if ("tree" in github_url_trees_data) else print(
                        "[Error] Tree array doesn't exist in: " + github_url_trees)

                    # Only retrieve the javascript files from a repo
                    # TODO: Should we also include extension '.ts'?
                    js_paths = []
                    for object in tree_array:
                        path = object['path']
                        if path.endswith('.js'):
                            js_paths.append(path)

                    if len(js_paths) == 0:
                        break

                    # Go into each javascript file to get the total number of code lines
                    for js_path in js_paths:
                        github_url_content = github_url_user_repo + "/contents/" + js_path
                        data_contents = requests.get(github_url_content, headers=headers).json()
                        download_url = data_contents['download_url'] if ("download_url" in data_contents) else print(
                            "[Error] Download url doesn't exists for: " + github_url_content)
                        download_url_request = requests.get(download_url, headers=headers)
                        js_file_content = download_url_request.text
                        line_count += count_line_number(js_file_content)

                        if line_count > MICROPACKAGE_LINE_THRESHOLD:
                            break

                    # Append the package with the status of the package (either it's micropackage or not)
                    if line_count <= MICROPACKAGE_LINE_THRESHOLD:
                        print("[Info] " + package_name + " is a micropackage, total number of code lines: " + str(line_count))
                        micropackage_csv.write(package_name + ", " + "Micropackage\n")
                    else:
                        print("[Info] " + package_name + " is NOT a micropackage")
                        micropackage_csv.write(package_name + ", " + "Not\n")

                    # break
            except:
                print("[Error] Issue with the following package: " + package_name)
                traceback.print_exc()

            print("[Info] Done with package: " + package_name)
        else:
            print("[Skip] Github link doesn't exist for: " + package_name)
        # break


if __name__ == "__main__":
    df = pandas.read_csv('package-names.csv', names=['name', 'npm-url'])
    micropackage_csv = open("../MicropackageFinder/micropackage.csv", "w+")
    main(df)
    micropackage_csv.close()
    print('[Info] ----- Program has completed -----')
