#!/bin/bash
echo "=> Waiting for DB to be online"
python manage.py wait_for_database -s 6

echo "=> Performing database migrations..."
python manage.py migrate

echo "=> Ensuring Superusers..."
python manage.py ensureadmin

echo "=> Ensuring Users..."
python manage.py ensureusers

echo "=> Ensuring Compositions..."
python manage.py ensurecompositions

echo "=> Ensuring Redeem Tokens..."
python manage.py ensuretokens

echo "=> Ensuring Apps..."
python manage.py ensureapps

echo "=> Collecting Static.."
python manage.py collectstatic --noinput

# Start the first process
echo "=> Starting Server"
daphne -b 0.0.0.0 -p 80 --websocket_timeout -1 lok.asgi:application 