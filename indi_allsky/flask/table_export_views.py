"""Download the user's current filtered table without browser blob URLs."""
import io
from flask import jsonify, request, send_file
from flask_login import login_required
from .base_views import BaseView
from ..modern_admin_table_export import MAX_PAYLOAD_BYTES, parse_table_payload, export_table


class ModernAdminTableExportView(BaseView):
    methods = ['POST']
    decorators = [login_required]

    def dispatch_request(self):
        if request.content_length and request.content_length > MAX_PAYLOAD_BYTES * 3:
            return jsonify(message='Export is too large. Narrow the table filters and try again.'), 413
        try:
            rows = parse_table_payload(request.form.get('table'))
            format_name = request.form.get('format')
            content, mime = export_table(rows, format_name)
        except ValueError as error:
            return jsonify(message=str(error)), 400
        return send_file(io.BytesIO(content), mimetype=mime, as_attachment=True,
                         download_name='hybrid-records.'+format_name, max_age=0)
