"""
Local proxy bridge — avoids browser CORS restrictions.
Forwards requests to the corporate LLM proxy at localhost:6655,
injecting the user-supplied API key as the Authorization header.
"""
import requests
from flask import Flask, request, Response, send_from_directory, jsonify
import db

app = Flask(__name__)
db.init_db()

PROXY = "http://localhost:6655"


def proxy_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
    }


# ── Serve the frontend ──────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ── Models endpoints ────────────────────────────────────────────────────────
@app.route("/api/models/<provider>")
def get_models(provider):
    api_key = request.headers.get("X-Api-Key", "")
    urls = {
        "anthropic": f"{PROXY}/anthropic/v1/models",
        "openai":    f"{PROXY}/openai/v1/models",
        "gemini":    f"{PROXY}/gemini/v1beta/models",
        "litellm":   f"{PROXY}/litellm/v1/models",
    }
    url = urls.get(provider)
    if not url:
        return jsonify({"error": "Unknown provider"}), 400
    try:
        r = requests.get(url, headers=proxy_headers(api_key), timeout=15)
        return Response(r.content, status=r.status_code, content_type="application/json")
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot reach proxy at localhost:6655"}), 502


# ── Chat endpoints ──────────────────────────────────────────────────────────
@app.route("/api/chat/<provider>", methods=["POST"])
def chat(provider):
    api_key = request.headers.get("X-Api-Key", "")
    body = request.get_json()

    if provider in ("openai", "litellm"):
        base = PROXY + ("/openai" if provider == "openai" else "/litellm")
        url = f"{base}/v1/chat/completions"
        streaming = body.get("stream", False)
        try:
            r = requests.post(url, headers=proxy_headers(api_key),
                              json=body, stream=streaming, timeout=120)
            if streaming:
                return Response(stream_passthrough(r), content_type="text/event-stream")
            return Response(r.content, status=r.status_code, content_type="application/json")
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "Cannot reach proxy"}), 502

    if provider == "anthropic":
        url = f"{PROXY}/anthropic/v1/messages"
        streaming = body.get("stream", False)
        try:
            r = requests.post(url, headers=proxy_headers(api_key),
                              json=body, stream=streaming, timeout=120)
            if streaming:
                return Response(stream_passthrough(r), content_type="text/event-stream")
            return Response(r.content, status=r.status_code, content_type="application/json")
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "Cannot reach proxy"}), 502

    if provider == "gemini":
        model = body.get("model", "")
        url = f"{PROXY}/gemini/v1beta/models/{model}:generateContent"
        payload = {k: v for k, v in body.items() if k != "model"}
        try:
            r = requests.post(url, headers=proxy_headers(api_key),
                              json=payload, timeout=120)
            return Response(r.content, status=r.status_code, content_type="application/json")
        except requests.exceptions.ConnectionError:
            return jsonify({"error": "Cannot reach proxy"}), 502

    return jsonify({"error": "Unknown provider"}), 400


def stream_passthrough(r):
    for chunk in r.iter_content(chunk_size=None):
        if chunk:
            yield chunk


# ── Session endpoints ───────────────────────────────────────────────────────
@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    return jsonify(db.list_sessions())


@app.route("/api/sessions", methods=["POST"])
def create_session():
    body = request.get_json() or {}
    sid = db.create_session(
        provider=body.get("provider", ""),
        model=body.get("model", ""),
        system_prompt=body.get("system_prompt", ""),
        is_compare=bool(body.get("is_compare", False)),
    )
    return jsonify({"id": sid}), 201


@app.route("/api/sessions", methods=["DELETE"])
def delete_all_sessions():
    db.delete_all_sessions()
    return jsonify({"ok": True})


@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    data = db.get_session(session_id)
    if not data:
        return jsonify({"error": "Not found"}), 404
    return jsonify(data)


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    db.delete_session(session_id)
    return jsonify({"ok": True})


@app.route("/api/sessions/<session_id>/messages", methods=["POST"])
def append_messages(session_id):
    body = request.get_json() or {}
    # pairs: [[role, content, provider, model], ...]
    raw_pairs = body.get("pairs", [])
    title = body.get("title")
    provider = body.get("provider")
    model = body.get("model")
    system_prompt = body.get("system_prompt")

    if not db.get_session(session_id):
        return jsonify({"error": "Session not found"}), 404

    if raw_pairs:
        # Normalise: old format [role, content], new format [role, content, provider, model]
        pairs = []
        for p in raw_pairs:
            role    = p[0]
            content = p[1]
            prov    = p[2] if len(p) > 2 else ""
            mdl     = p[3] if len(p) > 3 else ""
            pairs.append((role, content, prov, mdl))
        db.append_messages(session_id, pairs)

    if title:
        db.update_session_title(session_id, title)
    if provider or model or system_prompt is not None:
        db.update_session_meta(session_id, provider=provider, model=model,
                               system_prompt=system_prompt)
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("Starting chatbot server at http://localhost:8080")
    app.run(host="0.0.0.0", port=8080, debug=False)
