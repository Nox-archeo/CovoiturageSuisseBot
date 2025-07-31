# 🔧 Configuration stockage persistant sur Render

## ⚠️ PROBLÈME ACTUEL
Vos profils sont supprimés à chaque redéploiement car Render utilise un système de fichiers **éphémère**.

## ✅ SOLUTION : PostgreSQL persistant

### 1. **Créer base PostgreSQL sur Render**

1. **Dashboard Render** → **"New +"** → **"PostgreSQL"**
2. Configuration :
   - **Name** : `covoiturage-suisse-db`
   - **Database Name** : `covoiturage`
   - **User** : `covoiturage_user`
   - **Plan** : **Free** (95MB)
3. **Créer**

### 2. **Connecter à votre service web**

1. **Service Web** → **Settings** → **Environment**
2. Render ajoutera automatiquement `DATABASE_URL`
3. Si pas automatique, l'ajouter :
   ```
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

### 3. **Redéployer le bot**

1. **Cliquez "Deploy Latest Commit"**
2. Le bot détectera automatiquement PostgreSQL
3. **Vos données seront maintenant persistantes !**

## 🎯 Résultat

✅ **AVANT** : Profil supprimé à chaque redéploiement  
✅ **APRÈS** : Profil conservé en permanence

## 🔍 Vérification

Dans les logs Render, vous verrez :
```
🚀 Utilisation PostgreSQL pour production
✅ Base de données initialisée avec succès
```

Au lieu de :
```
🏠 Utilisation SQLite pour développement local
```

## 🚨 URGENT

**Faites cette configuration MAINTENANT** pour éviter de perdre vos données à chaque redéploiement !
