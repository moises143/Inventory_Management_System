from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db
from models import (User, InventoryItem, Supplier, StockTransaction, Sale, SaleItem, UserRole)
from auth_decorators import login_required, admin_required, staff_or_admin_required
from datetime import datetime, timedelta
from sqlalchemy import func, desc


# Authentication Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact admin.', 'error')
                return render_template('login.html')

            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role.value

            flash(f'Welcome back, {user.username}!', 'success')

            # Redirect based on role
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('sales_dashboard'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))


# Dashboard Routes
@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    if user.is_admin():
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('sales_dashboard'))


# Sales Routes
@app.route('/sales')
@staff_or_admin_required
def sales_dashboard():
    user = User.query.get(session['user_id'])

    # Get today's sales stats
    today = datetime.now().date()
    today_sales = Sale.query.filter(func.date(Sale.sale_date) == today).all()
    today_revenue = sum(sale.total_amount for sale in today_sales)

    # Get this week's stats
    week_start = today - timedelta(days=today.weekday())
    week_sales = Sale.query.filter(Sale.sale_date >= week_start).all()
    week_revenue = sum(sale.total_amount for sale in week_sales)

    # Get recent sales (staff sees only their sales)
    if user.is_admin():
        recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(10).all()
    else:
        recent_sales = Sale.query.filter_by(staff_id=user.id).order_by(Sale.sale_date.desc()).limit(10).all()

    # Get available products for sale
    available_products = InventoryItem.query.filter(
        InventoryItem.is_active == True,
        InventoryItem.quantity > 0
    ).all()

    return render_template('sales_dashboard.html',
                           today_sales_count=len(today_sales),
                           today_revenue=today_revenue,
                           week_sales_count=len(week_sales),
                           week_revenue=week_revenue,
                           recent_sales=recent_sales,
                           available_products=available_products,
                           user=user)


@app.route('/sales/new')
@staff_or_admin_required
def new_sale():
    available_products = InventoryItem.query.filter(
        InventoryItem.is_active == True,
        InventoryItem.quantity > 0
    ).all()
    return render_template('new_sale.html', products=available_products)


@app.route('/sales/create', methods=['POST'])
@staff_or_admin_required
def create_sale():
    try:
        customer_name = request.form.get('customer_name', '')
        payment_method = request.form.get('payment_method', 'cash')
        notes = request.form.get('notes', '')

        # Get cart items from form
        cart_items = []
        item_ids = request.form.getlist('item_id[]')
        quantities = request.form.getlist('quantity[]')

        if not item_ids:
            flash('Please add items to the sale.', 'error')
            return redirect(url_for('new_sale'))

        total_amount = 0

        # Validate items and calculate total
        for i, item_id in enumerate(item_ids):
            if not item_id:
                continue

            item = InventoryItem.query.get(int(item_id))
            quantity = int(quantities[i])

            if not item:
                flash(f'Invalid item selected.', 'error')
                return redirect(url_for('new_sale'))

            if quantity > item.quantity:
                flash(f'Insufficient stock for {item.name}. Available: {item.quantity}', 'error')
                return redirect(url_for('new_sale'))

            if quantity <= 0:
                flash(f'Invalid quantity for {item.name}.', 'error')
                return redirect(url_for('new_sale'))

            item_total = quantity * item.selling_price
            total_amount += item_total

            cart_items.append({
                'item': item,
                'quantity': quantity,
                'unit_price': item.selling_price,
                'total_price': item_total
            })

        if not cart_items:
            flash('Please add valid items to the sale.', 'error')
            return redirect(url_for('new_sale'))

        # Generate a temporary sale number first
        from datetime import datetime
        temp_sale_number = f"SALE-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Create sale with temporary sale number
        sale = Sale(
            sale_number=temp_sale_number,  # Use temporary number
            total_amount=total_amount,
            staff_id=session['user_id'],
            customer_name=customer_name,
            payment_method=payment_method,
            notes=notes
        )

        db.session.add(sale)
        db.session.flush()  # This gives us the sale ID

        # Now update with proper sale number using the ID
        sale.sale_number = f"SALE-{datetime.now().strftime('%Y%m%d')}-{sale.id:04d}"

        # Create sale items and update inventory
        for cart_item in cart_items:
            sale_item = SaleItem(
                sale_id=sale.id,
                item_id=cart_item['item'].id,
                quantity=cart_item['quantity'],
                unit_price=cart_item['unit_price'],
                total_price=cart_item['total_price']
            )
            db.session.add(sale_item)

            # Update inventory quantity
            cart_item['item'].quantity -= cart_item['quantity']

            # Record stock transaction
            stock_transaction = StockTransaction(
                item_id=cart_item['item'].id,
                transaction_type='sale',
                quantity=-cart_item['quantity'],
                notes=f'Sale #{sale.sale_number}',
                user_id=session['user_id']
            )
            db.session.add(stock_transaction)

        db.session.commit()
        flash(f'Sale #{sale.sale_number} completed successfully!', 'success')
        return redirect(url_for('sale_receipt', sale_id=sale.id))

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating sale: {str(e)}', 'error')
        return redirect(url_for('new_sale'))


