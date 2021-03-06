# Traitement de données distribuées - ENSAE 2020

* **César Roaldès**  - [Github](https://github.com/CesarRoaldes)
* **Morgane Hoffmann**  - [Github](https://github.com/cerezamo)


Ce projet est réalisé dans le cadre du cours Traitement de données distribuées enseigné par Antoine Ly et développé sous l'OS Ubuntu 18.04 LTS.

## Introduction 

Le projet a pour but de répliquer un pipeline de données mobiles en temps réels. L'architecture construite est représentée ci dessous : 

![image](https://github.com/cerezamo/mobile_data/blob/master/images/schema.PNG)

Imaginons que nous recevons des données en provenance des différentes antennes d'une ville. Elles nous renseignent chacune sur la position des téléphones mobiles et donc des individus présents. Nous simulons la réception de ces données en temps réels à partir des données d'un [simulateur](https://github.com/bogdanoancea/simulator) en les envoyant séquentiellement dans un topic Kafka. Elles sont ensuite consommées puis retraitées dans un script PySpark qui les renvoit vers un second topic Kafka. Une collection MongoDB est mise à jour à la réception des messages envoyés par ce second topic Kafka. Enfin les données sont récupérées par Flask qui présente dans une application web, les déplacements en temps réel des individus dans un graphique dynamique. 


Nous avons construit, dans un premier temps une architecture n'incluant pas MongoDB. L'architecture incluant MongoDB est en cours de réalisation. 


## Getting Started - Prérequis

Nous supposons que Python, Spark ainsi qu'un environnement Pyspark sont installés sur votre ordinateur. Si ce n'est pas le cas veuillez vous référer aux instructions qui figurent sur ce [GitLab](https://gitlab.com/AntoineLy/ensae_distributedcomputing/-/tree/master/TDs/Installation).

Si vous voulez être en mesure de faire vous-mêmes vos propres simulations, suivez cette première partie. Sinon, il vous suffit de cloner notre repo et d'utiliser les fichiers que nous avons simulé, dans ce cas passez à la partie suivant : **Déploiement de Kafka et MongoDB**.

### Installer le micro-simulateur et simuler des données 

#### Installation 

Avant toute chose, il faudra s'assurer d'installer la bibliothèque GEOS C++, elle peut être télécharger à l'adresse suivante :  https://trac.osgeo.org/geos (ATTENTION seule la version 3.7.1 est compatible !! )

Déployez la avec le code suivant : 

```
$ ./configure
$ make
$ make install
```
L'installation peut prendre quelques minutes. 


Pour installer le simulateur, télécharger le code source de la repository github : https://github.com/bogdanoancea/simulator 

```
$git clone https://github.com/bogdanoancea/simulator.git
```

Lorsque le répertoire est téléchargé, ouvrez le fichier *makefile.inc* avec l'éditeur de texte de votre choix et modifiez les variables PROJ_HOME et GEOS_HOME. PROJ_HOME doit pointer sur le fichier où vous avez téléchargé le code source du micro-simulateur alors que GEOS_HOME doit pointer sur le fichier du code source de GEOS. Dans notre implémentation nous avons par exemple : 


```
PROJ_HOME = /home/user/simulator
GEOS_HOME = /home/user/geos-3.7.1
```

Avant de passer à l'installation du simulateur, assurez-vous de copier le fichier *geos-3.7.1/src/.libs/libgeos.a* dans le dossier racine de GEOS. Pour celà, placer vous dans le dossier racine *geos-3.7.1/* puis exécuter la commande :

```
cp ./src/.libs/libgeos.a ./libgeos.a
```

Revenir dans le dossier racine du simulateur *simulator/* et procéder à l'installation avec les commandes :

```
make 
make install
```

Le simulateur est installé ! 

**Ces instructions sont valables pour Ubuntu 18.04 LTS, pour plus d'informations sur l'installation du simulateur sur les différents OS, veuillez vous référer aux instructions de https://github.com/bogdanoancea/simulator**

#### Simuler des données avec le micro-simulateur 

Avant de simuler les données allez regarder les inputs possibles (nombre d'antennes, d'individus, map, etc ...), les fichiers inputs se trouvent dans *data/* (notre simulation utilise la dataset2 ou simulation Madrid). Lorsque vous avez choisis l'ensemble de vos paramètres et avez modifié en conséquences les fichiers inputs ouvrez votre terminal, allez dans le dossier *simulator/* et tapez le code suivant (bien entendu si vous choisissez la dataset 1, ce code est sujet à modifications) : 

```
$Release/simulator -m ./data/dataset2/mapMadrid.wkt -s ./data/dataset2/simulation.xml -a ./data/dataset2/antennasMadrid.xml -p ./data/dataset2/persons.xml -pb ./data/dataset2/probabilities.xml -v -o
```

Les fichiers ont été simulé ! 


#### Préparation des données 

Vous pouvez à présent cloner notre repository : https://github.com/cerezamo/mobile_data. 
```
$ git clone https://github.com/cerezamo/mobile_data

```

Venez remplacer le dossier madrid_sim par les données que vous avez générées. 

Certains retraitements ont été effectué afin de simuler les envois des antennes vers Kafka et afficher les fonds de cartes dans le graphique. Pour les reproduire il vous suffit de vous placer dans le dossier app et de lancer le script *pretraitement.py*. Ce script vous permet alors de créer un fond de carte *antennes.json* à partir des données simulées, il est enregistré dans le dossier *app/static*. De plus, les données associées à chaque antenne sont groupées en un seul csv qui est enregistré sous le nom *kafka_ingestion.csv* et servira à simuler l'envoi en temps réel de données à Kafka. 



### Déploiement de Kafka et MongoDB

La suite des instructions est à présent obligatoire pour être en mesure de faire tourner le code. Si vous avez décidé d'utiliser notre simulation démarrez ici. 

Si ce n'est pas déjà fait obtenez notre repo avec le code suivant : 
```
$ git clone https://github.com/cerezamo/mobile_data

```

#### Kafka

Le code ci dessous permettra d'installer Kafka, dans le fichier que vous souhaitez : 

```

#Kafka 2.2.0 installation
curl https://www-us.apache.org/dist/kafka/2.2.0/kafka_2.12-2.2.0.tgz -o kafka_2.12-2.2.0.tgz
tar xzf kafka_2.12-2.2.0.tgz
ln -sf kafka_2.12-2.2.0 kafka

```


#### Mongo

Il faut maintenant installer MongoDB. 
```
sudo apt update
sudo apt install -y mongodb
```


## Running 

La première étape consiste à créer une variable d'environnement *KAFKA* pointant vers le fichier dans lequel est installé Kafka : 

```
$ export KAFKA path/to/kafka_folder 
```

Dans votre environnement pyspark, installez les dépendances nécessaires : 

```
$ conda install flask jinja2 pymongo flask_pymongo pykafka plotly pandas numpy 

```

Si une dépendance venait à manquer veuillz vous référer au fichier *requirements.yml* qui liste l'ensemble des packages que nous avons utilisé ainsi que leur version. 


Placez vous à la racine du répertoire mobile_data. Pour rendre les scripts *main.sh* et *main_mongo.sh* exécutables, effectuez la commande suivante : 
```
$ sudo chmod +x main.sh 
$ sudo chmod +x main_mongo.sh 

```

Il n'y a plus qu'à lancer le script : 

```
$ ./main.sh

```


Comme évoqué dans l'introduction, la version *main_mongo.sh* est en cours de réalisation car le graphique produit des résultats statiques pour le moment. 












