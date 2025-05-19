import json
import time
import random
from kafka import KafkaProducer

# Hàm mô phỏng crawl dữ liệu JSON ngẫu nhiên
def crawl_random_json():
    """
    Sinh một bản ghi JSON giả lập dữ liệu công việc.
    Mỗi lần gọi trả về dict ngẫu nhiên.
    """
    return {
        "job_id": random.randint(1000, 9999),
        "title": random.choice(["Developer", "Tester", "Manager", "Analyst"]),
        "company": random.choice(["ACME", "Globex", "Initech", "Umbrella Corp"]),
        "salary": random.choice(["10-15M", "15-20M", "20-25M"]),
        "timestamp": time.time()
    }

# Cấu hình KafkaProducer
def create_producer(bootstrap_servers):
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

# Vòng lặp crawl và gửi thẳng sang Kafka
def produce_real_time(producer, topic):
    print(f"Starting real-time producer for topic '{topic}'...")
    try:
        while True:
            record = crawl_random_json()
            future = producer.send(topic, value=record)
            metadata = future.get(timeout=10)
            print(f"Sent job_id={record['job_id']} to partition={metadata.partition} offset={metadata.offset}")
            # Không lưu vào file, gửi trực tiếp
            time.sleep(random.uniform(0.1, 1.0))  # thời gian nghỉ ngẫu nhiên
    except KeyboardInterrupt:
        print("Stopping producer...")

if __name__ == '__main__':
    # Thay 'localhost:9092' hoặc 'broker:29092' nếu chạy trong container
    producer = create_producer(['localhost:9092'])
    topic = 'jobs'
    produce_real_time(producer, topic)
    producer.flush()
    producer.close()
 