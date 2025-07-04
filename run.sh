#!/bin/bash
echo "=> Waiting for DB to be online"
uv run python manage.py wait_for_database -s 6

echo "=> Performing database migrations..."
uv run python manage.py migrate

echo "=> Ensuring Superusers..."
uv run python manage.py ensureadmin

echo "=> Ensuring Users..."
uv run python manage.py ensureusers


echo "=> Ensuring Composition..."
uv run python manage.py ensurecomposition

echo "=> Ensuring Redeem Tokens..."
uv run python manage.py ensuretokens

echo "=> Ensuring Apps..."
uv run python manage.py ensureapps

echo "=> Ensuring Token..."
uv run python manage.py ensuretokens

echo "=> Collecting Static.."
uv run python manage.py collectstatic --noinput

# Start the first process
echo "=> Starting Server"
uv run daphne -b 0.0.0.0 -p 80 --websocket_timeout -1 lok_server.asgi:application 