@app.route('/sales/<int:sale_id>/receipt')
@staff_or_admin_required
def sale_receipt(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    return render_template('sale_receipt.html', sale=sale)


@app.route('/sales/history')
@staff_or_admin_required
def sales_history():
    user = User.query.get(session['user_id'])
    page = request.args.get('page', 1, type=int)
    per_page = 20

    # If staff, show only their sales; if admin, show all
    if user.is_admin():
        sales = Sale.query.order_by(Sale.sale_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        sales = Sale.query.filter_by(staff_id=user.id).order_by(Sale.sale_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    return render_template('sales_history.html', sales=sales)


# Admin Routes
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Enhanced admin dashboard with sales analytics

    # Staff performance
    staff_performance = db.session.query(
        User.username,
        func.count(Sale.id).label('total_sales'),
        func.sum(Sale.total_amount).label('total_revenue')
    ).join(Sale, User.id == Sale.staff_id) \
        .filter(User.role == UserRole.STAFF) \
        .group_by(User.id, User.username) \
        .all()

    # Recent activity
    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(5).all()

    # Daily sales for the last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    daily_sales = db.session.query(
        func.date(Sale.sale_date).label('date'),
        func.count(Sale.id).label('sales_count'),
        func.sum(Sale.total_amount).label('revenue')
    ).filter(Sale.sale_date >= seven_days_ago) \
        .group_by(func.date(Sale.sale_date)) \
        .all()

    # Total stats
    total_staff = User.query.filter_by(role=UserRole.STAFF, is_active=True).count()
    total_sales_today = Sale.query.filter(
        func.date(Sale.sale_date) == datetime.now().date()
    ).count()

    # Get inventory stats
    total_items = InventoryItem.query.count()
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.reorder_point
    ).count()
    total_suppliers = Supplier.query.count()
    total_value = sum(item.total_value for item in InventoryItem.query.all())

    return render_template('admin_dashboard.html',
                           staff_performance=staff_performance,
                           recent_sales=recent_sales,
                           daily_sales=daily_sales,
                           total_staff=total_staff,
                           total_sales_today=total_sales_today,
                           total_items=total_items,
                           low_stock_items=low_stock_items,
                           total_suppliers=total_suppliers,
                           total_value=total_value)


@app.route('/admin/staff')
@admin_required
def staff_management():
    staff_members = User.query.filter_by(role=UserRole.STAFF).order_by(User.created_at.desc()).all()
    return render_template('staff_management.html', staff_members=staff_members)


@app.route('/admin/staff/add', methods=['POST'])
@admin_required
def add_staff():
    try:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('staff_management'))

        if User.query.filter_by(email=email).first():
            flash('Email already exists!', 'error')
            return redirect(url_for('staff_management'))

        # Create new staff user
        staff_user = User(
            username=username,
            email=email,
            role=UserRole.STAFF,
            created_by=session['user_id']
        )
        staff_user.set_password(password)

        db.session.add(staff_user)
        db.session.commit()

        flash(f'Staff member {username} added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding staff member: {str(e)}', 'error')

    return redirect(url_for('staff_management'))


