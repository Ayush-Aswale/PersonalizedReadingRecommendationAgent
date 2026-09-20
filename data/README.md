# Dataset Documentation

## Source

This dataset is a curated collection of ~800 well-known books across 10 major genres,
compiled for use in the Personalized Reading Recommendation Agent college project.

## Required Fields

| Field | Description | Source |
|-------|-------------|--------|
| `book_id` | Unique identifier (B0001–B0800) | Generated sequentially |
| `title` | Book title | Reference/public knowledge |
| `author` | Author name | Reference/public knowledge |
| `genre` | Primary genre | Assigned based on commonly accepted categorization |
| `sub_genre` | More specific sub-genre | Assigned based on commonly accepted categorization |
| `pages` | Page count (approximate) | Reference data; some values are approximate |
| `reading_level` | easy / medium / hard | **DERIVED** — see below |
| `avg_rating` | Average rating (1.0–5.0) | Approximate, based on publicly available aggregate ratings |
| `publish_year` | Year of publication | Reference/public knowledge |
| `description` | Short book description (1–3 sentences) | Written summaries |
| `tags` | Comma-separated descriptive tags | Assigned for search/similarity purposes |

## Derived / Synthetic Fields

### `reading_level` (Derived)

The `reading_level` field is derived using a page-count + genre heuristic:

- **easy**: pages ≤ 250, OR genre is typically accessible (e.g., Romance, Young Adult, Children's)
- **medium**: pages 251–450, OR general fiction/mainstream genres
- **hard**: pages > 450, OR genre is typically dense (e.g., Philosophy, Literary Fiction, Hard SF)

Some titles have manually overridden reading levels where the heuristic would be misleading
(e.g., a short but conceptually dense philosophy book is marked "hard" despite low page count).

### `avg_rating` (Approximate)

Ratings are approximate values based on publicly available aggregate data (e.g., Goodreads).
They are used as one signal among many in the deterministic scorer and should not be treated
as exact.

## Genres Covered

1. Science Fiction
2. Fantasy
3. Mystery / Thriller
4. Romance
5. Literary Fiction
6. Non-Fiction
7. Horror
8. Historical Fiction
9. Young Adult
10. Self-Help / Psychology

## Size

~800 books — large enough to feel like a real catalog, small enough to embed in minutes on a
laptop CPU and to inspect for correctness.
