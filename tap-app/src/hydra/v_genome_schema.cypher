// ============================================================================
// V-Genome schema for HYDRA (Neo4j 5.x)
// Branch: hybrid | APP_Opzione_Ibrida
// ============================================================================

// ----------------------------------------------------------------------------
// Constraints / indexes
// ----------------------------------------------------------------------------
CREATE CONSTRAINT attack_technique_id IF NOT EXISTS
    FOR (t:AttackTechnique) REQUIRE t.technique_id IS UNIQUE;

CREATE CONSTRAINT target_model_id IF NOT EXISTS
    FOR (m:TargetModel) REQUIRE m.model_id IS UNIQUE;

CREATE CONSTRAINT defense_layer_id IF NOT EXISTS
    FOR (d:DefenseLayer) REQUIRE d.layer_id IS UNIQUE;

CREATE INDEX technique_burned IF NOT EXISTS
    FOR (t:AttackTechnique) ON (t.burned);

CREATE INDEX technique_asr IF NOT EXISTS
    FOR (t:AttackTechnique) ON (t.asr);

CREATE INDEX technique_stealth IF NOT EXISTS
    FOR (t:AttackTechnique) ON (t.stealth);

// ----------------------------------------------------------------------------
// Example seed nodes (run after constraints)
// ----------------------------------------------------------------------------
CREATE (:TargetModel { model_id: "hackinga0", name: "@HackingA0", platform: "twitter" });

CREATE (:DefenseLayer { layer_id: "input_filter", name: "Input Filter" });
CREATE (:DefenseLayer { layer_id: "alignment", name: "Model Alignment" });
CREATE (:DefenseLayer { layer_id: "output_moderation", name: "Output Moderation" });

CREATE (:AttackTechnique {
    technique_id: "crescendo",
    name: "Crescendo / Foot-in-the-Door",
    category: "incremental",
    asr: 0.62,
    stealth: 0.78,
    burned: false,
    cost_usd: 0.04,
    avg_turns: 4.0,
    tags: ["persuasion", "multi-turn"]
});

CREATE (:AttackTechnique {
    technique_id: "pap_authority",
    name: "Psychological Authority Persuasion",
    category: "persuasion",
    asr: 0.55,
    stealth: 0.71,
    burned: false,
    cost_usd: 0.03,
    avg_turns: 2.5,
    tags: ["pap", "authority"]
});

// ----------------------------------------------------------------------------
// Example relationships
// ----------------------------------------------------------------------------
MATCH (t:AttackTechnique {technique_id: "crescendo"}),
      (m:TargetModel {model_id: "hackinga0"})
CREATE (t)-[:TARGETS {asr: 0.62, stealth: 0.78, observed_at: datetime()}]->(m);

MATCH (t:AttackTechnique {technique_id: "crescendo"}),
      (d:DefenseLayer {layer_id: "alignment"})
CREATE (t)-[:COUNTERS {evidence: "gradual escalation detected", observed_at: datetime()}]->(d);

MATCH (a:AttackTechnique {technique_id: "crescendo"}),
      (b:AttackTechnique {technique_id: "pap_authority"})
CREATE (a)-[:COMPLEMENTS {strength: 0.85}]->(b);
