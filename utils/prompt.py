def get_system_prompt(model_type: str = "slm") -> str:
    """
    Returns the system prompt depending on whether the model is a local SLM or cloud LLM.
    SLMs need simple, concise, and structured instructions to prevent hallucinations.
    LLMs can handle complex instructions.
    """
    if model_type == "slm":
        return (
            "You are a helpful, concise, and direct local AI assistant. "
            "You run offline. Answer the user's question as accurately and briefly as possible. "
            "If you do not know the answer, say 'I don't know' rather than making it up. "
            "Keep formatting clean and text short."
        )
    else:
        return (
            "You are an advanced, high-performance Hybrid AI Research Assistant. "
            "Provide deep, detailed, and comprehensive answers. Structure your responses with clear headings, "
            "bullet points, and sections where appropriate. Cite details and perform logical reasoning "
            "to give the user a complete analysis. If comparing concepts, use markdown tables."
        )

def format_chat_prompt(system_prompt: str, history: str, current_query: str) -> str:
    """
    Formats the conversation history and current query into a single string for inference.
    """
    return (
        f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
        f"{history}"
        f"<|im_start|>user\n{current_query}<|im_end|>\n"
        f"<|im_start|>assistant\n"
    )

def get_summarization_prompt(document_text: str, max_words: int = 150) -> str:
    """
    Generates a prompt for summarizing extracted document/PDF text.
    """
    return (
        f"Please provide a comprehensive yet concise summary of the following document. "
        f"The summary should be under {max_words} words, highlight key takeaways, and outline the main points.\n\n"
        f"Document Text:\n"
        f"\"\"\"\n{document_text[:8000]}\n\"\"\"\n\n"
        f"Summary:"
    )

def get_comparison_prompt(query: str, answer_slm: str, answer_llm: str) -> str:
    """
    Generates a prompt for comparing responses from SLM and LLM.
    This will be processed by the LLM to give an objective breakdown.
    """
    return (
        f"As an AI evaluator, analyze and compare the responses of a Local Small Language Model (SLM) "
        f"and a Cloud Large Language Model (LLM) for the given user query.\n\n"
        f"User Query: {query}\n\n"
        f"--- ANSWER A (Local SLM) ---\n"
        f"{answer_slm}\n\n"
        f"--- ANSWER B (Cloud LLM) ---\n"
        f"{answer_llm}\n\n"
        f"--- EVALUATION TASK ---\n"
        f"Compare the two responses on the following criteria:\n"
        f"1. Accuracy: Which response is more factually correct?\n"
        f"2. Detail & Depth: How deep did each model go?\n"
        f"3. Reasoning: Which one displayed better logical connection and analysis?\n"
        f"4. Conciseness: Did the models avoid unnecessary fluff?\n"
        f"5. Hallucination: Do you detect any manufactured facts in either?\n\n"
        f"Present your comparison as a structured report with a clean Markdown comparison table "
        f"evaluating both answers from 1-10 on each metric, followed by a brief summary of the trade-offs."
    )
