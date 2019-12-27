#!/bin/sh
# Mounts a fresh copy of the source code and starts an ephemeral container.
# Logs are captured so you can review them at your leisure.

OUTDIR="$(pwd)/output"



# https://stackoverflow.com/questions/2657935/checking-for-a-dirty-index-or-untracked-files-with-git
# Returns "*" if the current git branch is dirty.
evil_git_dirty() {
  [ "$(git diff --shortstat 2> /dev/null | tail -n1)" != "" ] && echo "*"
}
REVISION=$(evil_git_dirty)$(git log HEAD~.. --oneline)

# Make sure the output dir exists, otherwise docker will try to create it as root
mkdir -p "$OUTDIR"

# Run a new container as your current user so log files are created with sensible permissions
docker run --rm -it \
    -u "$(id -u):$(id -g)" \
    -v "${OUTDIR}:/proj/output" \
    -v "$(pwd)/shortcircuit:/proj/shortcircuit:ro" \
    -e "TERM=${TERM}" \
    -e "REVISION=${REVISION}" \
    short-circuit:latest \
    sh
    # python /proj/shortcircuit/main.py $@
