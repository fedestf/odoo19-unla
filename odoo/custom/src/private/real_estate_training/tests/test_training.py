from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTraining(TransactionCase):
    def setUp(self):
        super().setUp()
        self.property = self.env["estate.property"].create({"name": "U3 Property <safe>"})
        self.other_property = self.env["estate.property"].create({"name": "U3 Other"})
        self.salesperson = self.env["res.users"].create({
            "name": "U3 Seller", "login": "u3_training_seller",
            "group_ids": [Command.set([
                self.env.ref("base.group_user").id,
                self.env.ref("real_estate.group_estate_property_salesman").id,
            ])],
        })

    def wizard(self, properties=None):
        return self.env["estate.assign.salesman.wizard"].create({
            "property_ids": [Command.set((properties or self.property).ids)],
            "salesman_id": self.salesperson.id,
        })

    def test_wizard_default_selection(self):
        values = self.env["estate.assign.salesman.wizard"].with_context(
            active_model="estate.property", active_ids=self.property.ids,
        ).default_get(["property_ids"])
        self.assertEqual(values["property_ids"][0][2], self.property.ids)

    def test_wizard_reassigns_multiple(self):
        self.wizard(self.property | self.other_property).action_apply()
        self.assertEqual(self.property.salesman_id, self.salesperson)
        self.assertEqual(self.other_property.salesman_id, self.salesperson)

    def test_wizard_blocks_closed_without_partial_write(self):
        self.other_property.state = "canceled"
        previous = self.property.salesman_id
        with self.assertRaises(UserError):
            self.wizard(self.property | self.other_property).action_apply()
        self.assertEqual(self.property.salesman_id, previous)

    def test_salesperson_cannot_use_manager_actions(self):
        with self.assertRaises(AccessError):
            self.property.with_user(self.salesperson).action_training_assign_salesman()
        with self.assertRaises(AccessError):
            self.property.with_user(self.salesperson).action_training_mailhog()

    def test_html_report(self):
        content, kind = self.env["ir.actions.report"]._render_qweb_html(
            "real_estate_training.action_report_property_training", self.property.ids,
        )
        self.assertEqual(kind, "html")
        self.assertIn(b"U3 Property", content)
        self.assertIn(b"&lt;safe&gt;", content)

    def test_snapshot_same_day_is_updated(self):
        model = self.env["estate.training.snapshot"]
        first = model._capture_today()
        second = model._capture_today()
        self.assertEqual(first, second)
        self.assertEqual(first.property_count, self.env["estate.property"].search_count([]))
        model._cron_capture_daily()
        self.assertEqual(model.search_count([("capture_date", "=", first.capture_date)]), 1)

    def test_cron_configuration(self):
        cron = self.env.ref("real_estate_training.cron_daily_snapshot")
        self.assertTrue(cron.active)
        self.assertEqual(cron.interval_type, "days")
        self.assertEqual(cron.code, "model._cron_capture_daily()")

    def test_mail_uses_local_server_without_smtp_in_tests(self):
        with patch.object(type(self.env["mail.mail"]), "send", return_value=True) as send:
            self.property.action_training_mailhog()
        send.assert_called_once_with(raise_exception=True)
        mail = self.env["mail.mail"].search([
            ("email_to", "=", "odoo-study@localhost.test"),
        ], order="id desc", limit=1)
        self.assertTrue(mail)
        self.assertEqual(mail.mail_server_id.smtp_host, "smtp")
        self.assertIn("&lt;safe&gt;", mail.body_html)

    def test_mail_refuses_changed_server(self):
        server = self.env.ref("real_estate_training.mailhog_training_server")
        server.smtp_host = "external.example"
        with self.assertRaises(UserError):
            self.property.action_training_mailhog()
