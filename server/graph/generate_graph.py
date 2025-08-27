import graphviz

# Create a graph from the DOT source
graph = graphviz.Source('''
digraph FactCheckGraph {
    rankdir=LR;
    node [shape=box, style=rounded, fontname="Helvetica"];

    // Core
    ClaimModel [label="ClaimModel (claims)"];
    Source [label="Source (sources)"];
    Actor [label="Actor (actors)"];
    Entity [label="Entity (entities)"];
    ClaimEntity [label="ClaimEntity (claim_entities)"];
    ClaimEvent [label="ClaimEvent (claim_events)"];
    ActorMetricsDaily [label="ActorMetricsDaily"];
    SourceMetricsDaily [label="SourceMetricsDaily"];
    VariantCluster [label="VariantCluster"];
    EventVariant [label="EventVariant"];
    ClaimVariant [label="ClaimVariant"];

    // Relationships
    ClaimModel -> Source [label="source_id"];
    ClaimModel -> Actor [label="fact_checker_id"];
    ClaimModel -> Entity [label="many-to-many via ClaimEntity"];
    ClaimModel -> ClaimEvent [label="has events"];
    ClaimModel -> ClaimVariant [label="variant_id"];

    Source -> Actor [label="source_id"];
    Source -> ClaimEvent [label="events"];
    Source -> SourceMetricsDaily [label="metrics"];

    Actor -> ClaimEvent [label="events"];
    Actor -> ActorMetricsDaily [label="metrics"];
    Actor -> ClaimModel [label="fact_checked_claims"];

    Entity -> ClaimEntity [label="link table"];
    ClaimEntity -> ClaimModel;
    ClaimEntity -> Entity;

    ClaimEvent -> Actor;
    ClaimEvent -> Source;
    ClaimEvent -> VariantCluster [label="via EventVariant"];

    VariantCluster -> ClaimVariant [label="claims"];
    VariantCluster -> EventVariant [label="events"];
}
''')

# Render the graph to PNG format
graph.render("FactCheckGraph", format="png", cleanup=True)