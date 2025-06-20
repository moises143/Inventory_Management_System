import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Logging setup
logging.basicConfig(level=logging.DEBUG)


# DB base
class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# DB config
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///inventory.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

# Move everything else inside app context
with app.app_context():
    # Delayed import prevents circular import
    from models import User, Supplier, InventoryItem, UserRole, Sale, SaleItem, StockTransaction
    from werkzeug.security import generate_password_hash

    # Force recreate database with new schema
    logging.info("Recreating database with updated schema...")
    db.drop_all()
    db.create_all()
    logging.info("Database tables created successfully")

    # Create default admin user
    admin_user = User(
        username='admin',
        email='admin@inventory.com',
        role=UserRole.ADMIN
    )
    admin_user.set_password('admin123')
    db.session.add(admin_user)

    # Create default staff user
    staff_user = User(
        username='staff',
        email='staff@inventory.com',
        role=UserRole.STAFF
    )
    staff_user.set_password('staff123')
    db.session.add(staff_user)

    sample_items = [
        # BEVERAGES
        {
            'name': 'Coca-Cola 1.5L',
            'description': 'Coca-Cola soft drink 1.5 liter bottle',
            'sku': 'BEV001',
            'quantity': 50,
            'unit_price': 45.00,
            'selling_price': 65.00,
            'reorder_point': 20,
            'category': 'Beverages',
            'is_active': True
        },
        {
            'name': 'Pepsi 330ml Can',
            'description': 'Pepsi cola in 330ml aluminum can',
            'sku': 'BEV002',
            'quantity': 120,
            'unit_price': 15.00,
            'selling_price': 25.00,
            'reorder_point': 30,
            'category': 'Beverages',
            'is_active': True
        },
        {
            'name': 'Sprite 1L',
            'description': 'Sprite lemon-lime soda 1 liter bottle',
            'sku': 'BEV003',
            'quantity': 40,
            'unit_price': 35.00,
            'selling_price': 50.00,
            'reorder_point': 15,
            'category': 'Beverages',
            'is_active': True
        },
        {
            'name': 'Royal True Orange 330ml',
            'description': 'Royal True Orange flavored drink',
            'sku': 'BEV004',
            'quantity': 80,
            'unit_price': 12.00,
            'selling_price': 20.00,
            'reorder_point': 25,
            'category': 'Beverages',
            'is_active': True
        },
        {
            'name': 'C2 Green Tea 1L',
            'description': 'C2 Cool & Clean Green Tea',
            'sku': 'BEV005',
            'quantity': 30,
            'unit_price': 25.00,
            'selling_price': 40.00,
            'reorder_point': 10,
            'category': 'Beverages',
            'is_active': True
        },
        {
            'name': 'Nestea Iced Tea 1L',
            'description': 'Nestea Lemon Iced Tea',
            'sku': 'BEV006',
            'quantity': 35,
            'unit_price': 30.00,
            'selling_price': 45.00,
            'reorder_point': 12,
            'category': 'Beverages',
            'is_active': True
        },
        {
            'name': 'Nature Spring Water 1L',
            'description': 'Nature Spring purified drinking water',
            'sku': 'BEV007',
            'quantity': 100,
            'unit_price': 18.00,
            'selling_price': 25.00,
            'reorder_point': 40,
            'category': 'Beverages',
            'is_active': True
        },
        {
            'name': 'Zesto Orange Juice 200ml',
            'description': 'Zesto orange juice drink tetra pack',
            'sku': 'BEV008',
            'quantity': 60,
            'unit_price': 8.00,
            'selling_price': 15.00,
            'reorder_point': 20,
            'category': 'Beverages',
            'is_active': True
        },
        {
            'name': 'Bear Brand Milk 300ml',
            'description': 'Bear Brand sterilized milk',
            'sku': 'BEV009',
            'quantity': 45,
            'unit_price': 22.00,
            'selling_price': 35.00,
            'reorder_point': 15,
            'category': 'Beverages',
            'is_active': True
        },
        {
            'name': 'Red Bull Energy Drink 250ml',
            'description': 'Red Bull energy drink can',
            'sku': 'BEV010',
            'quantity': 50,
            'unit_price': 45.00,
            'selling_price': 65.00,
            'reorder_point': 20,
            'category': 'Beverages',
            'is_active': True
        },

        # RICE & GRAINS
        {
            'name': 'Jasmine Rice 25kg',
            'description': 'Premium jasmine rice sack',
            'sku': 'RIC001',
            'quantity': 20,
            'unit_price': 1200.00,
            'selling_price': 1500.00,
            'reorder_point': 5,
            'category': 'Rice & Grains',
            'is_active': True
        },
        {
            'name': 'White Rice 5kg',
            'description': 'Regular white rice pack',
            'sku': 'RIC002',
            'quantity': 30,
            'unit_price': 250.00,
            'selling_price': 320.00,
            'reorder_point': 10,
            'category': 'Rice & Grains',
            'is_active': True
        },
        {
            'name': 'Brown Rice 2kg',
            'description': 'Healthy brown rice pack',
            'sku': 'RIC003',
            'quantity': 25,
            'unit_price': 180.00,
            'selling_price': 250.00,
            'reorder_point': 8,
            'category': 'Rice & Grains',
            'is_active': True
        },
        {
            'name': 'Glutinous Rice 1kg',
            'description': 'Sticky rice for kakanin',
            'sku': 'RIC004',
            'quantity': 15,
            'unit_price': 80.00,
            'selling_price': 120.00,
            'reorder_point': 5,
            'category': 'Rice & Grains',
            'is_active': True
        },
        {
            'name': 'Oatmeal 500g',
            'description': 'Quaker oats rolled oats',
            'sku': 'RIC005',
            'quantity': 20,
            'unit_price': 85.00,
            'selling_price': 125.00,
            'reorder_point': 8,
            'category': 'Rice & Grains',
            'is_active': True
        },

        # MEAT & POULTRY
        {
            'name': 'Whole Chicken 1kg',
            'description': 'Fresh whole chicken per kilo',
            'sku': 'MEA001',
            'quantity': 25,
            'unit_price': 160.00,
            'selling_price': 220.00,
            'reorder_point': 8,
            'category': 'Meat & Poultry',
            'is_active': True
        },
        {
            'name': 'Chicken Breast 1kg',
            'description': 'Fresh boneless chicken breast',
            'sku': 'MEA002',
            'quantity': 20,
            'unit_price': 280.00,
            'selling_price': 350.00,
            'reorder_point': 6,
            'category': 'Meat & Poultry',
            'is_active': True
        },
        {
            'name': 'Chicken Wings 1kg',
            'description': 'Fresh chicken wings',
            'sku': 'MEA003',
            'quantity': 18,
            'unit_price': 200.00,
            'selling_price': 280.00,
            'reorder_point': 5,
            'category': 'Meat & Poultry',
            'is_active': True
        },
        {
            'name': 'Pork Belly 1kg',
            'description': 'Fresh pork belly sliced',
            'sku': 'MEA004',
            'quantity': 15,
            'unit_price': 320.00,
            'selling_price': 420.00,
            'reorder_point': 5,
            'category': 'Meat & Poultry',
            'is_active': True
        },
        {
            'name': 'Ground Pork 500g',
            'description': 'Fresh ground pork meat',
            'sku': 'MEA005',
            'quantity': 20,
            'unit_price': 140.00,
            'selling_price': 190.00,
            'reorder_point': 8,
            'category': 'Meat & Poultry',
            'is_active': True
        },
        {
            'name': 'Beef Steak Cut 1kg',
            'description': 'Fresh beef steak cut',
            'sku': 'MEA006',
            'quantity': 12,
            'unit_price': 450.00,
            'selling_price': 580.00,
            'reorder_point': 4,
            'category': 'Meat & Poultry',
            'is_active': True
        },
        {
            'name': 'Hotdog 1kg Pack',
            'description': 'CDO or Purefoods hotdog',
            'sku': 'MEA007',
            'quantity': 30,
            'unit_price': 180.00,
            'selling_price': 250.00,
            'reorder_point': 10,
            'category': 'Meat & Poultry',
            'is_active': True
        },
        {
            'name': 'Tocino 500g',
            'description': 'Sweet cured pork tocino',
            'sku': 'MEA008',
            'quantity': 25,
            'unit_price': 120.00,
            'selling_price': 180.00,
            'reorder_point': 8,
            'category': 'Meat & Poultry',
            'is_active': True
        },

        # SEAFOOD
        {
            'name': 'Tilapia 1kg',
            'description': 'Fresh tilapia fish',
            'sku': 'SEA001',
            'quantity': 15,
            'unit_price': 140.00,
            'selling_price': 200.00,
            'reorder_point': 5,
            'category': 'Seafood',
            'is_active': True
        },
        {
            'name': 'Bangus 1kg',
            'description': 'Fresh milkfish',
            'sku': 'SEA002',
            'quantity': 12,
            'unit_price': 180.00,
            'selling_price': 250.00,
            'reorder_point': 4,
            'category': 'Seafood',
            'is_active': True
        },
        {
            'name': 'Shrimp 500g',
            'description': 'Medium size fresh shrimp',
            'sku': 'SEA003',
            'quantity': 10,
            'unit_price': 250.00,
            'selling_price': 350.00,
            'reorder_point': 3,
            'category': 'Seafood',
            'is_active': True
        },
        {
            'name': 'Squid 1kg',
            'description': 'Fresh squid cleaned',
            'sku': 'SEA004',
            'quantity': 8,
            'unit_price': 200.00,
            'selling_price': 280.00,
            'reorder_point': 3,
            'category': 'Seafood',
            'is_active': True
        },

        # VEGETABLES
        {
            'name': 'Onions 1kg',
            'description': 'Red onions per kilo',
            'sku': 'VEG001',
            'quantity': 40,
            'unit_price': 60.00,
            'selling_price': 90.00,
            'reorder_point': 15,
            'category': 'Vegetables',
            'is_active': True
        },
        {
            'name': 'Garlic 500g',
            'description': 'Fresh garlic bulbs',
            'sku': 'VEG002',
            'quantity': 30,
            'unit_price': 80.00,
            'selling_price': 120.00,
            'reorder_point': 10,
            'category': 'Vegetables',
            'is_active': True
        },
        {
            'name': 'Tomatoes 1kg',
            'description': 'Fresh ripe tomatoes',
            'sku': 'VEG003',
            'quantity': 35,
            'unit_price': 50.00,
            'selling_price': 80.00,
            'reorder_point': 12,
            'category': 'Vegetables',
            'is_active': True
        },
        {
            'name': 'Potatoes 1kg',
            'description': 'Fresh potatoes',
            'sku': 'VEG004',
            'quantity': 45,
            'unit_price': 70.00,
            'selling_price': 100.00,
            'reorder_point': 15,
            'category': 'Vegetables',
            'is_active': True
        },
        {
            'name': 'Carrots 1kg',
            'description': 'Fresh carrots',
            'sku': 'VEG005',
            'quantity': 25,
            'unit_price': 80.00,
            'selling_price': 120.00,
            'reorder_point': 8,
            'category': 'Vegetables',
            'is_active': True
        },
        {
            'name': 'Cabbage 1 head',
            'description': 'Fresh cabbage per head',
            'sku': 'VEG006',
            'quantity': 20,
            'unit_price': 35.00,
            'selling_price': 55.00,
            'reorder_point': 8,
            'category': 'Vegetables',
            'is_active': True
        },
        {
            'name': 'Kangkong Bundle',
            'description': 'Water spinach bundle',
            'sku': 'VEG007',
            'quantity': 30,
            'unit_price': 15.00,
            'selling_price': 25.00,
            'reorder_point': 10,
            'category': 'Vegetables',
            'is_active': True
        },
        {
            'name': 'Pechay Bundle',
            'description': 'Bok choy bundle',
            'sku': 'VEG008',
            'quantity': 25,
            'unit_price': 20.00,
            'selling_price': 35.00,
            'reorder_point': 8,
            'category': 'Vegetables',
            'is_active': True
        },
        {
            'name': 'Eggplant 1kg',
            'description': 'Fresh purple eggplant',
            'sku': 'VEG009',
            'quantity': 20,
            'unit_price': 60.00,
            'selling_price': 90.00,
            'reorder_point': 6,
            'category': 'Vegetables',
            'is_active': True
        },
        {
            'name': 'Okra 500g',
            'description': 'Fresh lady finger okra',
            'sku': 'VEG010',
            'quantity': 15,
            'unit_price': 40.00,
            'selling_price': 65.00,
            'reorder_point': 5,
            'category': 'Vegetables',
            'is_active': True
        },

        # FRUITS
        {
            'name': 'Bananas 1kg',
            'description': 'Saba bananas per kilo',
            'sku': 'FRU001',
            'quantity': 40,
            'unit_price': 45.00,
            'selling_price': 70.00,
            'reorder_point': 15,
            'category': 'Fruits',
            'is_active': True
        },
        {
            'name': 'Mangoes 1kg',
            'description': 'Carabao mangoes',
            'sku': 'FRU002',
            'quantity': 25,
            'unit_price': 120.00,
            'selling_price': 180.00,
            'reorder_point': 8,
            'category': 'Fruits',
            'is_active': True
        },
        {
            'name': 'Apples 1kg',
            'description': 'Red delicious apples',
            'sku': 'FRU003',
            'quantity': 30,
            'unit_price': 150.00,
            'selling_price': 220.00,
            'reorder_point': 10,
            'category': 'Fruits',
            'is_active': True
        },
        {
            'name': 'Oranges 1kg',
            'description': 'Sweet oranges',
            'sku': 'FRU004',
            'quantity': 35,
            'unit_price': 100.00,
            'selling_price': 150.00,
            'reorder_point': 12,
            'category': 'Fruits',
            'is_active': True
        },
        {
            'name': 'Grapes 500g',
            'description': 'Red grapes pack',
            'sku': 'FRU005',
            'quantity': 20,
            'unit_price': 180.00,
            'selling_price': 260.00,
            'reorder_point': 6,
            'category': 'Fruits',
            'is_active': True
        },

        # DAIRY & EGGS
        {
            'name': 'Fresh Eggs 12pcs',
            'description': 'Farm fresh chicken eggs tray',
            'sku': 'DAI001',
            'quantity': 50,
            'unit_price': 80.00,
            'selling_price': 120.00,
            'reorder_point': 20,
            'category': 'Dairy & Eggs',
            'is_active': True
        },
        {
            'name': 'Alaska Milk 1L',
            'description': 'Alaska fresh milk carton',
            'sku': 'DAI002',
            'quantity': 30,
            'unit_price': 65.00,
            'selling_price': 95.00,
            'reorder_point': 10,
            'category': 'Dairy & Eggs',
            'is_active': True
        },
        {
            'name': 'Cheese Singles 200g',
            'description': 'Eden cheese slices',
            'sku': 'DAI003',
            'quantity': 25,
            'unit_price': 85.00,
            'selling_price': 125.00,
            'reorder_point': 8,
            'category': 'Dairy & Eggs',
            'is_active': True
        },
        {
            'name': 'Butter 227g',
            'description': 'Star margarine butter',
            'sku': 'DAI004',
            'quantity': 20,
            'unit_price': 45.00,
            'selling_price': 70.00,
            'reorder_point': 8,
            'category': 'Dairy & Eggs',
            'is_active': True
        },

        # PANTRY STAPLES
        {
            'name': 'Cooking Oil 1L',
            'description': 'Baguio cooking oil bottle',
            'sku': 'PAN001',
            'quantity': 40,
            'unit_price': 65.00,
            'selling_price': 95.00,
            'reorder_point': 15,
            'category': 'Pantry Staples',
            'is_active': True
        },
        {
            'name': 'Soy Sauce 1L',
            'description': 'Datu Puti soy sauce',
            'sku': 'PAN002',
            'quantity': 35,
            'unit_price': 45.00,
            'selling_price': 70.00,
            'reorder_point': 12,
            'category': 'Pantry Staples',
            'is_active': True
        },
        {
            'name': 'Vinegar 1L',
            'description': 'Datu Puti vinegar',
            'sku': 'PAN003',
            'quantity': 30,
            'unit_price': 35.00,
            'selling_price': 55.00,
            'reorder_point': 10,
            'category': 'Pantry Staples',
            'is_active': True
        },
        {
            'name': 'Salt 1kg',
            'description': 'Refined iodized salt',
            'sku': 'PAN004',
            'quantity': 25,
            'unit_price': 18.00,
            'selling_price': 30.00,
            'reorder_point': 8,
            'category': 'Pantry Staples',
            'is_active': True
        },
        {
            'name': 'Sugar 1kg',
            'description': 'Refined white sugar',
            'sku': 'PAN005',
            'quantity': 30,
            'unit_price': 55.00,
            'selling_price': 80.00,
            'reorder_point': 10,
            'category': 'Pantry Staples',
            'is_active': True
        },
        {
            'name': 'Fish Sauce 750ml',
            'description': 'Rufina patis fish sauce',
            'sku': 'PAN006',
            'quantity': 20,
            'unit_price': 40.00,
            'selling_price': 65.00,
            'reorder_point': 8,
            'category': 'Pantry Staples',
            'is_active': True
        },
        {
            'name': 'Oyster Sauce 510g',
            'description': 'Lee Kum Kee oyster sauce',
            'sku': 'PAN007',
            'quantity': 15,
            'unit_price': 85.00,
            'selling_price': 125.00,
            'reorder_point': 5,
            'category': 'Pantry Staples',
            'is_active': True
        },

        # SNACKS
        {
            'name': 'Chippy 110g',
            'description': 'Chippy corn chips barbecue',
            'sku': 'SNA001',
            'quantity': 50,
            'unit_price': 25.00,
            'selling_price': 40.00,
            'reorder_point': 20,
            'category': 'Snacks',
            'is_active': True
        },
        {
            'name': 'Piattos 85g',
            'description': 'Piattos potato chips cheese',
            'sku': 'SNA002',
            'quantity': 40,
            'unit_price': 30.00,
            'selling_price': 45.00,
            'reorder_point': 15,
            'category': 'Snacks',
            'is_active': True
        },
        {
            'name': 'Nova 78g',
            'description': 'Nova multigrain snack',
            'sku': 'SNA003',
            'quantity': 35,
            'unit_price': 22.00,
            'selling_price': 35.00,
            'reorder_point': 12,
            'category': 'Snacks',
            'is_active': True
        },
        {
            'name': 'Skyflakes 800g',
            'description': 'Skyflakes crackers family pack',
            'sku': 'SNA004',
            'quantity': 20,
            'unit_price': 65.00,
            'selling_price': 95.00,
            'reorder_point': 8,
            'category': 'Snacks',
            'is_active': True
        },
        {
            'name': 'Ricoa Flat Tops 24g',
            'description': 'Ricoa chocolate wafer',
            'sku': 'SNA005',
            'quantity': 60,
            'unit_price': 8.00,
            'selling_price': 15.00,
            'reorder_point': 25,
            'category': 'Snacks',
            'is_active': True
        },

        # INSTANT NOODLES
        {
            'name': 'Lucky Me Pancit Canton 60g',
            'description': 'Lucky Me instant pancit canton',
            'sku': 'NOO001',
            'quantity': 100,
            'unit_price': 12.00,
            'selling_price': 18.00,
            'reorder_point': 40,
            'category': 'Instant Noodles',
            'is_active': True
        },
        {
            'name': 'Nissin Cup Noodles 70g',
            'description': 'Nissin cup noodles seafood',
            'sku': 'NOO002',
            'quantity': 80,
            'unit_price': 18.00,
            'selling_price': 28.00,
            'reorder_point': 30,
            'category': 'Instant Noodles',
            'is_active': True
        },
        {
            'name': 'Maggi Magic Sarap 50g',
            'description': 'Maggi seasoning granules',
            'sku': 'NOO003',
            'quantity': 40,
            'unit_price': 22.00,
            'selling_price': 35.00,
            'reorder_point': 15,
            'category': 'Instant Noodles',
            'is_active': True
        },

        # CANNED GOODS
        {
            'name': 'Corned Beef 340g',
            'description': 'Argentina corned beef can',
            'sku': 'CAN001',
            'quantity': 50,
            'unit_price': 85.00,
            'selling_price': 125.00,
            'reorder_point': 20,
            'category': 'Canned Goods',
            'is_active': True
        },
        {
            'name': 'Sardines 155g',
            'description': 'Ligo sardines in tomato sauce',
            'sku': 'CAN002',
            'quantity': 60,
            'unit_price': 18.00,
            'selling_price': 28.00,
            'reorder_point': 25,
            'category': 'Canned Goods',
            'is_active': True
        },
        {
            'name': 'Tuna Flakes 180g',
            'description': 'Century tuna flakes in oil',
            'sku': 'CAN003',
            'quantity': 45,
            'unit_price': 45.00,
            'selling_price': 70.00,
            'reorder_point': 18,
            'category': 'Canned Goods',
            'is_active': True
        },
        {
            'name': 'Tomato Sauce 250g',
            'description': 'Del Monte tomato sauce',
            'sku': 'CAN004',
            'quantity': 40,
            'unit_price': 25.00,
            'selling_price': 40.00,
            'reorder_point': 15,
            'category': 'Canned Goods',
            'is_active': True
        },

        # BREAD & BAKERY
        {
            'name': 'Tasty Bread Loaf',
            'description': 'Gardenia Classic White Bread',
            'sku': 'BAK001',
            'quantity': 30,
            'unit_price': 42.00,
            'selling_price': 60.00,
            'reorder_point': 10,
            'category': 'Bread & Bakery',
            'is_active': True
        },
        {
            'name': 'Pandesal 10pcs',
            'description': 'Fresh pandesal pack',
            'sku': 'BAK002',
            'quantity': 25,
            'unit_price': 18.00,
            'selling_price': 30.00,
            'reorder_point': 8,
            'category': 'Bread & Bakery',
            'is_active': True
        },
        {
            'name': 'Mongo Bread',
            'description': 'Mongo (mung bean) filled bread',
            'sku': 'BAK003',
            'quantity': 20,
            'unit_price': 15.00,
            'selling_price': 25.00,
            'reorder_point': 8,
            'category': 'Bread & Bakery',
            'is_active': True
        },

        # CLEANING SUPPLIES
        {
            'name': 'Tide Powder 1kg',
            'description': 'Tide laundry detergent powder',
            'sku': 'CLE001',
            'quantity': 25,
            'unit_price': 120.00,
            'selling_price': 180.00,
            'reorder_point': 8,
            'category': 'Cleaning Supplies',
            'is_active': True
        },
        {
            'name': 'Joy Dishwashing Liquid 500ml',
            'description': 'Joy antibac dishwashing liquid',
            'sku': 'CLE002',
            'quantity': 30,
            'unit_price': 45.00,
            'selling_price': 70.00,
            'reorder_point': 10,
            'category': 'Cleaning Supplies',
            'is_active': True
        },
        {
            'name': 'Lysol Disinfectant 500ml',
            'description': 'Lysol multi-surface disinfectant',
            'sku': 'CLE003',
            'quantity': 20,
            'unit_price': 85.00,
            'selling_price': 125.00,
            'reorder_point': 6,
            'category': 'Cleaning Supplies',
            'is_active': True
        },

        # PERSONAL CARE
        {
            'name': 'Safeguard Soap 135g',
            'description': 'Safeguard antibacterial soap',
            'sku': 'PER001',
            'quantity': 40,
            'unit_price': 25.00,
            'selling_price': 40.00,
            'reorder_point': 15,
            'category': 'Personal Care',
            'is_active': True
        },
        {
            'name': 'Head & Shoulders 170ml',
            'description': 'Head & Shoulders anti-dandruff shampoo',
            'sku': 'PER002',
            'quantity': 25,
            'unit_price': 85.00,
            'selling_price': 125.00,
            'reorder_point': 8,
            'category': 'Personal Care',
            'is_active': True
        },
        {
            'name': 'Colgate Toothpaste 225g',
            'description': 'Colgate total whitening toothpaste',
            'sku': 'PER003',
            'quantity': 30,
            'unit_price': 65.00,
            'selling_price': 95.00,
            'reorder_point': 10,
            'category': 'Personal Care',
            'is_active': True
        },

        # CONDIMENTS & SAUCES
        {
            'name': 'Ketchup 320g',
            'description': 'Del Monte tomato ketchup',
            'sku': 'CON001',
            'quantity': 35,
            'unit_price': 45.00,
            'selling_price': 70.00,
            'reorder_point': 12,
            'category': 'Condiments',
            'is_active': True
        },
        {
            'name': 'Mayonnaise 470ml',
            'description': 'Lady\'s Choice real mayonnaise',
            'sku': 'CON002',
            'quantity': 25,
            'unit_price': 75.00,
            'selling_price': 110.00,
            'reorder_point': 8,
            'category': 'Condiments',
            'is_active': True
        },
        {
            'name': 'Banana Ketchup 550g',
            'description': 'UFC banana catsup sweet style',
            'sku': 'CON003',
            'quantity': 30,
            'unit_price': 55.00,
            'selling_price': 85.00,
            'reorder_point': 10,
            'category': 'Condiments',
            'is_active': True
        },

        # FROZEN GOODS
        {
            'name': 'Ice Cream 1.5L',
            'description': 'Selecta ice cream family pack',
            'sku': 'FRO001',
            'quantity': 15,
            'unit_price': 180.00,
            'selling_price': 260.00,
            'reorder_point': 5,
            'category': 'Frozen Goods',
            'is_active': True
        },
        {
            'name': 'Frozen Lumpia 500g',
            'description': 'Frozen vegetable lumpia',
            'sku': 'FRO002',
            'quantity': 20,
            'unit_price': 120.00,
            'selling_price': 180.00,
            'reorder_point': 6,
            'category': 'Frozen Goods',
            'is_active': True
        },

        # BABY PRODUCTS
        {
            'name': 'Enfamil Milk 900g',
            'description': 'Enfamil infant formula milk',
            'sku': 'BAB001',
            'quantity': 10,
            'unit_price': 850.00,
            'selling_price': 1200.00,
            'reorder_point': 3,
            'category': 'Baby Products',
            'is_active': True
        },
        {
            'name': 'Pampers Diapers S 40pcs',
            'description': 'Pampers baby dry diapers small',
            'sku': 'BAB002',
            'quantity': 15,
            'unit_price': 320.00,
            'selling_price': 450.00,
            'reorder_point': 5,
            'category': 'Baby Products',
            'is_active': True
        },

        # CIGARETTES & TOBACCO
        {
            'name': 'Marlboro Red Pack',
            'description': 'Marlboro cigarettes red pack',
            'sku': 'CIG001',
            'quantity': 50,
            'unit_price': 110.00,
            'selling_price': 140.00,
            'reorder_point': 20,
            'category': 'Cigarettes',
            'is_active': True
        },
        {
            'name': 'Philip Morris Pack',
            'description': 'Philip Morris cigarettes',
            'sku': 'CIG002',
            'quantity': 40,
            'unit_price': 95.00,
            'selling_price': 120.00,
            'reorder_point': 15,
            'category': 'Cigarettes',
            'is_active': True
        },

        # OFFICE/SCHOOL SUPPLIES
        {
            'name': 'Ballpen Blue 12pcs',
            'description': 'HBW ballpoint pen blue',
            'sku': 'OFF001',
            'quantity': 30,
            'unit_price': 60.00,
            'selling_price': 90.00,
            'reorder_point': 10,
            'category': 'Office Supplies',
            'is_active': True
        },
        {
            'name': 'Bond Paper 500 sheets',
            'description': 'A4 bond paper ream',
            'sku': 'OFF002',
            'quantity': 20,
            'unit_price': 180.00,
            'selling_price': 250.00,
            'reorder_point': 6,
            'category': 'Office Supplies',
            'is_active': True
        }
    ]

    for item_data in sample_items:
        item = InventoryItem(**item_data)
        db.session.add(item)

    try:
        db.session.commit()
        logging.info("Sample data added successfully")
        logging.info("Default admin user: admin/admin123")
        logging.info("Default staff user: staff/staff123")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding sample data: {e}")

# Import routes after app context
from routes import *

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)