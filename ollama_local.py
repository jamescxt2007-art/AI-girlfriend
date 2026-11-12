"""Small Ollama HTTP client. No cloud endpoints, keys, or demo fallbacks."""

import re

import requests

BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:1.5b"


class OllamaError(Exception):
    """A safe, actionable message suitable for display in the app."""


def request_json(method, path, *, payload=None, timeout=(3, 5)):
    # Ignore HTTP_PROXY environment variables for this strictly local service.
    try:
        with requests.Session() as session:
            session.trust_env = False
            response = session.request(
                method, BASE_URL + path, json=payload, timeout=timeout,
                allow_redirects=False,
            )
        if response.status_code == 404:
            raise OllamaError("The model is missing. Run `ollama pull MODEL_NAME` using the exact model name in the sidebar, then click Refresh connection.")
        if not 200 <= response.status_code < 300:
            raise OllamaError("Ollama could not complete the request. Close unused apps, check `ollama ps`, and try again. A smaller model may help if memory is low.")
        data = response.json()
        if not isinstance(data, dict) or data.get("error"):
            raise OllamaError("Ollama returned an error. Check your model with `ollama list` and restart Ollama if needed.")
        return data
    except requests.Timeout as error:
        raise OllamaError("Ollama took too long to respond. The first reply loads the model and can be slow. Close unused apps and retry, or choose a smaller model.") from error
    except requests.ConnectionError as error:
        raise OllamaError("Cannot connect to Ollama at http://localhost:11434. Open Ollama from the Start menu, or run `ollama serve` in another terminal, then click Refresh connection.") from error
    except (requests.RequestException, ValueError) as error:
        raise OllamaError("Ollama returned an unreadable response. Restart Ollama and click Refresh connection.") from error


def installed_models():
    models = request_json("GET", "/api/tags").get("models")
    if not isinstance(models, list) or any(not isinstance(item, dict) for item in models):
        raise OllamaError("Ollama returned an invalid model list. Restart or update Ollama.")
    # Reject remote models even if they appear in the local model catalogue.
    return [item["name"] for item in models
            if isinstance(item.get("name"), str)
            and not item.get("remote_host") and not item.get("remote_model")
            and not item["name"].lower().endswith(":cloud")]


def local_model_name(model):
    model = model.strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./:-]*", model) or ":cloud" in model.lower() or "://" in model:
        raise OllamaError("Choose a local model name such as qwen2.5:1.5b. Cloud models and URLs are disabled.")
    return model if ":" in model.rsplit("/", 1)[-1] else model + ":latest"


def chat_reply(messages, instructions, model):
    model = local_model_name(model)
    if model not in installed_models():
        raise OllamaError(f"Local model '{model}' is not installed. Run `ollama pull {model}` in PowerShell, then click Refresh connection.")
    # Bound history size for the small model's context and limited system memory.
    # Keep full recent turns, always including the newest message.
    recent = []
    size = 0
    for item in reversed(messages[-12:]):
        content = item["content"]
        if recent and size + len(content) > 6000:
            break
        recent.append({"role": item["role"], "content": content})
        size += len(content)
    recent.reverse()
    if recent and recent[0]["role"] == "assistant":
        recent.pop(0)
    data = request_json("POST", "/api/chat", payload={
        "model": model,
        "messages": [{"role": "system", "content": instructions}] + recent,
        "stream": False,
        "options": {"num_ctx": 4096, "num_predict": 300},
        "keep_alive": "2m",
    }, timeout=(3, 180))
    message = data.get("message")
    text = message.get("content") if isinstance(message, dict) else None
    if not isinstance(text, str) or not text.strip():
        raise OllamaError("Ollama returned no reply text. Try again or choose a different local chat model.")
    return text.strip()
