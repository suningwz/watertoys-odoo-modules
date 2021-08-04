# -*- coding: utf-8 -*-


from odoo.osv.expression import AND
from datetime import timedelta
import pytz
from odoo import api, fields, models, _, tools
from odoo.tests.common import Form