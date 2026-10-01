from bson import ObjectId

from .repositories import PosProductRepository

class PosCartService:
    def __init__(self, repository=None):
        self.repository = repository or PosProductRepository()

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

        return self.repository.products.find_one({
            "_id": object_id
        })