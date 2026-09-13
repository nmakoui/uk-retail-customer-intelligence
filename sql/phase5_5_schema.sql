-- Phase 5.5: bridge tables mirroring the enriched NLP output that also
-- lives in MongoDB (per-review documents) - same real data, two models,
-- for an honest SQL vs NoSQL comparison.

DROP TABLE IF EXISTS review_keywords;
DROP TABLE IF EXISTS review_aspects;
DROP TABLE IF EXISTS review_sentiment;

-- One row per review - fixed shape, so a normal table with fixed columns
-- is a natural fit (contrast with review_aspects below).
CREATE TABLE review_sentiment (
    review_id            INTEGER PRIMARY KEY REFERENCES reviews(review_id),
    vader_compound        NUMERIC(6, 4),
    vader_bucket          VARCHAR(20),
    bert_predicted_stars  SMALLINT,
    bert_bucket           VARCHAR(20),
    topic_id              INTEGER,
    topic_label           VARCHAR(200)
);

-- Zero-to-many rows per review (measured: only 59% of reviews have any
-- row here at all, and some have several) - the genuinely variable-shape
-- case. Modelling this in SQL means a separate child table + a JOIN to
-- reconstruct one review's full aspect list; MongoDB stores the same
-- list as a single embedded array in one document.
CREATE TABLE review_aspects (
    aspect_id       SERIAL PRIMARY KEY,
    review_id       INTEGER REFERENCES reviews(review_id),
    aspect          VARCHAR(50),
    sentence        TEXT,
    predicted_stars SMALLINT
);
CREATE INDEX idx_review_aspects_review_id ON review_aspects(review_id);

-- Up to a handful of rows per review (typically 5, fewer for very short
-- reviews) - one-to-many, but far less dramatically variable than aspects.
CREATE TABLE review_keywords (
    keyword_id SERIAL PRIMARY KEY,
    review_id  INTEGER REFERENCES reviews(review_id),
    keyword    VARCHAR(200)
);
CREATE INDEX idx_review_keywords_review_id ON review_keywords(review_id);