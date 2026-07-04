import os
import time
import logging
import google.generativeai as genai
from google.generativeai.types import GenerationConfig

logger = logging.getLogger(__name__)

# Pricing per million tokens (as of standard Gemini 1.5 pricing)
PRICING = {
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash-latest": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "gemini-1.5-pro-latest": {"input": 1.25, "output": 5.00},
    "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash-8b": {"input": 0.0375, "output": 0.15},
}

DEFAULT_API_KEY = ""
try:
    import streamlit as st
    if "GEMINI_API_KEY" in st.secrets:
        DEFAULT_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

def is_api_key_configured(api_key: str = None) -> bool:
    """
    Checks if a Gemini API key is configured.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or DEFAULT_API_KEY
    return bool(key)

def init_gemini(api_key: str = None):
    """
    Initializes the Gemini API client.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY") or DEFAULT_API_KEY
    if not key:
        raise ValueError("Gemini API Key is not set. Please provide it in settings/sidebar.")
    genai.configure(api_key=key)

def get_available_models(api_key: str = None) -> list[str]:
    """
    Retrieves the list of models supported by the API key.
    """
    try:
        init_gemini(api_key)
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                name = m.name
                if name.startswith("models/"):
                    name = name[7:]
                models.append(name)
        return models
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return []

def count_tokens_locally(text: str) -> int:
    """
    Rough fallback token estimator (approx 4 chars per token).
    """
    return len(text) // 4

def generate_llm_response(
    prompt: str,
    system_prompt: str = None,
    model_name: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    api_key: str = None,
    stream: bool = True
):
    """
    Generates a response using the Cloud Gemini API.
    Returns a dictionary with response text/stream and metadata (token count, cost, response time).
    """
    init_gemini(api_key)
    
    # Configure generation parameters
    gen_config = GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
    
    # Initialize the model with optional system instruction
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=gen_config,
        system_instruction=system_prompt
    )
    
    # Measure input tokens
    try:
        input_tokens = model.count_tokens(prompt).total_tokens
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}")
        input_tokens = count_tokens_locally(prompt)
        
    start_time = time.time()
    
    if stream:
        def stream_generator():
            full_response = ""
            try:
                response = model.generate_content(prompt, stream=True)
                for chunk in response:
                    chunk_text = chunk.text
                    full_response += chunk_text
                    yield chunk_text
                
                # Output stats after generation
                end_time = time.time()
                elapsed = end_time - start_time
                try:
                    output_tokens = model.count_tokens(full_response).total_tokens
                except Exception:
                    output_tokens = count_tokens_locally(full_response)
                
                # Calculate cost
                rate = PRICING.get(model_name, PRICING["gemini-1.5-flash"])
                cost = (input_tokens * rate["input"] + output_tokens * rate["output"]) / 1_000_000
                
                # Save stats to metadata dictionary
                stats = {
                    "model": model_name,
                    "response_time": elapsed,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": cost
                }
                yield stats
            except Exception as e:
                logger.error(f"Error in LLM stream generation: {e}")
                err_msg = f"\n[Error during generation: {str(e)}]"
                try:
                    models = get_available_models(api_key)
                    if models:
                        err_msg += f"\n\n🔍 **Diagnostics**: Available models for your API key:\n" + "\n".join([f"- `{m}`" for m in models])
                    else:
                        err_msg += f"\n\n🔍 **Diagnostics**: Checked your key, but no models were returned. Ensure the API key has active permission for Gemini models or try a different key."
                except Exception as diag_err:
                    err_msg += f"\n\n🔍 **Diagnostics**: Failed to run diagnostics check: {diag_err}"
                yield err_msg
                
        return {"stream": stream_generator()}
    else:
        try:
            response = model.generate_content(prompt)
            full_response = response.text
            end_time = time.time()
            elapsed = end_time - start_time
            
            try:
                output_tokens = model.count_tokens(full_response).total_tokens
            except Exception:
                output_tokens = count_tokens_locally(full_response)
                
            rate = PRICING.get(model_name, PRICING["gemini-1.5-flash"])
            cost = (input_tokens * rate["input"] + output_tokens * rate["output"]) / 1_000_000
            
            stats = {
                "model": model_name,
                "response_time": elapsed,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cost": cost
            }
            return {"text": full_response, "stats": stats}
        except Exception as e:
            logger.error(f"Error in LLM generation: {e}")
            raise e
