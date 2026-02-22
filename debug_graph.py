import sys
sys.path.insert(0, '.')
from tools.gimo_server.services.ops_service import OpsService
from tools.gimo_server.services.plan_graph_builder import build_graph_from_ops_plan

drafts = OpsService.list_drafts()
print(f'Total drafts: {len(drafts)}')
for d in drafts:
    print(f'  id={d.id} status={d.status} structured={d.context.get("structured")}')

structured_drafts = [d for d in drafts if d.context.get("structured") and d.status == "draft"]
print(f'\nStructured+draft: {len(structured_drafts)}')
if structured_drafts:
    latest = structured_drafts[0]
    print(f'Latest draft id: {latest.id}')
    print(f'Content preview: {latest.content[:200]}')
    try:
        nodes, edges = build_graph_from_ops_plan(latest.content, draft_id=latest.id)
        print(f'Nodes: {len(nodes)} Edges: {len(edges)}')
        if nodes:
            print('First node:', nodes[0])
    except Exception as e:
        import traceback
        print(f'ERROR in build_graph: {e}')
        traceback.print_exc()
