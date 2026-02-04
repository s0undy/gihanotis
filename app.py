"""
GiHaNotis - Crisis Resource Inventory Management System
A simple Flask application for managing resource requests and responses during crises.
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import os
import logging
from config import Config
from db import get_db_cursor, execute_query, execute_query_one, init_connection_pool
from validation import validate_request_data, validate_response_data, validate_pagination_params, ValidationError

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://"
)

# Initialize database connection pool
init_connection_pool(minconn=2, maxconn=10)

# Configure logging
logging.basicConfig(
    level=logging.INFO if Config.FLASK_ENV == 'production' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    logger.error(f"Configuration error: {e}")
    logger.error("Please ensure .env file is properly configured")


# ============================================================================
# AUTHENTICATION
# ============================================================================

def require_admin(f):
    """
    Decorator to require admin authentication for routes.
    Redirects to login page if not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# ADMIN AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
@csrf.exempt
@limiter.limit("5 per minute")
def api_login():
    """Admin login endpoint - validates credentials and creates session"""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password required'}), 400

    username = data.get('username')
    password = data.get('password')

    # Validate against environment credentials
    if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
        session['is_admin'] = True
        session['username'] = username
        session.permanent = True  # Enable session timeout
        return jsonify({'success': True, 'message': 'Login successful'})
    else:
        return jsonify({'error': 'Invalid username or password'}), 401


