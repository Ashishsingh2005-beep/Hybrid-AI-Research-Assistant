import os
import time
import subprocess
import requests
import zipfile
import io
import logging
import psutil
import streamlit as st
from huggingface_hub import hf_hub_download

logger = logging.getLogger(__name__)

# Model configurations
SLM_MODELS = {
    "SmolLM2-135M-Instruct (145MB)": {
        "repo_id": "bartowski/SmolLM2-135M-Instruct-GGUF",
        "filename": "SmolLM2-135M-Instruct-Q8_0.gguf",
        "context_window": 2048,
        "description": "Extremely fast, very small, great for basic tasks on CPUs."
    },
    "Qwen2.5-0.5B-Instruct (398MB)": {
        "repo_id": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "context_window": 4096,
        "description": "Well-balanced small model, excellent grammar and reasoning for its size."
    },
    "Phi-3-Mini-4K-Instruct (2.2GB)": {
        "repo_id": "microsoft/Phi-3-mini-4k-instruct-gguf",
        "filename": "Phi-3-mini-4k-instruct-q4.gguf",
        "context_window": 4096,
        "description": "Powerful 3.8B model, capable of complex local reasoning (requires more RAM/CPU)."
    }
}

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "local_models"))
LLAMA_BIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "llama_bin"))

# Global references for subprocesses
_server_process = None

def get_models_dir() -> str:
    os.makedirs(MODELS_DIR, exist_ok=True)
    return MODELS_DIR

def get_llama_bin_dir() -> str:
    os.makedirs(LLAMA_BIN_DIR, exist_ok=True)
    return LLAMA_BIN_DIR

def is_model_downloaded(model_name: str) -> bool:
    """
    Checks if the GGUF file exists locally.
    """
    if model_name not in SLM_MODELS:
        return False
    filename = SLM_MODELS[model_name]["filename"]
    path = os.path.join(get_models_dir(), filename)
    return os.path.exists(path)

def download_slm_model(model_name: str, progress_bar=None, status_text=None) -> str:
    """
    Downloads the model from Hugging Face to local directory.
    """
    if model_name not in SLM_MODELS:
        raise ValueError(f"Unknown model: {model_name}")
        
    config = SLM_MODELS[model_name]
    repo_id = config["repo_id"]
    filename = config["filename"]
    
    dest_path = os.path.join(get_models_dir(), filename)
    if os.path.exists(dest_path):
        return dest_path
        
    if status_text:
        status_text.text(f"Starting download of {filename} from {repo_id}...")
        
    # We will use huggingface_hub's hf_hub_download.
    # To show progress in Streamlit, we download manually if progress_bar is provided
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    block_size = 1024 * 1024 # 1MB
    
    downloaded = 0
    with open(dest_path, 'wb') as f:
        for data in response.iter_content(block_size):
            f.write(data)
            downloaded += len(data)
            if progress_bar and total_size > 0:
                progress = min(1.0, downloaded / total_size)
                progress_bar.progress(progress)
                if status_text:
                    status_text.text(f"Downloading {filename}: {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB ({progress*100:.1f}%)")
                    
    if status_text:
        status_text.text(f"Download complete: {dest_path}")
    return dest_path

