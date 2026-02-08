
from __future__ import annotations

import os
from typing import Dict, List, Any

import matplotlib.pyplot as plt
import networkx as nx


def render_taxonomy_graph(taxonomy: Dict[str, Any], out_path: str) -> None:
    """
    Creates a simple bipartite visualization:
    Cluster nodes on left, paper nodes on right, edges connect cluster->paper.
    """
    clusters: List[Dict[str, Any]] = taxonomy.get("clusters", [])
    if not clusters:
        raise ValueError("No clusters found in taxonomy JSON")

    G = nx.Graph()

    cluster_nodes = []
    paper_nodes = []

    for c in clusters:
        cid = c["cluster_id"]
        cname = c.get("name", cid)
        cnode = f"{cid}: {cname}"
        cluster_nodes.append(cnode)
        G.add_node(cnode, bipartite=0)

        for pid in c.get("paper_ids", []):
            pnode = pid
            if pnode not in paper_nodes:
                paper_nodes.append(pnode)
                G.add_node(pnode, bipartite=1)
            G.add_edge(cnode, pnode)

    # Positions: clusters on left (x=0), papers on right (x=1)
    pos = {}
    for i, n in enumerate(cluster_nodes):
        pos[n] = (0, -i)
    for i, n in enumerate(sorted(paper_nodes)):
        pos[n] = (1, -i)

    plt.figure(figsize=(10, max(4, 0.6 * max(len(cluster_nodes), len(paper_nodes)))))
    nx.draw(G, pos, with_labels=True, node_size=1600, font_size=9)
    plt.title(taxonomy.get("taxonomy_title", "Taxonomy"))
    plt.tight_layout()

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, dpi=200)
    plt.close()

