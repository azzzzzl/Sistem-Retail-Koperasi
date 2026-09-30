from bson import ObjectId

class PosCartService:

    @staticmethod
    def get_cart(request):
        return request.session.get("pos_cart", {})

    @staticmethod
    def save_cart(request, cart):
        request.session["pos_cart"] = cart
        request.session.modified = True

    @staticmethod
    def clear_cart(request):
        request.session["pos_cart"] = {}
        request.session.modified = True

    def get_product(self, product_id):
        try:
            object_id = ObjectId(product_id)
        except Exception:
            return None

        return self.products.find_one({
            "_id": object_id
        })