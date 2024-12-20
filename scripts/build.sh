g++ --version

#! https://stackoverflow.com/a/246128
SCRIPT_DIR=$(cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd)
ROOT_DIR=$(realpath $SCRIPT_DIR/..)

echo "Got root of directory: $ROOT_DIR"
mkdir -p $ROOT_DIR/build

echo "Building main.exe"
params="-Wall -std=c++20"
if [ "$1" == "debug" ]
then
    params="$params -g -D DEBUG"
    echo "Building in debug mode"

else
    params="$params -O3"
    echo "Building normally"

fi

command="g++ $params -D A_STAR $ROOT_DIR/src/main.cpp -o $ROOT_DIR/build/s_star.exe"
echo "Running \"$command\""
$command

command="g++ $params -D BFS $ROOT_DIR/src/main.cpp -o $ROOT_DIR/build/bfs.exe"
echo "Running \"$command\""
$command
