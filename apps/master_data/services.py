from .repositories import MasterDataRepository


class MasterDataService:
    def __init__(self):
        self.repository = MasterDataRepository()

    def get_categories(self):
        return self.repository.get_categories()

    def search_categories(self, search="", status=""):
        return self.repository.search_categories(
            search=search,
            status=status
        )
    
    def create_category(self, data):
        return self.repository.create_category(data)

    def category_code_exists(self, code, exclude_id=None):
        return self.repository.category_code_exists(
        code,
        exclude_id
    )

    def get_category_by_id(self, category_id):
        return self.repository.get_category_by_id(category_id)

    def update_category(self, category_id, data):
        return self.repository.update_category(category_id, data)

    def delete_category(self, category_id):
        return self.repository.delete_category(category_id)

    def get_products(self):
        return self.repository.get_products()

    def create_product(self, data):
        return self.repository.create_product(data)

    def get_product_by_id(self, product_id):
        return self.repository.get_product_by_id(product_id)

    def update_product(self, product_id, data):
        return self.repository.update_product(
            product_id,
            data
        )

    def delete_product(self, product_id):
        return self.repository.delete_product(product_id)

    def product_sku_exists(self, sku, exclude_id=None):
        return self.repository.product_sku_exists(
            sku,
            exclude_id
    )

    def product_barcode_exists(self, barcode, exclude_id=None):
        return self.repository.product_barcode_exists(barcode, exclude_id)

    def search_products(self, search="", status=""):
        return self.repository.search_products(
            search=search,
            status=status
    )

    # SUPPLIER

    def get_suppliers(self):
        return self.repository.get_suppliers()


    def search_suppliers(self, search="", status=""):
        return self.repository.search_suppliers(
            search=search,
            status=status
        )


    def create_supplier(self, data):
        return self.repository.create_supplier(data)


    def supplier_code_exists(self, code, exclude_id=None):
        return self.repository.supplier_code_exists(
            code,
            exclude_id
        )


    def get_supplier_by_id(self, supplier_id):
        return self.repository.get_supplier_by_id(supplier_id)


    def update_supplier(self, supplier_id, data):
        return self.repository.update_supplier(
            supplier_id,
            data
        )


    def delete_supplier(self, supplier_id):
        return self.repository.delete_supplier(supplier_id)

    # PRODUCT SUPPLIER

    def get_product_suppliers(self):
        return self.repository.get_product_suppliers()


    def create_product_supplier(self, data):
        return self.repository.create_product_supplier(data)


    def get_product_supplier_by_id(self, product_supplier_id):
        return self.repository.get_product_supplier_by_id(
            product_supplier_id
        )


    def update_product_supplier(self, product_supplier_id, data):
        return self.repository.update_product_supplier(
            product_supplier_id,
            data
        )


    def delete_product_supplier(self, product_supplier_id):
        return self.repository.delete_product_supplier(
            product_supplier_id
        )


    def product_supplier_exists(
        self,
        product_id,
        supplier_id,
        exclude_id=None
    ):
        return self.repository.product_supplier_exists(
            product_id,
            supplier_id,
            exclude_id
        )

    # MEMBERS

    def get_members(self):
        return self.repository.get_members()


    def search_members(self, search="", status=""):
        return self.repository.search_members(
            search=search,
            status=status
        )


    def create_member(self, data):
        return self.repository.create_member(data)


    def member_code_exists(self, member_code, exclude_id=None):
        return self.repository.member_code_exists(
            member_code,
            exclude_id
        )


    def get_member_by_id(self, member_id):
        return self.repository.get_member_by_id(member_id)


    def update_member(self, member_id, data):
        return self.repository.update_member(
            member_id,
            data
        )


    def delete_member(self, member_id):
        return self.repository.delete_member(member_id)