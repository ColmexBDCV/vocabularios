# Adding Future Vocabularies

Use one directory per vocabulary under `/vocabularios`.

## Required files

For a vocabulary with slug `example`:

```text
vocabularios/example/index.html
vocabularios/example.ttl
vocabularios/example.jsonld
```

This publishes:

- `/vocabularios/example`
- `/vocabularios/example.ttl`
- `/vocabularios/example.jsonld`

## Recommended RDF pattern

- Use a stable HTTPS namespace controlled by the repository.
- Define the vocabulary itself as a `skos:ConceptScheme` when it includes controlled values.
- Define metadata predicates as `rdf:Property`.
- Define controlled values as `skos:Concept`.
- Add `skos:inScheme` and `skos:topConceptOf` for controlled values.
- Use `rdfs:label` for property labels.
- Use `dcterms:description` and `rdfs:comment` for property definitions.

## Human-readable page checklist

Each vocabulary page should include:

- Vocabulary title.
- Namespace.
- Version or issue date.
- Maintainer.
- Properties with URI, label, and definition.
- Controlled values with URI and label, when applicable.
- Links to Turtle and JSON-LD.

## Index page checklist

Update `/vocabularios/index.html` whenever a vocabulary is added.

Add:

- Vocabulary name.
- Short description.
- Link to documentation page.
- Link to Turtle.
- Link to JSON-LD.

## Validation checklist

Update `tests/validate_vocab.py` or add a new test file so automated validation confirms:

- Turtle parses.
- JSON-LD parses.
- Turtle and JSON-LD contain the same required resources.
- Labels and definitions match the public documentation.
