#! /usr/bin/python3
# Inspired by
# https://stackoverflow.com/questions/28436473/build-gradle-repository-for-offline-development

import os
import glob
import shutil
import subprocess
import sys
from functools import total_ordering

APP_ID = "org.audiveris.audiveris"

@total_ordering
class Artifact:
    MAVEN_CENTRAL = "https://repo1.maven.org/maven2"
    JBOSS_3RDPARTY = "https://repository.jboss.org/nexus/content/repositories/thirdparty-releases"
    jboss_items = ("jai-core", "jai-codec")

    def __init__(self, group_id, artifact_id, version_id, item_name, sha1):
        self.group_id = group_id.replace(".", "/")
        self.artifact_id = artifact_id
        self.version_id = version_id
        self.item_name = item_name
        self.sha1 = "0" * (40 - len(sha1)) + sha1


    def dir(self):
        return "/".join([self.group_id, self.artifact_id, self.version_id])

    def path(self):
        return "/".join([self.dir(), self.item_name])

    def url(self):
        if self.artifact_id in self.jboss_items:
            host = self.JBOSS_3RDPARTY
        else:
            host = self.MAVEN_CENTRAL
        return "/".join([host, self.path()])

    def yml(self, indent=6):
        spc = indent * " "
        return f"""\
{spc}- type: file
{spc}  url: {self.url()}
{spc}  sha1: {self.sha1}
"""

    def script(self, dest="dependencies"):
        dir = "/".join([dest, self.dir()])
        return f"""\
mkdir -p {dir}
ln -f {self.item_name} {"/".join([dir, self.item_name])}
"""

    def __eq__(self, other):
        return (self.path(), self.sha1) == (other.path(), other.sha1)

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return (self.path(), self.sha1) < (other.path(), other.sha1)


def main(subdir):
    artifacts = []
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
                        artifacts.append(Artifact(cache_group_id, cache_artifact_id,
                                                  cache_version_id, cache_item_name,
                                                  os.path.basename(os.path.dirname(cache_item))))

    artifacts.sort()

    with open(APP_ID + ".yml.in", "r") as input:
        yml = input.read().rstrip()
    with open("lang_sources.yml", "r") as input:
        langs = input.read().rstrip()
    with open(APP_ID + ".yml", "w") as output:
        output.write(f"""
{yml}
{langs}
{"".join([a.yml() for a in artifacts])}
""")
    with open("mkgradlerepo.sh", "w") as out:
        out.write(f"""\
#! /bin/bash
{"".join([a.script() for a in artifacts])}
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
