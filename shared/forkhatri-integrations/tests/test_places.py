"""Run: python -m unittest discover -s shared/forkhatri-integrations/tests"""

from __future__ import annotations

import unittest

from forkhatri_integrations import places

SUBURB = {"category": "place", "type": "suburb", "addresstype": "suburb", "name": "Kondapur", "lat": "17.4587912", "lon": "78.3730556",
          "osm_type": "node", "osm_id": 1,
          "address": {"suburb": "Kondapur", "city": "Hyderabad", "state_district": "Ranga Reddy", "state": "Telangana", "country_code": "in"}}


class PlacesTest(unittest.IsolatedAsyncioTestCase):
    def test_area_is_parsed_with_city_district_state(self):
        p = places.parse_place(SUBURB)
        self.assertEqual((p.kind, p.locality, p.city, p.zone, p.state), ("area", "Kondapur", "Hyderabad", "Ranga Reddy", "Telangana"))
        self.assertEqual(p.label, "Kondapur, Hyderabad, Ranga Reddy, Telangana")

    def test_street_level_and_foreign_results_are_dropped(self):
        self.assertIsNone(places.parse_place({**SUBURB, "category": "highway", "addresstype": "road"}))
        self.assertIsNone(places.parse_place({**SUBURB, "address": {**SUBURB["address"], "country_code": "us"}}))

    def test_state_and_city_kinds(self):
        s = places.parse_place({"category": "boundary", "type": "administrative", "addresstype": "state", "name": "Telangana", "lat": "18", "lon": "79",
                                "address": {"state": "Telangana", "country_code": "in"}})
        self.assertEqual((s.kind, s.city, s.locality), ("state", "Telangana", None))
        c = places.parse_place({"category": "boundary", "type": "administrative", "addresstype": "city", "name": "Pune", "lat": "18.5", "lon": "73.8",
                                "address": {"city": "Pune", "state_district": "Pune", "state": "Maharashtra", "country_code": "in"}})
        self.assertEqual((c.kind, c.city, c.zone, c.locality), ("city", "Pune", None, None))

    async def test_off_without_a_base_url(self):
        self.assertEqual(places.get_provider("nominatim").name, "none")
        with self.assertRaises(places.PlacesNotConfigured):
            await places.get_provider("none").search("pune")


if __name__ == "__main__":
    unittest.main()
