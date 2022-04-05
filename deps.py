#! /usr/bin/python3
# Inspired by
# https://stackoverflow.com/questions/28436473/build-gradle-repository-for-offline-development

import os
import glob
import shutil
import subprocess
import sys

APP_ID = "org.audiveris.audiveris"

def main(subdir):
    commands = ""
    sources = ""
    project_dir = os.path.dirname(os.path.realpath(__file__))
    flat_dir = os.path.join(project_dir, "deps")
    if not os.path.isdir(flat_dir):
        os.makedirs(flat_dir)
    repo_dir = os.path.join(project_dir, "dependencies")
    if not os.path.isdir(repo_dir):
        os.makedirs(repo_dir)
    build_dir = os.path.join(project_dir, subdir)
    temp_home = os.path.join(build_dir, ".gradle_temp")
    if not os.path.isdir(build_dir):
        raise RuntimeError(f"{build_dir} does not exist")

    os.chdir(build_dir)
    # Fixme: do we need to call the "build" task, really?
    subprocess.call(["./gradlew", "--info", "-g", temp_home, "build"])
    os.chdir(project_dir)

    cache_files = os.path.join(temp_home, "caches", "modules-*", "files-*")
    for cache_dir in glob.glob(cache_files):
        for cache_group_id in os.listdir(cache_dir):
            cache_group_dir = os.path.join(cache_dir, cache_group_id)
            repo_group_dir = os.path.join(repo_dir, cache_group_id.replace('.', '/'))
            for cache_artifact_id in os.listdir(cache_group_dir):
                cache_artifact_dir = os.path.join(cache_group_dir, cache_artifact_id)
                repo_artifact_dir = os.path.join(repo_group_dir, cache_artifact_id)
                for cache_version_id in os.listdir(cache_artifact_dir):
                    cache_version_dir = os.path.join(cache_artifact_dir, cache_version_id)
                    repo_version_dir = os.path.join(repo_artifact_dir, cache_version_id)
                    if not os.path.isdir(repo_version_dir):
                        os.makedirs(repo_version_dir)
                    cache_items = os.path.join(cache_version_dir, "*/*")
                    for cache_item in glob.glob(cache_items):
                        cache_item_name = os.path.basename(cache_item)
                        sha1 = os.path.basename(os.path.dirname(cache_item))
                        sha1 = "0" * (40 - len(sha1)) + sha1
                        repo_item_path = os.path.join(repo_version_dir, cache_item_name)
                        repo_item_rel = repo_item_path.replace(project_dir + os.path.sep, "")
                        flat_item_path = os.path.join(flat_dir, cache_item_name)
                        cache_item_rel = cache_item.replace(temp_home + os.path.sep, "")
                        commands = commands + f"""\
mkdir -p {os.path.dirname(repo_item_rel)}
ln -f {cache_item_name} {repo_item_rel}
"""
                        sources = sources + f"""
      - type: file
        path: deps/{cache_item_name}
        sha1: {sha1}"""
                        if os.path.exists(flat_item_path):
                            raise RuntimeError(f"duplicate file name {flat_item_path}")
                        os.link(cache_item, flat_item_path)

    with open(APP_ID + ".yml.in", "r") as input:
        yml = input.read().rstrip()
    with open("lang_sources.yml", "r") as input:
        langs = input.read().rstrip()
    with open(APP_ID + ".yml", "w") as output:
        output.write(f"""
{yml}
{langs}{sources}
""")
    with open("mkgradlerepo.sh", "w") as out:
        out.write(f"""\
#! /bin/bash
{commands}
""")

    if os.path.islink(build_dir):
        shutil.rmtree(os.path.realpath(build_dir))
        os.unlink(build_dir)
    else:
        shutil.rmtree(build_dir)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        raise RuntimeError("This script takes max 1 argument")
    elif len(sys.argv) == 2:
        dir=sys.argv[1]
    else:
        dir=".flatpak-builder/build/dummy"
    main(dir)
