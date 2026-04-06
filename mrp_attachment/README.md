Major Developements:

* Download Attachments of product from mrp.bom and mrp.production

- On mrp.bom/mrp.production, when main product has any attachment in its product template record.
Also same for BOM lines(on mrp.bom)/ Component lines(on mrp.production), if any line having product which has any attachment in its product template record.
This gets downloaded to new directory having name as main product and all files related to main product and all files related to BOM lines product/Component lines product
For this, 'Download Attachments' is visible on both mrp.bom and mrp.production when one or more product is added to order lines having any attachment on its product template record.


* Automate remaining process on mrp.workorder

- On mrp.workorder by clicking on 'Run All' button it will automate all steps until quantity which is to be processed remains positive.
User having access to 'Process all quality checks' on its user's record is given access to see 'Run All' button.