@app.route('/admin/staff/<int:staff_id>/toggle', methods=['POST'])
@admin_required
def toggle_staff_status(staff_id):
    staff = User.query.get_or_404(staff_id)

    if staff.role != UserRole.STAFF:
        flash('Can only modify staff accounts!', 'error')
        return redirect(url_for('staff_management'))

    staff.is_active = not staff.is_active
    db.session.commit()

    status = "activated" if staff.is_active else "deactivated"
    flash(f'Staff member {staff.username} {status} successfully!', 'success')

    return redirect(url_for('staff_management'))


@app.route('/admin/staff/<int:staff_id>/reset-password', methods=['POST'])
@admin_required
def reset_staff_password(staff_id):
    staff = User.query.get_or_404(staff_id)
    new_password = request.form['new_password']

    if staff.role != UserRole.STAFF:
        flash('Can only modify staff accounts!', 'error')
        return redirect(url_for('staff_management'))

    staff.set_password(new_password)
    db.session.commit()

    flash(f'Password reset for {staff.username} successfully!', 'success')
    return redirect(url_for('staff_management'))


# Existing Inventory Routes (Enhanced)
@app.route('/inventory')
@login_required
def inventory():
    search = request.args.get('search', '')
    category = request.args.get('category', '')

    query = InventoryItem.query

    if search:
        query = query.filter(InventoryItem.name.contains(search))

    if category:
        query = query.filter(InventoryItem.category == category)

    items = query.all()

    # Get all categories for filter
    categories = db.session.query(InventoryItem.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]

    # Get suppliers for dropdown
    suppliers = Supplier.query.all()

    return render_template('inventory.html',
                           items=items,
                           categories=categories,
                           suppliers=suppliers)


@app.route('/inventory/add', methods=['POST'])
@admin_required
def add_inventory_item():
    try:
        name = request.form['name']
        description = request.form.get('description', '')
        sku = request.form.get('sku', '')
        quantity = int(request.form['quantity'])
        unit_price = float(request.form['unit_price'])
        selling_price = float(request.form.get('selling_price', unit_price * 1.2))  # Default 20% markup
        reorder_point = int(request.form['reorder_point'])
        category = request.form.get('category', '')
        supplier_id = request.form.get('supplier_id')

        if supplier_id:
            supplier_id = int(supplier_id)
        else:
            supplier_id = None

        item = InventoryItem(
            name=name,
            description=description,
            sku=sku,
            quantity=quantity,
            unit_price=unit_price,
            selling_price=selling_price,
            reorder_point=reorder_point,
            category=category,
            supplier_id=supplier_id
        )

        db.session.add(item)
        db.session.commit()

        # Record stock transaction
        if quantity > 0:
            transaction = StockTransaction(
                item_id=item.id,
                transaction_type='in',
                quantity=quantity,
                notes='Initial stock',
                user_id=session['user_id']
            )
            db.session.add(transaction)
            db.session.commit()

        flash(f'Item "{name}" added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding item: {str(e)}', 'error')

    return redirect(url_for('inventory'))


@app.route('/inventory/update/<int:item_id>', methods=['POST'])
@admin_required
def update_inventory_item(item_id):
    try:
        item = InventoryItem.query.get_or_404(item_id)

        old_quantity = item.quantity

        item.name = request.form['name']
        item.description = request.form.get('description', '')
        item.sku = request.form.get('sku', '')
        item.quantity = int(request.form['quantity'])
        item.unit_price = float(request.form['unit_price'])
        item.selling_price = float(request.form.get('selling_price', item.unit_price * 1.2))
        item.reorder_point = int(request.form['reorder_point'])
        item.category = request.form.get('category', '')

        supplier_id = request.form.get('supplier_id')
        if supplier_id:
            item.supplier_id = int(supplier_id)
        else:
            item.supplier_id = None

        item.updated_at = datetime.utcnow()

        # Record quantity change as transaction
        quantity_diff = item.quantity - old_quantity
        if quantity_diff != 0:
            transaction_type = 'in' if quantity_diff > 0 else 'out'
            transaction = StockTransaction(
                item_id=item.id,
                transaction_type='adjustment',
                quantity=quantity_diff,
                notes=f'Manual adjustment: {old_quantity} → {item.quantity}',
                user_id=session['user_id']
            )
            db.session.add(transaction)

        db.session.commit()
        flash(f'Item "{item.name}" updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating item: {str(e)}', 'error')

    return redirect(url_for('inventory'))


