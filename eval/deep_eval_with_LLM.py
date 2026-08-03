import csv
import json
import os
import time

from deepeval import evaluate
from deepeval.metrics import AnswerRelevancyMetric, GEval
from deepeval.models import GeminiModel
from deepeval.test_case import LLMTestCase, SingleTurnParams
from openai import OpenAI

# ---------------------------------------------------------------------------
# 1. Setup Gemini Judge & Rate Limit Settings
# ---------------------------------------------------------------------------
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
VLLM_URL = os.getenv("VLLM_BASE_URL") + "/v1"

# Throttle delay to prevent rate limits
REQUEST_DELAY_SECONDS = 20.0

# Initialize Gemini as Judge Model
judge_model = GeminiModel(
    model="gemini-3.1-flash-lite",
    api_key=GEMINI_KEY,
    temperature=0.0
)

# ---------------------------------------------------------------------------
# 2. Define DeepEval Metrics
# ---------------------------------------------------------------------------
relevancy_metric = AnswerRelevancyMetric(
    threshold=0.7,
    model=judge_model
)

correctness_metric = GEval(
    name="Arabic Instruction & Correctness",
    criteria="Determine whether the 'actual_output' accurately answers the Arabic 'input', maintains fluent Arabic phrasing, and aligns with 'expected_output'.",
    evaluation_params=[
        SingleTurnParams.INPUT,
        SingleTurnParams.ACTUAL_OUTPUT,
        SingleTurnParams.EXPECTED_OUTPUT
    ],
    threshold=0.7,
    model=judge_model
)

metrics = [relevancy_metric, correctness_metric]

# ---------------------------------------------------------------------------
# 3. Load Dataset & Run Evaluation
# ---------------------------------------------------------------------------
def run_evaluation():
    client = OpenAI(base_url=VLLM_URL, api_key="EMPTY")
    model_name = client.models.list().data[0].id
    clean_model_name = model_name.replace("/", "_").replace("\\", "_")
    csv_filename = f"{clean_model_name}_deepeval.csv"
    
    print(f"Loaded vLLM model: {model_name}")
    with open(r"golden-set-v1.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    dataset = dataset[29:50]  # sample dataset
    print(f"🚀 Starting evaluation for model: {model_name}")
    print(f"📊 Total items: {len(dataset)} | Judge: Gemini API")

    test_cases = []
    
    # 1. Get predictions from local vLLM
    for idx, item in enumerate(dataset):
        query = item.get("prompt")
        expected = item.get("response")
        
        res = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "أنت مساعد ذكي ومفيد."},
                {"role": "user", "content": query}
            ],
            temperature=0.2
        )
        actual_output = res.choices[0].message.content

        tc = LLMTestCase(
            input=query,
            actual_output=actual_output,
            expected_output=expected
        )
        print(f"Test no: {idx}\nPrompt: {query}\nActual Output: {actual_output}")
        test_cases.append(tc)

    # 2. Rate-limited evaluation loop with CSV logging
    print("\n⚖️ Running DeepEval Evaluation with Gemini Judge...")
    for idx, tc in enumerate(test_cases, start=29):
        print(f"\n--- Evaluating Test Case {idx + 1}/{len(test_cases)} ---")
        
        # Capture evaluation result object
        results = evaluate([tc], metrics)
        
        ans_rel = 0.0
        exp_out_rel = 0.0

        if results and results.test_results and results.test_results[0].metrics_data:
            for m_data in results.test_results[0].metrics_data:
                # Use 'in' substring matching to account for DeepEval's '[GEval]' suffix
                if "Answer Relevancy" in m_data.name:
                    ans_rel = m_data.score if m_data.score is not None else 0.0
                elif "Arabic Instruction & Correctness" in m_data.name:
                    exp_out_rel = m_data.score if m_data.score is not None else 0.0

        print(f"Scores -> Answer Relevancy: {ans_rel}, Correctness: {exp_out_rel}")

        # Write to CSV
        file_exists = os.path.isfile(csv_filename)
        with open(csv_filename, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["Test_no", "answer_relevance", "expected_output_relevance"])
            writer.writerow([idx, ans_rel, exp_out_rel])
        
        time.sleep(REQUEST_DELAY_SECONDS)

if __name__ == "__main__":
    run_evaluation()