#!/bin/bash
set -eu -o pipefail
SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )/../.."
echo $SCRIPT_DIR
REPO_DIR="$SCRIPT_DIR/.."
echo $REPO_DIR
ROOT_DIR="$REPO_DIR/.."
echo $ROOT_DIR
BUILD_DIR="$ROOT_DIR/W3DBuilds"
echo $BUILD_DIR

function sync {
    rclone sync $BUILD_DIR W3D_Builds:W3D_Development
}

function create_platform_specifics {
    cd $SCRIPT_DIR
    for dir in `ls -d */`
    do
        platform=${dir%?}
        cd "$ROOT_DIR/W3DZip-$platform/Writing3D"
        git fetch --tags
        git reset --hard $(git describe --tags `git rev-list --tags --max-count=1`)
        for script in `ls scripts/$dir`
        do
            script_loc="scripts/$platform/$script"
            if ! [ -f $script_loc ]
            then
                continue
            fi
            if [ "$platform" == "Windows" ]
            then
                echo '@echo off' > "../$script"
                echo "%~dp0\\Writing3D\\scripts\\$platform\\$script %*" >> "../$script"
            else
                echo '#!/bin/bash' > "../$script"
                echo 'SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"' >> "../$script"
                echo '$SCRIPT_DIR/Writing3D/scripts/'"$platform/$script"' "$@"' >> "../$script"
                chmod +x "../$script"
            fi
        done
        if [ "$platform" == "Linux" ]
        then
            tar czf "$BUILD_DIR/W3DZip-$platform.tar.gz" "$ROOT_DIR/W3DZip-$platform"
        else
            zip -r "$BUILD_DIR/W3DZip-$platform.zip" "$ROOT_DIR/W3DZip-$platform"
        fi
    done
}

function create_tag {
    git checkout master
    git push
    echo "Last version was `git tag | tail -1`"
    read -p "Version? v" version
    version="v$version"
    echo $version
    git tag -s $version
    git push --follow-tags
}

function build {
    create_tag
    echo "Creating zip installs for each platform..."
    create_platform_specifics
    echo "Sending build to Google Drive..."
    sync
    echo "Build complete and synced."
}

cd $REPO_DIR
git status
echo "Given the above git status, do you wish to build?"
select yn in "Yes" "No";
do
    case $yn in
        Yes ) build; break;;
        No ) exit;;
    esac
done
