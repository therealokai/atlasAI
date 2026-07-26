// eval/k6-golden-set.js
//
// Day 9 — load generator. Replays every prompt in golden-set-v1.json
// against the gateway's /v1/chat pass-through, at a configurable
// concurrency. This is the plumbing that Day 10 drives at concurrency
// 1 / 4 / 16 / 64 to produce the baseline report.
//
// k6 gives end-to-end request latency (client -> gateway -> vLLM ->
// client). The finer-grained TTFT / TPOT numbers come from vLLM's own
// /metrics histograms scraped by Prometheus — this script's job is
// purely to *generate the traffic*, not to measure the internals.
//
// Run (no host install needed — official image + host network):
//   docker run --rm -i --network host -v "$PWD/eval:/eval" \
//     grafana/k6 run -e CONCURRENCY=1 /eval/k6-golden-set.js
//
// Day 10 just changes -e CONCURRENCY=4 / 16 / 64.

import http from 'k6/http';
import { check } from 'k6';
import { SharedArray } from 'k6/data';
import exec from 'k6/execution';

const GATEWAY_URL = __ENV.GATEWAY_URL || 'http://localhost:8081/v1/chat';
const MODEL_NAME = __ENV.MODEL_NAME || 'Qwen/Qwen2.5-3B-Instruct-AWQ';
const CONCURRENCY = parseInt(__ENV.CONCURRENCY || '1', 10);

// Same persona the Day 8 eval harness (run_golden_set.py) uses, so the
// load test exercises the model under the prompt AtlasAI ships with —
// not a bare prompt with a different token profile.
const SYSTEM_PROMPT =
  'أنت أطلس، مساعد عقاري ذكي. تتحدث دائمًا باللغة العربية الفصحى، ' +
  'بأسلوب مختصر وواضح ومباشر، مثل محادثة إنسانية طبيعية وليس كإجابة رسمية طويلة.';

// Loaded once and shared across all VUs (SharedArray) instead of each
// VU parsing the JSON into its own memory.
const prompts = new SharedArray('golden set', function () {
  return JSON.parse(open('./golden-set-v1.json'));
});

export const options = {
  scenarios: {
    replay: {
      // Replay the golden set exactly once, total, spread across
      // CONCURRENCY virtual users. iterations = number of prompts.
      executor: 'shared-iterations',
      vus: CONCURRENCY,
      iterations: prompts.length,
      maxDuration: '10m',
    },
  },
  thresholds: {
    // Not SLO gates yet (that's Day 10 vs §1.3) — just a sanity floor so
    // a totally broken harness fails loudly instead of "passing" empty.
    http_req_failed: ['rate<0.05'],
  },
};

export default function () {
  // Global iteration index -> prompt index, so across all VUs each
  // prompt is sent exactly once.
  const record = prompts[exec.scenario.iterationInTest];

  const payload = JSON.stringify({
    model: MODEL_NAME,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      { role: 'user', content: record.prompt },
    ],
    max_tokens: 300,
    temperature: 0.3,
  });

  const res = http.post(GATEWAY_URL, payload, {
    headers: { 'Content-Type': 'application/json' },
    timeout: '120s',
    tags: { message_type: record.message_type },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has a completion': (r) => {
      try {
        return !!r.json('choices.0.message.content');
      } catch (e) {
        return false;
      }
    },
  });
}
