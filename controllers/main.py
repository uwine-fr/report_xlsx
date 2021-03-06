# Copyright (C) 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl.html).
import json
import time

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi

from addons.web import controllers
from odoo.tools.safe_eval import safe_eval
from odoo import http
from odoo.http import content_disposition, request
from odoo.exceptions import UserError, ValidationError


class ReportController(controllers.main.ReportController):

    @http.route()
    def report_routes(self, reportname, docids=None, converter=None, **data):
        if converter == 'xlsx':
            try:
                report = request.env['ir.actions.report']._get_report_from_name(
                    reportname)
                context = dict(request.env.context)
                if docids:
                    docids = [int(i) for i in docids.split(',')]
                if data.get('options'):
                    data.update(json.loads(data.pop('options')))
                if data.get('context'):
                    # Ignore 'lang' here, because the context in data is the one
                    # from the webclient *but* if the user explicitely wants to
                    # change the lang, this mechanism overwrites it.
                    data['context'] = json.loads(data['context'])
                    if data['context'].get('lang'):
                        del data['context']['lang']
                    context.update(data['context'])
                xlsx = report.with_context(context).render_xlsx(
                    docids, data=data
                )[0]
                report_name = report.report_file
                if report.print_report_name and not len(docids) > 1:
                    obj = request.env[report.model].browse(docids[0])
                    report_name = safe_eval(report.print_report_name,
                                            {'object': obj, 'time': time})
            except (UserError, ValidationError) as odoo_error:
                raise werkzeug.exceptions.HTTPException(
                    description='{error_name}. {error_value}'.format(
                        error_name=odoo_error.name,
                        error_value=odoo_error.value,
                    ))
            if not report_name or report_name == '':
                report_name = 'default_name'
            xlsxhttpheaders = [
                ('Content-Type', 'application/vnd.openxmlformats-'
                                 'officedocument.spreadsheetml.sheet'),
                ('Content-Length', len(xlsx)),
                (
                    'Content-Disposition',
                    content_disposition(report_name + '.xlsx')
                )
            ]
            return request.make_response(xlsx, headers=xlsxhttpheaders)
        return super(ReportController, self).report_routes(
            reportname, docids, converter, **data
        )
