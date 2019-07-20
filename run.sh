#!/bin/sh
# Mounts a fresh copy of the source code and starts an ephemeral container.
# Logs are captured so you can review them at your leisure.

LOGFILE="$(pwd)/gameplay.log"



# https://stackoverflow.com/questions/2657935/checking-for-a-dirty-index-or-untracked-files-with-git
# Returns "*" if the current git branch is dirty.
evil_git_dirty() {
  [ "$(git diff --shortstat 2> /dev/null | tail -n1)" != "" ] && echo "*"
}
REVISION=$(evil_git_dirty)$(git log HEAD~.. --oneline)

# Make sure the log file exists, otherwise docker will try and create it as a dir
if [ ! -f "${LOGFILE}" ]; then touch "${LOGFILE}"; fi

# Run a new container as your current user so log files are created with sensible permissions
docker run --rm -it \
    -u "$(id -u):$(id -g)" \
    -v "${LOGFILE}:/proj/gameplay.log" \
    -v "$(pwd)/src:/proj/src:ro" \
    -e "TERM=${TERM}" \
    -e "REVISION=${REVISION}" \
    short-circuit:latest \
    python /proj/src/main.py
