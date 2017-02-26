#!/bin/sh
# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=sh textwidth=76
#
# File:
#   /usr/bin/thunderbird
#
# Purpose:
#   This is a wrapper script for starting the thunderbird binary with taking
#   care of the searching for a old user Icedove profile folder and copying
#   the folder into the new place if possible.
#
# Environment:
#   The Icedove binary was using the profile folder '${HOME}/.icedove'. The
#   Mozilla default for the Thunderbird binary is '${HOME}/.thunderbird'.
#   The script will looking for the old profile folder and will copy the
#   folder into the new used profile folder.
#
# Copyright:
#   Licensed under the terms of GPLv2+.

#set -x

TB_HELPER="/usr/lib/thunderbird/thunderbird-wrapper-helper.sh"
# sourcing external variables and helper functions
if [ -f ${TB_HELPER} ]; then
    . ${TB_HELPER}
else
    # this needs improving, the user isn't seen this error!
    echo "helper ${TB_HELPER} not found!"
    exit 1
fi

# some global variables
MOZ_APP_NAME=thunderbird
MOZ_APP_LAUNCHER=`which $0`
MOZ_LIBDIR=/usr/lib/${MOZ_APP_NAME}
ID_PROFILE_FOLDER=${HOME}/.icedove
TB_PROFILE_FOLDER=${HOME}/.thunderbird

# set MOZ_APP_LAUNCHER for gnome-session
export MOZ_APP_LAUNCHER

TB_ARGS=""
while [ $# -gt 0 ]; do
    ARG="$1"
    case ${ARG} in
        --fixmime)
            FIXMIME=1
            ;;
        -g)
            DEBUGGER=1
            DEBUG=1
            ;;
#       -d)
#            USER_DEBUGGER=$2
#            DEBUG=1
#            shift
#            ;;
        --help)
            HELP=1
            usage
            exit 0
            ;;
        --show-backup)
            do_collect_backup_files
            exit 0
            ;;
        --verbose) echo "[[ ... using verbose mode ... ]]"
            VERBOSE=1
            ;;
        '?')
            usage >&2
            exit 1
            ;;
        # every other argument is needed to get down to the TB starting call
        *) TB_ARGS="${TB_ARGS} ${ARG}"
        ;;
    esac
    shift
done

# sanity check
if [ "$DEBUGGER" != "" ] && [ "$USER_DEBUGGER" != "" ]; then
    echo "You can't use option '-g and '-d' at the same time!"
    usage
    exit 1
fi

if [ "${FIXMIME}" = "1" ]; then
    do_fix_mimetypes_rdf
    do_collect_backup_files
    exit 0
fi

#############################################################################
#                  User Thunderbird Profile Adoptions                       #
#                                                                           #
# The users Icedove/Thunderbird profile(s) doesn't need to be modified in a #
# different and complicated way. We simply need to ensure that the          #
# Thunderbird binary is finding the existing profiles in the folder         #
# $(HOME)/.thunderbird folder or a valid symlink pointing to the profiles.  #
#                                                                           #
# To "migrate" a old existing Icedove profile we can simply do a symlink    #
# from $(HOME)/.thunderbird --> $(HOME)/.icedove .                          #
#                                                                           #
# Afterwards do some changes to the file mimeTypes.rdf within every         #
# profile. Also we can modify existing *icedove*.desktop entries in the     #
# files.                                                                    #
#                                                                           #
#     $(HOME)/.config/mimeapps.list                                         #
#     $(HOME)/.local/share/applications/mimeapps.list                       #
#                                                                           #
#############################################################################

# First try the default case for modification, there is only a folder
# ${ID_PROFILE_FOLDER} and we can symlink to this.
if [ -d "${ID_PROFILE_FOLDER}" -o -L "${ID_PROFILE_FOLDER}" ] && \
   [ ! -d "${TB_PROFILE_FOLDER}" -a ! -L "${TB_PROFILE_FOLDER}" ]; then
    debug "found folder '${ID_PROFILE_FOLDER}'"
    debug "not found folder or symlink '${TB_PROFILE_FOLDER}'"
    debug "Start Thunderbird profile adoptions, please be patient!"

    # open a pop-up window with a message about starting migration
    do_inform_migration_start

    # do the symlinking
    do_thunderbird2icedove_symlink

    # fixing mimeTypes.rdf which may have registered the iceweasel binary
    # as browser, instead of x-www-browser
    do_fix_mimetypes_rdf

    # Fix local mimeapp.list and *.desktop entries
    do_migrate_old_icedove_desktop

    # we are finished
    debug "Thunderbird Profile adoptions done."
    do_collect_backup_files
