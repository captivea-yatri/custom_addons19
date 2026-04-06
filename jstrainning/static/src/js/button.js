/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
publicWidget.registry.HelloWorldWidget = publicWidget.Widget.extend({
    selector: "#wrapwrap",
    
     events: {
            'click .hello-btn': '_onHelloBtnMouseover',
            'change #nameInput': '_displayInput',
        },
         _onHelloBtnMouseover: function (ev) {
            ev.preventDefault();
            alert("Hello World from Odoo 19 Public Widget!");
        },
        _displayInput: function (ev) {
            ev.preventDefault();
             const inputField = ev.target.value;
             const so = parseInt(ev.target.dataset.saleOrder, 10);
             rpc('/simple/hello',{'value':inputField , 'saleorder':so})
              console.log(so);
//             alert("Hello, " + so + "!"); // Or update an HTML element
        },
//start: function () {
//            console.log("HelloWorldWidget Loaded");
//            return this._super(...arguments);
//        },


});
