Controller
=============================
* Handle HTTP GET requests to the route '/product_purchase/product_purchase/'.

                Returns:
                    str: A simple string response, "Hello, world".

* Handle HTTP GET requests to the route '/product_purchase/product_purchase/objects/'.

                Returns:
                    rendered using a template called 'product_purchase.listing'.

* Handle HTTP GET requests to the route '/product_purchase/product_purchase/objects/<model("product_purchase.product_purchase"):obj>/'.

                Returns:
                    rendered using a template called 'product_purchase.object'.

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
      converted in float value and divide the value of field named value

* product_template.py

    - In this product.py model we inherit the product.template
      model and add one field in product.template model
    - The added field named:
        - purchase_count
    - and we define one compute method called def _purchase_count(self):
      its used to get purchase count from product.product model and sum
      of all purchases and set that value in purchase count field in product.template


Views
-------
* templates.xml

    - In this template.xml file we create Two template
        1. listing:
            - This template is show when we called /product_purchase/product_purchase/objects/ controller.
        2. object:
            - This template is called when we called /product_purchase/product_purchase/objects/<model("product_purchase.product_purchase"):obj controller.

* product_template.xml

    - In this product_template.xml file we inherit the product.template model and add one button in product.template form view.
    - The added button named:
        - Purchases : In this button count the filed value of product_order_count in the product.product model.
                      When we click on this button its open the purchase.order.line object.
    - and we create the product_purchase list view and add three fields in list view named:
        - name
        - value
        - value2
    - and define its action and its menu item.
