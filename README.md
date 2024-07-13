# news-scraper-pdf

Ce script récupère la dernière édition depuis Europresse au format PDF avec un compte BNF.  
Il vient palier à l'interface d'Europresse non optimisée pour lire facilement un journal.

## Description

Il est nécessaire de posséder un compte BNF pour s'y connecter.  

Le script est développé en python en se basant sur Selenium.  
Différentes options existent pour écrire le fichier PDF dans un dossier spécifique, ou directement dans un répertoire Nextcloud.

## Installation

### Installation via pip (recommandée)

Méthode d'installation simple qui convient à un usage normal.

> [!NOTE]
> Pré-requis :
> * python3
> * pip

Installation depuis pip :
```shell
pip install news-scraper-pdf
```

### Installation localement depuis git 

> [!NOTE]
> Pré-requis :
> * python3
> * pip
> * git
> * virtual env via `pip install virtualenv` (seulement avec un installation depuis git)

1. Ouvrir un terminal.
2. Récupérer le projet. `git clone https://github.com/pressomanic/news-scraper-pdf.git`
3. Se placer dans le répertoire du projet. `cd news-scraper-pdf`
4. Construire le projet avec venv. Recommandé pour tester. [Option 1]
   1. Créer le venv. `python3 -m venv venv`
   2. Se sourcer sur venv. 
      * windows `.\venv\Scripts\Activate.bat`
      * linux `source venv/bin/activate`
   3. Installer les requirements. `pip install -r requiements.txt`
   4. Créer un package pour être disponible directement dans le pip du venv. `pip install -e . ` 
5. Construire directement le projet avec la configuration globale python du système (no venv). [Option 2]
   1. Installer les requirements. `pip install -r requiements.txt`
   2. Créer un package pour être disponible directement dans le pip du venv. `pip install -e . ` 
6. Le package est maintenant disponible localement dans pip. Tester avec `news-scraper-pdf -h` pour afficher l'aide.




## Utilisation

### Squelette
```shell
$ news-scraper-pdf --help                
usage: get_edition.py [-h] [-e ENV] [-f FIRST_PAGES] [-v] [-n NEXTCLOUD_PATH]
                      [-o OUTPUT_PATH]
                      source

positional arguments:
  source                Source of media to find latest publication.

options:
  -h, --help            show this help message and exit
  -e ENV, --env ENV     Specify the file env variables.By default taking file
                        referenced in os variable ENV_NEWS_SCRAPER.
  -f FIRST_PAGES, --first-pages FIRST_PAGES
                        Get the first N pages. Useful to test a newspaper
                        before getting all pages.
  -v, --verbose         Enable verbose mode.
  -n NEXTCLOUD_PATH, --nextcloud-path NEXTCLOUD_PATH
                        Set Nextcloud upload directory path. Need to configure
                        valid connection with --env
  -o OUTPUT_PATH, --output-path OUTPUT_PATH
                        Write file to a specific path.
```

### Chercher un journal
Le script utilise la valeur dans l'argument `source`.  
Il essaye de trouver la meilleure correspondance parmi les journaux disponibles.
Dans les logs du script (output dans la console), le score est affichée par rapport à la `source`.  
Par exemple, si le script est démarré avec `source` égale à `monde`. 
```text
Found better score for "01 net" with score 36.
Found better score for "20 minutes" with score 40.
Found better score for "gourmand" with score 46.
Found better score for "monde campus, le" with score 48.
Found better score for "monde, le" with score 71.
Publication identified for "Monde, Le" from the given input "monde"
```
Le script essaye de trouver la meilleure correspondance, ici `monde` correspond à `monde, le` avec un score de 71.  

Dans le cas où le journal trouvé ne correspond, il faut vérifier la syntaxe saisie et si possible de rajouter des détails (comme "monde, le").

### Configuration du fichier env
Le script a besoin d'avoir la configuration du compte BNF.  
De même, si l'envoie sur nextcloud est activé via l'option `-n`.  
Ces configurations doivent être placées dans un fichier env. Ci-dessous un exemple :
```text
# Mandatory 
BNF_LOGIN="your@email.fr"
BNF_PASSWORD="your-password"

# Optional to use nextcloud
NEXTCLOUD_URL="https://your.private.nextcloud"
NEXTCLOUD_USER="your-nextcloud-user"
NEXTCLOUD_PASSWORD="your-nextcloud-password"
```


## Exemples

### Récupérer l'édition du Monde
```shell
$ news-scraper-pdf -e .env monde
```

### Récupérer l'édition du Monde dans un dossier spécifique
```shell
$ news-scraper-pdf -e .env -o my/specific/folder monde
```

### Récupérer l'édition du Monde pour l'envoyer dans un répertoire Nextcloud
```shell
$ news-scraper-pdf -e .env -n my/specific/nextcloud monde
```

### Récupérer l'édition du Monde avec seulement les 3 premières pages
```shell
$ news-scraper-pdf -e .env -f 3 monde
```

## Liens
* PYPI : https://pypi.org/project/news-scraper-pdf/

## Disclaimer

Ce script utilise les fonctionnalités prévues nativement dans Europresse.  
Il automatise certains "cliques" pour éviter des actions redondantes dans la lecture des journaux.  
Aucun accès illégal à des ressources n'est réalisé. 