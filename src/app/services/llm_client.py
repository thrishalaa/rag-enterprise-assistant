import re
import os
from llama_cpp import Llama
from pathlib import Path
from src.utils.logger import get_logger

LLAMA_MODEL_PATH = Path(os.getenv("LLAMA_MODEL_PATH"))
logger = get_logger(__name__)

class LLMClient:
    def __init__(self):
        self.llm = Llama(
            model_path=str(LLAMA_MODEL_PATH),
            n_ctx=8192,
            n_threads=8,
            temperature=0.6,
            top_p=0.9,
            repeat_penalty=1.05,
            verbose=False
        )

    # ---------------------------------------------------------
    # Extract final answer after </think>
    # ---------------------------------------------------------
    def extract_final_answer(self, text: str) -> str:
        if not text or not isinstance(text, str):
            return "I don't know."

        # Remove hidden chain-of-thought block
        if "</think>" in text:
            text = text.split("</think>")[-1]

        # Remove all HTML/XML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Remove escaped HTML like &lt;div&gt;
        text = text.replace("&lt;", "").replace("&gt;", "")

        # Remove markdown artifacts
        text = re.sub(r"`+", "", text)
        text = re.sub(r"\*+", "", text)

        # Remove leftover junk
        text = text.replace("Answer:", "")
        text = text.replace("Final answer:", "")

        # Normalize whitespace
        text = " ".join(text.split()).strip()

        if len(text) < 2:
            return "I don't know."

        return text

    # ---------------------------------------------------------
    # Main generation method
    # ---------------------------------------------------------
    def generate(self, prompt: str) -> str:
        try:
            system_prompt = (
                "You are an enterprise HR assistant. "
                "Use ONLY the provided context. "
                "Provide a clear factual answer. "
                "If answer is not in the context, reply: 'I don't know.' "
                "Output plain text only."
            )

            full_prompt = (
                f"{system_prompt}\n\n"
                f"{prompt}\n\n"
                f"Answer:"
            )

            raw = self.llm.create_completion(
                prompt=full_prompt,
                max_tokens=700,
                temperature=0.6,
                top_p=0.9,
                repeat_penalty=1.05
            )

            output = raw["choices"][0]["text"]
            final = self.extract_final_answer(output)

            # Final safety pass
            final = re.sub(r"<[^>]+>", "", final)
            final = final.replace("&lt;", "").replace("&gt;", "")
            final = " ".join(final.split()).strip()

            # Ensure it's valid
            if final == "" or final.lower().startswith("context") or len(final) < 2:
                return "I don't know."

            return final

        except Exception as e:
            logger.error(f"LLM error: {e}")
            return "I don't know."