@app.route('/inventory/delete/<int:item_id>', methods=['POST'])
@admin_required
def delete_inventory_item(item_id):
    try:
        item = InventoryItem.query.get_or_404(item_id)
        item_name = item.name

        db.session.delete(item)
        db.session.commit()

        flash(f'Item "{item_name}" deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {str(e)}', 'error')

    return redirect(url_for('inventory'))


# Existing Supplier Routes
@app.route('/suppliers')
@admin_required
def suppliers():
    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers)


@app.route('/suppliers/add', methods=['POST'])
@admin_required
def add_supplier():
    try:
        name = request.form['name']
        contact_person = request.form.get('contact_person', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')

        supplier = Supplier(
            name=name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            address=address
        )

        db.session.add(supplier)
        db.session.commit()

        flash(f'Supplier "{name}" added successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error adding supplier: {str(e)}', 'error')

    return redirect(url_for('suppliers'))


@app.route('/suppliers/update/<int:supplier_id>', methods=['POST'])
@admin_required
def update_supplier(supplier_id):
    try:
        supplier = Supplier.query.get_or_404(supplier_id)

        supplier.name = request.form['name']
        supplier.contact_person = request.form.get('contact_person', '')
        supplier.email = request.form.get('email', '')
        supplier.phone = request.form.get('phone', '')
        supplier.address = request.form.get('address', '')

        db.session.commit()
        flash(f'Supplier "{supplier.name}" updated successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating supplier: {str(e)}', 'error')

    return redirect(url_for('suppliers'))


@app.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
@admin_required
def delete_supplier(supplier_id):
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        supplier_name = supplier.name

        db.session.delete(supplier)
        db.session.commit()

        flash(f'Supplier "{supplier_name}" deleted successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting supplier: {str(e)}', 'error')

    return redirect(url_for('suppliers'))


# Reports Route (Enhanced)
@app.route('/reports')
@login_required
def reports():
    user = User.query.get(session['user_id'])

    # Basic inventory stats
    total_items = InventoryItem.query.count()
    total_value = sum(item.total_value for item in InventoryItem.query.all())
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.reorder_point
    ).all()

    # Category summary
    category_summary = db.session.query(
        InventoryItem.category,
        func.count(InventoryItem.id),
        func.sum(InventoryItem.quantity * InventoryItem.unit_price)
    ).group_by(InventoryItem.category).all()

    # Recent transactions
    recent_transactions = db.session.query(StockTransaction, InventoryItem.name) \
        .join(InventoryItem, StockTransaction.item_id == InventoryItem.id) \
        .order_by(StockTransaction.timestamp.desc()) \
        .limit(20).all()

    # Sales data (if admin or staff can see their own sales)
    sales_data = []
    if user.is_admin():
        sales_data = Sale.query.order_by(Sale.sale_date.desc()).limit(10).all()
    elif user.is_staff():
        sales_data = Sale.query.filter_by(staff_id=user.id).order_by(Sale.sale_date.desc()).limit(10).all()

    return render_template('reports.html',
                           total_items=total_items,
                           total_value=total_value,
                           low_stock_items=low_stock_items,
                           category_summary=category_summary,
                           recent_transactions=recent_transactions,
                           sales_data=sales_data,
                           user=user)


