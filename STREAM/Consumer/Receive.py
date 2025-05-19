import json
from kafka import KafkaConsumer

# Hàm khởi tạo KafkaConsumer
# - auto_offset_reset='earliest': đọc từ đầu nếu chưa có offset
# - enable_auto_commit=True: tự động commit offset sau khi đọc
# - value_deserializer: chuyển bytes JSON về dict Python

def create_consumer(bootstrap_servers, topic, group_id=None):
    consumer = KafkaConsumer(
        topic,
        bootstrap_servers=bootstrap_servers,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id=group_id,
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    return consumer

# Hàm tiêu thụ và xử lý message từ Kafka

def consume_messages(consumer):
    print("Starting Kafka consumer...")
    try:
        for message in consumer:
            data = message.value
            partition = message.partition
            offset = message.offset
            # Hiển thị chi tiết dữ liệu nhận được
            print(f"Received job_id={data.get('job_id')}, title={data.get('title')}, "
                  f"company={data.get('company')}, salary={data.get('salary')}, timestamp={data.get('timestamp')}")
            print(f"Partition: {partition}, Offset: {offset}\n")
    except KeyboardInterrupt:
        print("Stopping consumer...")
    finally:
        consumer.close()

if __name__ == '__main__':
    # Cấu hình Kafka bootstrap server và topic
    bootstrap_servers = ['localhost:9092']  # hoặc ['broker:29092'] trong môi trường container
    topic = 'jobs'
    group_id = 'jobs-consumer-group'

    # Tạo và chạy consumer
    consumer = create_consumer(bootstrap_servers, topic, group_id)
    consume_messages(consumer)