def download_llama_binaries(progress_bar=None, status_text=None) -> bool:
    """
    Downloads precompiled llama.cpp Windows binaries from GitHub releases.
    """
    bin_dir = get_llama_bin_dir()
    exe_path = os.path.join(bin_dir, "llama-server.exe")
    if os.path.exists(exe_path):
        return True
        
    if status_text:
        status_text.text("Fetching latest llama.cpp releases from GitHub...")
        
    try:
        download_url = None
        try:
            url = "https://api.github.com/repos/ggml-org/llama.cpp/releases/latest"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                for asset in data.get("assets", []):
                    name = asset.get("name", "")
                    if "bin-win-avx2-x64.zip" in name or ("bin-win" in name and "avx2-x64.zip" in name):
                        download_url = asset.get("browser_download_url")
                        break
                if not download_url:
                    for asset in data.get("assets", []):
                        name = asset.get("name", "")
                        if "win" in name and name.endswith(".zip"):
                            download_url = asset.get("browser_download_url")
                            break
        except Exception as fetch_err:
            logger.warning(f"GitHub API fetch failed (rate limit or network): {fetch_err}")

        if not download_url:
            # Direct fallback link to official llama.cpp release asset
            download_url = "https://github.com/ggml-org/llama.cpp/releases/download/b3600/llama-b3600-bin-win-avx2-x64.zip"
                
        if status_text:
            status_text.text(f"Downloading llama.cpp from {download_url}...")
            
        # Download zip
        resp = requests.get(download_url, stream=True)
        resp.raise_for_status()
        total_size = int(resp.headers.get('content-length', 0))
        
        zip_data = io.BytesIO()
        downloaded = 0
        block_size = 1024 * 1024 # 1MB
        for chunk in resp.iter_content(block_size):
            zip_data.write(chunk)
            downloaded += len(chunk)
            if progress_bar and total_size > 0:
                progress = min(1.0, downloaded / total_size)
                progress_bar.progress(progress)
                if status_text:
                    status_text.text(f"Downloading llama.cpp: {downloaded / (1024*1024):.1f}MB / {total_size / (1024*1024):.1f}MB ({progress*100:.1f}%)")
                        
        if status_text:
            status_text.text("Extracting llama.cpp zip archive...")
            
        zip_data.seek(0)
        with zipfile.ZipFile(zip_data) as zip_ref:
            zip_ref.extractall(bin_dir)
            
        if status_text:
            status_text.text("Extraction complete. llama.cpp ready!")
        return True
    except Exception as e:
        logger.error(f"Error downloading llama.cpp: {e}")
        if status_text:
            status_text.text(f"Error: {e}. Llama-cpp-python build or mock mode will be used.")
        return False

def check_llama_cpp_library() -> bool:
    """
    Checks if llama-cpp-python is installed and working.
    """
    try:
        import llama_cpp
        return True
    except ImportError:
        return False

def terminate_existing_llama_server():
    """
    Terminates any background llama-server process.
    """
    global _server_process
    if _server_process:
        try:
            _server_process.terminate()
            _server_process.wait(timeout=3)
        except Exception:
            pass
        _server_process = None
        
    # Also search by process name
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == 'llama-server.exe' or proc.info['name'] == 'llama-server':
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

