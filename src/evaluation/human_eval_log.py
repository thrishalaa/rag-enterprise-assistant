import json
from datetime import datetime

LOG_PATH = "evaluation/human_eval_log.jsonl"

def log_evaluation(question, answer, context, correct, hallucination, notes=""):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "answer": answer,
        "context_used": context,
        "correct": correct,      # 1 or 0
        "hallucination": hallucination,  # 1 or 0
        "notes": notes
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
