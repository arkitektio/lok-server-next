#!/bin/bash
echo "=> Waiting for DB to be online"
uv run python manage.py wait_for_database -s 2

echo "=> Performing database migrations..."
uv run python manage.py migrate

echo "=> Ensuring Kommunity Partners..."
uv run python manage.py ensurepartners

echo "=> Ensuring OpenID Partners..."
uv run python manage.py ensureopenid

echo "=> Ensuring Users..."
uv run python manage.py ensureusers

echo "=> Ensuring Organizations (with auto-configured compositions)..."
uv run python manage.py ensureorganizations

echo "=> Ensuring Memberships..."
uv run python manage.py ensurememberships

echo "=> Ensuring Token..."
uv run python manage.py ensuretokens

export AUTHLIB_INSECURE_TRANSPORT=1
# Start the first process
echo "=> Starting Server"
uv run python manage.py runserver 0.0.0.0:80