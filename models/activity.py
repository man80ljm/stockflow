class Activity:
    def __init__(self, activity_id, brand_id, month, target_type, target_item, target_value, rebate_rule, status):
        self.activity_id = activity_id
        self.brand_id = brand_id
        self.month = month
        self.target_type = target_type  # 'total_amount' 或 'item_quantity'
        self.target_item = target_item
        self.target_value = target_value
        self.rebate_rule = rebate_rule
        self.status = status

    def calculate_progress(self, purchases):
        """计算活动完成进度"""
        if self.target_type == "total_amount":
            current_amount = sum(p.total_amount for p in purchases)
            remaining = max(0, self.target_value - current_amount)
            return current_amount, remaining
        else:  # item_quantity
            current_quantity = sum(p.quantity for p in purchases if p.item_name == self.target_item)
            remaining = max(0, self.target_value - current_quantity)
            return current_quantity, remaining