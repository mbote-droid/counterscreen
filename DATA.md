# Data sources and their terms

Every external dataset this project touches is recorded here before it is
used, with the terms it arrives under and the obligation those terms place on
us. Licences on biological databases are not uniform: some are public domain,
some require attribution, and some are share-alike, which can reach through
into anything we redistribute.

## The rule

**A source whose `Status` below is not `confirmed` must not be ingested.**

This is a gate, not a note. The reason is asymmetry: using a CC0 source as
though it were share-alike costs nothing, while redistributing a share-alike
database as though it were public domain is a licensing breach that is
awkward to undo once results are published and mirrored. The cost of
confirming a row is one visit to the source's terms page; the cost of getting
it wrong is retraction of a release.

Confirming a row means: open the source's own terms page, record the licence
identifier and the retrieval date, and attach the checksum of what was
actually downloaded to the provenance manifest. A licence identifier
remembered from elsewhere is not a confirmation.

## Sources

| Source | What we take | Terms | Obligation on us | Status |
|---|---|---|---|---|
| RCSB PDB | Experimental structures for targets and decoys | CC0 1.0 (public domain dedication) | Cite the individual structure DOIs; no licence obligation | `confirmed` |
| UniProt | Reference sequences, isoform records | CC-BY-4.0 | Attribute UniProt in any redistribution | `confirmed` |
| AlphaFold DB | Predicted structures where no experimental one exists | CC-BY-4.0 | Attribute; note model confidence alongside any use | `confirmed` |
| IEDB | Epitope records for the counter-screen panel | Free to use, attribution required | Cite IEDB; re-check whether redistribution of derived subsets is permitted | `unconfirmed` |
| VDJdb | TCR specificity records | Attribution-style, believed CC-BY | Attribute, and cite the contributing studies, not only the database | `unconfirmed` |
| Open Data Commons source (ODC-ODbL) | To be identified | ODbL 1.0, share-alike | Share-alike reaches derived databases: a derived database we publish must carry ODbL too | `unconfirmed` |
| Foldseek reference databases | Novelty search against known folds (gate G9) | Depends on the specific database built or downloaded | Record which database build was used; terms follow its constituent sources | `unconfirmed` |

## Why the share-alike rows matter most

ODbL's share-alike condition applies to a *derived database*, which is a
broader category than a derived work. A counter-screen panel assembled from
an ODbL source, and shipped in this repository as a table, is plausibly a
derived database. If that is so, the panel file carries ODbL regardless of
this project's MIT and CC-BY-4.0 licences, and the repository must say so at
the file level rather than only at the root.

That determination has to be made before the panel is committed, because
`campaigns/*/results/` is append-only: a file committed under the wrong
licence cannot be quietly removed from history.

## Model weights and third-party software

Weights and large databases are never committed (see `.gitignore`); they are
checksummed in the provenance manifest instead. Their licences are separate
from the data licences above and are recorded per-adapter:

| Component | Licence status |
|---|---|
| RFdiffusion | Open weights; confirm the release's own terms |
| ProteinMPNN | MIT |
| ESMFold2 | Confirm; ESM releases have varied in terms between versions |
| Protenix | Confirm per release |
| Boltz | Confirm per release |
| AF2-initial-guess | Derived from AlphaFold2; non-commercial restrictions may apply to weights |
| PyRosetta | Licence required; free for non-commercial academic use, commercial use is separately licensed — **unresolved, see open questions** |

## Open questions

- PyRosetta licence status for this project's intended use.
- Which Open Data Commons source is in scope, and whether the panel we
  derive from it is a "derived database" under ODbL 1.0.
- Whether IEDB permits redistribution of derived subsets, or only citation.
