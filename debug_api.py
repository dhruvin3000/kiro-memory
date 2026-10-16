"""Debug: import and hit the API route directly to surface any error."""
import sys, os, traceback
sys.path.insert(0, r'C:\Users\dhruv\kiro-memory')
os.environ['WORKSPACE_PATH'] = r'C:\Users\dhruv\kiro-memory'

try:
    from src.api.app import create_app, get_engine
    print("create_app import OK")
except Exception as e:
    print("IMPORT ERROR:", e)
    traceback.print_exc()
    sys.exit(1)

try:
    # Simulate what get_engine does inside a route
    from src.store.decision_store import DecisionStore
    from src.search.vector_index import VectorIndex
    from src.search.search_engine import SearchEngine
    from pathlib import Path

    decisions_path = r'C:\Users\dhruv\kiro-memory\.kiro\decisions'
    store = DecisionStore(decisions_path)
    index = VectorIndex(str(Path(decisions_path) / 'chroma'))
    engine = SearchEngine(store, index)

    records = store.get_all()
    print(f"Store OK: {len(records)} records")

    from src.api.app import _to_response
    resp = [_to_response(r) for r in records[:2]]
    print(f"Serialization OK: {[r.decision for r in resp]}")
except Exception as e:
    print("RUNTIME ERROR:", e)
    traceback.print_exc()
