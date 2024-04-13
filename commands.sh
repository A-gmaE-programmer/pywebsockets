echo "python -m http.server"
echo "c;ncat -lkv 127.0.0.1 3002 -c 'tee /dev/stderr | ncat -v 127.0.0.1 3001 | tee /dev/stderr'"
echo "c;python server.py"
