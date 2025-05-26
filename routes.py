from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app import app, db
from models import User, InventoryItem, Supplier, StockTransaction
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import logging

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get dashboard statistics
    total_items = InventoryItem.query.count()
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.reorder_point
    ).count()
    total_suppliers = Supplier.query.count()
    total_value = db.session.query(db.func.sum(
        InventoryItem.quantity * InventoryItem.unit_price
    )).scalar() or 0
    
    # Get recent low stock alerts
    low_stock_alerts = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.reorder_point
    ).limit(5).all()
    
    return render_template('dashboard.html', 
                         total_items=total_items,
                         low_stock_items=low_stock_items,
                         total_suppliers=total_suppliers,
                         total_value=total_value,
                         low_stock_alerts=low_stock_alerts)

@app.route('/inventory')
def inventory():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    
    query = InventoryItem.query
    
    if search:
        query = query.filter(InventoryItem.name.contains(search))
    
    if category:
        query = query.filter(InventoryItem.category == category)
    
    items = query.all()
    suppliers = Supplier.query.all()
    
    # Get unique categories for filter
    categories = db.session.query(InventoryItem.category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]
    
    return render_template('inventory.html', items=items, suppliers=suppliers, categories=categories)

@app.route('/inventory/add', methods=['POST'])
def add_inventory_item():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        item = InventoryItem(
            name=request.form['name'],
            description=request.form.get('description', ''),
            sku=request.form.get('sku', ''),
            quantity=int(request.form.get('quantity', 0)),
            unit_price=float(request.form.get('unit_price', 0)),
            reorder_point=int(request.form.get('reorder_point', 10)),
            supplier_id=int(request.form['supplier_id']) if request.form.get('supplier_id') else None,
            category=request.form.get('category', '')
        )
        
        db.session.add(item)
        db.session.commit()
        
        # Record stock transaction
        transaction = StockTransaction(
            item_id=item.id,
            transaction_type='in',
            quantity=item.quantity,
            notes='Initial stock',
            user_id=session['user_id']
        )
        db.session.add(transaction)
        db.session.commit()
        
        flash('Item added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding item: {str(e)}', 'danger')
        logging.error(f"Error adding inventory item: {str(e)}")
    
    return redirect(url_for('inventory'))

@app.route('/inventory/update/<int:item_id>', methods=['POST'])
def update_inventory_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        item = InventoryItem.query.get_or_404(item_id)
        old_quantity = item.quantity
        
        item.name = request.form['name']
        item.description = request.form.get('description', '')
        item.sku = request.form.get('sku', '')
        item.quantity = int(request.form.get('quantity', 0))
        item.unit_price = float(request.form.get('unit_price', 0))
        item.reorder_point = int(request.form.get('reorder_point', 10))
        item.supplier_id = int(request.form['supplier_id']) if request.form.get('supplier_id') else None
        item.category = request.form.get('category', '')
        item.updated_at = datetime.utcnow()
        
        # Record stock transaction if quantity changed
        if old_quantity != item.quantity:
            transaction_type = 'in' if item.quantity > old_quantity else 'out'
            quantity_change = abs(item.quantity - old_quantity)
            
            transaction = StockTransaction(
                item_id=item.id,
                transaction_type=transaction_type,
                quantity=quantity_change,
                notes='Quantity adjustment',
                user_id=session['user_id']
            )
            db.session.add(transaction)
        
        db.session.commit()
        flash('Item updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating item: {str(e)}', 'danger')
        logging.error(f"Error updating inventory item: {str(e)}")
    
    return redirect(url_for('inventory'))

@app.route('/inventory/delete/<int:item_id>', methods=['POST'])
def delete_inventory_item(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        item = InventoryItem.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {str(e)}', 'danger')
        logging.error(f"Error deleting inventory item: {str(e)}")
    
    return redirect(url_for('inventory'))

@app.route('/suppliers')
def suppliers():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    suppliers = Supplier.query.all()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/suppliers/add', methods=['POST'])
def add_supplier():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        supplier = Supplier(
            name=request.form['name'],
            contact_person=request.form.get('contact_person', ''),
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            address=request.form.get('address', '')
        )
        
        db.session.add(supplier)
        db.session.commit()
        flash('Supplier added successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding supplier: {str(e)}', 'danger')
        logging.error(f"Error adding supplier: {str(e)}")
    
    return redirect(url_for('suppliers'))

@app.route('/suppliers/update/<int:supplier_id>', methods=['POST'])
def update_supplier(supplier_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        supplier.name = request.form['name']
        supplier.contact_person = request.form.get('contact_person', '')
        supplier.email = request.form.get('email', '')
        supplier.phone = request.form.get('phone', '')
        supplier.address = request.form.get('address', '')
        
        db.session.commit()
        flash('Supplier updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating supplier: {str(e)}', 'danger')
        logging.error(f"Error updating supplier: {str(e)}")
    
    return redirect(url_for('suppliers'))

@app.route('/suppliers/delete/<int:supplier_id>', methods=['POST'])
def delete_supplier(supplier_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        supplier = Supplier.query.get_or_404(supplier_id)
        db.session.delete(supplier)
        db.session.commit()
        flash('Supplier deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting supplier: {str(e)}', 'danger')
        logging.error(f"Error deleting supplier: {str(e)}")
    
    return redirect(url_for('suppliers'))

@app.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Inventory summary
    total_items = InventoryItem.query.count()
    total_value = db.session.query(db.func.sum(
        InventoryItem.quantity * InventoryItem.unit_price
    )).scalar() or 0
    
    # Low stock report
    low_stock_items = InventoryItem.query.filter(
        InventoryItem.quantity <= InventoryItem.reorder_point
    ).all()
    
    # Category summary
    category_summary = db.session.query(
        InventoryItem.category,
        db.func.count(InventoryItem.id).label('count'),
        db.func.sum(InventoryItem.quantity * InventoryItem.unit_price).label('value')
    ).group_by(InventoryItem.category).all()
    
    # Recent transactions
    recent_transactions = db.session.query(StockTransaction, InventoryItem.name)\
        .join(InventoryItem)\
        .order_by(StockTransaction.timestamp.desc())\
        .limit(10).all()
    
    return render_template('reports.html',
                         total_items=total_items,
                         total_value=total_value,
                         low_stock_items=low_stock_items,
                         category_summary=category_summary,
                         recent_transactions=recent_transactions)
