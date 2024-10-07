from uagents import Models


class KeyValue(Model):
    currency: str
    product_name: str
    unit_price: int
    units: int


class StripePaymentRequest(Model):
    item_in_cart: list[KeyValue]
    customer_email: str
    order_id: str


class PaymentStatus(Model):
    client_reference_id: str
    data: dict


class QueryPaymentStatus(Model):
    client_reference_id: str


class PaymentLinkRequest(Model):
    no_of_items: int = Field(default=1,
                             description="This field describes the number of items user wants to buy. It should be MORE THAN 0.")
    item_in_list: List[KeyValue] = Field(
        description="This field describes the List of items in KeyValue Model Format. It should never be Null or Blank.")
    customer_email: str = Field(description="This field describes the Email of Customer Placing Order.")