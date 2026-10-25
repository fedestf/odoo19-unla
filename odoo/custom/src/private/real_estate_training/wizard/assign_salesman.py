from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError


class EstateAssignSalesmanWizard(models.TransientModel):
    _name = "estate.assign.salesman.wizard"
    _description = "Assign property salesperson"

    property_ids = fields.Many2many("estate.property", string="Properties", required=True)
    salesman_id = fields.Many2one(
        "res.users", string="Salesperson", required=True,
        domain=[("share", "=", False), ("active", "=", True)],
        default=lambda self: self.env.user,
    )

    @api.model
    def default_get(self, field_names):
        values = super().default_get(field_names)
        if "property_ids" in field_names and self.env.context.get("active_model") == "estate.property":
            properties = self.env["estate.property"].browse(self.env.context.get("active_ids", [])).exists()
            properties.check_access("read")
            values["property_ids"] = [Command.set(properties.ids)]
        return values

    def action_apply(self):
        self.ensure_one()
        if not self.env.su and not self.env.user.has_group("real_estate.group_estate_property_manager"):
            raise AccessError(_("Only property managers can reassign properties."))
        properties = self.property_ids.exists()
        if not properties:
            raise UserError(_("Select at least one property."))
        if not self.salesman_id.active or self.salesman_id.share:
            raise UserError(_("Select an active internal user as salesperson."))
        properties.check_access("write")
        if any(record.state in ("sold", "canceled") for record in properties):
            raise UserError(_("Sold or cancelled properties cannot be reassigned with this wizard."))
        properties.write({"salesman_id": self.salesman_id.id})
        return {"type": "ir.actions.act_window_close"}