fi

# We found both profile folder,
# we need to check if .thunderbird is symlinked to .icedove
if [ -d "${ID_PROFILE_FOLDER}" -a -L "${TB_PROFILE_FOLDER}" ] && \
   [ "$(/usr/bin/readlink ${TB_PROFILE_FOLDER})" != "${ID_PROFILE_FOLDER}" ];then
    debug "Found folder ${ID_PROFILE_FOLDER} and a symlink ${TB_PROFILE_FOLDER} that is linked to ${ID_PROFILE_FOLDER}"

# ... or if .icedove is symlinked to .thunderbird
elif [ -d "${TB_PROFILE_FOLDER}" -a -L "${ID_PROFILE_FOLDER}" ] && \
     [ "$(/usr/bin/readlink ${ID_PROFILE_FOLDER})" != "${TB_PROFILE_FOLDER}" ];then
    debug "Found folder ${TB_PROFILE_FOLDER} and a symlink ${ID_PROFILE_FOLDER} that is linked to ${TB_PROFILE_FOLDER}"
    debug "You may want to remove the symlink ${ID_PROFILE_FOLDER}? It's probably not needed anymore."

    if [ ! -f ${TB_PROFILE_FOLDER}/.migrated ]; then
        # fixing mimeTypes.rdf which may have registered the iceweasel binary
        # as browser, instead of x-www-browser
        do_fix_mimetypes_rdf

        # Fix local mimeapp.list and *.desktop entries
        do_migrate_old_icedove_desktop
        /usr/bin/touch ${TB_PROFILE_FOLDER}/.migrated
    fi

# We found both profile folder, but they are not linked to each other! This
# is a state we can't solve on our own !!! The user needs to interact and
# has probably a old or otherwise used Thunderbird installation.
elif [ -d "${ID_PROFILE_FOLDER}" -o -L "${ID_PROFILE_FOLDER}" ] && \
     [ -d "${TB_PROFILE_FOLDER}" -o -L "${TB_PROFILE_FOLDER}" ] && \
     [ "$(/usr/bin/readlink ${TB_PROFILE_FOLDER})" != "${ID_PROFILE_FOLDER}" ]; then

    debug "There is already a folder '${TB_PROFILE_FOLDER}', will do nothing."
    debug "Please investigate by yourself!"
    logger -i -p warning -s "$0: [profile migration] Couldn't migrate Icedove into Thunderbird profile due existing folder '${TB_PROFILE_FOLDER}'!"

    # display a graphical advice if possible
    do_thunderbird2icedove_error_out
fi

if [ "$FAIL" = 1 ]; then
    echo "A error happened while trying to migrate the old Icedove profile folder '${ID_PROFILE_FOLDER}'."
    echo "Please take a look into the syslog file!"
    exit 1
fi

# We have nothing to migrate or adopt, going further by starting Thunderbird.

if [ "${DEBUG}" = "" ]; then
    debug "call '$MOZ_LIBDIR/$MOZ_APP_NAME ${TB_ARGS}'"
    $MOZ_LIBDIR/$MOZ_APP_NAME ${TB_ARGS}
else
    # User has selected GDB?
    if [ "$DEBUGGER" = "1" ]; then
        # checking for GDB
        if [ -f /usr/bin/gdb ]; then
            if [ -f /usr/lib/debug/usr/lib/thunderbird/thunderbird ]; then
                echo "Starting Thunderbird with GDB ..."
                LANG= /usr/lib/thunderbird/run-mozilla.sh -g /usr/lib/thunderbird/thunderbird-bin "${TB_ARGS}"
            else
                echo "No package 'thunderbird-dbg' installed! Please install first and restart."
                exit 1
            fi
        else
            echo "No package 'gdb' installed! Please install first and try again."
            exit 1
        fi
    fi
fi

exit 0
