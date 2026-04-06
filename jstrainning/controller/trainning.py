from odoo import http
from odoo.http import request


class SimpleController(http.Controller):

    @http.route('/simple/hello', methods=['get', 'post'], type='jsonrpc', auth="public", csrf=False)
    def hello_world(self, value, saleorder, **kw):
        # Print the input parameters for debugging
        print(f"Sale Order ID: {saleorder}")
        print(f"Value: {value}")
        print(f"Additional Arguments: {kw}")

        sale_order_record = request.env['sale.order'].browse(saleorder)

        if sale_order_record.exists():
            sale_order_record.write({
                'note': value
            })
            print("Successfully updated Sale Order.")
        else:
            print(f"Sale Order with ID {saleorder} does not exist.")

        return True