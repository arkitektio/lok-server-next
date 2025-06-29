#!/bin/bash
echo "=> Waiting for DB to be online"
uv run python manage.py wait_for_database -s 2

echo "=> Performing database migrations..."
uv run python manage.py migrate

echo "=> Ensuring Superusers..."
uv run python manage.py ensureadmin

echo "=> Ensuring Users..."
uv run python manage.py ensureusers

echo "=> Ensuring Groups..."
uv run python manage.py ensuregroups


echo "=> Ensuring Composition..."
uv run python manage.py ensurecomposition

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