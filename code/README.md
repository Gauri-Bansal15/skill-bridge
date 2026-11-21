# code/

The source code lives at the top level of the repository so it can be run and deployed directly:

| What | Where |
|---|---|
| Web app (Streamlit) | [`../app.py`](../app.py) |
| Python package (analyzer, Gemini client, privacy, scoring, offline engine, CLI) | [`../src/skillbridge/`](../src/skillbridge/) |
| Tests (pytest) | [`../tests/`](../tests/) |
| Evaluation and test-table runners | [`../evaluation/`](../evaluation/) |
| Helper scripts (diagrams, submission check) | [`../scripts/`](../scripts/) |

Run it: `pip install -r requirements.txt` then `streamlit run app.py`.