@app.route('/api/auth/logout', methods=['POST'])
@csrf.exempt
def api_logout():
    """Admin logout endpoint - clears session"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'})


@app.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    """Check if user is authenticated"""
    return jsonify({
        'authenticated': session.get('is_admin', False),
        'username': session.get('username', None)
    })


# ============================================================================
# ADMIN API ROUTES (CRUD for requests)
# ============================================================================

@app.route('/api/requests', methods=['GET'])
@require_admin
def api_get_requests():
    """Get all requests with response counts (paginated)"""
    try:
        # Parse and validate pagination parameters
        page = request.args.get('page', 1)
        per_page = request.args.get('per_page', 50)

        try:
            page, per_page = validate_pagination_params(page, per_page)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        offset = (page - 1) * per_page

        query = """
            SELECT r.*, COUNT(resp.id) as response_count
            FROM requests r
            LEFT JOIN responses resp ON r.id = resp.request_id
            GROUP BY r.id
            ORDER BY r.created_at DESC
            LIMIT %s OFFSET %s
        """
        requests = execute_query(query, (per_page, offset))

        # Get total count for pagination metadata
        count_query = "SELECT COUNT(*) as total FROM requests"
        total = execute_query_one(count_query)['total']

        return jsonify({
            'success': True,
            'data': requests,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/requests', methods=['POST'])
@csrf.exempt
@require_admin
def api_create_request():
    """Create a new request"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ['item_name', 'quantity_needed', 'unit']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate and sanitize input
        try:
            validate_request_data(data)
        except ValidationError as e:
            logger.warning(f"Validation error in create_request: {e}")
            return jsonify({'error': str(e)}), 400

        # Insert request
        query = """
            INSERT INTO requests (item_name, quantity_needed, unit, description)
            VALUES (%s, %s, %s, %s)
            RETURNING id, item_name, quantity_needed, unit, description, created_at, status
        """
        params = (
            data['item_name'].strip(),
            data['quantity_needed'],
            data['unit'].strip(),
            data.get('description', '').strip() if data.get('description') else ''
        )

        result = execute_query_one(query, params)
        logger.info(f"Request created: ID={result['id']}, item={result['item_name']}, by={session.get('username')}")
        return jsonify({'success': True, 'data': result}), 201

    except Exception as e:
        logger.error(f"Error creating request: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/requests/<int:request_id>', methods=['GET'])
@require_admin
def api_get_request(request_id):
    """Get a single request with all responses"""
    try:
        query = """
            SELECT r.*,
                   json_agg(
                       json_build_object(
                           'id', resp.id,
                           'responder_name', resp.responder_name,
                           'responder_contact', resp.responder_contact,
                           'quantity_available', resp.quantity_available,
                           'location', resp.location,
                           'notes', resp.notes,
                           'accepted', resp.accepted,
                           'created_at', resp.created_at
                       ) ORDER BY resp.created_at DESC
                   ) FILTER (WHERE resp.id IS NOT NULL) as responses
            FROM requests r
            LEFT JOIN responses resp ON r.id = resp.request_id
            WHERE r.id = %s
            GROUP BY r.id
        """
        result = execute_query_one(query, (request_id,))

        if not result:
            return jsonify({'error': 'Request not found'}), 404

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/requests/<int:request_id>', methods=['PUT'])
@csrf.exempt
@require_admin
def api_update_request(request_id):
    """Update a request (e.g., change status to closed)"""
    try:
        data = request.get_json()

        # Check if request exists
        check_query = "SELECT id FROM requests WHERE id = %s"
        existing = execute_query_one(check_query, (request_id,))
        if not existing:
            return jsonify({'error': 'Request not found'}), 404

        # Build update query dynamically based on provided fields
        allowed_fields = ['item_name', 'quantity_needed', 'unit', 'description', 'status']
        update_fields = []
        params = []

        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        params.append(request_id)
        query = f"""
            UPDATE requests
            SET {', '.join(update_fields)}
            WHERE id = %s
            RETURNING id, item_name, quantity_needed, unit, description, status, created_at
        """

        result = execute_query_one(query, params)
        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/requests/<int:request_id>', methods=['DELETE'])
@csrf.exempt
@require_admin
def api_delete_request(request_id):
    """Delete a request"""
    try:
        query = "DELETE FROM requests WHERE id = %s RETURNING id"
        result = execute_query_one(query, (request_id,))

        if not result:
            return jsonify({'error': 'Request not found'}), 404

        return jsonify({'success': True, 'message': 'Request deleted'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ADMIN RESPONSE MANAGEMENT ROUTES
# ============================================================================

@app.route('/api/responses/<int:response_id>/accept', methods=['POST'])
@csrf.exempt
@require_admin
def api_accept_response(response_id):
    """Accept a response and update request quantity accordingly"""
    try:
        # Use a single transaction for both operations
        with get_db_cursor() as cur:
            # Get the response details
            query = """
                SELECT r.id, r.request_id, r.quantity_available, r.accepted,
                       req.quantity_needed
                FROM responses r
                JOIN requests req ON r.request_id = req.id
                WHERE r.id = %s
            """
            cur.execute(query, (response_id,))
            response = cur.fetchone()

            if not response:
                return jsonify({'error': 'Response not found'}), 404

            if response['accepted']:
                return jsonify({'error': 'Response already accepted'}), 400

            # Calculate new quantity needed
            new_quantity = max(0, response['quantity_needed'] - response['quantity_available'])

            # Update response to mark as accepted
            update_response_query = """
                UPDATE responses
                SET accepted = TRUE
                WHERE id = %s
            """
            cur.execute(update_response_query, (response_id,))

            # Update request quantity needed
            update_request_query = """
                UPDATE requests
                SET quantity_needed = %s
                WHERE id = %s
            """
            cur.execute(update_request_query, (new_quantity, response['request_id']))

            # Transaction will auto-commit when context exits successfully

        logger.info(f"Response accepted: ID={response_id}, request_id={response['request_id']}, by={session.get('username')}")
        return jsonify({
            'success': True,
            'message': 'Response accepted',
            'new_quantity_needed': new_quantity
        })

    except Exception as e:
        logger.error(f"Error accepting response: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/responses/<int:response_id>/unaccept', methods=['POST'])
@csrf.exempt
@require_admin
def api_unaccept_response(response_id):
    """Unaccept a response and restore request quantity"""
    try:
        # Use a single transaction for both operations
        with get_db_cursor() as cur:
            # Get the response details
            query = """
                SELECT r.id, r.request_id, r.quantity_available, r.accepted,
                       req.quantity_needed
                FROM responses r
                JOIN requests req ON r.request_id = req.id
                WHERE r.id = %s
            """
            cur.execute(query, (response_id,))
            response = cur.fetchone()

            if not response:
                return jsonify({'error': 'Response not found'}), 404

            if not response['accepted']:
                return jsonify({'error': 'Response is not accepted'}), 400

            # Calculate new quantity needed (add back the quantity)
            new_quantity = response['quantity_needed'] + response['quantity_available']

            # Update response to mark as not accepted
            update_response_query = """
                UPDATE responses
                SET accepted = FALSE
                WHERE id = %s
            """
            cur.execute(update_response_query, (response_id,))

            # Update request quantity needed
            update_request_query = """
                UPDATE requests
                SET quantity_needed = %s
                WHERE id = %s
            """
            cur.execute(update_request_query, (new_quantity, response['request_id']))

            # Transaction will auto-commit when context exits successfully

        logger.info(f"Response unaccepted: ID={response_id}, request_id={response['request_id']}, by={session.get('username')}")
        return jsonify({
            'success': True,
            'message': 'Response unaccepted',
            'new_quantity_needed': new_quantity
        })

    except Exception as e:
        logger.error(f"Error unaccepting response: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# PUBLIC API ROUTES
# ============================================================================

@app.route('/api/public/requests', methods=['GET'])
async def api_get_public_requests():
    """Get all open requests (public endpoint, paginated)"""
    try:
        # Parse and validate pagination parameters
        page = request.args.get('page', 1)
        per_page = request.args.get('per_page', 50)

        try:
            page, per_page = validate_pagination_params(page, per_page)
        except ValidationError as e:
            return jsonify({'error': str(e)}), 400

        offset = (page - 1) * per_page

        query = """
            SELECT id, item_name, quantity_needed, unit, description, created_at
            FROM requests
            WHERE status = 'open'
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        requests = execute_query(query, (per_page, offset))

        # Get total count for pagination metadata
        count_query = "SELECT COUNT(*) as total FROM requests WHERE status = 'open'"
        total = execute_query_one(count_query)['total']

        return jsonify({
            'success': True,
            'data': requests,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/public/requests/<int:request_id>', methods=['GET'])
async def api_get_public_request(request_id):
    """Get a single open request (public endpoint)"""
    try:
        query = """
            SELECT id, item_name, quantity_needed, unit, description, created_at
            FROM requests
            WHERE id = %s AND status = 'open'
        """
        result = execute_query_one(query, (request_id,))

        if not result:
            return jsonify({'error': 'Request not found or closed'}), 404

        return jsonify({'success': True, 'data': result})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/public/requests/<int:request_id>/responses', methods=['POST'])
@csrf.exempt
async def api_create_response(request_id):
    """Submit a response to a request (public endpoint)"""
    try:
        data = request.get_json()

        # Verify request exists and is open
        check_query = "SELECT id FROM requests WHERE id = %s AND status = 'open'"
        existing = execute_query_one(check_query, (request_id,))
        if not existing:
            return jsonify({'error': 'Request not found or closed'}), 404

        # Validate required fields
        required_fields = ['quantity_available', 'location']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Validate and sanitize input
        try:
            validate_response_data(data)
        except ValidationError as e:
            logger.warning(f"Validation error in create_response: {e}")
            return jsonify({'error': str(e)}), 400

        # Insert response
        query = """
            INSERT INTO responses
                (request_id, responder_name, responder_contact, quantity_available, location, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, request_id, responder_name, responder_contact,
                      quantity_available, location, notes, created_at
        """
        params = (
            request_id,
            data.get('responder_name', '').strip() if data.get('responder_name') else None,
            data.get('responder_contact', '').strip() if data.get('responder_contact') else None,
            data['quantity_available'],
            data['location'].strip(),
            data.get('notes', '').strip() if data.get('notes') else None
        )

        result = execute_query_one(query, params)
        logger.info(f"Response created: ID={result['id']}, request_id={request_id}, quantity={result['quantity_available']}")
        return jsonify({'success': True, 'data': result}), 201

    except Exception as e:
        logger.error(f"Error creating response: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ADMIN TEMPLATE ROUTES
# ============================================================================

@app.route('/admin/login')
def admin_login():
    """Admin login page"""
    if session.get('is_admin'):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/login.html')


@app.route('/admin')
@require_admin
def admin_dashboard():
    """Admin dashboard - create requests and view all requests"""
    try:
        # Get all requests with response counts
        query = """
            SELECT r.*, COUNT(resp.id) as response_count
            FROM requests r
            LEFT JOIN responses resp ON r.id = resp.request_id
            GROUP BY r.id
            ORDER BY r.created_at DESC
        """
        requests = execute_query(query)
        return render_template('admin/dashboard.html', requests=requests)

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('admin/dashboard.html', requests=[])


@app.route('/admin/request/<int:request_id>')
@require_admin
def admin_request_detail(request_id):
    """Admin view of single request with all responses"""
    try:
        # Get request with responses
        query = """
            SELECT r.*
            FROM requests r
            WHERE r.id = %s
        """
        req = execute_query_one(query, (request_id,))

        if not req:
            flash('Request not found', 'error')
            return redirect(url_for('admin_dashboard'))

        # Get responses separately
        responses_query = """
            SELECT *
            FROM responses
            WHERE request_id = %s
            ORDER BY created_at DESC
        """
        responses = execute_query(responses_query, (request_id,))

        return render_template('admin/request_detail.html', request=req, responses=responses)

    except Exception as e:
        flash(f'Error loading request: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))


# ============================================================================
# PUBLIC TEMPLATE ROUTES
# ============================================================================

@app.route('/')
def public_index():
    """Public landing page - list all open requests"""
    try:
        query = """
            SELECT id, item_name, quantity_needed, unit, description, created_at
            FROM requests
            WHERE status = 'open'
            ORDER BY created_at DESC
        """
        requests = execute_query(query)
        return render_template('public/index.html', requests=requests)

    except Exception as e:
        flash(f'Error loading requests: {str(e)}', 'error')
        return render_template('public/index.html', requests=[])


@app.route('/respond/<int:request_id>')
def public_respond(request_id):
    """Public response form for a specific request"""
    try:
        query = """
            SELECT id, item_name, quantity_needed, unit, description, created_at
            FROM requests
            WHERE id = %s AND status = 'open'
        """
        req = execute_query_one(query, (request_id,))

        if not req:
            flash('Request not found or closed', 'error')
            return redirect(url_for('public_index'))

        return render_template('public/respond.html', request=req)

    except Exception as e:
        flash(f'Error loading request: {str(e)}', 'error')
        return redirect(url_for('public_index'))


# ============================================================================
# HEALTH CHECK & API DOCUMENTATION
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring and load balancers"""
    try:
        # Simple query to verify database connectivity
        execute_query_one("SELECT 1 as check")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    status = "ok" if db_status == "connected" else "degraded"

    return jsonify({
        'status': status,
        'database': db_status
    }), 200 if status == "ok" else 503


@app.route('/docs')
def api_docs():
    """Scalar API documentation"""
    return render_template('docs.html')


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.is_json:
        return jsonify({'error': 'Not found'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    if request.is_json:
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('500.html'), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("GiHaNotis - Crisis Resource Inventory System")
    print("=" * 60)
    print(f"Environment: {Config.FLASK_ENV}")
    print(f"Debug mode: {Config.DEBUG}")
    print(f"Database: {Config.DB_NAME}@{Config.DB_HOST}")
    print(f"Admin username: {Config.ADMIN_USERNAME}")
    print("=" * 60)
    print("Admin interface: http://localhost:5000/admin")
    print("Public interface: http://localhost:5000/")
    print("=" * 60)

    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)
