import json
import traceback

import requests as requests
from bs4 import BeautifulSoup

# Initialized variables
registry_url = 'https://registry.npmjs.com/'
replicate_url = 'https://replicate.npmjs.com/'
npmjs_url = 'https://www.npmjs.com/package/'
top_ten_packages_list = ["lodash", "chalk", "request", "commander", "react", "express", "debug", "async", "fs-extra",
                         "moment"]
# top_ten_packages_list = ["request"]
file = open("../TopTen_DependencyCollaborators/top_ten_packages_details.json", "w")
file2 = open("../TopTen_DependencyCollaborators/top_ten_packages_average.json", "w")


# Crawler for npmjs
def crawler(package_name):
    # print("Going to crawl " + package_name)
    collaborators_list = []
    url = npmjs_url + package_name

    try:
        npmjs_request = requests.get(url, headers={'User-Agent': 'Chrome/35.0.1916.47'}).text
        npm_bs = BeautifulSoup(npmjs_request, 'html.parser')
        body = npm_bs.find('body')
        # collaborators_div = body.find_all("div", {"class": "w-100"})
        collaborators_div = body.find("ul", {"class": "list pl0 cf"})

        for li in collaborators_div:
            a = li.find('a')
            username = str(a['href']).replace('/~', '')
            collaborators_list.append(username)
    except:
        print('[Error] while crawling npmjs for package: ' + package_name + ' and url: ' + url)
        print("body ------ " + str(body))
        traceback.print_exc()
        return collaborators_list

    return collaborators_list


def metadata_extraction(package_name):
    error = "{\"error\":\"not_found\",\"reason\": \"missing\"}"

    url = replicate_url + package_name
    replicate_request = requests.get(url)
    # Converts data to a json object
    data = replicate_request.json()

    if "error" in data:
        print("There's no data in the replicate endpoint for " + package_name + ". Checking registry endpoint.")

        url = registry_url + package_name
        registry_request = requests.get(registry_url + package_name)
        # Converts data to a json object
        data = registry_request.json()

    try:
        # dist_tags contains the latest version this package is on
        dist_tags = data["dist-tags"]
        latest_version = dist_tags["latest"]

        # versions is a map of all the previous versions along with the data for each version
        versions = data["versions"]
        version_data = versions[latest_version]
    except:
        print("URL: " + url)
        print('[Error] at metadata_extraction_dependencies while retrieving data from ' + package_name)
        traceback.print_exc()

    # ----- Dependencies -----
    dependencies = version_data["dependencies"] if ("dependencies" in version_data) else None

    # ----- Dev Dependencies -----
    dev_dependencies = version_data["devDependencies"] if ("devDependencies" in version_data) else None

    # Crawl npmjs URL
    collaborator_list = crawler(package_name)

    # ----- Create Map of all relevant information for the top 10 packages -----
    package_map = {"package_name": package_name, "version": latest_version,
                   "collaborators": len(collaborator_list), "dependencies": dependencies,
                   "dev_dependencies": dev_dependencies}

    return package_map


def create_dependency_map(transitive_dependencies):
    total_collaborators = 0
    dependencies_map = {}

    if (transitive_dependencies is None) or (len(transitive_dependencies) == 0):
        # dependencies_map["average_collaborators"] = 0
        return None
    else:
        size = len(transitive_dependencies)
        # print("transitive_dependencies -----" + str(transitive_dependencies))

        for item in transitive_dependencies.items():
            dependency_name = item[0]

            # Crawl npmjs URL
            collaborators_list = crawler(dependency_name)

            # ----- Create Map of all relevant information for the top 10 packages -----
            package_map = {"collaborators": len(collaborators_list)}
            total_collaborators += len(collaborators_list)
            dependencies_map[dependency_name] = package_map

        dependencies_map["total_collaborators"] = total_collaborators
        dependencies_map["total_dependencies"] = size
        dependencies_map["average_collaborators"] = (total_collaborators / size)

    return dependencies_map


# Main method
def main():
    count = 0
    for package_name in top_ten_packages_list:
        package_map = metadata_extraction(package_name)

        # Get all the dependencies from the top 10 packages
        transitive_dependencies = package_map.get("dependencies")
        dev_transitive_dependencies = package_map.get("dev_dependencies")

        full_package_map = {"package_name": package_map["package_name"], "version": package_map["version"],
                            "collaborators": package_map["collaborators"], "dependencies": transitive_dependencies,
                            "dev_dependencies": dev_transitive_dependencies}

        file.write(json.dumps(full_package_map) + "\n")

        # Creates a new map, each transitive dependency contains the dependency name and number of contributors
        transitive_dependencies_map = create_dependency_map(transitive_dependencies)
        dev_transitive_dependencies_map = create_dependency_map(dev_transitive_dependencies)

        # sum_average = 0
        # if ("average_collaborators" in transitive_dependencies_map) and (
        #         "average_collaborators" in dev_transitive_dependencies_map):
        #     sum_average = transitive_dependencies_map.get("average_collaborators") + dev_transitive_dependencies_map.get(
        #         "average_collaborators")
        # else:
        #     sum_average = 0

        # ----- Create Map of all relevant information for the top 10 packages -----

        full_package_map2 = {"package_name": package_map["package_name"], "version": package_map["version"],
                             "collaborators": package_map["collaborators"],
                             "dependencies": transitive_dependencies_map,
                             "dev_dependencies": dev_transitive_dependencies_map}
                             # "average_transitive_dependencies_collaborators": dev_transitive_dependencies_map}

        file2.write(json.dumps(full_package_map2) + "\n")

        # count += 1
        # if count > 1:
        #     break


if __name__ == "__main__":
    main()
    print('[Info] Program has completed.')