def start_llama_server(model_path: str, context_size: int = 2048) -> bool:
    """
    Starts llama-server.exe in the background.
    """
    global _server_process
    terminate_existing_llama_server()
    
    bin_dir = get_llama_bin_dir()
    exe_path = os.path.join(bin_dir, "llama-server.exe")
    if not os.path.exists(exe_path):
        return False
        
    cmd = [
        exe_path,
        "-m", model_path,
        "-c", str(context_size),
        "--port", "8080",
        "--threads", "4",
        "--nobrowser"
    ]
    
    try:
        logger.info(f"Starting llama-server: {' '.join(cmd)}")
        _server_process = subprocess.Popen(
            cmd,
            cwd=bin_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        # Wait a few seconds for the server to load the model
        time.sleep(4)
        return True
    except Exception as e:
        logger.error(f"Failed to start llama-server: {e}")
        return False

def generate_local_slm_response(
    prompt: str,
    model_name: str,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    stream: bool = True
):
    """
    Generates a response using the local SLM.
    Uses llama-cpp-python if available, otherwise attempts to use llama-server,
    and falls back to simulated offline SLM if no model is loaded.
    """
    filename = SLM_MODELS[model_name]["filename"]
    model_path = os.path.join(get_models_dir(), filename)
    ctx_size = SLM_MODELS[model_name]["context_window"]
    
    start_time = time.time()
    
    if not os.path.exists(model_path):
        logger.warning(f"Model file not found at {model_path}. Checking for Cloud LLM fallback...")
        try:
            from models.llm import is_api_key_configured, generate_llm_response
            if is_api_key_configured():
                # On cloud hosts like Render where GGUF files aren't pre-downloaded, seamlessly fallback to Cloud LLM
                clean_p = prompt
                if "Query: " in prompt:
                    try:
                        clean_p = prompt.split("Query: ")[-1].split("Assistant:")[0].strip()
                    except Exception:
                        pass
                
                llm_res = generate_llm_response(prompt=clean_p, stream=stream)
                if stream:
                    def stream_with_badge():
                        yield f"*(⚡ Local SLM `{model_name.split(' ')[0]}` GGUF not on cloud server — using Cloud Gemini API fallback)*\n\n"
                        for chunk in llm_res["stream"]:
                            yield chunk
                    return {"stream": stream_with_badge()}
                else:
                    return {
                        "text": f"*(⚡ Local SLM `{model_name.split(' ')[0]}` GGUF not on cloud server — using Cloud Gemini API fallback)*\n\n" + llm_res["text"],
                        "stats": llm_res["stats"]
                    }
        except Exception as fallback_err:
            logger.warning(f"Cloud fallback failed: {fallback_err}")

        # Fall back to Simulated Offline Mode if API key is also missing
        if stream:
            def simulated_stream():
                response_text = f"*(Note: Local model file not found on disk. Running in Simulated Offline Mode. Go to Settings to download model or configure API key)*\n\n" + get_simulated_response(prompt, model_name)
                words = response_text.split(" ")
                full_response = ""
                for word in words:
                    yield word + " "
                    full_response += word + " "
                    time.sleep(0.04)
                elapsed = time.time() - start_time
                stats = {
                    "model": f"{model_name.split(' ')[0]} (Simulated)",
                    "response_time": elapsed,
                    "input_tokens": len(prompt) // 4,
                    "output_tokens": len(full_response) // 4,
                    "cost": 0.0
                }
                yield stats
            return {"stream": simulated_stream()}
        else:
            text = f"*(Note: Local model file not found on disk. Running in Simulated Offline Mode. Go to Settings to download model or configure API key)*\n\n" + get_simulated_response(prompt, model_name)
            elapsed = time.time() - start_time
            stats = {
                "model": f"{model_name.split(' ')[0]} (Simulated)",
                "response_time": elapsed,
                "input_tokens": len(prompt) // 4,
                "output_tokens": len(text) // 4,
                "cost": 0.0
            }
            return {"text": text, "stats": stats}
            
    
    # 1. Try Llama-cpp-python
    if check_llama_cpp_library():
        try:
            import llama_cpp
            
            # Use cached model in session state to avoid reloading it on every request
            if "local_model_instance" not in st.session_state or st.session_state.get("local_model_name") != model_name:
                st.write("Loading model into memory...")
                st.session_state["local_model_instance"] = llama_cpp.Llama(
                    model_path=model_path,
                    n_ctx=ctx_size,
                    verbose=False
                )
                st.session_state["local_model_name"] = model_name
                
            llm = st.session_state["local_model_instance"]
            
            if stream:
                def stream_generator():
                    full_response = ""
                    try:
                        response = llm.create_chat_completion(
                            messages=[{"role": "user", "content": prompt}],
                            temperature=temperature,
                            max_tokens=max_tokens,
                            stream=True
                        )
                        for chunk in response:
                            delta = chunk['choices'][0]['delta']
                            if 'content' in delta:
                                text_chunk = delta['content']
                                full_response += text_chunk
                                yield text_chunk
                                
                        elapsed = time.time() - start_time
                        input_toks = len(llm.tokenize(prompt.encode('utf-8')))
                        output_toks = len(llm.tokenize(full_response.encode('utf-8')))
                        
                        # Return stats at the end
                        stats = {
                            "model": model_name,
                            "response_time": elapsed,
                            "input_tokens": input_toks,
                            "output_tokens": output_toks,
                            "cost": 0.0 # Free!
                        }
                        yield stats
                    except Exception as e:
                        yield f"\n[Error in Local SLM: {str(e)}]"
                return {"stream": stream_generator()}
            else:
                response = llm.create_chat_completion(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                text = response['choices'][0]['message']['content']
                elapsed = time.time() - start_time
                input_toks = len(llm.tokenize(prompt.encode('utf-8')))
                output_toks = len(llm.tokenize(text.encode('utf-8')))
                stats = {
                    "model": model_name,
                    "response_time": elapsed,
                    "input_tokens": input_toks,
                    "output_tokens": output_toks,
                    "cost": 0.0
                }
                return {"text": text, "stats": stats}
        except Exception as e:
            logger.error(f"llama-cpp-python failed: {e}. Trying server fallback...")
            
    # 2. Try llama-server fallback
    exe_path = os.path.join(get_llama_bin_dir(), "llama-server.exe")
    if os.path.exists(exe_path):
        # Ensure server is running
        server_running = False
        try:
            r = requests.get("http://localhost:8080/health", timeout=1)
            if r.status_code == 200:
                server_running = True
        except Exception:
            pass
            
        if not server_running:
            with st.spinner("Starting background llama-server..."):
                start_llama_server(model_path, ctx_size)
                
        # Call llama-server API
        url = "http://localhost:8080/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if stream:
            def stream_generator():
                full_response = ""
                try:
                    r = requests.post(url, json=data, headers=headers, stream=True)
                    r.raise_for_status()
                    
                    import json
                    for line in r.iter_lines():
                        if line:
                            decoded = line.decode('utf-8')
                            if decoded.startswith("data: "):
                                data_str = decoded[6:]
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    json_data = json.loads(data_str)
                                    delta = json_data['choices'][0]['delta']
                                    if 'content' in delta:
                                        chunk_text = delta['content']
                                        full_response += chunk_text
                                        yield chunk_text
                                except Exception:
                                    pass
                                    
                    elapsed = time.time() - start_time
                    # Token estimation
                    input_toks = len(prompt) // 4
                    output_toks = len(full_response) // 4
                    stats = {
                        "model": model_name,
                        "response_time": elapsed,
                        "input_tokens": input_toks,
                        "output_tokens": output_toks,
                        "cost": 0.0
                    }
                    yield stats
                except Exception as e:
                    yield f"\n[Error with local llama-server: {str(e)}]"
            return {"stream": stream_generator()}
        else:
            try:
                r = requests.post(url, json=data, headers=headers)
                r.raise_for_status()
                res = r.json()
                text = res['choices'][0]['message']['content']
                elapsed = time.time() - start_time
                stats = {
                    "model": model_name,
                    "response_time": elapsed,
                    "input_tokens": len(prompt) // 4,
                    "output_tokens": len(text) // 4,
                    "cost": 0.0
                }
                return {"text": text, "stats": stats}
            except Exception as e:
                logger.error(f"llama-server call failed: {e}")
                
    # 3. Simulated/Mock local SLM if everything else is not working
    logger.info("Running in Simulated Local SLM mode")
    if stream:
        def simulated_stream():
            response_text = get_simulated_response(prompt, model_name)
            words = response_text.split(" ")
            full_response = ""
            for word in words:
                yield word + " "
                full_response += word + " "
                time.sleep(0.04) # Simulate network/generation latency
            elapsed = time.time() - start_time
            stats = {
                "model": f"{model_name} (Simulated)",
                "response_time": elapsed,
                "input_tokens": len(prompt) // 4,
                "output_tokens": len(full_response) // 4,
                "cost": 0.0
            }
            yield stats
        return {"stream": simulated_stream()}
    else:
        text = get_simulated_response(prompt, model_name)
        elapsed = time.time() - start_time
        stats = {
            "model": f"{model_name} (Simulated)",
            "response_time": elapsed,
            "input_tokens": len(prompt) // 4,
            "output_tokens": len(text) // 4,
            "cost": 0.0
        }
        return {"text": text, "stats": stats}

def get_simulated_response(prompt: str, model_name: str) -> str:
    """
    Provides rich mock answers offline for common concepts to demonstrate SLM capabilities.
    """
    clean_prompt = prompt
    if "Query: " in prompt:
        try:
            clean_prompt = prompt.split("Query: ")[-1].split("Assistant:")[0].strip()
        except Exception:
            pass
            
    p_lower = clean_prompt.lower()
    
    if "ai agent" in p_lower or "agent" in p_lower:
        return (
            "### 🤖 What are AI Agents?\n\n"
            "An **AI Agent** is an autonomous system powered by AI models (such as LLMs or SLMs) "
            "that can perceive its environment, reason about tasks, make decisions, and execute actions using tools to accomplish specific goals.\n\n"
            "**Key Capabilities of AI Agents:**\n"
            "- 🧠 **Reasoning & Planning:** Breaks complex goals into step-by-step sub-tasks.\n"
            "- 🛠️ **Tool Usage:** Calls external web search, code interpreters, APIs, and databases.\n"
            "- 💾 **Memory Management:** Utilizes short-term context and long-term vector storage (RAG).\n"
            "- 🔄 **Autonomous Loop:** Continuously acts, evaluates outcome, and adjusts strategy."
        )
    elif "what is python" in p_lower or "python" in p_lower:
        return (
            "Python is a high-level, interpreted programming language known for its simplicity and readability. "
            "It supports multiple programming paradigms, including structured, object-oriented, and functional programming. "
            "It is widely used in data science, artificial intelligence, web development, and automation."
        )
    elif "machine learning" in p_lower or " ml " in p_lower or p_lower.startswith("ml"):
        return (
            "Machine Learning (ML) is a branch of artificial intelligence focused on building systems "
            "that learn from data, discover hidden patterns, and make predictions or decisions without being explicitly programmed."
        )
    elif "rag" in p_lower or "retrieval" in p_lower:
        return (
            "Retrieval-Augmented Generation (RAG) is an architecture that grounds language models on custom data. "
            "It retrieves relevant text snippets from documents or vector databases and injects them into the prompt before generating answers."
        )
    elif "slm" in p_lower or "small language" in p_lower:
        return (
            "Small Language Models (SLMs) are lightweight AI models (typically under 7 billion parameters, like SmolLM2 or Phi-3) "
            "optimized to run locally on edge devices and CPUs with low latency, zero API cost, and total privacy."
        )
    elif "llm" in p_lower or "large language" in p_lower:
        return (
            "Large Language Models (LLMs) are massive AI models (e.g. Gemini, GPT-4) trained on massive internet datasets. "
            "They excel at deep reasoning, broad world knowledge, and processing large context windows."
        )
    elif "summarize" in p_lower:
        return (
            "This is a quick local summary of your text. The document discusses key technological concepts and highlights "
            "how Small Language Models (SLMs) can process data offline with zero cost and high speed, making them "
            "suitable for edge devices and specific tasks, while Cloud LLMs handle heavy analysis."
        )
    elif "grammar" in p_lower or "correct" in p_lower:
        return "Grammar Correction (Local SLM): The sentence appears correct. Here is a cleaner version if needed: 'Please review the documents and let me know your thoughts.'"
    elif "code" in p_lower or "function" in p_lower:
        return (
            "```python\n# Code generated by local SLM\n"
            "def calculate_stats(tokens, time_taken):\n"
            "    if time_taken == 0:\n"
            "        return 0\n"
            "    return tokens / time_taken  # tokens per second\n"
            "```"
        )
    elif "capital of america" in p_lower or "capital of the us" in p_lower or "washington" in p_lower:
        return "The capital of the United States of America is Washington, D.C. It was founded on July 16, 1790."
    elif "capital of india" in p_lower or "delhi" in p_lower:
        return "The capital of India is New Delhi. It serves as the seat of all three branches of the Government of India."
    elif p_lower in ["hi", "hello", "hey", "hola"]:
        return "Hello! How can I help you today? You can ask me about AI agents, Python, RAG, or configure your Gemini API key in Settings for live cloud AI capabilities!"
    else:
        return (
            f"### Response to: '{clean_prompt}'\n\n"
            f"An AI model processes your request by analyzing syntax, extracting intent, "
            f"and generating structured natural language text based on its learned representations.\n\n"
            f"💡 *Tip: For live, real-time AI responses to any custom question, enter your Gemini API key on the **Settings** page!*"
        )
