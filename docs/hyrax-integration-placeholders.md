# Hyrax Integration Placeholders

This vocabulary package is deployed outside Hyrax. Hyrax should reference the public URIs and controlled values, not serve the files itself.

Inspect your local Hyrax version, work type classes, form classes, indexers, and presenter/display conventions before applying the placeholders below.

## Vocabulary constants

Create an application-level constant or configuration file in Hyrax:

```ruby
# PLACEHOLDER_HYRAX_APP_PATH/config/initializers/local_vocabularies.rb
module LocalVocabularies
  module SEAES
    NAMESPACE = 'https://biblioteca.colmex.mx/vocabularios/seaes#'

    PROPERTIES = {
      criterio_seaes: "#{NAMESPACE}criterio_seaes",
      justificacion_seaes: "#{NAMESPACE}justificacion_seaes",
      seaes: "#{NAMESPACE}seaes"
    }.freeze

    CRITERIA = {
      'compromiso_responsabilidad_social' => 'Compromiso con la responsabilidad social',
      'equidad_social_genero' => 'Equidad social y de género',
      'inclusion' => 'Inclusión',
      'excelencia' => 'Excelencia',
      'innovacion_social' => 'Innovación social',
      'vanguardia' => 'Vanguardia',
      'interculturalidad' => 'Interculturalidad'
    }.freeze
  end
end
```

## Thesis work model

Add properties to the thesis work model using the local Hyrax pattern for RDF predicates.

```ruby
property :criterio_seaes,
         predicate: RDF::URI(LocalVocabularies::SEAES::PROPERTIES.fetch(:criterio_seaes)),
         multiple: true

property :justificacion_seaes,
         predicate: RDF::URI(LocalVocabularies::SEAES::PROPERTIES.fetch(:justificacion_seaes)),
         multiple: true

property :seaes,
         predicate: RDF::URI(LocalVocabularies::SEAES::PROPERTIES.fetch(:seaes)),
         multiple: true
```

Use `criterio_seaes` for controlled vocabulary selection, search indexing, facets, and reporting.

Use `justificacion_seaes` for free-text student explanation.

Use `seaes` as the authoritative display/export value when the UI cannot safely preserve the order pairing between criteria and justifications.

## Data rule

Only affirmative correlations should be stored.

Do not store criteria marked `No se correlaciona` in `criterio_seaes` or `seaes`.

## Pairing rule

When saving a selected criterion and its explanation, persist a combined `seaes` value:

```text
Criterion: justification
```

Example:

```text
Inclusión: La tesis se correlaciona con este criterio porque analiza condiciones de participación social y acceso institucional de grupos en situación de desigualdad.
```

If the Hyrax form stores repeatable field arrays independently, treat `seaes` as the display/export source because it preserves the criterion-to-justification relationship in one value.

## Labels

Use these labels in model/forms/display:

```yaml
es:
  simple_form:
    labels:
      defaults:
        criterio_seaes: Criterio SEAES
        justificacion_seaes: Justificación SEAES
        seaes: Criterios SEAES
  blacklight:
    search:
      fields:
        facet:
          criterio_seaes_sim: Criterio SEAES
        show:
          seaes_tesim: Criterios SEAES
```

Adjust Solr field suffixes to match repository conventions.

## Form behavior

Recommended form behavior:

- `criterio_seaes`: controlled select or checkbox list using `LocalVocabularies::SEAES::CRITERIA`.
- `justificacion_seaes`: free text input paired in the UI with the selected criterion.
- `seaes`: generated hidden or read-only repeated value containing `Criterion: justification`.

Do not present `No se correlaciona` as a stored vocabulary value. If it appears in the UI, treat it as an instruction to omit that criterion.

## Indexing

Index according to local repository conventions:

```ruby
def generate_solr_document
  super.tap do |solr_doc|
    solr_doc['criterio_seaes_sim'] = object.criterio_seaes
    solr_doc['seaes_tesim'] = object.seaes
  end
end
```

Do not add `justificacion_seaes` as a facet.

## Display

Public display should show:

```text
Criterios SEAES
```

Values should come from `seaes`, not from independently zipped `criterio_seaes` and `justificacion_seaes`, unless the application has a tested pairing mechanism.

## Hyrax test checklist

Add or update application tests for:

- Thesis model properties and predicates.
- Thesis form labels and controlled values.
- Free text entry for `justificacion_seaes`.
- Combined `seaes` persistence.
- `criterio_seaes` indexing for search/faceting/reporting.
- `seaes` display/export indexing.
- No facet on `justificacion_seaes`.
- Public show page displays `Criterios SEAES` and combined values.
- Negative values are not persisted or indexed.
