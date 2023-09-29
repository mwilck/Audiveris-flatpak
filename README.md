# Building Audiveris

Run the build:

    flatpak-builder --force-clean build org.audiveris.audiveris.yml

See [Building your first Flatpak](https://docs.flatpak.org/en/latest/first-build.html)
for additional options to the **flatpak-builder** command.

# Pulling the dependencies and creating the flatpak file

The steps below are only necessary if you want to change the list
of supported languages for the Tesseract OCR engine, or if the Java
dependencies need to be updated. It will always be necessary in the `scripts`
branch, which contains no autogenerated files.

## Selecting languages

Audiveris requires Tesseract "trained data" for different languages to
decode human language. A helper script `languages.sh` is provided to select
languages. Start it in interactive mode:

    ./languages.sh --interactive

Type `?` to show the available and currently configured languages. Add a
language by entering  either the number
or the abbreviation of the language you wish to add. When done selecting,
simply press ENTER to start the download.

If you know which languages to configure, simply the script like this

	./languages.sh ita fra

To see a the list of available languages, run:

	./languages.sh --list

The script creates suitable YAML with checksums for inclusion in the flatpak
manifest. The output is gathered in the file `lang_sources.yml`, which will
be included in the build manifest for Audiveris in the next step.

## Determine Java Dependencies

This is only necessary if some dependencies have changed. The audiveris
build must be run online (i.e. with network access once). A script will
determine the necessary Java libraries and meta data that **flatpak-builder**
will need to fetch in order to run the build.

This step is required because flatpak builds need to run offline, always,
whereas the **gradle** build system used by Audiveris needs access online
resources to download Java libraries. **gradle** resolves library dependencies
dynamically, which can't be done with a static flatpak manifest. The `deps.py`
script lets gradle download all dependencies, stores them for offline use,
and adds the proper entires in the flatpak manifest.

### 1. Run build for "dummy.yml"

    flatpak-builder --force-clean --disable-cache --keep-build-dirs dummy dummy.yml

This creates a build directory under `.flatpak-builder/build/dummy`.
If you need to change anything for the subsequent build step, you can
edit files in this directory now. For example, I need to add proxy settings
to `gradle.properties`:

	systemProp.https.proxyHost=192.168.1.5
	systemProp.https.proxyPort=3128

### 2. Run deps.py script

Now run `./deps.py`. This command runs the *audiveris* build in the temporary
directory and generates the buildscript `mkgradlerepo.sh` and the list of sources
for the flatpak source file `io.github.Audivervis.audiveris.yml`.

**Important:** Building **audiveris** 5.2.5 and newer requires **JDK 17**.
Make sure that not only the paths to `java` and `javac`, but also the
environment variables `JAVA_HOME` etc. point to the correct

### 3. Build Audiveris

Now run the actual Audiveris build, like above:

    flatpak-builder --force-clean build org.audiveris.audiveris.yml

# Running Audiveris

This section lists some special properties of the Flatpak edition of
Audiveris. Please see the [Audiveris
handbook](https://audiveris.github.io/audiveris/_pages/handbook/) for general
information and program usage.

## Paths

The general remarks from
[Folders](https://audiveris.github.io/audiveris/_pages/folders/) apply, as
modified by Flatpak:

 * The **config folder** is
   `$HOME/.var/app/org.audiveris.audiveris/config/AudiverisLtd/audiveris`.
 * **Log files** are stored under
   `$HOME/.var/app/org.audiveris.audiveris/cache/AudiverisLtd/audiveris/log`.

### Example: Enabling Debug Logging

To enable debug logging for certain java classes:

    <?xml version="1.0" encoding="UTF-8"?>
    <configuration>
        <include optional="true" resource="res/logback-elements.xml"/>
        <logger name="org.audiveris.omr.text.tesseract.TesseractOCR" level="DEBUG"/>
        <logger name="org.audiveris.omr.text.tesseract.TesseractOrder" level="DEBUG"/>
        <root level="INFO">
            <appender-ref ref="CONSOLE" />
        </root>
    </configuration>

To enable debug logging globally, simply use `<root level="DEBUG">` above.
