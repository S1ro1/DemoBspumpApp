from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9093',
)

producer.send('sample_input_topic', ('{"name": "new", "value": "7"}').encode('utf-8'))

producer.flush()
