from models.brand import add_purchase

class Purchase:
    def __init__(self, purchase_id, item_id, brand_id, quantity, unit, unit_price, total_amount, date, remarks, item_name, spec):
        self.purchase_id = purchase_id
        self.item_id = item_id
        self.brand_id = brand_id
        self.quantity = quantity
        self.unit = unit
        self.unit_price = unit_price
        self.total_amount = total_amount
        self.date = date
        self.remarks = remarks
        self.item_name = item_name
        self.spec = spec

    def save(self):
        """保存进货记录到数据库"""
        if not self.purchase_id:
            purchase_id = add_purchase(
                self.item_id, self.brand_id, self.quantity, self.unit,
                self.unit_price, self.total_amount, self.date, self.remarks
            )
            if purchase_id:
                self.purchase_id = purchase_id
            return purchase_id
        return None