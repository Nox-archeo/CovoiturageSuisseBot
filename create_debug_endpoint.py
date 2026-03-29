#!/usr/bin/env python3
"""
Script de debug à exécuter sur Render pour analyser le problème de paiement
Sera ajouté comme endpoint temporaire dans webhook_server.py
"""

async def debug_production_trip_endpoint(request):
    """Endpoint de debug pour analyser le trajet problématique"""
    try:
        from database.database import get_db
        from database.models import Trip, User
        from datetime import datetime, timedelta
        
        db = get_db()
        
        # Chercher les trajets récents
        today = datetime.now()
        two_days_ago = today - timedelta(days=2)
        
        trips = db.query(Trip).filter(
            Trip.departure_time >= two_days_ago
        ).order_by(Trip.id.desc()).limit(20).all()
        
        result = {
            "total_trips": len(trips),
            "trips": []
        }
        
        for trip in trips:
            trip_info = {
                "id": trip.id,
                "departure_city": trip.departure_city,
                "arrival_city": trip.arrival_city,
                "departure_time": str(trip.departure_time),
                "driver_id": trip.driver_id,
                "status": getattr(trip, 'status', 'NONE'),
                "driver_details": None
            }
            
            # Analyser le conducteur
            if trip.driver_id:
                driver = db.query(User).filter(User.id == trip.driver_id).first()
                if driver:
                    trip_info["driver_details"] = {
                        "name": f"{driver.first_name} {driver.last_name}",
                        "paypal_email": driver.paypal_email,
                        "telegram_id": driver.telegram_id
                    }
            
            # Marquer les trajets Posieux/Corpataux
            dep_city = trip.departure_city or ''
            arr_city = trip.arrival_city or ''
            if ('posieux' in dep_city.lower() and 'corpataux' in arr_city.lower()):
                trip_info["is_target_trip"] = True
            
            result["trips"].append(trip_info)
        
        # Retourner en JSON pour debug
        import json
        return {
            "status": 200,
            "body": json.dumps(result, indent=2),
            "headers": {"Content-Type": "application/json"}
        }
        
    except Exception as e:
        return {
            "status": 500,
            "body": f"Erreur: {str(e)}",
            "headers": {"Content-Type": "text/plain"}
        }

# Code pour l'ajouter temporairement à webhook_server.py
debug_endpoint_code = '''
# ENDPOINT DE DEBUG TEMPORAIRE - À SUPPRIMER APRÈS INVESTIGATION
@app.get("/debug-trips")
async def debug_trips_endpoint(request):
    """Endpoint temporaire pour débugger le problème de paiement"""
    try:
        from database.database import get_db
        from database.models import Trip, User
        from datetime import datetime, timedelta
        
        db = get_db()
        
        # Chercher les trajets récents
        today = datetime.now()
        two_days_ago = today - timedelta(days=2)
        
        trips = db.query(Trip).filter(
            Trip.departure_time >= two_days_ago
        ).order_by(Trip.id.desc()).limit(20).all()
        
        html_content = "<h1>DEBUG TRAJETS PRODUCTION</h1>"
        html_content += f"<p>Total trajets récents: {len(trips)}</p>"
        
        for trip in trips:
            html_content += f"<div style='border:1px solid #ccc; margin:10px; padding:10px;'>"
            html_content += f"<h3>TRAJET {trip.id}</h3>"
            html_content += f"<p><b>{trip.departure_city} → {trip.arrival_city}</b></p>"
            html_content += f"<p>Date: {trip.departure_time}</p>"
            html_content += f"<p>Driver ID: {trip.driver_id}</p>"
            html_content += f"<p>Status: {getattr(trip, 'status', 'NONE')}</p>"
            
            # Marquer le trajet cible
            dep_city = trip.departure_city or ''
            arr_city = trip.arrival_city or ''
            if ('posieux' in dep_city.lower() and 'corpataux' in arr_city.lower()):
                html_content += f"<p style='color:red; font-weight:bold;'>🎯 TRAJET CIBLE!</p>"
            
            # Analyser le conducteur
            if trip.driver_id:
                driver = db.query(User).filter(User.id == trip.driver_id).first()
                if driver:
                    html_content += f"<p>🚗 Conducteur: {driver.first_name} {driver.last_name}</p>"
                    html_content += f"<p>📧 PayPal: {driver.paypal_email}</p>"
                else:
                    html_content += f"<p>❌ Driver ID {trip.driver_id} non trouvé</p>"
            else:
                html_content += f"<p>❌ Driver ID est None</p>"
            
            html_content += "</div>"
        
        return Response(html_content, media_type="text/html")
        
    except Exception as e:
        return Response(f"Erreur: {str(e)}", media_type="text/plain")
'''

print("Code pour ajouter l'endpoint de debug à webhook_server.py:")
print("=" * 60)
print(debug_endpoint_code)
