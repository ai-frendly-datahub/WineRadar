"""Plotly network graph plugin for WineRadar unified templates."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any


def get_chart_config(store: Any = None, articles: Any = None) -> dict[str, Any] | None:
    """Generate Plotly network graph config for grape variety-region co-occurrence.

    Args:
        store: Graph store object (unused, for plugin interface compatibility)
        articles: Articles list (unused, for plugin interface compatibility)

    Returns:
        Plugin config dict with id, title, and config_json, or None if generation fails
    """
    # For now, return None since we don't have access to sections data
    # This will be called from reporter.py with proper context
    return None


def get_chart_config_from_sections(
    sections: dict[str, list[Any]],
    target_nodes: int = 80,
) -> dict[str, Any] | None:
    """Generate Plotly network graph from report sections.

    Args:
        sections: Dictionary of report sections with ViewItem lists
        target_nodes: Target number of nodes to display (50-100)

    Returns:
        Plugin config dict with id, title, and config_json, or None if generation fails
    """
    try:
        import networkx as nx
        import plotly.graph_objects as go
    except ModuleNotFoundError:
        return None

    bounded_target_nodes = max(50, min(100, target_nodes))

    edge_weights: Counter[tuple[str, str]] = Counter()
    node_weights: Counter[tuple[str, str]] = Counter()

    for item in _collect_unique_items(sections):
        entities = _extract_entities(item)

        grape_varieties = sorted(set(_normalize_entity_values(entities.get("grape_variety"))))
        regions = sorted(set(_normalize_entity_values(entities.get("region"))))

        if not grape_varieties or not regions:
            continue

        for grape_variety in grape_varieties:
            for region in regions:
                edge_weights[(grape_variety, region)] += 1
                node_weights[("grape_variety", grape_variety)] += 1
                node_weights[("region", region)] += 1

    if not edge_weights:
        return None

    selected_node_keys = {
        node_key
        for node_key, _ in node_weights.most_common(min(bounded_target_nodes, len(node_weights)))
    }

    graph = nx.Graph()
    for node_type, label in selected_node_keys:
        graph.add_node(
            f"{node_type}:{label}",
            label=label,
            node_type=node_type,
            weight=node_weights[(node_type, label)],
        )

    for (grape_variety, region), weight in edge_weights.items():
        variety_key = ("grape_variety", grape_variety)
        region_key = ("region", region)
        if variety_key in selected_node_keys and region_key in selected_node_keys:
            graph.add_edge(
                f"grape_variety:{grape_variety}",
                f"region:{region}",
                weight=weight,
            )

    isolated_nodes = [node for node, degree in graph.degree() if degree == 0]
    graph.remove_nodes_from(isolated_nodes)

    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        return None

    if graph.number_of_nodes() <= 2:
        positions = nx.circular_layout(graph)
    else:
        positions = nx.spring_layout(graph, seed=42, weight="weight")

    edge_traces = []
    for source, target, metadata in graph.edges(data=True):
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        weight = metadata.get("weight", 1)
        hover_text = (
            f"{graph.nodes[source]['label']} ↔ {graph.nodes[target]['label']}"
            f"<br>Co-occurrence: {weight}"
        )

        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line={
                    "width": 0.75 + min(weight, 8) * 0.35,
                    "color": "rgba(120, 120, 120, 0.45)",
                },
                hoverinfo="text",
                text=[hover_text, hover_text, hover_text],
                showlegend=False,
            )
        )

    def _build_node_trace(
        node_type: str,
        trace_name: str,
        color: str,
    ) -> Any | None:
        node_x: list[float] = []
        node_y: list[float] = []
        labels: list[str] = []
        weights: list[int] = []

        for node_id, metadata in graph.nodes(data=True):
            if metadata.get("node_type") != node_type:
                continue

            x_pos, y_pos = positions[node_id]
            node_x.append(float(x_pos))
            node_y.append(float(y_pos))
            labels.append(str(metadata.get("label", "")))
            weights.append(int(metadata.get("weight", 1)))

        if not node_x:
            return None

        marker_sizes = [10 + min(weight, 20) * 1.2 for weight in weights]

        return go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            text=labels,
            customdata=weights,
            hovertemplate="<b>%{text}</b><br>Co-occurrence score: %{customdata}<extra></extra>",
            marker={
                "size": marker_sizes,
                "color": color,
                "line": {"width": 1.4, "color": "#ffffff"},
                "opacity": 0.9,
            },
            name=trace_name,
        )

    traces: list[Any] = list(edge_traces)
    variety_trace = _build_node_trace("grape_variety", "Grape Variety", "#7b3f98")
    region_trace = _build_node_trace("region", "Region", "#2f7f5f")
    if variety_trace is not None:
        traces.append(variety_trace)
    if region_trace is not None:
        traces.append(region_trace)

    fig = go.Figure(data=traces)
    fig.update_layout(
        title="Variety-Region Co-occurrence Network",
        template="plotly_white",
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
        height=680,
        margin={"l": 20, "r": 20, "t": 70, "b": 20},
        xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        hovermode="closest",
    )

    html_content = fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={"displayModeBar": False, "responsive": True},
    )

    return {
        "id": "network_graph",
        "title": "Entity Co-occurrence Network",
        "config_json": html_content,
    }


def _collect_unique_items(sections: dict[str, list[Any]]) -> list[Any]:
    """Collect unique items from all sections by URL."""
    unique_items: dict[str, Any] = {}

    for items in sections.values():
        for item in items:
            url = item.get("url")
            if isinstance(url, str) and url and url not in unique_items:
                unique_items[url] = item

    return list(unique_items.values())


def _normalize_entity_values(values: Any) -> list[str]:
    """Normalize entity values to list of strings."""
    if not isinstance(values, list):
        return []

    normalized: list[str] = []
    for value in values:
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                normalized.append(cleaned)

    return normalized


def _extract_entities(item: Any) -> dict[str, list[str]]:
    """Extract entities from a ViewItem."""
    item_data: dict[str, Any] = dict(item)

    entities_obj = item_data.get("entities")
    if isinstance(entities_obj, dict):
        normalized_entities: dict[str, list[str]] = {}
        for entity_type, values in entities_obj.items():
            normalized_values = _normalize_entity_values(values)
            if normalized_values:
                normalized_entities[entity_type] = normalized_values
        if normalized_entities:
            return normalized_entities

    entities_json = item_data.get("entities_json")
    if not isinstance(entities_json, str):
        return {}

    try:
        parsed_entities = json.loads(entities_json)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed_entities, dict):
        return {}

    normalized_from_json: dict[str, list[str]] = {}
    for entity_type, values in parsed_entities.items():
        normalized_values = _normalize_entity_values(values)
        if normalized_values:
            normalized_from_json[entity_type] = normalized_values

    return normalized_from_json
