from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class EstateTrainingSnapshot(models.Model):
    _name = "estate.training.snapshot"
    _description = "Real estate daily snapshot"
    _rec_name = "capture_date"
    _order = "capture_date desc, id desc"

    _unique_capture_date = models.Constraint(
        "UNIQUE(capture_date)", "There can only be one snapshot per day."
    )

    capture_date = fields.Date(string="Date", default=fields.Date.context_today, required=True)
    generated_at = fields.Datetime(string="Last generated at", readonly=True)
    property_count = fields.Integer(string="Properties", readonly=True)
    available_count = fields.Integer(string="Available properties", readonly=True)
    offer_count = fields.Integer(string="Offers", readonly=True)
    pending_offer_count = fields.Integer(string="Pending offers", readonly=True)

    @api.model
    def _capture_today(self):
        today = fields.Date.context_today(self)
        values = {
            "capture_date": today,
            "generated_at": fields.Datetime.now(),
            "property_count": self.env["estate.property"].search_count([]),
            "available_count": self.env["estate.property"].search_count([
                ("state", "in", ["new", "offer_received"]),
            ]),
            "offer_count": self.env["estate.property.offer"].search_count([]),
            "pending_offer_count": self.env["estate.property.offer"].search_count([
                ("status", "=", False),
            ]),
        }
        snapshot = self.search([("capture_date", "=", today)], limit=1)
        if snapshot:
            snapshot.write(values)
        else:
            snapshot = self.create(values)
        return snapshot

    @api.model
    def _cron_capture_daily(self):
        # No email, state changes, deletion or explicit transaction commits.
        self._capture_today()

    @api.model
    def action_capture_today(self):
        if not self.env.su and not self.env.user.has_group("real_estate.group_estate_property_manager"):
            raise AccessError(_("Only property managers can capture a snapshot."))
        snapshot = self._capture_today()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": snapshot.id,
            "view_mode": "form",
            "target": "current",
        }
