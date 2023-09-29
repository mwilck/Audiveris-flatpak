#!/bin/bash
trap 'echo "ERROR in $BASH_COMMAND" >&2; exit 1' ERR
YML=org.audiveris.audiveris.yml

# Make sure argument is given and is a directory
[[ "$1" && -d "$1" ]]
# make sure .yml exists
[[ -f "$YML" ]]

mapfile -t FILES < <(sed -En 's/.* path: //p' "$YML")

cp -fvt "$1" "$YML" "${FILES[@]}"
git -C "$1" add "$YML" "${FILES[@]}"
git -C "$1" commit -m 'imported files from Audiveris-flatpak'
