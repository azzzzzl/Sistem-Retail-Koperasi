from bson import ObjectId

from database.mongodb import get_database


class MasterDataRepository:
    def __init__(self):
        self.db = get_database()

        self.categories = self.db["categories"]
        self.products = self.db["products"]
        self.suppliers = self.db["suppliers"]
        self.product_suppliers = self.db["product_suppliers"]
        self.members = self.db["members"]

    # ==========================================================
    # CATEGORY
    # ==========================================================

    def get_categories(self):
        categories = list(
            self.categories.find(
                {},
                {
                    "_id": 1,
                    "code": 1,
                    "name": 1,
                    "description": 1,
                    "status": 1,
                }
            ).sort("name", 1)
        )

        for category in categories:
            category["id"] = str(category["_id"])

        return categories

    def search_categories(self, search="", status=""):
        query = {}

        # Search berdasarkan kode atau nama
        if search:
            query["$or"] = [
                {
                    "code": {
                        "$regex": search,
                        "$options": "i"
                    }
                },
                {
                    "name": {
                        "$regex": search,
                        "$options": "i"
                    }
                }
            ]

        # Filter berdasarkan status
        if status:
            query["status"] = status

        categories = list(
            self.categories.find(
                query,
                {
                    "_id": 1,
                    "code": 1,
                    "name": 1,
                    "description": 1,
                    "status": 1,
                }
            ).sort("name", 1)
        )

        for category in categories:
            category["id"] = str(category["_id"])

        return categories

    def create_category(self, data):
        return self.categories.insert_one(data)

    def get_category_by_id(self, category_id):
        return self.categories.find_one({
            "_id": ObjectId(category_id)
        })

    def category_code_exists(self, code, exclude_id=None):
        query = {
        "code": code
    }

        if exclude_id:
            query["_id"] = {
            "$ne": ObjectId(exclude_id)
        }

        return self.categories.find_one(query) is not None

    def update_category(self, category_id, data):
        return self.categories.update_one(
            {
                "_id": ObjectId(category_id)
            },
            {
                "$set": data
            }
        )

    def delete_category(self, category_id):
        return self.categories.delete_one({
            "_id": ObjectId(category_id)
        })

    def get_products(self):
        products = list(
            self.products.find(
                {},
                {
                    "_id": 1,
                    "sku": 1,
                    "barcode": 1,
                    "name": 1,
                    "category_id": 1,
                    "purchase_price": 1,
                    "selling_price": 1,
                    "stock": 1,
                    "minimumStock": 1,
                    "minimum_stock": 1,
                    "status": 1,
                }
            ).sort("name", 1)
        )

        for product in products:
            product["id"] = str(product["_id"])
            product["categoryId"] = product.get("categoryId", product.get("category_id"))
            product["purchasePrice"] = product.get("purchasePrice", product.get("purchase_price", 0))
            product["sellingPrice"] = product.get("sellingPrice", product.get("selling_price", 0))
            product["minimumStock"] = product.get("minimumStock", product.get("minimum_stock", 0))
        return products

    def search_products(self, search="", status=""):
        query = {}

        if search:
            query["$or"] = [
                {"sku": {"$regex": search, "$options": "i"}},
                {"barcode": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}},
            ]

        if status:
            query["status"] = status

        products = list(
            self.products.find(
                query,
                {
                    "_id": 1,
                    "sku": 1,
                    "barcode": 1,
                    "name": 1,
                    "category_id": 1,
                    "purchase_price": 1,
                    "selling_price": 1,
                    "stock": 1,
                    "minimumStock": 1,
                    "minimum_stock": 1,
                    "status": 1,
                }
            ).sort("name", 1)
        )

        for product in products:
            product["id"] = str(product["_id"])
            product["categoryId"] = product.get("categoryId", product.get("category_id"))
            product["purchasePrice"] = product.get("purchasePrice", product.get("purchase_price", 0))
            product["sellingPrice"] = product.get("sellingPrice", product.get("selling_price", 0))
            product["minimumStock"] = product.get("minimumStock", product.get("minimum_stock", 0))
        return products

    def create_product(self, data):
        return self.products.insert_one(data)

    def get_product_by_id(self, product_id):
        return self.products.find_one({
        "_id": ObjectId(product_id)
    })


    def update_product(self, product_id, data):
        return self.products.update_one(
        {
            "_id": ObjectId(product_id)
        },
        {
            "$set": data
        }
    )


    def delete_product(self, product_id):
        return self.products.delete_one({
        "_id": ObjectId(product_id)
    })

    def product_sku_exists(self, sku, exclude_id=None):
        query = {
        "sku": sku
    }

        if exclude_id:
            query["_id"] = {
            "$ne": ObjectId(exclude_id)
        }

        return self.products.find_one(query) is not None

    def product_barcode_exists(self, barcode, exclude_id=None):
        query = {"barcode": barcode}

        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}

        return self.products.find_one(query) is not None

    def get_suppliers(self):
        suppliers = list(
        self.suppliers.find(
            {},
            {
                "_id": 1,
                "code": 1,
                "name": 1,
                "phone": 1,
                "email": 1,
                "address": 1,
                "status": 1,
            }
        ).sort("name", 1)
    )

        for supplier in suppliers:
            supplier["id"] = str(supplier["_id"])
        return suppliers


    def search_suppliers(self, search="", status=""):
        query = {}

        if search:
            query["$or"] = [
                {"code": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}},
            ]

        if status:
            query["status"] = status

        suppliers = list(
            self.suppliers.find(
                query,
                {
                    "_id": 1,
                    "code": 1,
                    "name": 1,
                    "phone": 1,
                    "email": 1,
                    "address": 1,
                    "status": 1,
                }
            ).sort("name", 1)
        )

        for supplier in suppliers:
            supplier["id"] = str(supplier["_id"])
        return suppliers


    def create_supplier(self, data):
        return self.suppliers.insert_one(data)


    def get_supplier_by_id(self, supplier_id):
        return self.suppliers.find_one(
            {"_id": ObjectId(supplier_id)}
        )


    def update_supplier(self, supplier_id, data):
        return self.suppliers.update_one(
            {"_id": ObjectId(supplier_id)},
            {"$set": data}
        )


    def delete_supplier(self, supplier_id):
        return self.suppliers.delete_one(
            {"_id": ObjectId(supplier_id)}
        )


    def supplier_code_exists(self, code, exclude_id=None):
        query = {"code": code}

        if exclude_id:
            query["_id"] = {"$ne": ObjectId(exclude_id)}

        return self.suppliers.find_one(query) is not None

    # PRODUCT SUPPLIER

    def get_product_suppliers(self):
        product_suppliers = list(
            self.product_suppliers.find(
                {},
                {
                    "_id": 1,
                    "product_id": 1,
                    "supplier_id": 1,
                    "supplier_product_code": 1,
                    "purchase_price": 1,
                    "status": 1,
                }
            )
        )

        for item in product_suppliers:
            item["id"] = str(item["_id"])

        return product_suppliers


    def create_product_supplier(self, data):
        return self.product_suppliers.insert_one(data)


    def get_product_supplier_by_id(self, product_supplier_id):
        return self.product_suppliers.find_one(
            {"_id": ObjectId(product_supplier_id)}
        )


    def update_product_supplier(self, product_supplier_id, data):
        return self.product_suppliers.update_one(
            {"_id": ObjectId(product_supplier_id)},
            {"$set": data}
        )


    def delete_product_supplier(self, product_supplier_id):
        return self.product_suppliers.delete_one(
            {"_id": ObjectId(product_supplier_id)}
        )


    def product_supplier_exists(
        self,
        product_id,
        supplier_id,
        exclude_id=None
    ):
        query = {
            "product_id": product_id,
            "supplier_id": supplier_id,
        }

        if exclude_id:
            query["_id"] = {
                "$ne": ObjectId(exclude_id)
            }

        return self.product_suppliers.find_one(query) is not None

    # MEMBERS

    def get_members(self):
        members = list(
            self.members.find(
                {},
                {
                    "_id": 1,
                    "member_code": 1,
                    "name": 1,
                    "phone": 1,
                    "email": 1,
                    "address": 1,
                    "status": 1,
                }
            ).sort("name", 1)
        )

        for member in members:
            member["id"] = str(member["_id"])
            member["memberCode"] = member.get("memberCode", member.get("member_code"))
        return members


    def search_members(self, search="", status=""):
        query = {}

        if search:
            query["$or"] = [
                {"member_code": {"$regex": search, "$options": "i"}},
                {"name": {"$regex": search, "$options": "i"}},
                {"phone": {"$regex": search, "$options": "i"}},
            ]

        if status:
            query["status"] = status

        members = list(
            self.members.find(
                query,
                {
                    "_id": 1,
                    "member_code": 1,
                    "name": 1,
                    "phone": 1,
                    "email": 1,
                    "address": 1,
                    "status": 1,
                }
            ).sort("name", 1)
        )

        for member in members:
            member["id"] = str(member["_id"])
            member["memberCode"] = member.get("memberCode", member.get("member_code"))
        return members


    def create_member(self, data):
        return self.members.insert_one(data)


    def get_member_by_id(self, member_id):
        return self.members.find_one(
            {"_id": ObjectId(member_id)}
        )


    def update_member(self, member_id, data):
        return self.members.update_one(
            {"_id": ObjectId(member_id)},
            {"$set": data}
        )


    def delete_member(self, member_id):
        return self.members.delete_one(
            {"_id": ObjectId(member_id)}
        )


    def member_code_exists(self, member_code, exclude_id=None):
        query = {"member_code": member_code}

        if exclude_id:
            query["_id"] = {
                "$ne": ObjectId(exclude_id)
            }

        return self.members.find_one(query) is not None