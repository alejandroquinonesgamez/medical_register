import os
from pathlib import Path

from flask import Blueprint, Response, abort, render_template_string
from .config import API_DOCS_ENABLED

docs = Blueprint("api_docs", __name__)


def _docs_enabled() -> bool:
    return API_DOCS_ENABLED and os.environ.get("API_DOCS_ENABLED", "1").lower() in {"1", "true", "yes"}


@docs.route("/api/openapi.yaml", methods=["GET"])
def openapi_yaml():
    if not _docs_enabled():
        abort(404)

    spec_path = Path(__file__).resolve().parent.parent / "docs" / "openapi.yaml"
    if not spec_path.exists():
        abort(404)

    return Response(spec_path.read_text(encoding="utf-8"), mimetype="application/yaml")


@docs.route("/swagger", methods=["GET"])
def swagger_ui():
    if not _docs_enabled():
        abort(404)

    return render_template_string(
        """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>Medical Register API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    <style>
      body { margin: 0; }
      .topbar { display: none; }
    </style>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.ui = SwaggerUIBundle({
        url: "/api/openapi.yaml",
        dom_id: "#swagger-ui",
        deepLinking: true,
        tryItOutEnabled: true,
        persistAuthorization: true,
      });
    </script>
  </body>
</html>
        """
    )
