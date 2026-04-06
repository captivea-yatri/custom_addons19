/** Hard patch for removed zoomOdoo plugin — Odoo 19 **/
(function () {
    // ensure jQuery is available globally before defining
    const waitForJQuery = setInterval(() => {
        if (window.jQuery) {
            clearInterval(waitForJQuery);
            const $ = window.jQuery;
            if (!$.fn.zoomOdoo) {
                $.fn.zoomOdoo = function () {
                    console.warn("zoomOdoo() deprecated — stubbed in Odoo 19.");
                    return this;
                };
            }
        }
    }, 20);
})();