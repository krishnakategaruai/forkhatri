# Place data attribution

`places.tsv` is derived from **GeoNames** (https://www.geonames.org), used under
the **Creative Commons Attribution 4.0 International** licence
(https://creativecommons.org/licenses/by/4.0/).

Changes made: selected columns only (name, ASCII name, up to six ASCII alternate
names, first-level region, country, latitude and longitude rounded to four
decimals, IANA time zone, population); India from `cities5000`, other countries
from `cities15000`. Rebuild with `scripts/build_places.py`.

The place picker in Mangaly shows "Places: GeoNames (CC BY 4.0)" beneath the
search results, which satisfies the attribution requirement.
