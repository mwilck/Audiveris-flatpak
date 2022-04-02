#! /bin/bash
trap 'echo "ERROR in $BASH_COMMAND" >&2' ERR

TESSDATA=https://api.github.com/repos/tesseract-ocr/tessdata
TAG_304=$(curl -s  "$TESSDATA/tags" | jq -r '.[] | select(.name=="3.04.00").commit.sha')
[[ $TAG_304 ]]

mapfile -t LANG \
	< <(curl -s "$TESSDATA/git/trees/$TAG_304" | \
		jq -r '.tree[] | select (.path|endswith(".traineddata")) |  [ .path,.sha | rtrimstr(".traineddata") ] | join(":")')

mkdir -p languages

print_languages() {
    echo "=== Available languages ==="

    for i in "${!LANG[@]}"; do
	printf "$i ${LANG[$i]%:*}\n"
    done
}

print_languages

lang_files=""
while true; do
    echo -n "enter number to download, ENTER to end, ? to list languages: " >&2
    read lang

    case $lang in
	"") break;;
	"?") print_languages; continue;;
    esac
    name=${LANG[$lang]%:*}
    [[ $name ]] || continue
    hash=${LANG[$lang]#*:}
    file=languages/"$name.traineddata"
    curl "$TESSDATA/git/blobs/$hash" | jq -r '.content' | \
	base64 -d >"$file"
    [[ -f "$file" ]]
    check=$(cat <(printf 'blob %d\0' "$(stat -c %s "$file")") "$file" | \
		sha1sum | cut -d " " -f 1)
    if [[ $check != $hash ]] ; then
	echo "sha1 hash of $file doesn't match expected $hash" >&2
	continue
    else
	echo "git blob sha1 of $file verified" >&2
    fi
    lang_files="$lang_files\
      - type: file
        path: $file
        sha1: $(sha1sum $file | cut -d " " -f 1)"
done

echo "$lang_files" >>lang_sources.yml

echo "lang_sources.yml generated" >&2