# API Routes for AJAX
@app.route('/api/product/<int:product_id>')
@staff_or_admin_required
def get_product_info(product_id):
    product = InventoryItem.query.get_or_404(product_id)
    return jsonify({
        'id': product.id,
        'name': product.name,
        'selling_price': product.selling_price,
        'quantity': product.quantity,
        'sku': product.sku
    })


# Admin DB View (Enhanced)
@app.route('/admin/db-view')
@admin_required
def admin_db_view():
    try:
        users = User.query.all()
        items = InventoryItem.query.all()
        suppliers = Supplier.query.all()
        sales = Sale.query.order_by(Sale.sale_date.desc()).limit(50).all()  # Last 50 sales
        transactions = StockTransaction.query.order_by(StockTransaction.timestamp.desc()).limit(
            50).all()  # Last 50 transactions

        return render_template('admin_db_view.html',
                               users=users,
                               items=items,
                               suppliers=suppliers,
                               sales=sales,
                               transactions=transactions)
    except Exception as e:
        flash(f'Error loading database view: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))


@app.route('/admin/db/clear-all', methods=['POST'])
@admin_required
def clear_all_data():
    try:
        confirmation = request.form.get('confirm_clear')
        if confirmation != 'DELETE_ALL_DATA':
            flash('Please type "DELETE_ALL_DATA" to confirm deletion.', 'error')
            return redirect(url_for('admin_db_view'))

        # Delete in proper order to avoid foreign key constraints
        db.session.execute('DELETE FROM sale_item')
        db.session.execute('DELETE FROM stock_transaction')
        db.session.execute('DELETE FROM sale')
        db.session.execute('DELETE FROM inventory_item')
        db.session.execute('DELETE FROM supplier')

        # Keep users but reset staff users (keep admin)
        staff_users = User.query.filter_by(role=UserRole.STAFF).all()
        for staff in staff_users:
            db.session.delete(staff)

        # Reset auto-increment counters (SQLite specific)
        db.session.execute(
            'DELETE FROM sqlite_sequence WHERE name IN ("sale_item", "stock_transaction", "sale", "inventory_item", "supplier")')

        db.session.commit()

        flash('All data cleared successfully! Database has been reset.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing data: {str(e)}', 'error')

    return redirect(url_for('admin_db_view'))


@app.route('/admin/db/clear-table/<table_name>', methods=['POST'])
@admin_required
def clear_table_data(table_name):
    try:
        confirmation = request.form.get('confirm_table_clear')
        if confirmation != f'DELETE_{table_name.upper()}':
            flash(f'Please type "DELETE_{table_name.upper()}" to confirm deletion.', 'error')
            return redirect(url_for('admin_db_view'))

        # Map table names to models and their dependencies
        table_dependencies = {
            'sale_item': ['sale_item'],
            'stock_transaction': ['stock_transaction'],
            'sale': ['sale_item', 'sale'],
            'inventory_item': ['sale_item', 'stock_transaction', 'inventory_item'],
            'supplier': ['inventory_item', 'sale_item', 'stock_transaction', 'supplier'],
            'user': ['sale', 'stock_transaction']  # Only staff users
        }

        if table_name not in table_dependencies:
            flash('Invalid table name.', 'error')
            return redirect(url_for('admin_db_view'))

        # Delete in proper order
        for dep_table in table_dependencies[table_name]:
            if dep_table == 'user':
                # Only delete staff users, keep admin
                db.session.execute('DELETE FROM user WHERE role = "staff"')
            else:
                db.session.execute(f'DELETE FROM {dep_table}')

        # Reset auto-increment counter
        if table_name != 'user':
            db.session.execute(f'DELETE FROM sqlite_sequence WHERE name = "{table_name}"')

        db.session.commit()

        flash(f'Table "{table_name}" cleared successfully!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing table: {str(e)}', 'error')

    return redirect(url_for('admin_db_view'))


@app.route('/admin/db/populate-sample', methods=['POST'])
@admin_required
def populate_sample_data():
    try:
        # Add sample suppliers
        if Supplier.query.count() == 0:
            suppliers = [
                Supplier(name='Tech Supplies PH', contact_person='Juan Dela Cruz',
                         email='juan@techsupplies.ph', phone='+63-917-123-4567',
                         address='123 Tech Street, Makati City'),
                Supplier(name='Office Depot Manila', contact_person='Maria Santos',
                         email='maria@officedepot.ph', phone='+63-918-765-4321',
                         address='456 Business Ave, BGC, Taguig'),
                Supplier(name='Gadget World Cebu', contact_person='Carlos Reyes',
                         email='carlos@gadgetworld.ph', phone='+63-919-987-6543',
                         address='789 IT Park, Lahug, Cebu City')
            ]
            for supplier in suppliers:
                db.session.add(supplier)
            db.session.flush()

        # Add sample inventory items with Philippine pricing
        if InventoryItem.query.count() == 0:
            sample_items = [
                {
                    'name': 'Samsung Galaxy A54',
                    'description': 'Samsung Galaxy A54 5G 128GB - Latest smartphone with great camera',
                    'sku': 'PHONE001',
                    'quantity': 15,
                    'unit_price': 18000.00,
                    'selling_price': 25000.00,
                    'reorder_point': 5,
                    'category': 'Mobile Phones',
                    'supplier_id': 1,
                    'is_active': True
                },
                {
                    'name': 'iPhone 14',
                    'description': 'Apple iPhone 14 128GB - Premium smartphone',
                    'sku': 'PHONE002',
                    'quantity': 8,
                    'unit_price': 45000.00,
                    'selling_price': 55000.00,
                    'reorder_point': 3,
                    'category': 'Mobile Phones',
                    'supplier_id': 1,
                    'is_active': True
                },
                {
                    'name': 'Office Chair Ergonomic',
                    'description': 'High-back ergonomic office chair with lumbar support',
                    'sku': 'CHR001',
                    'quantity': 25,
                    'unit_price': 3500.00,
                    'selling_price': 5500.00,
                    'reorder_point': 5,
                    'category': 'Furniture',
                    'supplier_id': 2,
                    'is_active': True
                },
                {
                    'name': 'Gaming Chair RGB',
                    'description': 'Racing style gaming chair with RGB lighting',
                    'sku': 'CHR002',
                    'quantity': 12,
                    'unit_price': 8000.00,
                    'selling_price': 12000.00,
                    'reorder_point': 3,
                    'category': 'Furniture',
                    'supplier_id': 2,
                    'is_active': True
                },
                {
                    'name': 'Logitech Wireless Mouse',
                    'description': 'Logitech M705 Marathon Wireless Mouse',
                    'sku': 'MOU001',
                    'quantity': 50,
                    'unit_price': 800.00,
                    'selling_price': 1200.00,
                    'reorder_point': 10,
                    'category': 'Computer Accessories',
                    'supplier_id': 3,
                    'is_active': True
                },
                {
                    'name': 'Gaming Mouse RGB',
                    'description': 'High-DPI gaming mouse with RGB lighting',
                    'sku': 'MOU002',
                    'quantity': 30,
                    'unit_price': 1500.00,
                    'selling_price': 2500.00,
                    'reorder_point': 8,
                    'category': 'Computer Accessories',
                    'supplier_id': 3,
                    'is_active': True
                },
                {
                    'name': 'USB-C Cable',
                    'description': 'Premium USB-C to USB-A cable, 2m length',
                    'sku': 'CAB001',
                    'quantity': 100,
                    'unit_price': 150.00,
                    'selling_price': 299.00,
                    'reorder_point': 20,
                    'category': 'Cables & Adapters',
                    'supplier_id': 3,
                    'is_active': True
                },
                {
                    'name': 'HDMI Cable 4K',
                    'description': 'High-speed HDMI cable supports 4K@60Hz, 3m length',
                    'sku': 'CAB002',
                    'quantity': 75,
                    'unit_price': 300.00,
                    'selling_price': 500.00,
                    'reorder_point': 15,
                    'category': 'Cables & Adapters',
                    'supplier_id': 3,
                    'is_active': True
                },
                {
                    'name': 'Mechanical Keyboard RGB',
                    'description': 'Gaming mechanical keyboard with RGB backlighting',
                    'sku': 'KEY001',
                    'quantity': 20,
                    'unit_price': 2500.00,
                    'selling_price': 4200.00,
                    'reorder_point': 5,
                    'category': 'Computer Accessories',
                    'supplier_id': 1,
                    'is_active': True
                },
                {
                    'name': 'Laptop Stand Aluminum',
                    'description': 'Adjustable aluminum laptop stand with cooling',
                    'sku': 'STA001',
                    'quantity': 40,
                    'unit_price': 800.00,
                    'selling_price': 1500.00,
                    'reorder_point': 8,
                    'category': 'Computer Accessories',
                    'supplier_id': 2,
                    'is_active': True
                }
            ]

            for item_data in sample_items:
                item = InventoryItem(**item_data)
                db.session.add(item)

        db.session.commit()
        flash('Sample data populated successfully! Added suppliers and inventory items with Philippine pricing.',
              'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error populating sample data: {str(e)}', 'error')

    return redirect(url_for('admin_db_view'))


@app.route('/admin/db/delete-record/<table_name>/<int:record_id>', methods=['POST'])
@admin_required
def delete_individual_record(table_name, record_id):
    try:
        if table_name == 'user':
            record = User.query.get_or_404(record_id)
            if record.role == UserRole.ADMIN:
                flash('Cannot delete admin user!', 'error')
                return redirect(url_for('admin_db_view'))

            record_name = record.username

            # Before deleting user, update related records to handle the foreign key
            # Update sales to set staff_id to NULL
            sales_updated = Sale.query.filter_by(staff_id=record_id).update({'staff_id': None})

            # Update stock transactions to set user_id to NULL
            transactions_updated = StockTransaction.query.filter_by(user_id=record_id).update({'user_id': None})

            # Now delete the user
            db.session.delete(record)

            flash(
                f'User "{record_name}" deleted successfully! Updated {sales_updated} sales and {transactions_updated} transactions.',
                'success')

        elif table_name == 'inventory_item':
            record = InventoryItem.query.get_or_404(record_id)
            record_name = record.name

            # Check for existing sales
            existing_sales = SaleItem.query.filter_by(item_id=record_id).count()
            existing_transactions = StockTransaction.query.filter_by(item_id=record_id).count()

            if existing_sales > 0 or existing_transactions > 0:
                flash(
                    f'Warning: Deleting "{record_name}" will also remove {existing_sales} sale records and {existing_transactions} transaction records.',
                    'warning')

            # CASCADE will handle related records automatically
            db.session.delete(record)
            flash(f'Inventory item "{record_name}" deleted successfully!', 'success')

        elif table_name == 'supplier':
            record = Supplier.query.get_or_404(record_id)
            record_name = record.name

            # Count related items
            related_items = InventoryItem.query.filter_by(supplier_id=record_id).count()

            if related_items > 0:
                flash(
                    f'Warning: Deleting supplier "{record_name}" will also remove {related_items} inventory items and their related data.',
                    'warning')

            # First delete related inventory items (which will cascade to sales/transactions)
            InventoryItem.query.filter_by(supplier_id=record_id).delete()

            # Then delete the supplier
            db.session.delete(record)
            flash(f'Supplier "{record_name}" deleted successfully!', 'success')

        elif table_name == 'sale':
            record = Sale.query.get_or_404(record_id)
            record_name = record.sale_number

            # CASCADE will handle sale items automatically
            db.session.delete(record)
            flash(f'Sale "{record_name}" deleted successfully!', 'success')

        elif table_name == 'stock_transaction':
            record = StockTransaction.query.get_or_404(record_id)
            record_name = f'Transaction #{record.id}'

            db.session.delete(record)
            flash(f'{record_name} deleted successfully!', 'success')

        else:
            flash('Invalid table name.', 'error')
            return redirect(url_for('admin_db_view'))

        db.session.commit()

    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting record: {str(e)}', 'error')

    return redirect(url_for('admin_db_view'))