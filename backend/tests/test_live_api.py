import urllib.request
import json

BASE_URL = "http://localhost:8000"

def test_live_health():
    url = f"{BASE_URL}/api/health"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode())
        assert data["status"] == "healthy"
        print(f"PASS Live Health: {data}")

def test_live_samples():
    url = f"{BASE_URL}/api/samples"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode())
        assert len(data) >= 4
        print(f"PASS Live Samples: fetched {len(data)} educational samples")

def test_live_analyze():
    url = f"{BASE_URL}/api/analyze"
    payload = json.dumps({
        "source_code": "int main() { int x = 5 + 10 * 2; return x; }"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode())
        assert data["success"] is True
        assert data["is_syntactically_valid"] is True
        assert len(data["tokens"]) > 0
        assert data["ast"] is not None
        assert len(data["symbol_table"]) >= 1
        assert len(data["intermediate_code"]) >= 1
        print(f"PASS Live Analyze: {len(data['tokens'])} tokens, {len(data['symbol_table'])} symbols, {len(data['intermediate_code'])} TAC instrs")

def test_live_diagnose_and_fix():
    url = f"{BASE_URL}/api/ai/diagnose-and-fix"
    payload = json.dumps({
        "source_code": "int main() { int x = 10\n return 0;\n"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode())
        assert data["is_parser_validated"] is True
        assert data["validation_status"] == "PARSER_VALIDATED"
        assert len(data["diff_lines"]) > 0
        print(f"PASS Live AI Diagnose & Fix: status={data['validation_status']}, provider={data['provider_used']}")

def test_live_concept_explain():
    url = f"{BASE_URL}/api/ai/explain-concept"
    payload = json.dumps({
        "concept_id": "syntax_analysis"
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode())
        assert "Syntax Analysis" in data["title"]
        print(f"PASS Live Concept Explain: {data['title']}")

if __name__ == "__main__":
    test_live_health()
    test_live_samples()
    test_live_analyze()
    test_live_diagnose_and_fix()
    test_live_concept_explain()
    print("\n=== ALL LIVE API TESTS PASSED! ===")
