#!/usr/bin/env python3
"""
Script pour ajouter un endpoint admin de nettoyage des réservations
"""

# Contenu à ajouter au webhook_server.py
admin_cleanup_endpoint = '''
@app.post("/admin/cleanup-bookings")
async def cleanup_bookings(request: Request):
    """Endpoint pour supprimer toutes les réservations de test"""
    try:
        # Vérification simple de sécurité
        client_ip = request.client.host
        print(f"🔧 Demande de nettoyage depuis IP: {client_ip}")
        
        from database.db_manager import get_db
        from database.models import Booking
        
        db = get_db()
        
        # Compter avant suppression
        total_bookings = db.query(Booking).count()
        print(f"📊 Réservations à supprimer: {total_bookings}")
        
        # Supprimer toutes les réservations
        deleted_count = db.query(Booking).delete()
        db.commit()
        
        print(f"✅ {deleted_count} réservations supprimées!")
        
        return {
            "status": "success", 
            "deleted_count": deleted_count,
            "message": f"{deleted_count} réservations supprimées avec succès"
        }
        
    except Exception as e:
        print(f"❌ Erreur nettoyage: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
'''

print("📋 Voici le code à ajouter au webhook_server.py:")
print(admin_cleanup_endpoint)
print("\n🔧 Je vais l'ajouter automatiquement...")
