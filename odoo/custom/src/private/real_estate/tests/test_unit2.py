from datetime import timedelta
from unittest.mock import patch

from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestUnit2(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Property = self.env["estate.property"]
        self.Offer = self.env["estate.property.offer"]
        self.partners = self.env["res.partner"].create([
            {"name": "U2 Ofertante 1"}, {"name": "U2 Ofertante 2"},
        ])
        self.property = self.Property.create({"name": "U2 Prueba", "expected_price": 100000})

    def offer(self, price, partner=None, property_record=None):
        return self.Offer.create({
            "price": price,
            "partner_id": (partner or self.partners[0]).id,
            "property_id": (property_record or self.property).id,
        })

    def test_surface_and_garden(self):
        self.property.write({"living_area": 100, "garden_area": 25})
        self.assertEqual(self.property.total_area, 125)
        self.property.garden = True
        self.property._onchange_garden()
        self.assertEqual(self.property.garden_area, 10)
        self.assertEqual(self.property.total_area, 110)
        self.property.garden = False
        self.property._onchange_garden()
        self.assertEqual(self.property.garden_area, 0)

    def test_deadline_inverse_and_related(self):
        offer = self.offer(50000)
        base = offer._get_deadline_base_date()
        self.assertEqual((offer.date_deadline - base).days, 7)
        offer.validity = 10
        self.assertEqual((offer.date_deadline - base).days, 10)
        offer.write({"date_deadline": base + timedelta(days=13)})
        self.assertEqual(offer.validity, 13)
        types = self.env["estate.property.type"].create([
            {"name": "U2 Tipo A"}, {"name": "U2 Tipo B"},
        ])
        self.property.property_type_id = types[0]
        self.assertEqual(offer.property_type_id, types[0])
        self.property.property_type_id = types[1]
        self.assertEqual(offer.property_type_id, types[1])

    def test_creation_and_acceptance(self):
        first = self.offer(50000)
        second = self.offer(65000, self.partners[1])
        self.assertEqual(self.property.state, "offer_received")
        self.assertEqual(self.property.best_offer, 65000)
        self.assertEqual(set(self.property.offer_partner_ids.ids), set(self.partners.ids))
        second.action_accept()
        self.assertEqual(second.status, "accepted")
        self.assertEqual(first.status, "refused")
        self.assertEqual(self.property.buyer_id, self.partners[1])
        self.assertEqual(self.property.selling_price, 65000)
        self.assertEqual(self.property.state, "offer_accepted")
        with self.assertRaises(UserError):
            self.offer(70000)

    def test_best_offer_and_batch(self):
        self.assertEqual(self.property.best_offer, 0)
        self.Offer.create([
            {"price": 50000, "partner_id": self.partners[0].id, "property_id": self.property.id},
            {"price": 65000, "partner_id": self.partners[1].id, "property_id": self.property.id},
        ])
        for price in (64000, 65000):
            with self.assertRaises(UserError):
                self.offer(price)
        self.assertEqual(self.property.best_offer, 65000)

    def test_unique_names(self):
        for model_name in ("estate.property.tag", "estate.property.type"):
            model = self.env[model_name]
            model.create({"name": "U2 Nombre único"})
            with self.assertRaises(IntegrityError), self.cr.savepoint():
                model.create({"name": "U2 Nombre único"})
                self.env.flush_all()

    def test_unique_partner_per_property(self):
        self.offer(50000)
        with self.assertRaises(IntegrityError), self.cr.savepoint():
            self.offer(65000)
            self.env.flush_all()
        other_property = self.Property.create({"name": "U2 Otra"})
        self.offer(65000, property_record=other_property)

    def test_tag_commands(self):
        tags = self.env["estate.property.tag"].create([
            {"name": "U2 Luminosa"}, {"name": "U2 Espaciosa"},
        ])
        self.property.write({"tag_ids": [Command.set(tags.ids)]})
        self.property.action_clear_tags()
        self.assertFalse(self.property.tag_ids)
        self.assertTrue(tags.exists())
        self.property.action_load_all_tags()
        self.assertTrue(set(tags.ids) <= set(self.property.tag_ids.ids))
        self.property.action_add_brand_new_tag()
        self.property.action_add_brand_new_tag()
        brand_new = self.env["estate.property.tag"].search([("name", "=", "A estrenar")])
        self.assertEqual(len(brand_new), 1)
        self.assertIn(brand_new, self.property.tag_ids)

    @patch("odoo.addons.real_estate.models.estate_property.random.randint", side_effect=lambda low, high: low)
    def test_automatic_offer(self, random_price):
        before = self.property.offer_ids
        self.property.action_generate_offer()
        offer = self.property.offer_ids - before
        self.assertEqual(len(offer), 1)
        self.assertTrue(offer.partner_id.active)
        self.assertGreaterEqual(offer.price, 70000)
        self.assertLessEqual(offer.price, 130000)
        self.assertEqual(self.property.state, "offer_received")
        self.property.action_generate_offer()
        self.assertEqual(len(set(self.property.offer_ids.partner_id.ids)), 2)

    def test_delete_states_and_users_inverse(self):
        self.assertIn(self.property, self.env.user.property_ids)
        self.property.state = "offer_received"
        with self.assertRaises(UserError):
            self.property.unlink()
        self.property.state = "canceled"
        self.property.unlink()
        new_property = self.Property.create({"name": "U2 Borrable"})
        new_property.unlink()

    def test_closed_states(self):
        self.property.action_cancel()
        with self.assertRaises(UserError):
            self.property.action_sold()
        with self.assertRaises(UserError):
            self.offer(50000)
        other = self.Property.create({"name": "U2 Vendida", "buyer_id": self.partners[0].id, "selling_price": 50000})
        # Writing state isolates the base rule from the optional accounting module.
        other.state = "sold"
        with self.assertRaises(UserError):
            other.action_cancel()
