# Pulling the dependencies and creating the flatpak file

## Run build for "dummy.yml"

This is only necessary in order to initialize the git repo for audiveris
and download the gradle package.

    flatpak-builder --force-clean build dummy.yml

This creates a build directory under `.flatpak-builder/build`; on my system
it's called `.flatpak-builder/build/audivers-1`. Copy this directory.

    cp -rl .flatpak-builder/build/audivers-1 temp

## Run gradle and create dependencies

Note: you must be online to run this step. It's only necessary if the
dependencies (under `deps/`) haven't been gathered yet, or if they need
to be changed or updated.

	cd temp
	./gradlew -g .gradle build

If you are behind a proxy, you may need something like this instead:

	./gradlew -g .gradle \
		-Dhttps.proxyHost=192.168.1.5 -Dhttps.proxyPort=3128 \
		-Dhttp.nonProxyHosts=localhost build

The gradle command will build *audiveris* and more importantly, pull in
all dependencies. After a while, you shoud see something like this:

	BUILD SUCCESSFUL in 51s
	12 actionable tasks: 12 executed

