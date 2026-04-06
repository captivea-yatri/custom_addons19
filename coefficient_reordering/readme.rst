* This Odoo module enhances the Bill of Materials functionality by adding a new
field called 'Reordering Rule' to the BOM lines.

* The XML file modifies the standard BOM form view (`mrp.mrp_bom_form_view`) to include the
'Reordering Rule' field in the BOM lines.

*The 'Reordering Rule' field displays the reordering rules associated with each BOM line product.
If there are order points defined for the product, the names of these order points are displayed in the field.
