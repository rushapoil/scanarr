# Déploiement sur Synology NAS

## Prérequis

- DSM 7.x avec **Container Manager** installé
- SSH activé (Panneau de configuration → Terminal & SNMP)
- Au moins **512 MB de RAM disponible** pour le build (ou build sur le PC)
- Docker 20.10+

---

## Méthode recommandée : build sur le PC, déploiement sur le NAS

### 1. Builder l'image sur votre PC Windows

```powershell
cd C:\dev\scanarr

# Build multi-architecture (si vous avez buildx, sinon juste amd64)
docker build -t scanarr:latest .

# Exporter l'image
docker save scanarr:latest | gzip > scanarr.tar.gz
```

### 2. Copier sur le NAS

```powershell
# Via SCP (remplacez l'IP et le chemin)
scp scanarr.tar.gz admin@192.168.1.x:/volume1/docker/
```

### 3. Charger l'image sur le NAS

```bash
# SSH sur le NAS
ssh admin@192.168.1.x

# Charger l'image
docker load < /volume1/docker/scanarr.tar.gz
# → Loaded image: scanarr:latest
```

### 4. Créer les dossiers persistants

```bash
mkdir -p /volume1/docker/scanarr/config
mkdir -p /volume1/manga
```

### 5. Générer le hash du mot de passe

```bash
docker run --rm python:3.12-slim \
  python -c "from passlib.context import CryptContext; \
             print(CryptContext(['bcrypt']).hash('VOTRE_MOT_DE_PASSE'))"
```

Copiez le hash généré (commence par `$2b$`).

### 6. Créer le fichier de configuration

```bash
cat > /volume1/docker/scanarr/docker-compose.yml << 'EOF'
version: "3.9"
services:
  scanarr:
    image: scanarr:latest
    container_name: scanarr
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - /volume1/docker/scanarr/config:/config
      - /volume1/manga:/manga
    environment:
      - CONFIG_DIR=/config
      - DATA_DIR=/manga
      - LOG_LEVEL=info
      - AUTH_REQUIRED=true
      - AUTH_USERNAME=admin
      - AUTH_PASSWORD_HASH=$2b$12$VOTRE_HASH_ICI
      - TZ=Europe/Paris
    mem_limit: 256m
    healthcheck:
      test: ["CMD", "curl", "-sf", "http://localhost:8080/api/v1/system/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
EOF
```

### 7. Démarrer

```bash
cd /volume1/docker/scanarr
docker compose up -d

# Vérifier
docker compose logs -f
```

### 8. Accéder à l'interface

Ouvrez `http://IP_DU_NAS:8080` dans votre navigateur.

---

## Méthode alternative : Container Manager (GUI)

1. Ouvrez **Container Manager** → **Project**
2. Cliquez **Create** → **Upload**
3. Importez `docker-compose.synology.yml`
4. Remplissez `AUTH_PASSWORD_HASH` dans l'éditeur
5. Cliquez **Build** puis **Start**

---

## Configuration post-démarrage

1. **Settings → Prowlarr** : entrez l'URL et l'API key de votre instance Prowlarr
2. **Settings → Prowlarr → Sync Indexers** : importe vos indexeurs
3. **Settings → Download Clients** : ajoutez qBittorrent / SABnzbd
4. **Library → Add Manga** : cherchez et ajoutez vos mangas

---

## Récupérer l'API Key Scanarr

```bash
# Depuis le NAS
curl -u admin:VOTRE_MOT_DE_PASSE \
  http://localhost:8080/api/v1/system/apikey
```

---

## Mise à jour

```powershell
# Sur le PC
docker build -t scanarr:latest .
docker save scanarr:latest | gzip > scanarr.tar.gz
scp scanarr.tar.gz admin@NAS:/volume1/docker/
```

```bash
# Sur le NAS
docker load < /volume1/docker/scanarr.tar.gz
cd /volume1/docker/scanarr
docker compose up -d
```

---

## Volumes et données persistantes

| Volume | Contenu |
|---|---|
| `/config` | `scanarr.db`, `secret.key`, `covers/`, `logs/` |
| `/manga` | Vos fichiers manga téléchargés |

> **Important** : ne supprimez jamais `/config/secret.key` — il chiffre tous vos mots de passe stockés.

---

## Dépannage

```bash
# Voir les logs
docker logs scanarr --tail 50 -f

# Relancer après un crash
docker compose restart

# Accéder à la base de données
docker exec -it scanarr sqlite3 /config/scanarr.db ".tables"

# Vérifier l'API
curl http://IP_NAS:8080/api/v1/system/health
```
