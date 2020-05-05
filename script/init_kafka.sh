echo "Suppression des anciens dossiers :\n- /tmp/zookeeper/\n- /tmp/kafka-logs/\n- $KAFKA/checkpoint ..."
sudo rm -rf /tmp/zookeeper/
sudo rm -rf /tmp/kafka-logs/
# A rajouter " si existe" ??  
sudo rm -rf $KAFKA/checkpoint	
echo "Suppression effectuée."

echo "Démarrage du zookeeper sur le port 2181..."
$KAFKA/bin/zookeeper-server-start.sh -daemon $KAFKA/config/zookeeper.properties
echo "Démarrage du zookeeper réussi."
echo "Mode de démarage du zookeeper :"
sleep 1
echo stat | nc localhost 2181 | grep Mode

echo "Démarrage du serveur Kafka sur le port 2181..."
$KAFKA/bin/kafka-server-start.sh -daemon $KAFKA/config/server.properties
sleep 3 #?? 
echo "Démarrage du serveur Kafka réussi."
echo "ID du serveur Kafka :"
$KAFKA/bin/zookeeper-shell.sh localhost:2181 ls /brokers/ids
#Rajouter 'verifier que c'est ok il y a quelque chose'

echo "Création des 2 topics Kafka antennesIntput et antennesOutput..."
$KAFKA/bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic antennesIntput
echo "antennesIntput : OK"
$KAFKA/bin/kafka-topics.sh --create --zookeeper localhost:2181 --replication-factor 1 --partitions 1 --topic antennesOutput
echo "antennesOutput : OK"
echo "Instanciations réussites."
echo "Liste des topics Kafka créés :"
$KAFKA/bin/zookeeper-shell.sh localhost:2181 ls /brokers/topics

echo "L'environnement a été mis en place avec succès !"