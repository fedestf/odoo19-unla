{
    "name": "Real Estate Training - Unit 3",
    "version": "19.0.1.0.0",
    "summary": "Wizards, QWeb, scheduled actions, MailHog, tests and translations",
    "author": "Federico-UNLA",
    "license": "LGPL-3",
    "depends": ["real_estate", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/assign_salesman_views.xml",
        "report/property_report.xml",
        "views/estate_property_views.xml",
        "views/snapshot_views.xml",
        "data/mailhog_server.xml",
        "data/snapshot_cron.xml",
    ],
    "installable": True,
    "application": False,
}
