#!/bin/bash
echo "=> Waiting for DB to be online"
python manage.py wait_for_database -s 6

echo "=> Performing database migrations..."
python manage.py migrate

echo "=> Ensuring Kommunity Partners..."
python manage.py ensurepartners

echo "=> Ensuring OpenID Partners..."
python manage.py ensureopenid

echo "=> Ensuring Users..."
python manage.py ensureusers

echo "=> Ensuring Organizations (with auto-configured compositions)..."
python manage.py ensureorganizations

echo "=> Ensuring Memberships..."
python manage.py ensurememberships

echo "=> Ensuring Token..."
python manage.py ensuretokens


# Start the first process
echo "=> Starting Server"
daphne -b 0.0.0.0 -p 80 --websocket_timeout -1 lok_server.asgi:application 