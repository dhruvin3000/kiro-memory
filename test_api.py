import sys, os
sys.path.insert(0, '.')
os.environ['WORKSPACE_PATH'] = r'C:\Users\dhruv\kiro-memory'

try:
    from src.store.decision_store import DecisionStore
    from src.search.vector_index import VectorIndex
    from src.search.search_engine import SearchEngine
    from pathlib import Path

    workspace = os.environ['WORKSPACE_PATH']
    decisions_path = str(Path(workspace) / '.kiro' / 'decisions')
    store = DecisionStore(decisions_path)
    index = VectorIndex(str(Path(decisions_path) / 'chroma'))
    engine = SearchEngine(store, index)

    records = store.get_all()
    print(f"Store OK: {len(records)} decisions")

    results = engine.search("database", top_k=3)
    print(f"Search OK: {len(results)} results for 'database'")
    for r in results:
        print(f"  - {r.decision}")
except Exception as e:
    import traceback
    traceback.print_exc()
