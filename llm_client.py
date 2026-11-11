"""OpenAI call for AI justifications. Plugs into justification.make_justifier(llm).

The API key is read from the OPENAI_API_KEY environment variable (or a local .env file).
Never put a key in the code or commit .env. The openai and dotenv packages are imported
only when needed, so the rest of the program still runs without them (template only).
"""
import os

DEFAULT_MODEL = "gpt-5.5"      # override with the OPENAI_MODEL environment variable
MAX_OUTPUT_TOKENS = 500        # generous: reasoning models count thinking tokens too


def make_openai_llm(client, model, max_output_tokens=MAX_OUTPUT_TOKENS):
    """Return llm(instructions, facts_json, timeout_seconds) -> text.

    Raises if the response is not complete, so the caller falls back to the template.
    """
    def llm(instructions, facts_json, timeout):
        response = client.with_options(timeout=timeout).responses.create(
            model=model,
            instructions=instructions,   # fixed text
            input=facts_json,            # the item data, kept separate from the instructions
            max_output_tokens=max_output_tokens,
        )
        status = getattr(response, "status", "completed")
        if status != "completed":
            raise RuntimeError(f"response status: {status}")
        return response.output_text

    return llm


def load_llm(use_env_file=True, client_factory=None):
    """Build the OpenAI llm function if everything is available.

    Returns (llm, note). llm is None when the AI cannot be used; note says why, in a form
    that is safe to print (it never includes the key).
    """
    if use_env_file:
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass  # .env support is optional; the key can also be set in the environment

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None, "AI justifications: OFF (OPENAI_API_KEY is not set), using the template"

    if client_factory is None:
        try:
            from openai import OpenAI
        except ImportError:
            return None, "AI justifications: OFF (the 'openai' package is not installed), using the template"

        def client_factory(key):
            return OpenAI(api_key=key, max_retries=0)

    model = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)
    return make_openai_llm(client_factory(api_key), model), f"AI justifications: ON (model {model})"