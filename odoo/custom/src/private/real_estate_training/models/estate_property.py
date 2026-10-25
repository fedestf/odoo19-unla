from markupsafe import Markup

from odoo import _, models
from odoo.exceptions import AccessError, UserError


class EstateProperty(models.Model):
    _inherit = "estate.property"

    def _check_training_manager(self):
        if not self.env.su and not self.env.user.has_group("real_estate.group_estate_property_manager"):
            raise AccessError(_("Only property managers can perform this training action."))

    def action_training_assign_salesman(self):
        self._check_training_manager()
        self.check_access("write")
        action = self.env.ref("real_estate_training.action_assign_salesman_wizard").read()[0]
        action["context"] = dict(
            self.env.context,
            active_model="estate.property",
            active_ids=self.ids,
        )
        return action

    def action_training_mailhog(self):
        self.ensure_one()
        self._check_training_manager()
        self.check_access("read")
        server = self.env.ref("real_estate_training.mailhog_training_server").sudo()
        # This specific training button must never fall back to a production SMTP.
        if (
            not server.active or server.smtp_host != "smtp" or server.smtp_port != 1025
            or server.smtp_authentication != "login" or server.smtp_encryption != "none"
            or server.smtp_user or server.smtp_pass
        ):
            raise UserError(_("The training mail server must use smtp:1025 (MailHog)."))
        body = Markup("<p>%s</p><p>%s</p>") % (
            _("This is a local MailHog training message for the property:"), self.name,
        )
        # mail.mail is technical; elevation is limited to a fixed local recipient/server.
        mail = self.env["mail.mail"].sudo().create({
            "subject": _("Unit 3 - MailHog test"),
            "body_html": body,
            "email_from": "training@localhost.test",
            "email_to": "odoo-study@localhost.test",
            "mail_server_id": server.id,
            "auto_delete": False,
        })
        mail.send(raise_exception=True)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("MailHog"),
                "message": _("The test message was delivered to the local MailHog inbox."),
                "type": "success",
                "sticky": False,
            },
        }
