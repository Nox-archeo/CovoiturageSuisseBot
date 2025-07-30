#!/usr/bin/env python3
"""
Calcul de faisabilité pour tester TOUTES les communes (741)
"""

import math

def calculate_feasibility():
    """Calcule si on peut tester toutes les communes"""
    
    total_communes = 741
    
    print(f"=== CALCUL DE FAISABILITÉ ===")
    print(f"Nombre total de communes: {total_communes}")
    
    # Calcul du nombre de combinaisons possibles
    # Formule: C(n,2) = n! / (2! * (n-2)!) = n*(n-1)/2
    total_combinations = total_communes * (total_communes - 1) // 2
    print(f"Nombre total de trajets possibles: {total_combinations:,}")
    
    # Limites pratiques
    print(f"\n=== LIMITES PRATIQUES ===")
    
    # Limite API (2000 requêtes/jour selon les headers vus)
    api_limit_per_day = 2000
    print(f"Limite API OpenRouteService: {api_limit_per_day} requêtes/jour")
    
    # Temps par requête (observé: ~0.3-0.5s + pause)
    time_per_request = 0.5  # secondes
    pause_between_requests = 0.3  # pour ne pas surcharger
    total_time_per_request = time_per_request + pause_between_requests
    
    print(f"Temps estimé par requête: {total_time_per_request}s")
    
    # Calculs temporels
    total_time_seconds = total_combinations * total_time_per_request
    total_time_hours = total_time_seconds / 3600
    total_time_days = total_time_hours / 24
    
    print(f"\n=== TEMPS NÉCESSAIRE ===")
    print(f"Temps total: {total_time_seconds:,.0f} secondes")
    print(f"Temps total: {total_time_hours:,.1f} heures")
    print(f"Temps total: {total_time_days:,.1f} jours")
    
    # Nombre de jours nécessaires selon la limite API
    days_needed_api = math.ceil(total_combinations / api_limit_per_day)
    print(f"Jours nécessaires (limite API): {days_needed_api} jours")
    
    # Recommandations
    print(f"\n=== RECOMMANDATIONS ===")
    
    if total_combinations > 50000:
        print("❌ TROP CONSÉQUENT - Test complet impossible")
        
        # Échantillons alternatifs
        samples = [100, 500, 1000, 2000]
        for sample_size in samples:
            if sample_size < total_communes:
                sample_combinations = sample_size * (sample_size - 1) // 2
                sample_days = math.ceil(sample_combinations / api_limit_per_day)
                sample_hours = (sample_combinations * total_time_per_request) / 3600
                
                print(f"📊 Échantillon {sample_size} communes:")
                print(f"   - {sample_combinations:,} trajets")
                print(f"   - {sample_hours:.1f} heures")
                print(f"   - {sample_days} jour(s)")
        
        # Stratégie recommandée
        print(f"\n🎯 STRATÉGIE RECOMMANDÉE:")
        print(f"   - Échantillon stratifié de 200-300 communes")
        print(f"   - Représentant tous les cantons")
        print(f"   - Mix: grandes villes + villages + zones alpines")
        print(f"   - Temps: 2-4 heures max")
        
    else:
        print("✅ FAISABLE - Mais long")
        print(f"Recommandation: Faire par batch de {api_limit_per_day} requêtes/jour")

if __name__ == "__main__":
    calculate_feasibility()
