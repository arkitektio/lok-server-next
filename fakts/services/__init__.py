"""Service layer for the ``fakts`` app.

Business logic lives here, grouped by responsibility, so that HTTP views
(``fakts/views.py``) and GraphQL resolvers (in both the in-organization
``fakts`` API and the admin ``api.management`` API) stay thin and simply call
into these functions. Services operate on Django models and Pydantic
``base_models`` — they are presentation-agnostic and own their own
transactions.

``fakts.logic`` and ``fakts.builders`` remain as thin re-export shims for
backwards compatibility with existing importers.
"""
