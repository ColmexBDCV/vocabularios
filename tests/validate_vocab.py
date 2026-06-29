from pathlib import Path
import json

from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS, SKOS, DCTERMS


ROOT = Path(__file__).resolve().parents[1]
TTL = ROOT / "vocabularios" / "seaes.ttl"
JSONLD = ROOT / "vocabularios" / "seaes.jsonld"
BASE = "https://biblioteca.colmex.mx/vocabularios/seaes"
NS = f"{BASE}#"

PROPERTIES = {
    "criterio_seaes": (
        "Criterio SEAES",
        "Registra el criterio SEAES con el que una tesis se correlaciona.",
    ),
    "justificacion_seaes": (
        "Justificación SEAES",
        "Registra la justificación breve de la correlación entre una tesis y el criterio SEAES seleccionado.",
    ),
    "seaes": (
        "SEAES",
        "Registra en una sola expresión el criterio SEAES y su justificación.",
    ),
}

CONCEPTS = {
    "compromiso_responsabilidad_social": "Compromiso con la responsabilidad social",
    "equidad_social_genero": "Equidad social y de género",
    "inclusion": "Inclusión",
    "excelencia": "Excelencia",
    "innovacion_social": "Innovación social",
    "vanguardia": "Vanguardia",
    "interculturalidad": "Interculturalidad",
}


def parse_graph(path, fmt):
    graph = Graph()
    graph.parse(path, format=fmt)
    return graph


def literal_values(graph, subject, predicate):
    return {str(value) for value in graph.objects(subject, predicate)}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def validate_graph(graph, label):
    scheme = URIRef(BASE)
    require((scheme, RDF.type, SKOS.ConceptScheme) in graph, f"{label}: missing ConceptScheme")

    for name, (expected_label, expected_definition) in PROPERTIES.items():
        uri = URIRef(f"{NS}{name}")
        require((uri, RDF.type, RDF.Property) in graph, f"{label}: {name} is not rdf:Property")
        require(expected_label in literal_values(graph, uri, RDFS.label), f"{label}: missing label for {name}")
        require(
            expected_definition in literal_values(graph, uri, DCTERMS.description),
            f"{label}: missing definition for {name}",
        )

    for name, expected_label in CONCEPTS.items():
        uri = URIRef(f"{NS}{name}")
        require((uri, RDF.type, SKOS.Concept) in graph, f"{label}: {name} is not skos:Concept")
        require(expected_label in literal_values(graph, uri, SKOS.prefLabel), f"{label}: missing prefLabel for {name}")
        require((uri, SKOS.inScheme, scheme) in graph, f"{label}: {name} missing skos:inScheme")


def resource_set(graph):
    expected = {URIRef(BASE)}
    expected.update(URIRef(f"{NS}{name}") for name in PROPERTIES)
    expected.update(URIRef(f"{NS}{name}") for name in CONCEPTS)
    return {subject for subject in graph.subjects() if subject in expected}


def main():
    with JSONLD.open("r", encoding="utf-8") as handle:
        json.load(handle)

    turtle_graph = parse_graph(TTL, "turtle")
    jsonld_graph = parse_graph(JSONLD, "json-ld")

    validate_graph(turtle_graph, "Turtle")
    validate_graph(jsonld_graph, "JSON-LD")

    require(
        resource_set(turtle_graph) == resource_set(jsonld_graph),
        "Turtle and JSON-LD do not define the same SEAES resources",
    )

    print("SEAES vocabulary validation passed.")


if __name__ == "__main__":
    main()
