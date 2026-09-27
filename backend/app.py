"""
Flask backend for deployment dashboard
Provides API endpoints for querying deployment metadata from DynamoDB
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import boto3
from boto3.dynamodb.conditions import Key
import os
from datetime import datetime
from decimal import Decimal

app = Flask(__name__)

# Configure CORS - allow dashboard origin
allowed_origins = os.environ.get('DASHBOARD_ORIGIN', '*')
if allowed_origins != '*':
    allowed_origins = allowed_origins.split(',')
CORS(app, origins=allowed_origins)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
table_name = os.environ.get('DEPLOYMENT_TABLE', 'deployment-metadata')
table = dynamodb.Table(table_name)


def decimal_default(obj):
    """JSON serializer for Decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError


@app.route('/')
@app.route('/api/deployments')
def get_deployments():
    """
    Get all deployment records from DynamoDB
    Returns JSON with services array and metadata
    """
    try:
        # Scan table for all records
        response = table.scan()
        items = response.get('Items', [])

        # Handle pagination if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))

        # Sort by service name, then environment
        items.sort(key=lambda x: (x.get('service_name', ''), x.get('environment', '')))

        return jsonify({
            'services': items,
            'count': len(items),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

    except Exception as e:
        app.logger.error(f"Error fetching deployments: {str(e)}")
        return jsonify({
            'error': str(e),
            'services': [],
            'count': 0
        }), 500


@app.route('/api/deployments/<service_name>')
def get_service_deployments(service_name):
    """
    Get all deployment records for a specific service across all environments
    """
    try:
        response = table.query(
            KeyConditionExpression=Key('service_name').eq(service_name)
        )
        items = response.get('Items', [])

        return jsonify({
            'service_name': service_name,
            'deployments': items,
            'count': len(items)
        })

    except Exception as e:
        app.logger.error(f"Error fetching service {service_name}: {str(e)}")
        return jsonify({
            'error': str(e),
            'service_name': service_name,
            'deployments': [],
            'count': 0
        }), 500


@app.route('/api/deployments/<service_name>/<environment>')
def get_specific_deployment(service_name, environment):
    """
    Get deployment record for a specific service in a specific environment
    """
    try:
        response = table.get_item(
            Key={
                'service_name': service_name,
                'environment': environment
            }
        )
        item = response.get('Item')

        if item:
            return jsonify({
                'service_name': service_name,
                'environment': environment,
                'deployment': item
            })
        else:
            return jsonify({
                'error': 'Deployment not found',
                'service_name': service_name,
                'environment': environment
            }), 404

    except Exception as e:
        app.logger.error(f"Error fetching {service_name}/{environment}: {str(e)}")
        return jsonify({
            'error': str(e),
            'service_name': service_name,
            'environment': environment
        }), 500


@app.route('/api/environments/<environment>')
def get_environment_deployments(environment):
    """
    Get all deployments for a specific environment using GSI
    """
    try:
        response = table.query(
            IndexName='environment-index',
            KeyConditionExpression=Key('environment').eq(environment)
        )
        items = response.get('Items', [])

        return jsonify({
            'environment': environment,
            'services': items,
            'count': len(items)
        })

    except Exception as e:
        app.logger.error(f"Error fetching environment {environment}: {str(e)}")
        return jsonify({
            'error': str(e),
            'environment': environment,
            'services': [],
            'count': 0
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test DynamoDB connection
        table.table_status
        return jsonify({
            'status': 'healthy',
            'table': table_name,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503


@app.route('/api/stats')
def get_stats():
    """Get deployment statistics"""
    try:
        response = table.scan()
        items = response.get('Items', [])

        # Calculate stats
        stats = {
            'total_services': len(items),
            'by_environment': {},
            'by_status': {},
            'recent_deployments': []
        }

        for item in items:
            env = item.get('environment', 'unknown')
            status = item.get('status', 'unknown')

            stats['by_environment'][env] = stats['by_environment'].get(env, 0) + 1
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

        # Get 5 most recent deployments
        sorted_items = sorted(
            items,
            key=lambda x: x.get('deployed_at', ''),
            reverse=True
        )
        stats['recent_deployments'] = sorted_items[:5]

        return jsonify(stats)

    except Exception as e:
        app.logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
