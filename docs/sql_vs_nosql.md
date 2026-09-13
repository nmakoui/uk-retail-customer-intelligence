# SQL vs NoSQL: a real comparison, not a token add-on

Both PostgreSQL and MongoDB now hold the same real enrichment data —
9,999 Trustpilot reviews' sentiment scores, topic assignments, aspect-
level sentiment, and extracted keywords — loaded independently into
each store from the same Phase 5 output files. This isn't a synthetic
toy dataset built to make NoSQL look good; it's the actual customer-
voice data this project already produced, modelled two different ways.

## The concrete evidence

Review 10166 (a 3-star review about a faulty returns process) has an
unusually rich aspect breakdown: 20 separate aspect mentions across its
text, plus 5 extracted keywords.

**Reconstructing that one review's full profile in SQL** requires
joining `reviews` to three child tables (`review_sentiment`,
`review_aspects`, `review_keywords`):

```sql
SELECT r.review_id, r.stars, rs.vader_bucket, rs.topic_label,
       ra.aspect, ra.sentence AS aspect_sentence,
       rk.keyword
FROM reviews r
JOIN review_sentiment rs ON rs.review_id = r.review_id
LEFT JOIN review_aspects ra ON ra.review_id = r.review_id
LEFT JOIN review_keywords rk ON rk.review_id = r.review_id
WHERE r.review_id = 10166;
```

**Result: 100 rows returned for one review** — the two one-to-many
joins (20 aspects × 5 keywords) multiply against each other, a classic
relational "join fan-out." None of those 100 rows is wrong, but none of
them is independently meaningful either — they're all fragments of one
review's profile that has to be reassembled by the calling code.

**The same review in MongoDB is one call, one document:**

```python
db["reviews"].find_one({"_id": 10166})
```

Returns a single document with `aspects` as a 20-item array and
`keywords` as a 5-item array, nested exactly where they belong — no
reassembly required.

## How common is this, not just how extreme

Review 10166 is a striking example, not a cherry-picked worst case in
the other direction: across the full 9,999-review sample, only 5,895
reviews (59%) have *any* aspect mention at all — the other 41% have
none. Among the ones that do, aspect count varies from 1 up to 20+.
That's a genuinely variable, sparse shape, not an evenly-distributed
one — exactly the case a fixed-column relational table struggles to
represent efficiently, and a document model represents naturally as
"however many array elements this particular document happens to have."

## Where the relational model is the better fit

The parts of this same enrichment that *are* fixed-shape — one VADER
score, one BERT sentiment label, one topic assignment per review — sit
comfortably in `review_sentiment` as a plain table with a foreign key
back to `reviews(review_id)`. That gets real, enforced referential
integrity for free (Postgres will reject an aspect row for a review_id
that doesn't exist; MongoDB's per-review documents don't have an
equivalent database-level guarantee, since each document is
self-contained rather than checked against a canonical source table).
It also means this data lives in the same schema, same connection, and
same SQL toolkit (joins, CTEs, window functions) as the rest of the
project's customer and transaction data from Phase 3.5/4 — one
consistent way of querying, rather than switching mental models for
one table out of many.

## The honest conclusion

Neither store is simply "better" here — they're better *at different
parts of the same real dataset*, which is why this project ended up
with both rather than picking one:

- **Fixed-shape, always-present, one-per-review data** (star rating,
  sentiment scores, topic ID) → relational, for integrity and
  consistency with the rest of the schema.
- **Sparse, variable-cardinality, nested data** (which aspects were
  mentioned, how many, extracted keywords) → document store, because
  the shape genuinely varies review to review and forcing it into
  fixed columns either wastes space (many NULL aspect columns) or
  causes join fan-out (a separate child table, as shown above).

One honest limitation: this comparison is about data-modelling fit and
query ergonomics, not a load-tested performance benchmark. At 9,999
reviews, both databases handle either approach instantly — the real
argument for polyglot persistence shows up as data volume and
variability grow, not as a raw speed difference at this scale.