# Map boundaries used by the Members dashboard (/insights)

- `world.topo.json`: Natural Earth 1:10m Admin 0 countries, India
  point-of-view edition (`ne_10m_admin_0_countries_ind`), public domain. It
  draws every border as the Government of India does — full Jammu & Kashmir,
  Ladakh and Arunachal Pradesh — which is why the generic Natural Earth
  editions are not used (they draw Kashmir per the international view;
  owner, 2026-09-27: that is wrong for this product). India's small offshore
  island fragments (Andaman & Nicobar, Lakshadweep) are dropped at this
  scale; simplified to 5% with mapshaper and cleaned; fields kept: `iso`
  (ISO_A2_EH, with Taiwan's non-standard code corrected to TW) and `name`
  (NAME_EN).

  The dashboard deliberately renders this world map as a flat, neutral
  backdrop with one marker per country that has members, never as a
  choropleth: at ~150px wide, a single shaded country's real political shape
  misleads more than it informs (India's mainland and Northeast, joined by
  the thin Siliguri corridor, read as detached fragments — and the corridor
  cannot be visually "filled" without painting over Bangladesh and Nepal).
  Per-value shading lives on the India state map, where there is room for it.
- `india-states.topo.json`: DataMeet India, `maps/States/Admin2`
  (https://github.com/datameet/maps), CC BY 4.0, by the DataMeet India community.
  Simplified to 1.5% with mapshaper; `name` is ST_NM with "&" written as "and"
  so it matches GeoNames state names.

The dashboard credits both beneath its maps.
