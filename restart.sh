#!/bin/sh

pid=$(cat process.id)
echo "Killing process with PID $pid..."
kill -9 $pid

echo "Restarting data collector..."
nohup ./run.sh > output.log 2> error.log &
sleep 10

pid=$(cat process.id)
echo "New PID is $pid."
echo "Done."


