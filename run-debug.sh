#!/bin/bash
echo "=> Waiting for DB to be online"
uv run python manage.py wait_for_database -s 2

echo "=> Performing database migrations..."
uv run python manage.py migrate

echo "=> Ensuring Roles..."
uv run python manage.py ensureroles

echo "=> Ensuring Superusers..."
uv run python manage.py ensureadmin

echo "=> Ensuring Kommunity Partners..."
uv run python manage.py ensure_kommunity

echo "=> Ensuring Users..."
uv run python manage.py ensureusers

echo "=> Ensuring Organizations (with auto-configured compositions)..."
uv run python manage.py ensureorganizations

echo "=> Ensuring Apps..."
uv run python manage.py ensureapps

echo "=> Ensuring Token..."
uv run python manage.py ensuretokens

echo "=> Collecting Static.."
uv run python manage.py collectstatic --noinput


export AUTHLIB_INSECURE_TRANSPORT=1
# Start the first process
echo "=> Starting Server"
uv run python manage.py runserver 0.0.0.0:80