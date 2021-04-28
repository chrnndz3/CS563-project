import json
import traceback
import requests as requests

# Initialized variables
registry_url = 'https://registry.npmjs.com/'
# top_ten_packages_list = ["lodash", "chalk", "request", "commander", "react", "express", "debug", "async", "fs-extra",
#                          "moment"]
top_ten_packages_list = ["lodash", "react", "chalk", "tslib", "axios", "express", "commander", "request", "moment", "react-dom"]
file = open("new_results/top_ten_packages_details.json", "w")
file2 = open("new_results/top_ten_packages_average.json", "w")


def metadata_extraction(package_name):
    error = "{\"error\":\"not_found\",\"reason\": \"missing\"}"

    url = registry_url + package_name
    registry_url_request = requests.get(url)
    # Converts data to a json object
    data = registry_url_request.json()

    if "error" in data:
        print("There's no data in the replicate endpoint for " + package_name + ". Checking registry endpoint.")

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

    # ----- Maintainers -----
    maintainers = data["maintainers"] if ("maintainers" in data) else None

    # ----- Dependencies -----
    dependencies = version_data["dependencies"] if ("dependencies" in version_data) else None

    # ----- Dev Dependencies -----
    dev_dependencies = version_data["devDependencies"] if ("devDependencies" in version_data) else None

    # ----- Create Map of all relevant information for the top 10 packages -----
    package_map = {"package_name": package_name, "version": latest_version,
                   "maintainers": len(maintainers), "dependencies": dependencies,
                   "dev_dependencies": dev_dependencies}

    return package_map


def maintainer_extraction(package_name):
    url = registry_url + package_name
    registry_url_request = requests.get(url)
    data = registry_url_request.json()

    if "error" in data:
        print("There's no data in the replicate endpoint for " + package_name + ". Checking registry endpoint.")

    # ----- Maintainers -----
    maintainers = data["maintainers"] if ("maintainers" in data) else None

    return len(maintainers)


def create_dependency_map(transitive_dependencies):
    total_collaborators = 0
    total_dependencies = 0
    dependencies_map = {}

    if (transitive_dependencies is None) or (len(transitive_dependencies) == 0):
        return None
    else:
        total_dependencies = len(transitive_dependencies)
        for item in transitive_dependencies.items():
            dependency_name = item[0]

            collaborators_per_dependency = maintainer_extraction(dependency_name)

            # ----- Create Map of all relevant information for the top 10 packages -----
            total_collaborators += collaborators_per_dependency

        dependencies_map["total_collaborators"] = total_collaborators
        dependencies_map["total_dependencies"] = total_dependencies
        dependencies_map["average_collaborators"] = (total_collaborators / total_dependencies)

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
                            "collaborators": package_map["maintainers"], "dependencies": transitive_dependencies,
                            "dev_dependencies": dev_transitive_dependencies}

        file.write(json.dumps(full_package_map) + "\n")

        # Creates a new map, each transitive dependency contains the dependency name and number of contributors
        transitive_dependencies_map = create_dependency_map(transitive_dependencies)
        dev_transitive_dependencies_map = create_dependency_map(dev_transitive_dependencies)

        # ----- Create Map of all relevant information for the top 10 packages -----
        full_package_map2 = {"package_name": package_map["package_name"], "version": package_map["version"],
                             "collaborators": package_map["maintainers"],
                             "dependencies": transitive_dependencies_map,
                             "dev_dependencies": dev_transitive_dependencies_map}

        file2.write(json.dumps(full_package_map2) + "\n")

        # count += 1
        # if count > 1:
        #     break


if __name__ == "__main__":
    main()
    print('[Info] Program has completed.')