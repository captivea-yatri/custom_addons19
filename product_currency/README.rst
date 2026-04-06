Controller
=============================
* Handle HTTP GET requests to the route '/product_currency/product_currency/'.

                Returns:
                    str: A simple string response, "Hello, world".

* Handle HTTP GET requests to the route '/product_currency/product_currency/objects/'.

                Returns:
                    rendered using a template called 'product_currency.listing'.

* Handle HTTP GET requests to the route '/product_currency/product_currency/objects/<model("product_currency.product_currency"):obj>/'.

                Returns:
                    rendered using a template called 'product_currency.object'.

Demo
=============
* Demo file is used to create demo data when we install
  the module the demo date will create automatically.

Models
-------
* models.py
    - In this models.py file we added 4 fields named:
        - name
        - value
        - value2
        - description

    - and we called the compute method for the value2 field its used to
      convert in float value and divide the value of field value

* product.py

    - In this product.py model we inherit the product.template
      model and add one field in product.template model
    - The added field named:
        -bom_currency_id
    - and we define one method called def _get_default_currency_id(self):
      its used to get default currency based on the company


Views
-------
* templates.xml

    - In this template.xml file we create Two template
        1. listing:
            - This template is show when we called /product_currency/product_currency/objects/ controller.
        2. object:
            - This template is called when we called /product_currency/product_currency/objects/<model("product_currency.product_currency"):obj controller.

* views.xml

    - In this Views.xml file we inherit the product.template model and add one field in product.template form view.
    - The added field named:
        - bom_currency_id
    - and we create the product_currency list view and add three fields in list view named:
        - name
        - value
        - value2
    - and define its action and its menu item.
