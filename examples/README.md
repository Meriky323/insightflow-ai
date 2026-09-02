# Evidence import template

Use `evidence_import_template.csv` as a clean starting point. Only `text` is required.

Recommended fields:

- `source`: Reddit export / TikTok export / Survey / Support / etc.
- `market`: US / AU / UK / CA / GLOBAL. Leave blank if geography is not actually known.
- `text`: raw review/comment/feedback text.
- `review_date`: ISO date if available.
- `url`: original evidence URL when available.
- `rating`, `helpful`, `product_*`: optional.

Do not guess market, author demographics, or ratings when the source does not provide them.
